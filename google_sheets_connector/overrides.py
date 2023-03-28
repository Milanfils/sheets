import frappe

import google_sheets_connector


def has_permission(doc, ptype, user):
    if (
        doc.attached_to_doctype == doc.attached_to_name == google_sheets_connector.SHEETS_SETTINGS
    ) and (doc.attached_to_field == google_sheets_connector.SHEETS_CREDENTIAL_FIELD):
        raise frappe.PermissionError("Not allowed to access")


def update_record_patch(self, doc):
    from frappe import _
    from frappe.core.doctype.data_import.importer import get_diff, get_id_field

    id_field = get_id_field(self.doctype)
    unique_field = None

    # if no id field is set, try to find a unique field
    if not doc.get(id_field.fieldname):
        unique_fields = [df for df in frappe.get_meta(self.doctype).fields if df.unique]
        for field in unique_fields:
            if doc.get(field.fieldname):
                unique_field = field
                break

    if unique_field:
        existing_doc = frappe.get_doc(
            self.doctype, {unique_field.fieldname: doc.get(unique_field.fieldname)}
        )
        updated_doc = frappe.get_doc(
            self.doctype, {unique_field.fieldname: doc.get(unique_field.fieldname)}
        )
    else:
        existing_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))
        updated_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))

    updated_doc.update(doc)

    if get_diff(existing_doc, updated_doc):
        # update doc if there are changes
        updated_doc.flags.updater_reference = {
            "doctype": self.data_import.doctype,
            "docname": self.data_import.name,
            "label": _("via Data Import"),
        }
        updated_doc.save()
        return updated_doc
    return existing_doc
