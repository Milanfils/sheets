from . import __version__ as app_version  # noqa

app_name = "google_sheets_connector"
app_title = "Google Sheets Data Sync"
app_publisher = "Gavin D'souza"
app_description = "Sync data from Google Sheets to your DocTypes"
app_email = "gavin18d@gmail.com"
app_license = "No License"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/google_sheets_connector/css/google_sheets_connector.css"
# app_include_js = "/assets/google_sheets_connector/js/google_sheets_connector.js"

# include js, css files in header of web template
# web_include_css = "/assets/google_sheets_connector/css/google_sheets_connector.css"
# web_include_js = "/assets/google_sheets_connector/js/google_sheets_connector.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "google_sheets_connector/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "google_sheets_connector.utils.jinja_methods",
# 	"filters": "google_sheets_connector.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "google_sheets_connector.install.before_install"
after_install = "google_sheets_connector.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "google_sheets_connector.uninstall.before_uninstall"
# after_uninstall = "google_sheets_connector.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "google_sheets_connector.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
has_permission = {
    "File": "google_sheets_connector.overrides.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"google_sheets_connector.tasks.all"
# 	],
# 	"daily": [
# 		"google_sheets_connector.tasks.daily"
# 	],
# 	"hourly": [
# 		"google_sheets_connector.tasks.hourly"
# 	],
# 	"weekly": [
# 		"google_sheets_connector.tasks.weekly"
# 	],
# 	"monthly": [
# 		"google_sheets_connector.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "google_sheets_connector.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "google_sheets_connector.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "google_sheets_connector.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"google_sheets_connector.auth.validate"
# ]
