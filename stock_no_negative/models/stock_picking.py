# Copyright 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        pickings = self.filtered(lambda x: not x._is_subcontract())
        res = super(StockPicking, pickings)._action_done()
        for picking in self - pickings:
            if picking._is_subcontract():
                super(
                    StockPicking, picking.with_context(no_negative_check=True)
                )._action_done()
        return res
