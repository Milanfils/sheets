from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def create_data_import_fields():
    create_custom_field(
        "Data Import",
        {
            "fieldname": "google_spreadsheet_id",
            "label": "Google SpreadSheet ID",
            "fieldtype": "Link",
            "options": "Google SpreadSheet",
            "insert_after": "import_file",
            "read_only": 1,
        },
    )
    create_custom_field(
        "Data Import",
        {
            "fieldname": "google_worksheet_id",
            "label": "Google Worksheet ID",
            "fieldtype": "Link",
            "options": "DocType Worksheet Mapping",
            "insert_after": "google_spreadsheet_id",
            "hidden": 1,
        },
    )


def after_install():
    create_data_import_fields()
