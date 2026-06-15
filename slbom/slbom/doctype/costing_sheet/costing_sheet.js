// slbom/slbom/doctype/costing_sheet/costing_sheet.js

frappe.ui.form.on("Costing Sheet", {
    setup(frm) {
        if (frm.is_new()) {
            frappe.db.get_single_value("Costing Settings", "default_price_list")
                .then((val) => {
                    if (val && !frm.doc.price_list) frm.set_value("price_list", val);
                });
            frappe.db.get_single_value("Costing Settings", "default_overhead_pct")
                .then((val) => {
                    if (val && !frm.doc.overhead_pct) frm.set_value("overhead_pct", val);
                });
            frappe.db.get_single_value("Costing Settings", "default_margin_pct")
                .then((val) => {
                    if (val && !frm.doc.profit_margin_pct) frm.set_value("profit_margin_pct", val);
                });
        }
    },

    refresh(frm) {
        if (frm.doc.status === "Finalised") {
            frm.set_intro(
                '<span style="color:green;font-weight:bold;">FINALISED - Linked BOMs are locked. Change status to Draft to edit.</span>'
            );
        }

        if (!frm.is_new() && frm.doc.status !== "Finalised") {
            frm.add_custom_button(__("Refresh Prices"), function () {
                frappe.call({
                    method: "slbom.slbom.doctype.costing_sheet.costing_sheet.refresh_prices",
                    args: { costing_sheet_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Refreshing prices from Item Price..."),
                    callback(r) {
                        frm.reload_doc();
                        if (r.message) {
                            frappe.show_alert({
                                message: __("Prices refreshed. Selling Price: {0}",
                                    [format_currency(r.message.selling_price)]),
                                indicator: "green",
                            });
                        }
                    },
                });
            }, __("Actions"));
        }
    },

    overhead_pct(frm) { _live_compute(frm); },
    labour_cost(frm) { _live_compute(frm); },
    profit_margin_pct(frm) { _live_compute(frm); },
});


frappe.ui.form.on("Costing Sheet BOM Line", {
    bom(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.bom) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Custom BOM",
                    name: row.bom,
                },
                callback(r) {
                    if (r.message) {
                        let bom = r.message;
                        frappe.model.set_value(cdt, cdn, "bom_item",
                            bom.item_name || bom.item);
                        frappe.model.set_value(cdt, cdn, "bom_version",
                            bom.version);

                        let cost = flt(bom.total_material_cost) * flt(row.quantity_factor || 1);
                        frappe.model.set_value(cdt, cdn, "material_cost", cost);
                        _recompute_shares(frm);
                        _live_compute(frm);
                    }
                },
            });
        }
    },

    quantity_factor(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.bom) {
            frappe.db.get_value("Custom BOM", row.bom, "total_material_cost")
                .then((r) => {
                    let bom_cost = r && r.message ? flt(r.message.total_material_cost) : 0;
                    let cost = bom_cost * flt(row.quantity_factor);
                    frappe.model.set_value(cdt, cdn, "material_cost", cost);
                    _recompute_shares(frm);
                    _live_compute(frm);
                });
        }
    },

    bom_lines_remove(frm) {
        _recompute_shares(frm);
        _live_compute(frm);
    },
});


function _recompute_shares(frm) {
    let total = 0;
    (frm.doc.bom_lines || []).forEach((row) => {
        total += flt(row.material_cost);
    });
    frm.set_value("total_material_cost", total);
    (frm.doc.bom_lines || []).forEach((row) => {
        let pct = total > 0 ? (flt(row.material_cost) / total) * 100 : 0;
        frappe.model.set_value(row.doctype, row.name, "share_pct", pct);
    });
}


function _live_compute(frm) {
    let total_material = flt(frm.doc.total_material_cost);
    let overhead = total_material * flt(frm.doc.overhead_pct) / 100;
    let total_cost = total_material + overhead + flt(frm.doc.labour_cost);
    let profit = total_cost * flt(frm.doc.profit_margin_pct) / 100;
    let selling = total_cost + profit;

    frm.set_value("overhead_amount", overhead);
    frm.set_value("total_cost", total_cost);
    frm.set_value("profit_amount", profit);
    frm.set_value("selling_price", selling);
}
