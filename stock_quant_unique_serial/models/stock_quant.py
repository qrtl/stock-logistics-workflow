# Copyright 2023 Quartile Limited Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("product_id", "lot_id")
    def _check_stock_quant_unique(self):
        for record in self:
            if (
                record.location_id.usage != "inventory"
                and record.lot_id
                and record.product_id.tracking == "serial"
            ):
                existing_rec = self.search(
                    [
                        ("product_id", "=", record.product_id.id),
                        ("lot_id", "=", record.lot_id.id),
                        ("id", "!=", self.id),
                    ]
                )
                if existing_rec:
                    raise ValidationError(
                        _(
                            "The serial number has already been "
                            "assigned: \n Product: %(Product)s, "
                            "Serial Number: %(Serial Number)s"
                        )
                        % {
                            "Product": record.product_id.display_name,
                            "Serial Number": record.lot_id.name,
                        }
                    )
