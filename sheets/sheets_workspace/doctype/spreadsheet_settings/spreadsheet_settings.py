# Copyright (c) 2023, Gavin D'souza and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from sheets.billing import clear_cache


class SpreadSheetSettings(Document):
    def on_change(self):
        clear_cache()
