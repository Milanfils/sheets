// Copyright (c) 2023, Gavin D'souza and contributors
// For license information, please see license.txt

frappe.provide("gsc");

const color = {
    success: "green",
    failure: "red",
}

frappe.ui.form.on("Google SpreadSheet", {
    onload(frm) {
        (!gsc.all_frequency) && frappe.xcall("google_sheets_connector.api.get_all_frequency").then(value_in_minutes => {
            gsc.all_frequency = value_in_minutes;
        });
    },
    import_frequency(frm) {
        if (!frm.doc.import_frequency) {
            frm.set_value("frequency_description", null);
        } else if (frm.doc.import_frequency === "Frequently") {
            frm.set_value("frequency_description", `Every ${gsc.all_frequency} Minutes`);
        } else if (frm.doc.import_frequency === "Custom") {
            if (frm.doc.frequency_cron && frm.doc.frequency_cron.split(" ").length >= 5) {
                frappe.xcall("google_sheets_connector.api.describe_cron", {"cron": frm.doc.frequency_cron }).then(message => {
                    frm.set_value("frequency_description", message);
                });
            } else {
                frm.set_value("frequency_description", null);
            }
        } else {
            frappe.xcall("google_sheets_connector.api.describe_cron", {"cron": frm.doc.import_frequency }).then(message => {
                frm.set_value("frequency_description", message);
            });
        }
    },
    frequency_cron(frm) {
        frm.trigger("import_frequency");
    },
    refresh(frm) {
        // workaround for highlighting status - frm.set_indicator_formatter didn't work?
        frm.fields_dict.worksheet_ids.grid.grid_rows.forEach((row, idx) => {
            const child = frm.doc.worksheet_ids[idx];
            const status_field = $(row.columns.mapped_doctype);

            if (child.skip_failures) {
                status_field.addClass(`indicator ${color.success}`);
            } else {
                frappe.db.get_value("Data Import", child.last_import, "status", ({status}) => {
                    status_field.addClass(`indicator ${status === "Success" ? color.success : color.failure}`);
                });
            }
        });

        frm.add_custom_button("Trigger Import", () => {
            frm.call("trigger_import").then(r => {
                frappe.show_alert({message: "Import Triggered", indicator: "green"}, 10);
            });
        });
    }
});

frappe.ui.form.on("DocType Worksheet Mapping", {
    reset_worksheet_on_import(frm, cdt, cdn) {
        let child_doc = locals[cdt][cdn];
        let mapped_doctype = child_doc.mapped_doctype;
        let to_enable = child_doc.reset_worksheet_on_import;

        let confirm_message = to_enable ?
            `Enabling this means all imported ${mapped_doctype} data from Google SpreadSheet will be deleted. Counter will also be reset.` :
            `Disabling this means the data in the SpreadSheet will not changed after successful imports. Counter will be used to keep track of imported ${mapped_doctype} data`;

        frappe.confirm(confirm_message, ()=>{
            // if enabling 'reset worksheet', reset counter variable on confirm action
            if (to_enable) {
                child_doc.counter = 0;
                frm.fields_dict.worksheet_ids.refresh();
            }
        }, () => {
            // revert 'reset worksheet' on rejection action
            child_doc.reset_worksheet_on_import = !to_enable;
            frm.fields_dict.worksheet_ids.refresh();
        });
    }
})