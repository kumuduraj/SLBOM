# slbom/slbom/doctype/custom_bom/custom_bom.py

import json
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, flt


class CustomBOM(Document):

    def validate(self):
        self._validate_locked()
        self._validate_components()
        self._validate_default_bom()
        self._validate_circular_reference()
        self._validate_dates()
        self._compute_totals()

    def before_save(self):
        if not self.is_new():
            self._increment_version()

    def _validate_locked(self):
        if self.bom_locked:
            frappe.throw(
                "This BOM is referenced by a Finalised Costing Sheet. "
                "Cancel the Costing Sheet first before editing this BOM.",
                title="BOM Locked"
            )

    def _validate_components(self):
        if not self.components:
            frappe.throw("A BOM must have at least one component.")

        for row in self.components:
            if flt(row.quantity) <= 0:
                frappe.throw(
                    f"Row {row.idx}: Quantity must be greater than zero."
                )
            row.amount = flt(row.quantity) * flt(row.rate)

    def _validate_default_bom(self):
        if self.is_default:
            existing = frappe.db.exists(
                "Custom BOM",
                {
                    "item": self.item,
                    "is_default": 1,
                    "name": ("!=", self.name),
                    "status": ("!=", "Cancelled"),
                },
            )
            if existing:
                frappe.throw(
                    f"Item {self.item} already has a default BOM: {existing}. "
                    "Unset it first before marking this one as default."
                )

    def _validate_circular_reference(self):
        for row in self.components:
            if row.item == self.item:
                frappe.throw(
                    f"Row {row.idx}: Component item cannot be the same as "
                    f"the BOM item ({self.item}). Circular reference detected."
                )

    def _validate_dates(self):
        if self.effective_from and self.effective_to:
            if self.effective_from > self.effective_to:
                frappe.throw("Effective From date cannot be after Effective To date.")

    def _compute_totals(self):
        self.total_material_cost = sum(flt(row.amount) for row in self.components)

    def _increment_version(self):
        self.version = (self.version or 1) + 1

        snapshot = []
        for row in self.components:
            snapshot.append({
                "item": row.item,
                "item_name": row.item_name,
                "item_group": row.item_group,
                "uom": row.uom,
                "quantity": row.quantity,
                "rate": row.rate,
                "price_list": row.price_list,
                "amount": row.amount,
                "remarks": row.remarks,
            })

        version_doc = frappe.new_doc("Custom BOM Version")
        version_doc.bom = self.name
        version_doc.version_number = self.version
        version_doc.snapshot_date = now_datetime()
        version_doc.modified_by_user = frappe.session.user
        version_doc.components_json = json.dumps(snapshot, default=str)

        frappe.flags.slbom_creating_version = True
        version_doc.insert(ignore_permissions=True)
        frappe.flags.slbom_creating_version = False

        frappe.msgprint(
            f"BOM version incremented to v{self.version}. Snapshot created.",
            indicator="blue",
            alert=True,
        )
