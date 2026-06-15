# slbom/slbom/doctype/costing_sheet/costing_sheet.py

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today


class CostingSheet(Document):

    def validate(self):
        self._validate_finalised_lock()
        self._validate_bom_line_count()
        self._validate_bom_lines()
        self._set_defaults_from_settings()
        self._compute_bom_line_costs()
        self._compute_totals()
        self._handle_status_transitions()

    def _validate_finalised_lock(self):
        if not self.is_new():
            old_status = frappe.db.get_value("Costing Sheet", self.name, "status")
            if old_status == "Finalised" and self.status == "Finalised":
                frappe.throw(
                    "This Costing Sheet is Finalised. Change status to Draft first to edit.",
                    title="Costing Sheet Locked"
                )

    def _validate_bom_line_count(self):
        max_lines = frappe.db.get_single_value("Costing Settings", "max_bom_lines") or 3
        if len(self.bom_lines) > max_lines:
            frappe.throw(
                f"Maximum {max_lines} BOMs allowed per Costing Sheet. "
                f"You have {len(self.bom_lines)}."
            )

    def _validate_bom_lines(self):
        for row in self.bom_lines:
            if flt(row.quantity_factor) <= 0:
                frappe.throw(
                    f"Row {row.idx}: Quantity Factor must be greater than zero."
                )

            bom_doc = frappe.get_doc("Custom BOM", row.bom)
            if bom_doc.status not in ("Active", "Draft"):
                frappe.throw(
                    f"Row {row.idx}: Custom BOM {row.bom} has status '{bom_doc.status}'. "
                    "Only Active or Draft BOMs can be linked."
                )

            row.bom_item = bom_doc.item_name or bom_doc.item
            row.bom_version = bom_doc.version

    def _set_defaults_from_settings(self):
        if self.is_new():
            settings = frappe.get_single("Costing Settings")
            if not self.price_list and settings.default_price_list:
                self.price_list = settings.default_price_list
            if not self.overhead_pct and settings.default_overhead_pct:
                self.overhead_pct = settings.default_overhead_pct
            if not self.profit_margin_pct and settings.default_margin_pct:
                self.profit_margin_pct = settings.default_margin_pct

    def _compute_bom_line_costs(self):
        for row in self.bom_lines:
            bom_total = frappe.db.get_value(
                "Custom BOM", row.bom, "total_material_cost"
            ) or 0
            row.material_cost = flt(bom_total) * flt(row.quantity_factor)

        total = sum(flt(row.material_cost) for row in self.bom_lines)
        self.total_material_cost = total

        for row in self.bom_lines:
            if total > 0:
                row.share_pct = (flt(row.material_cost) / total) * 100
            else:
                row.share_pct = 0

    def _compute_totals(self):
        self.overhead_amount = flt(self.total_material_cost) * flt(self.overhead_pct) / 100
        self.total_cost = (
            flt(self.total_material_cost)
            + flt(self.overhead_amount)
            + flt(self.labour_cost)
        )
        self.profit_amount = flt(self.total_cost) * flt(self.profit_margin_pct) / 100
        self.selling_price = flt(self.total_cost) + flt(self.profit_amount)

    def _handle_status_transitions(self):
        if not self.is_new():
            old_status = frappe.db.get_value("Costing Sheet", self.name, "status")

            if old_status != "Finalised" and self.status == "Finalised":
                self._lock_boms(lock=True)

            if old_status == "Finalised" and self.status == "Draft":
                self._unlock_boms()

            if self.status == "Approved" and old_status != "Approved":
                self.approved_by = frappe.session.user
                self.approval_date = today()

    def _lock_boms(self, lock=True):
        for row in self.bom_lines:
            frappe.db.set_value(
                "Custom BOM", row.bom, "bom_locked", 1 if lock else 0
            )
        if lock:
            frappe.msgprint(
                "Linked BOMs have been locked.",
                indicator="blue",
                alert=True,
            )

    def _unlock_boms(self):
        for row in self.bom_lines:
            other_cs = frappe.db.exists(
                "Costing Sheet BOM Line",
                {
                    "bom": row.bom,
                    "parent": ("!=", self.name),
                    "parenttype": "Costing Sheet",
                },
            )
            if other_cs:
                parent_name = frappe.db.get_value(
                    "Costing Sheet BOM Line", other_cs, "parent"
                )
                parent_status = frappe.db.get_value(
                    "Costing Sheet", parent_name, "status"
                )
                if parent_status == "Finalised":
                    continue

            frappe.db.set_value("Custom BOM", row.bom, "bom_locked", 0)

    def on_trash(self):
        if self.status == "Finalised":
            for row in self.bom_lines:
                frappe.db.set_value("Custom BOM", row.bom, "bom_locked", 0)


@frappe.whitelist()
def refresh_prices(costing_sheet_name):
    cs = frappe.get_doc("Costing Sheet", costing_sheet_name)

    if cs.status == "Finalised":
        frappe.throw("Cannot refresh prices on a Finalised Costing Sheet.")

    warnings = []

    for bom_row in cs.bom_lines:
        bom_doc = frappe.get_doc("Custom BOM", bom_row.bom)
        bom_total = 0

        for comp in bom_doc.components:
            from slbom.api.price_fetch import get_item_price
            price = get_item_price(
                item_code=comp.item,
                price_list=cs.price_list,
                uom=comp.uom or "",
            )
            if price is not None:
                comp.rate = flt(price)
            else:
                comp.rate = 0
                warnings.append(f"{comp.item} - no price in {cs.price_list}")

            comp.amount = flt(comp.quantity) * flt(comp.rate)
            bom_total += comp.amount

        bom_doc.total_material_cost = bom_total
        bom_doc.save(ignore_permissions=True)

    cs.reload()
    cs.save(ignore_permissions=True)

    result = {
        "selling_price": cs.selling_price,
        "total_cost": cs.total_cost,
        "total_material_cost": cs.total_material_cost,
        "warnings": warnings,
    }

    if warnings:
        frappe.msgprint(
            "<br>".join(warnings),
            title="Price Warnings",
            indicator="orange",
        )

    return result
