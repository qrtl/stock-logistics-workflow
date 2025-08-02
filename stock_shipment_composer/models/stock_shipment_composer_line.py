# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockShipmentComposerLine(models.Model):
    _name = "stock.shipment.composer.line"
    _description = "Stock Shipment Composer Line"

    composer_id = fields.Many2one(
        "stock.shipment.composer", required=True, ondelete="cascade"
    )
    move_id = fields.Many2one("stock.move", required=True)
    picking_id = fields.Many2one(related="move_id.picking_id", string="Transfer")
    price_unit = fields.Float("Unit Price", related="move_id.sale_line_id.price_unit")
    price_declared = fields.Float(
        "Declared Price",
        compute="_compute_price_declared",
        store=True,
        readonly=False,
        required=True,
    )
    quantity = fields.Float(compute="_compute_quantity", store="True", readonly=False)
    product_uom_qty = fields.Float(related="move_id.product_uom_qty")
    reserved_availability = fields.Float(related="move_id.reserved_availability")
    quantity_done = fields.Float(related="move_id.quantity_done")
    uom_id = fields.Many2one(related="move_id.product_uom", string="UoM")
    move_state = fields.Selection(related="move_id.state", string="Move Status")
    amount_subtotal = fields.Monetary(compute="_compute_amount", string="Subtotal")
    amount_declared = fields.Monetary(
        compute="_compute_amount", string="Declared Amount"
    )
    remarks = fields.Text()
    currency_id = fields.Many2one(related="composer_id.currency_id")
    state = fields.Selection(related="composer_id.state", store=True)
    reserved_enough = fields.Boolean(compute="_compute_reserved_enough")
    location_id = fields.Many2one(
        related="move_id.location_id", string="Source Location"
    )
    location_dest_id = fields.Many2one(
        related="move_id.location_dest_id", string="Destination Location"
    )

    @api.depends("move_id", "move_id.sale_line_id.price_unit")
    def _compute_price_declared(self):
        for rec in self:
            rec.price_declared = rec.move_id.sale_line_id.price_unit

    @api.depends("move_id")
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.move_id.composer_unallocated_qty

    @api.depends("quantity", "price_unit", "price_declared")
    def _compute_amount(self):
        for rec in self:
            rec.amount_subtotal = rec.price_unit * rec.quantity
            rec.amount_declared = rec.price_declared * rec.quantity

    @api.depends("quantity", "reserved_availability")
    def _compute_reserved_enough(self):
        for rec in self:
            rec.reserved_enough = rec.reserved_availability >= rec.quantity

    def action_product_forecast_report(self):
        self.ensure_one()
        return self.move_id.action_product_forecast_report()

    def action_show_details(self):
        self.ensure_one()
        return self.move_id.action_show_details()
