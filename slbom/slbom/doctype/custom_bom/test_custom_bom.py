# slbom/slbom/doctype/custom_bom/test_custom_bom.py

import frappe
import unittest
from frappe.utils import flt


class TestCustomBOM(unittest.TestCase):

    def setUp(self):
        self._ensure_item("TEST-FG-001", "Finished Good Test Item", "Products")
        self._ensure_item("TEST-RM-001", "Raw Material 1", "Raw Material")
        self._ensure_item("TEST-RM-002", "Raw Material 2", "Raw Material")
        self._ensure_price_list("BOM Costing Test")
        self._ensure_item_price("TEST-RM-001", "BOM Costing Test", 100)
        self._ensure_item_price("TEST-RM-002", "BOM Costing Test", 50)

        settings = frappe.get_single("Costing Settings")
        settings.default_price_list = "BOM Costing Test"
        settings.default_overhead_pct = 15
        settings.default_margin_pct = 20
        settings.max_bom_lines = 3
        settings.save(ignore_permissions=True)

    def test_create_bom(self):
        bom = self._create_bom()
        self.assertEqual(bom.version, 1)
        self.assertEqual(bom.status, "Draft")
        self.assertEqual(bom.total_material_cost, 250)

    def test_version_increment(self):
        bom = self._create_bom()
        self.assertEqual(bom.version, 1)

        bom.reload()
        bom.components[0].quantity = 2
        bom.save()
        self.assertEqual(bom.version, 2)

        versions = frappe.get_all(
            "Custom BOM Version",
            filters={"bom": bom.name},
            fields=["version_number"],
        )
        self.assertTrue(len(versions) >= 1)

    def test_circular_reference_blocked(self):
        bom = frappe.new_doc("Custom BOM")
        bom.item = "TEST-FG-001"
        bom.uom = "Nos"
        bom.quantity = 1
        bom.append("components", {
            "item": "TEST-FG-001",
            "uom": "Nos",
            "quantity": 1,
            "rate": 100,
        })
        self.assertRaises(frappe.exceptions.ValidationError, bom.insert)

    def test_only_one_default(self):
        bom1 = self._create_bom()
        bom1.is_default = 1
        bom1.save()

        bom2 = self._create_bom()
        bom2.is_default = 1
        self.assertRaises(frappe.exceptions.ValidationError, bom2.save)

    def test_locked_bom_cannot_save(self):
        bom = self._create_bom()
        frappe.db.set_value("Custom BOM", bom.name, "bom_locked", 1)
        bom.reload()
        bom.remarks = "trying to edit"
        self.assertRaises(frappe.exceptions.ValidationError, bom.save)

    def _create_bom(self):
        bom = frappe.new_doc("Custom BOM")
        bom.item = "TEST-FG-001"
        bom.uom = "Nos"
        bom.quantity = 1
        bom.status = "Draft"
        bom.append("components", {
            "item": "TEST-RM-001",
            "uom": "Nos",
            "quantity": 1,
            "rate": 100,
        })
        bom.append("components", {
            "item": "TEST-RM-002",
            "uom": "Nos",
            "quantity": 1,
            "rate": 50,
        })
        bom.append("components", {
            "item": "TEST-RM-001",
            "uom": "Nos",
            "quantity": 1,
            "rate": 100,
        })
        bom.insert(ignore_permissions=True)
        return bom

    def _ensure_item(self, code, name, group):
        if not frappe.db.exists("Item", code):
            item = frappe.new_doc("Item")
            item.item_code = code
            item.item_name = name
            item.item_group = group
            item.stock_uom = "Nos"
            item.is_stock_item = 1
            item.insert(ignore_permissions=True)

    def _ensure_price_list(self, name):
        if not frappe.db.exists("Price List", name):
            pl = frappe.new_doc("Price List")
            pl.price_list_name = name
            pl.buying = 1
            pl.insert(ignore_permissions=True)

    def _ensure_item_price(self, item, price_list, rate):
        existing = frappe.db.exists("Item Price", {
            "item_code": item, "price_list": price_list
        })
        if not existing:
            ip = frappe.new_doc("Item Price")
            ip.item_code = item
            ip.price_list = price_list
            ip.price_list_rate = rate
            ip.insert(ignore_permissions=True)
