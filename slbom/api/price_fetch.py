# slbom/api/price_fetch.py

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_item_price(item_code, price_list, uom=""):
    if not item_code or not price_list:
        return None

    if uom:
        rate = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "price_list": price_list,
                "uom": uom,
            },
            "price_list_rate",
        )
        if rate is not None:
            return flt(rate)

    stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
    base_rate = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": price_list,
            "uom": ("in", [stock_uom, "", None]),
        },
        "price_list_rate",
    )

    if base_rate is None:
        base_rate = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "price_list": price_list,
            },
            "price_list_rate",
        )

    if base_rate is None:
        return None

    base_rate = flt(base_rate)

    if uom and uom != stock_uom:
        conversion = _get_uom_conversion(item_code, uom, stock_uom)
        if conversion:
            return base_rate * conversion
        else:
            return base_rate

    return base_rate


@frappe.whitelist()
def validate_uom_conversion(item_code, uom):
    stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")

    if uom == stock_uom:
        return {"valid": True, "stock_uom": stock_uom}

    conversion = _get_uom_conversion(item_code, uom, stock_uom)
    return {
        "valid": conversion is not None,
        "stock_uom": stock_uom,
    }


def _get_uom_conversion(item_code, from_uom, to_uom):
    if from_uom == to_uom:
        return 1.0

    conversion = frappe.db.get_value(
        "UOM Conversion Detail",
        {"parent": item_code, "parenttype": "Item", "uom": from_uom},
        "conversion_factor",
    )
    if conversion:
        return flt(conversion)

    conversion = frappe.db.get_value(
        "UOM Conversion Factor",
        {"from_uom": from_uom, "to_uom": to_uom},
        "value",
    )
    if conversion:
        return flt(conversion)

    conversion = frappe.db.get_value(
        "UOM Conversion Factor",
        {"from_uom": to_uom, "to_uom": from_uom},
        "value",
    )
    if conversion and flt(conversion) != 0:
        return 1.0 / flt(conversion)

    return None
