# Copyright 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        for picking in self:
            for move in picking.move_ids_without_package:
                if move.state == "assigned":
                    picking = picking.with_context(no_negative_check=True)
            return super(StockPicking, picking)._action_done()
