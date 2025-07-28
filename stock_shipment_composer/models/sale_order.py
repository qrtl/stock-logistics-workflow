# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models

# from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    shipment_composer_ids = fields.Many2many(
        "stock.shipment.composer", compute="_compute_shipment_composer_ids"
    )

    def _compute_shipment_composer_ids(self):
        for rec in self:
            rec.shipment_composer_ids = rec.order_line.move_ids.shipment_composer_ids

    def action_view_shipment_composers(self):
        return self.env["stock.picking"]._get_action_view_shipment_composer(
            self.shipment_composer_ids
        )
