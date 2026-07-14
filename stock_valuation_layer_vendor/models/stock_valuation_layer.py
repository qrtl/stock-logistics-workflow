# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    vendor_id = fields.Many2one(
        "res.partner",
        readonly=True,
        index=True,
        help="Vendor of the purchase order linked to the stock move, if any.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            order = rec.stock_move_id.purchase_line_id.order_id
            if order:
                rec.vendor_id = order.partner_id.id
        return recs
