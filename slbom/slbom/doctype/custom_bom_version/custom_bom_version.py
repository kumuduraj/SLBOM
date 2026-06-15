# slbom/slbom/doctype/custom_bom_version/custom_bom_version.py

import frappe
from frappe.model.document import Document


class CustomBOMVersion(Document):
    def validate(self):
        if not frappe.flags.in_migrate and not frappe.flags.in_install:
            if not frappe.flags.slbom_creating_version:
                frappe.throw(
                    "BOM Versions are auto-created when a Custom BOM is saved. "
                    "Manual creation is not allowed."
                )
