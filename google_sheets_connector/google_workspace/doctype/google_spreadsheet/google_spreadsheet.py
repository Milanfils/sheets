# Copyright (c) 2023, Gavin D'souza and contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

import frappe
import gspread as gs
from frappe.model.document import Document

import google_sheets_connector

if TYPE_CHECKING:
    from frappe.core.doctype.file import File


class GoogleSpreadSheet(Document):
    def validate(self):
        # validate sheet access
        file: "File" = frappe.get_doc(
            "File",
            {
                "attached_to_doctype": google_sheets_connector.SHEETS_SETTINGS,
                "attached_to_name": google_sheets_connector.SHEETS_SETTINGS,
                "attached_to_field": google_sheets_connector.SHEETS_CREDENTIAL_FIELD,
            },
        )
        gc = gs.service_account(file.get_full_path())

        try:
            sheet = gc.open_by_url(self.sheet_url)
        except gs.exceptions.APIError as e:
            frappe.throw(
                f"Share spreadsheet with the following Service Account Email and try again: <b style='cursor: copy;'>{gc.auth.service_account_email}</b>",
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
