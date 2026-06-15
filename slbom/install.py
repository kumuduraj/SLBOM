# slbom/install.py

import frappe
import json


def after_install():
    _create_desktop_icon()
    _create_workspace()
    _add_to_all_desktop_layouts()
    frappe.db.commit()


def before_uninstall():
    _remove_desktop_icon()
    _remove_workspace()
    frappe.db.commit()


def _create_desktop_icon():
    if frappe.db.exists("Desktop Icon", "SLBOM"):
        return
    di = frappe.new_doc("Desktop Icon")
    di.name = di.label = "SLBOM"
    di.app = "slbom"
    di.icon = "tool"
    di.icon_type = "Link"
    di.link_type = "Workspace Sidebar"
    di.link_to = "SLBOM"
    di.hidden = 0
    di.standard = 1
    di.flags.ignore_links = True
    di.insert(ignore_permissions=True)


def _create_workspace():
    if frappe.db.exists("Workspace", "SLBOM"):
        return
    ws = frappe.new_doc("Workspace")
    ws.name = ws.label = ws.title = "SLBOM"
    ws.module = "SLBOM"
    ws.icon = "tool"
    ws.type = "Workspace"
    ws.public = 1
    ws.app = "slbom"
    ws.content = json.dumps([
        {"id": "slbom-header", "type": "header", "data": {"text": "<b>SLBOM</b> - BOM & Costing", "col": 12}},
        {"id": "slbom-card", "type": "card", "data": {"card_name": "BOM & Costing", "col": 4}},
    ])
    ws.append("links", {
        "type": "Card Break", "label": "BOM & Costing"
    })
    ws.append("links", {
        "type": "Link", "label": "Custom BOM",
        "link_to": "Custom BOM", "link_type": "DocType", "onboard": 1
    })
    ws.append("links", {
        "type": "Link", "label": "Costing Sheet",
        "link_to": "Costing Sheet", "link_type": "DocType", "onboard": 1
    })
    ws.append("links", {
        "type": "Link", "label": "Costing Settings",
        "link_to": "Costing Settings", "link_type": "DocType", "onboard": 1
    })
    ws.append("links", {
        "type": "Link", "label": "BOM Version History",
        "link_to": "Custom BOM Version", "link_type": "DocType"
    })
    ws.insert(ignore_permissions=True)


def _add_to_all_desktop_layouts():
    """Add SLBOM tile to all existing users' saved Desktop Layouts."""
    for dl_name in frappe.get_all("Desktop Layout", pluck="name"):
        try:
            dl = frappe.get_doc("Desktop Layout", dl_name)
            layout = json.loads(dl.layout or "[]")
            if any(x.get("label") == "SLBOM" for x in layout):
                continue
            layout.append({
                "label": "SLBOM",
                "link_type": "Workspace Sidebar",
                "link_to": "SLBOM",
                "app": "slbom",
                "icon_type": "Link",
                "icon": "tool",
                "parent_icon": "",
                "hidden": 0,
                "idx": len(layout) + 1,
            })
            dl.layout = json.dumps(layout)
            dl.save(ignore_permissions=True)
        except Exception:
            pass


def _remove_desktop_icon():
    if frappe.db.exists("Desktop Icon", "SLBOM"):
        frappe.delete_doc("Desktop Icon", "SLBOM", ignore_permissions=True)


def _remove_workspace():
    if frappe.db.exists("Workspace", "SLBOM"):
        frappe.delete_doc("Workspace", "SLBOM", ignore_permissions=True)
