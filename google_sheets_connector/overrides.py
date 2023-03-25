import frappe

import google_sheets_connector


def has_permission(doc, ptype, user):
    if (
        doc.attached_to_doctype == doc.attached_to_name == google_sheets_connector.SHEETS_SETTINGS
    ) and (doc.attached_to_field == google_sheets_connector.SHEETS_CREDENTIAL_FIELD):
        raise frappe.PermissionError("Not allowed to access")
