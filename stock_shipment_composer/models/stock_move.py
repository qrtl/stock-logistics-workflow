# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    composer_line_ids = fields.One2many(
        "stock.shipment.composer.line",
        "move_id",
        string="Shipment Composer Lines",
        copy=False,
    )
    shipment_composer_ids = fields.Many2many(
        "stock.shipment.composer", compute="_compute_shipment_composer_ids"
    )
    composer_line_qty = fields.Float(compute="_compute_composer_line_qty", store=True)
    move_split_origin_id = fields.Many2one(
        "stock.move",
        string="Split Origin Move",
        copy=False,
        help="The original move from which this move was split.",
    )

    def _compute_shipment_composer_ids(self):
        for rec in self:
            rec.shipment_composer_ids = rec.composer_line_ids.composer_id

    @api.depends("composer_line_ids.quantity", "composer_line_ids.state")
    def _compute_composer_line_qty(self):
        for rec in self:
            rec.composer_line_qty = sum(
                rec.composer_line_ids.filtered(
                    lambda x: x.state == "in_progress"
                ).mapped("quantity")
            )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if len(res) == 1 and res.move_split_origin_id:
            group_lines = res.move_split_origin_id.composer_line_ids.filtered(
                lambda x: x.state not in ["done", "cancel"]
            )
            if group_lines:
                group_lines.move_id = res.id
        return res

    def _split(self, qty, restrict_partner_id=False):
        res = super()._split(qty, restrict_partner_id=restrict_partner_id)
        res[0]["move_split_origin_id"] = self.id
        return res

    def name_get(self):
        res = []
        if not self.env.context.get("is_shipment_composer"):
            return super().name_get()
        for move in self:
            res.append(
                (
                    move.id,
                    "%s%s%s"
                    % (
                        move.picking_id.origin
                        and "%s: " % move.picking_id.origin
                        or "",
                        move.sale_line_id
                        and "%s " % move.sale_line_id.name
                        or move.product_id.display_name
                        or "",
                        "(%s)" % move.product_uom_qty,
                    ),
                )
            )
        return res
