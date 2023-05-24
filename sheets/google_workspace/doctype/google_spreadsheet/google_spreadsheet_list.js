frappe.listview_settings["Google SpreadSheet"] = {
    onload: function (list_view) {
        list_view.page.add_menu_item("SpreadSheet Settings", () => {
            frappe.set_route("Form", "Google SpreadSheet Settings");
        });
    },
};
