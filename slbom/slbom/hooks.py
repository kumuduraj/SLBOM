# slbom/slbom/hooks.py — Package level (frappe.get_hooks() reads THIS)

app_name = "slbom"
app_title = "SLBOM"
app_description = "Custom BOM and Costing Module"
app_publisher = "rajgills.it@gmail.com"
app_email = "rajgills.it@gmail.com"
app_license = "MIT"
app_version = "1.0.0"

required_apps = ["frappe", "erpnext"]

# Lifecycle
after_install = "slbom.install.after_install"
before_uninstall = "slbom.install.before_uninstall"

# JS/CSS injected into every desk page
app_include_js = ["/assets/slbom/js/desk_fixes.js"]

# Fixtures
fixtures = [
    {
        "dt": "Role",
        "filters": [
            ["name", "in", ["BOM Manager", "Costing Manager", "BOM Viewer"]]
        ]
    },
    {"dt": "Workspace", "filters": [["app", "=", "slbom"]]},
    {"dt": "Desktop Icon", "filters": [["app", "=", "slbom"]]},
]
