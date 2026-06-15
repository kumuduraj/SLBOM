frappe.query_reports["BOM Component Cost Report"] = {
    filters: [
        {
            fieldname: "custom_bom",
            label: __("Custom BOM"),
            fieldtype: "Link",
            options: "Custom BOM",
            reqd: 1,
        },
        {
            fieldname: "price_list",
            label: __("Price List"),
            fieldtype: "Link",
            options: "Price List",
        },
    ],
};
