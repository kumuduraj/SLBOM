# slbom/slbom/doctype/costing_sheet/test_costing_sheet.py

import frappe
import unittest
from frappe.utils import flt


class TestCostingSheet(unittest.TestCase):

    def setUp(self):
        from slbom.slbom.doctype.custom_bom.test_custom_bom import TestCustomBOM
        helper = TestCustomBOM()
        helper.setUp()

        self.bom = helper._create_bom()
        self.bom.status = "Active"
        self.bom.save(ignore_permissions=True)

    def test_create_costing_sheet(self):
        cs = self._create_cs()
        self.assertGreater(cs.total_material_cost, 0)
        self.assertGreater(cs.selling_price, 0)

    def test_cost_calculations(self):
        cs = self._create_cs()
        expected_material = flt(self.bom.total_material_cost) * 1
        expected_overhead = expected_material * 15 / 100
        expected_total = expected_material + expected_overhead + 500
        expected_profit = expected_total * 20 / 100
        expected_selling = expected_total + expected_profit

        self.assertAlmostEqual(cs.total_material_cost, expected_material, places=2)
        self.assertAlmostEqual(cs.overhead_amount, expected_overhead, places=2)
        self.assertAlmostEqual(cs.total_cost, expected_total, places=2)
        self.assertAlmostEqual(cs.selling_price, expected_selling, places=2)

    def test_max_bom_lines_validation(self):
        frappe.db.set_single_value("Costing Settings", "max_bom_lines", 1)

        cs = frappe.new_doc("Costing Sheet")
        cs.title = "Test Max Lines"
        cs.date = frappe.utils.today()
        cs.price_list = "BOM Costing Test"
        cs.overhead_pct = 15
        cs.profit_margin_pct = 20
        cs.labour_cost = 0
        cs.append("bom_lines", {"bom": self.bom.name, "quantity_factor": 1})
        cs.append("bom_lines", {"bom": self.bom.name, "quantity_factor": 1})
        self.assertRaises(frappe.exceptions.ValidationError, cs.insert)

        frappe.db.set_single_value("Costing Settings", "max_bom_lines", 3)

    def test_finalise_locks_bom(self):
        cs = self._create_cs()
        cs.status = "Finalised"
        cs.save(ignore_permissions=True)

        self.bom.reload()
        self.assertEqual(self.bom.bom_locked, 1)

    def test_unfinalise_unlocks_bom(self):
        cs = self._create_cs()
        cs.status = "Finalised"
        cs.save(ignore_permissions=True)

        cs.status = "Draft"
        cs.save(ignore_permissions=True)

        self.bom.reload()
        self.assertEqual(self.bom.bom_locked, 0)

    def test_zero_quantity_factor_blocked(self):
        cs = frappe.new_doc("Costing Sheet")
        cs.title = "Test Zero QF"
        cs.date = frappe.utils.today()
        cs.price_list = "BOM Costing Test"
        cs.overhead_pct = 15
        cs.profit_margin_pct = 20
        cs.labour_cost = 0
        cs.append("bom_lines", {"bom": self.bom.name, "quantity_factor": 0})
        self.assertRaises(frappe.exceptions.ValidationError, cs.insert)

    def _create_cs(self):
        cs = frappe.new_doc("Costing Sheet")
        cs.title = "Test Costing"
        cs.date = frappe.utils.today()
        cs.price_list = "BOM Costing Test"
        cs.overhead_pct = 15
        cs.profit_margin_pct = 20
        cs.labour_cost = 500
        cs.append("bom_lines", {
            "bom": self.bom.name,
            "quantity_factor": 1,
        })
        cs.insert(ignore_permissions=True)
        return cs
