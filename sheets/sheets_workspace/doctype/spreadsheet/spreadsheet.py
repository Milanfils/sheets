# Copyright (c) 2023, Gavin D'souza and contributors
# For license information, please see license.txt

from contextlib import contextmanager
from csv import reader as csv_reader
from csv import writer as csv_writer
from difflib import SequenceMatcher
from io import StringIO
from typing import TYPE_CHECKING

import frappe
import gspread as gs
from croniter import croniter
from frappe.core.doctype.data_import.importer import get_autoname_field
from frappe.model.document import Document
from frappe.utils import get_link_to_form

import sheets
from sheets.api import describe_cron, get_all_frequency
from sheets.constants import INSERT, UPDATE, UPSERT
from sheets.overrides import update_record_patch

if TYPE_CHECKING:
    from frappe.core.doctype.data_import.data_import import DataImport
    from frappe.core.doctype.file import File

    from sheets.sheets_workspace.doctype.doctype_worksheet_mapping.doctype_worksheet_mapping import (
        DocTypeWorksheetMapping,
    )


class SpreadSheet(Document):
    @property
    def frequency_description(self):
        match self.import_frequency:
            case None | "":
                return
            case "Custom":
                return describe_cron(self.frequency_cron)
            case "Frequently":
                return describe_cron(f"0/{get_all_frequency()} * * * *")
            case _:
                return describe_cron(self.import_frequency)

    def get_sheet_client(self):
        if not hasattr(self, "_gc"):
            file: "File" = frappe.get_doc(
                "File",
                {
                    "attached_to_doctype": sheets.SHEETS_SETTINGS,
                    "attached_to_name": sheets.SHEETS_SETTINGS,
                    "attached_to_field": sheets.SHEETS_CREDENTIAL_FIELD,
                },
            )
            self._gc = gs.service_account(file.get_full_path())
        return self._gc

    def validate(self):
        self.validate_base_settings()
        self.validate_sync_settings()
        self.validate_sheet_access()

    def validate_base_settings(self):
        # validate sheet url uniqueness
        if another_exists := frappe.get_all(
            self.doctype,
            filters={"sheet_url": self.sheet_url, "name": ("!=", self.name)},
            limit=1,
            pluck="name",
        ):
            frappe.throw(
                f"Sheet URL must be unique. Another sheet exists with the same URL: {get_link_to_form(self.doctype, another_exists[0])}",
                title="Sheet URL must be unique",
            )

    def validate_sync_settings(self):
        # validate cron pattern
        if self.frequency_cron and self.import_frequency == "Custom":
            croniter(self.frequency_cron)

        # setup server script
        if self.has_value_changed("import_frequency") or self.has_value_changed("frequency_cron"):
            script_name = f"SpreadSheet Import - {self.sheet_name}"

            if self.import_frequency == "Custom":
                event_frequency = "Cron"
            elif self.import_frequency == "Frequently":
                event_frequency = "All"
            else:
                event_frequency = self.import_frequency

            if not self.server_script:
                script = frappe.new_doc("Server Script").update(
                    {
                        "__newname": script_name,
                        "script_type": "Scheduler Event",
                        "script": f"frappe.get_doc('SpreadSheet', '{self.name}').trigger_import()",
                        "event_frequency": event_frequency,
                        "cron_format": self.frequency_cron,
                    }
                )

            else:
                script = frappe.get_doc("Server Script", self.server_script).update(
                    {
                        "event_frequency": event_frequency,
                        "cron_format": self.frequency_cron,
                    }
                )

            script.disabled = not self.import_frequency
            script.save()
            self.server_script = script.name

    def validate_sheet_access(self):
        sheet_client = self.get_sheet_client()

        try:
            sheet = sheet_client.open_by_url(self.sheet_url)
        except gs.exceptions.APIError as e:
            frappe.throw(
                f"Share spreadsheet with the following Service Account Email and try again: <b>{sheet_client.auth.service_account_email}</b>",
                exc=e,
            )
        self.set_sheet_metadata(sheet)

    def set_sheet_metadata(self, sheet: "gs.Spreadsheet"):
        # set sheet name if not set
        self.sheet_name = self.sheet_name or sheet.title

        # set & validate worksheet ids
        worksheet_ids = [str(w.id) for w in sheet.worksheets()]
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

        # set default counter for worksheets
        for worksheet in self.worksheet_ids:
            worksheet.counter = worksheet.counter or 1

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
        with patch_importer():
            for worksheet in self.worksheet_ids:
                self.import_work_sheet(worksheet)
            self.save()
        frappe.msgprint("Import Triggered Successfully", indicator="blue", alert=True)
        return self

    def get_id_field_for_upsert(self, worksheet: "DocTypeWorksheetMapping") -> str:
        worksheet_gdoc = (
            self.get_sheet_client()
            .open_by_url(self.sheet_url)
            .get_worksheet_by_id(worksheet.worksheet_id)
        )
        header_row = worksheet_gdoc.row_values(1)

        if "ID" in header_row:
            return "ID"

        autoname_field = get_autoname_field(worksheet.mapped_doctype)
        if autoname_field and autoname_field.label in header_row:
            return autoname_field.label

        dt = frappe.get_meta(worksheet.mapped_doctype)
        unique_fields = [df.label for df in dt.fields if df.unique]

        for field in unique_fields:
            if field in header_row:
                return field

        # Note: Should we provide a `worksheet.id_field` field to allow users to specify the ID field?
        frappe.throw(f"Could not find ID or Unique field in {worksheet.doctype}")

    def import_work_sheet(self, worksheet: "DocTypeWorksheetMapping"):
        if worksheet.get_import_type() == UPSERT:
            self.upsert_worksheet(worksheet)
        else:
            self.insert_worksheet(worksheet)

    def upsert_worksheet(self, worksheet: "DocTypeWorksheetMapping"):
        id_field = self.get_id_field_for_upsert(worksheet)  # required for upsert

        successful_insert_imports = frappe.get_all(
            "Data Import",
            filters={
                "spreadsheet_id": self.name,
                "worksheet_id": worksheet.name,
                "import_type": INSERT,
                "status": ("in", ["Success", "Partial Success"]),
            },
            fields=["name", "import_file"],
            order_by="creation",
        )

        if not successful_insert_imports:
            frappe.msgprint(
                "No successful inserts found to continue UPSERT. Falling back to INSERT instead.",
                alert=True,
                indicator="orange",
            )
            return self.insert_worksheet(worksheet)

        successful_update_imports = frappe.get_all(
            "Data Import",
            filters={
                "spreadsheet_id": self.name,
                "worksheet_id": worksheet.name,
                "import_type": UPDATE,
                "status": ("in", ["Success", "Partial Success"]),
            },
            fields=["name", "import_file"],
            order_by="creation",
        )
        update_csv_geneator = (
            frappe.get_doc("File", {"file_url": x.import_file}).get_content()
            for x in successful_update_imports
        )

        csv_geneator = (
            frappe.get_doc("File", {"file_url": x.import_file}).get_content()
            for x in successful_insert_imports
        )

        data_imported_csv = ""
        for csv_file in csv_geneator:  # order of imports (first to last)
            if not data_imported_csv:
                data_imported_csv = csv_file
            else:
                data_imported_csv += "\n" + csv_file.split("\n", 1)[-1]

        data_imported_csv_file = list(csv_reader(StringIO(data_imported_csv)))
        data_imported_csv_file_header = data_imported_csv_file[0]
        id_field_imported_index = data_imported_csv_file_header.index(id_field)

        # apply updates to the data imported
        for csv_file in update_csv_geneator:
            update_csv_reader = csv_reader(StringIO(csv_file))

            header_row = next(update_csv_reader)
            id_field_index = header_row.index(id_field)

            for update_row in update_csv_reader:
                for idx, data_row in enumerate(data_imported_csv_file):
                    if update_row[id_field_index] == data_row[id_field_imported_index]:
                        data_imported_csv_file[idx] = update_row

        # Hack! use csv module to convert list to csv later
        data_imported_csv = [",".join(x) for x in data_imported_csv_file]

        equivalent_spreadsheet_csv = self.fetch_entire_worksheet(
            worksheet_id=worksheet.worksheet_id
        ).splitlines()[: worksheet.counter]

        diff_opcodes = SequenceMatcher(
            None, data_imported_csv, equivalent_spreadsheet_csv
        ).get_grouped_opcodes(0)
        diff_slices = [y[3:5] for y in [x[1] for x in diff_opcodes]]

        updated_data = data_imported_csv[:1] + [
            item
            for sublist in [equivalent_spreadsheet_csv[slice(*x)] for x in diff_slices]
            for item in sublist
        ]

        if len(updated_data) > 1:
            updated_data_csv = "\n".join(updated_data)
            di = self.create_data_import(updated_data_csv, worksheet, update=True)
            di.start_import()
            worksheet.last_update_import = di.name
            worksheet.save()
        else:
            frappe.msgprint(
                "No updates found to continue UPSERT. Falling back to INSERT instead.",
                alert=True,
                indicator="orange",
            )

        return self.insert_worksheet(worksheet)

    def insert_worksheet(self, worksheet: "DocTypeWorksheetMapping"):
        if worksheet.last_import:
            data_import_status = frappe.db.get_value(
                "Data Import", worksheet.last_import, "status"
            )

            if data_import_status in ("Success", "Partial Success"):
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
            frappe.enqueue_doc(
                di.doctype, di.name, method="start_import", enqueue_after_commit=True
            )
            worksheet.last_import = di.name
            worksheet.counter = (worksheet.counter or 1) + (counter - 1)  # subtract header row
        else:
            frappe.msgprint("No data found to import.", alert=True, indicator="orange")

        return worksheet.save()

    def create_data_import(
        self, data: str, worksheet: "DocTypeWorksheetMapping", update: bool = False
    ) -> "DataImport":
        data_import = frappe.new_doc("Data Import")
        data_import.update(
            {
                "reference_doctype": worksheet.mapped_doctype,
                "import_type": UPDATE if update else INSERT,
                "mute_emails": worksheet.mute_emails,
                "submit_after_import": worksheet.submit_after_import,
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

        data_import.spreadsheet_id = self.name
        data_import.worksheet_id = worksheet.name
        data_import.import_file = import_file.file_url

        return data_import.save()

    def get_import_file_name(self, worksheet_id: int):
        return f"{self.sheet_name}-worksheet-{worksheet_id}-{frappe.generate_hash(length=6)}.csv"


@contextmanager
def patch_importer():
    from frappe.core.doctype.data_import.importer import Importer

    _official_method = Importer.update_record
    Importer.update_record = update_record_patch
    Importer.patched = True
    yield
    Importer.update_record = _official_method
    del Importer.patched
