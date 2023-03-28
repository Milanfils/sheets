# Copyright (c) 2023, Gavin D'souza and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from google_sheets_connector.constants import INSERT, UPSERT


class DocTypeWorksheetMapping(Document):
    def get_import_type(self):
        match self.import_type:
            case "Insert":
                return INSERT
            case "Upsert":
                return UPSERT
            case _:
                raise ValueError("Invalid import type")
