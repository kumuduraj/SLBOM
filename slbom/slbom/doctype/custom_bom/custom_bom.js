// slbom/slbom/doctype/custom_bom/custom_bom.js

frappe.ui.form.on("Custom BOM", {
    refresh(frm) {
        if (frm.doc.bom_locked) {
            frm.set_intro(
                '<span style="color:red;font-weight:bold;">LOCKED - This BOM is referenced by a Finalised Costing Sheet. Cancel the Costing Sheet to edit.</span>'
            );
            frm.disable_save();
            frm.set_read_only();
        }

        if (!frm.is_new()) {
            frm.add_custom_button(__("Version History"), function () {
                frappe.route_options = { bom: frm.doc.name };
                frappe.set_route("List", "Custom BOM Version");
            }, __("View"));
        }
    },

    item(frm) {
        if (frm.doc.item) {
            frappe.db.get_single_value("Costing Settings", "default_price_list")
                .then((price_list) => {
                    if (price_list) {
                        (frm.doc.components || []).forEach((row) => {
                            if (!row.price_list) {
                                frappe.model.set_value(
                                    row.doctype, row.name,
                                    "price_list", price_list
                                );
                            }
                        });
                    }
                });
        }
    },
});


frappe.ui.form.on("Custom BOM Component", {
    item(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            _fetch_price(frm, row);
        }
    },

    uom(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item && row.uom) {
            _validate_uom_conversion(frm, row);
            _fetch_price(frm, row);
        }
    },

    quantity(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        _compute_row_amount(frm, row);
    },

    rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        _compute_row_amount(frm, row);
    },

    components_remove(frm) {
        _compute_total(frm);
    },
});


function _fetch_price(frm, row) {
    let price_list = row.price_list;
    if (!price_list) {
        frappe.db.get_single_value("Costing Settings", "default_price_list")
            .then((default_pl) => {
                if (default_pl) {
                    frappe.model.set_value(
                        row.doctype, row.name, "price_list", default_pl
                    );
                    _do_fetch_price(frm, row, default_pl);
                }
            });
    } else {
        _do_fetch_price(frm, row, price_list);
    }
}


function _do_fetch_price(frm, row, price_list) {
    frappe.call({
        method: "slbom.api.price_fetch.get_item_price",
        args: {
            item_code: row.item,
            price_list: price_list,
            uom: row.uom || "",
        },
        callback(r) {
            if (r.message !== undefined && r.message !== null) {
                frappe.model.set_value(
                    row.doctype, row.name, "rate", r.message
                );
                _compute_row_amount(frm, row);
            } else {
                frappe.show_alert({
                    message: __("No price found for {0} in {1}", [row.item, price_list]),
                    indicator: "orange",
                });
                frappe.model.set_value(row.doctype, row.name, "rate", 0);
                _compute_row_amount(frm, row);
            }
        },
    });
}


function _validate_uom_conversion(frm, row) {
    frappe.call({
        method: "slbom.api.price_fetch.validate_uom_conversion",
        args: {
            item_code: row.item,
            uom: row.uom,
        },
        callback(r) {
            if (r.message && !r.message.valid) {
                frappe.msgprint({
                    title: __("UOM Conversion Missing"),
                    message: __(
                        "No UOM conversion defined for {0} -> {1} on item {2}. Please define it in the Item master or UOM Conversion Factor.",
                        [row.uom, r.message.stock_uom, row.item]
                    ),
                    indicator: "red",
                });
            }
        },
    });
}


function _compute_row_amount(frm, row) {
    let amount = flt(row.quantity) * flt(row.rate);
    frappe.model.set_value(row.doctype, row.name, "amount", amount);
    _compute_total(frm);
}


function _compute_total(frm) {
    let total = 0;
    (frm.doc.components || []).forEach((row) => {
        total += flt(row.amount);
    });
    frm.set_value("total_material_cost", total);
}
