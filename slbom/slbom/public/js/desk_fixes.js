// slbom/public/js/desk_fixes.js
// Fixes for Frappe v16 sidebar bugs

// 1. Ensure sidebar_item_map exists before Frappe reads it
(function () {
    if (localStorage.getItem("sidebar_item_map") === null) {
        localStorage.setItem("sidebar_item_map", "{}");
    }
})();

$(document).ready(function () {
    // 2. Guard sidebar.setup() against undefined workspace_title
    if (frappe.ui?.Sidebar?.prototype?.setup) {
        var _origSetup = frappe.ui.Sidebar.prototype.setup;
        frappe.ui.Sidebar.prototype.setup = function (workspace_title) {
            if (workspace_title == null) return;
            return _origSetup.call(this, workspace_title);
        };
    }

    // 3. Skip divider items in add_app_item() to prevent GET /undefined
    if (frappe.ui?.SidebarHeader?.prototype?.add_app_item) {
        var _origAddAppItem = frappe.ui.SidebarHeader.prototype.add_app_item;
        frappe.ui.SidebarHeader.prototype.add_app_item = function (item) {
            if (item.is_divider || (!item.icon && !item.icon_url)) return;
            return _origAddAppItem.call(this, item);
        };
    }
});
