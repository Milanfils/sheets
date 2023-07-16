from datetime import datetime
from urllib.parse import urljoin

import frappe
import requests
from frappe.utils import get_datetime
from frappe.utils.caching import redis_cache
from frappe.utils.password import get_decrypted_password

import sheets
from sheets.hooks import app_name

VALIDATE_PLANS_ENDPOINT = urljoin(sheets.BILLING_API, f"/apps/{app_name}/plan")
AVAILABLE_PLANS_ENDPOINT = urljoin(sheets.BILLING_API, f"/apps/{app_name}/plans")


@redis_cache
def get_available_plans():
    res = requests.get(AVAILABLE_PLANS_ENDPOINT).json()["plans"]
    return {plan["plan_id"]: plan for plan in res}


def get_sheets_auth_token():
    return get_decrypted_password(
        sheets.SHEETS_SETTINGS, sheets.SHEETS_SETTINGS, "sheets_user_id", raise_exception=False
    )


def get_sheets_active_plan():
    plan = frappe.cache.get_value("sheets_active_plan", expires=True)

    if plan and not is_plan_expired(plan):
        return plan

    plan = fetch_active_plan_from_api()
    expires_in_sec = 24 * 60 * 60
    frappe.cache.set_value("sheets_active_plan", plan, expires_in_sec=expires_in_sec)
    frappe.cache.set_value(
        "sheets_restrict_doctypes",
        {d["doctype"] for d in plan["meta"]["metadata"]["limits"]},
        expires_in_sec=expires_in_sec,
    )

    return plan


def is_plan_expired(plan):
    expires_on = plan.get("expires_on")
    if expires_on:
        return get_datetime(expires_on).date() > datetime.now().date()
    return False


def fetch_active_plan_from_api():
    auth_token = get_sheets_auth_token()
    plan_def = requests.get(
        VALIDATE_PLANS_ENDPOINT,
        json={
            "auth_token": auth_token,
        },
    ).json()
    return {**plan_def, "meta": get_available_plans()[plan_def["plan"]]}


def validate(doc, method: str | None = None):
    if doc.doctype not in (frappe.cache.get_value("sheets_restrict_doctypes") or {}):
        return

    delta = 1 if doc.get("__islocal") else 0
    active_plan_meta = get_sheets_active_plan()["meta"]
    plan_limits: dict = active_plan_meta["metadata"]["limits"]

    for limit in plan_limits:
        if (frappe.db.count(limit["doctype"]) + delta) > limit["value"]:
            plan_name = frappe.bold(
                f"{active_plan_meta['description']} ({active_plan_meta['plan_name']})"
            )
            frappe.throw(
                f"Upgrade your current plan '{plan_name}' to create more Pipelines. {sheets.PLAN_MANAGEMENT_MSG}",
            )


def clear_cache():
    frappe.cache.delete_value("sheets_active_plan")
    frappe.cache.delete_value("sheets_restrict_doctypes")
    get_available_plans.clear_cache()
