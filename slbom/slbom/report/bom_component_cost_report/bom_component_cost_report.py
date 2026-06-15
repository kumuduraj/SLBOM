import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": "Quantity", "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": "BOM Rate", "fieldname": "bom_rate", "fieldtype": "Currency", "width": 120},
        {"label": "Current Rate", "fieldname": "current_rate", "fieldtype": "Currency", "width": 120},
        {"label": "BOM Amount", "fieldname": "bom_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Current Amount", "fieldname": "current_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Variance", "fieldname": "variance", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    if not filters or not filters.get("custom_bom"):
        return []

    bom_name = filters.get("custom_bom")
    price_list = filters.get("price_list") or frappe.db.get_single_value(
        "Costing Settings", "default_price_list"
    )

    components = frappe.get_all(
        "Custom BOM Component",
        filters={"parent": bom_name},
        fields=["item", "item_name", "uom", "quantity", "rate", "amount"],
        order_by="idx",
    )

    data = []
    for comp in components:
        current_rate = frappe.db.get_value(
            "Item Price",
            {"item_code": comp.item, "price_list": price_list},
            "price_list_rate",
        ) or 0

        current_amount = flt(comp.quantity) * flt(current_rate)
        variance = current_amount - flt(comp.amount)

        data.append({
            "item": comp.item,
            "item_name": comp.item_name,
            "uom": comp.uom,
            "quantity": comp.quantity,
            "bom_rate": comp.rate,
            "current_rate": flt(current_rate),
            "bom_amount": comp.amount,
            "current_amount": current_amount,
            "variance": variance,
        })

    return data
