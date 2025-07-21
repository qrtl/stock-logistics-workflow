# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Shipment Composer",
    "version": "16.0.1.0.0",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "category": "Inventory",
    "license": "AGPL-3",
    "depends": ["sale_stock", "stock_move_actual_date"],
    "data": [
        "data/stock_shipment_composer_data.xml",
        "security/ir.model.access.csv",
        "security/stock_shipment_composer_security.xml",
        "views/sale_order_views.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_shipment_composer_views.xml",
    ],
    "installable": True,
}
