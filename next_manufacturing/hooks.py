# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "next_manufacturing"
app_title = "Next Manufacturing"
app_publisher = "Dexciss Technology"
app_description = "nextmanufacturing"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "demo@dexciss.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/next_manufacturing/css/next_manufacturing.css"
# app_include_js = "/assets/next_manufacturing/js/next_manufacturing.js"

# include js, css files in header of web template
# web_include_css = "/assets/next_manufacturing/css/next_manufacturing.css"
# web_include_js = "/assets/next_manufacturing/js/next_manufacturing.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "next_manufacturing/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"BOM": "public/js/bom.js",
	"Work Order": "public/js/work_order.js",
	"Job Card": "public/js/job_card.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "next_manufacturing.install.before_install"
# after_install = "next_manufacturing.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "next_manufacturing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Stock Entry": "next_manufacturing.next_manufacturing.custom_stock_entry.CustomStockEntry",
	"Work Order": "next_manufacturing.next_manufacturing.custom_work_order.CustomWorkOrder"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Work Order":{
		"after_insert": "next_manufacturing.next_manufacturing.custom_work_order.after_insert",
		"before_save": "next_manufacturing.next_manufacturing.custom_work_order.after_insert",
		"on_submit": "next_manufacturing.next_manufacturing.custom_work_order.change_status"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"next_manufacturing.tasks.all"
# 	],
# 	"daily": [
# 		"next_manufacturing.tasks.daily"
# 	],
# 	"hourly": [
# 		"next_manufacturing.tasks.hourly"
# 	],
# 	"weekly": [
# 		"next_manufacturing.tasks.weekly"
# 	]
# 	"monthly": [
# 		"next_manufacturing.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "next_manufacturing.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.manufacturing.doctype.work_order.work_order.create_pick_list": "next_manufacturing.next_manufacturing.custom_work_order.create_pick_list"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Work Order": "next_manufacturing.next_manufacturing.work_order_dashboard.get_data",
	"Job Card": "next_manufacturing.next_manufacturing.job_card_dashboard.get_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

