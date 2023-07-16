import json

import frappe
from cron_descriptor import get_description

import sheets
from sheets.billing import get_sheets_active_plan

CRON_MAP = {
    "Yearly": "0 0 1 1 *",
    "Monthly": "0 0 1 * *",
    "Weekly": "0 0 * * 0",
    "Daily": "0 0 * * *",
    "Hourly": "0 * * * *",
}


@frappe.whitelist(methods=["GET"])
def get_all_frequency():
    return (frappe.conf.scheduler_interval or 240) // 60


@frappe.whitelist(methods=["GET"])
def describe_cron(cron: str):
    if cron in CRON_MAP:
        cron = CRON_MAP[cron]
    return get_description(cron)


@frappe.whitelist(methods=["GET"])
def get_active_plan():
    # Note: Infinity is not a valid JSON value so we need to replace it with null
    d = json.loads(json.dumps(get_sheets_active_plan()).replace("Infinity", "null"))
    d["PLAN_MANAGEMENT_MSG"] = sheets.PLAN_MANAGEMENT_MSG
    return d
