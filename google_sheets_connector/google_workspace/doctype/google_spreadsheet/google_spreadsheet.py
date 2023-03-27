# Copyright (c) 2023, Gavin D'souza and contributors
# For license information, please see license.txt

from csv import writer as csv_writer
from io import StringIO
from typing import TYPE_CHECKING

import frappe
import gspread as gs
from croniter import croniter
from frappe.model.document import Document

import google_sheets_connector
from google_sheets_connector.api import get_all_frequency, get_description

if TYPE_CHECKING:
    from frappe.core.doctype.data_import.data_import import DataImport
    from frappe.core.doctype.file import File

    from google_sheets_connector.google_workspace.doctype.doctype_worksheet_mapping.doctype_worksheet_mapping import (
    	DocTypeWorksheetMapping,
    )


UPSERT = "Update Existing Records or Insert New Records"


class GoogleSpreadSheet(Document):
    @property
    def frequency_description(self):
        match self.import_frequency:
            case None | "":
                return
            case "Custom":
                return get_description(self.frequency_cron)
            case "Frequently":
                return get_description(f"0/{get_all_frequency()} * * * *")
            case _:
                return get_description(self.import_frequency)

    def get_sheet_client(self):
        if not hasattr(self, "_gc"):
            file: "File" = frappe.get_doc(
                "File",
                {
                    "attached_to_doctype": google_sheets_connector.SHEETS_SETTINGS,
                    "attached_to_name": google_sheets_connector.SHEETS_SETTINGS,
                    "attached_to_field": google_sheets_connector.SHEETS_CREDENTIAL_FIELD,
                },
            )
            self._gc = gs.service_account(file.get_full_path())
        return self._gc

    def validate(self):
        # validate sheet access
        sheet_client = self.get_sheet_client()

        try:
            sheet = sheet_client.open_by_url(self.sheet_url)
        except gs.exceptions.APIError as e:
            frappe.throw(
                f"Share spreadsheet with the following Service Account Email and try again: <b>{sheet_client.auth.service_account_email}</b>",
                exc=e,
            )

        worksheet_ids = [str(w.id) for w in sheet.worksheets()]

        # set sheet name
        self.sheet_name = self.sheet_name or sheet.title

        # set worksheet IDs
        if "gid=" in self.sheet_url:
            self.sheet_url, gid = self.sheet_url.split("gid=", 1)
            if gid not in worksheet_ids:
                frappe.throw(f"Invalid Worksheet ID {gid}")
            if not self.get("worksheet_ids", {"worksheet_id": gid}):
                self.append(
                    "worksheet_ids",
                    {
                        "worksheet_id": gid,
                    },
                )
        elif not self.get("worksheet_ids"):
            self.extend("worksheet_ids", [{"worksheet_id": gid} for gid in worksheet_ids])

        # validate cron pattern
        if self.frequency_cron and self.import_frequency == "Custom":
            croniter(self.frequency_cron)

    def fetch_entire_worksheet(self, worksheet_id: int):
        spreadsheet = self.get_sheet_client().open_by_url(self.sheet_url)
        worksheet = spreadsheet.get_worksheet_by_id(worksheet_id)

        buffer = StringIO()
        csv_writer(buffer).writerows(worksheet.get_all_values())
        return buffer.getvalue()

    def get_prepared_sheet(self, worksheet_id: int, counter: int = 0) -> str:
        full_sheet_content = self.fetch_entire_worksheet(worksheet_id=worksheet_id)

        if counter:
            full_sheet_lines = full_sheet_content.splitlines()
            return "\n".join(full_sheet_lines[:1] + full_sheet_lines[counter:])
        return full_sheet_content

    @frappe.whitelist()
    def trigger_import(self):
        for worksheet in self.worksheet_ids:
            self.import_work_sheet(worksheet)
        self.save()

    def import_work_sheet(self, worksheet: "DocTypeWorksheetMapping"):
        if worksheet.last_import:
            data_import = frappe.get_doc("Data Import", worksheet.last_import)

            if (data_import.status == "Success") or (data_import.status == "Partial Success"):
                if worksheet.reset_worksheet_on_import:
                    raise NotImplementedError
                    spreadsheet = self.get_sheet_client().open_by_url(self.sheet_url)
                    worksheet = spreadsheet.get_worksheet_by_id(worksheet.worksheet_id)
                    worksheet.delete_rows(2, worksheet.counter - 1)
                    worksheet.counter = 0

            else:
                return

        if worksheet.reset_worksheet_on_import:
            data = self.get_prepared_sheet(worksheet_id=worksheet.worksheet_id)
        else:
            data = self.get_prepared_sheet(
                worksheet_id=worksheet.worksheet_id, counter=worksheet.counter
            )

        # length includes header row
        if (counter := len(data.splitlines())) > 1:
            di = self.create_data_import(data, worksheet)
            di.start_import()
            worksheet.last_import = di.name
            worksheet.counter = (worksheet.counter or 1) + (counter - 1)  # subtract header row

        return worksheet.save()

    def create_data_import(self, data: str, worksheet: "DocTypeWorksheetMapping") -> "DataImport":
        data_import = frappe.new_doc("Data Import")
        data_import.update(
            {
                "reference_doctype": worksheet.mapped_doctype,
                "import_type": "Insert New Records"
                if worksheet.import_type == "Insert"
                else "Update Existing Records",
                "mute_emails": 1,
            }
        )
        data_import.save()

        import_file = frappe.new_doc("File")
        import_file.update(
            {
                "attached_to_doctype": data_import.doctype,
                "attached_to_name": data_import.name,
                "attached_to_field": "import_file",
                "file_name": self.get_import_file_name(worksheet_id=worksheet.worksheet_id),
                "is_private": 1,
            }
        )
        import_file.content = data.encode("utf-8")
        import_file.save()

        data_import.import_file = import_file.file_url
        return data_import.save()

    def get_import_file_name(self, worksheet_id: int):
        return f"{self.sheet_name}-worksheet-{worksheet_id}-{frappe.generate_hash(length=6)}.csv"
