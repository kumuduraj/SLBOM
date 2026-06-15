import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Costing Sheet", "fieldname": "name", "fieldtype": "Link", "options": "Costing Sheet", "width": 160},
        {"label": "Title", "fieldname": "title", "fieldtype": "Data", "width": 200},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Material Cost", "fieldname": "total_material_cost", "fieldtype": "Currency", "width": 130},
        {"label": "Overhead", "fieldname": "overhead_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Labour", "fieldname": "labour_cost", "fieldtype": "Currency", "width": 110},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Profit %", "fieldname": "profit_margin_pct", "fieldtype": "Float", "width": 90},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 130},
    ]


def get_data(filters):
    conditions = {}

    if filters:
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")
        status = filters.get("status")

        if from_date and to_date:
            conditions["date"] = ("between", [from_date, to_date])
        elif from_date:
            conditions["date"] = (">=", from_date)
        elif to_date:
            conditions["date"] = ("<=", to_date)

        if status:
            conditions["status"] = status

    return frappe.get_all(
        "Costing Sheet",
        filters=conditions,
        fields=[
            "name", "title", "date", "status",
            "total_material_cost", "overhead_amount", "labour_cost",
            "total_cost", "profit_margin_pct", "selling_price",
        ],
        order_by="date desc",
    )
