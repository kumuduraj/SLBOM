# slbom/slbom/doctype/costing_settings/costing_settings.py

import frappe
from frappe.model.document import Document


class CostingSettings(Document):
    def validate(self):
        if self.max_bom_lines and (self.max_bom_lines < 1 or self.max_bom_lines > 5):
            frappe.throw("Max BOM Lines must be between 1 and 5.")

        if self.default_overhead_pct and self.default_overhead_pct < 0:
            frappe.throw("Default Overhead % cannot be negative.")

        if self.default_margin_pct and self.default_margin_pct < 0:
            frappe.throw("Default Profit Margin % cannot be negative.")
