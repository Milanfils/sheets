// Copyright (c) 2023, Gavin D'souza and contributors
// For license information, please see license.txt

frappe.ui.form.on("SpreadSheet Settings", {
  refresh(frm) {
    let html_wrapper = frm.get_field("sheets_plan_details").$wrapper;

    frappe.call({
      method: "sheets.api.get_active_plan",
      type: "GET",
      callback: ({ message }) => {
        let planMeta = message.meta;
        const planName = `${planMeta.description} (${planMeta.plan_name})`;
        const isUnlimitedPlan =
          planMeta.metadata.limits && planMeta.metadata.limits[0].value == null;
        let planTitle = `Active Plan: ${planName}
Limits: ${
          isUnlimitedPlan
            ? "You have no limits"
            : planMeta.metadata.limits
                .map((x) => `${x.value} ${x.doctype}`)
                .join(", ")
        }`;
        let planMessage = `Your site is running on the ${planName}. ${message.PLAN_MANAGEMENT_MSG}`;

        html_wrapper.html(`<div class="row text-primary rounded p-2" style="background: ${
          planMeta.metadata.requires_activation ? "aliceblue" : "antiquewhite"
        };border-style: dotted;">
                <div class="col-xs-12" title="${planTitle}">
                    ${planMessage}
                </div>
            </div>`);
      },
    });
  },
});
