# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestStockValuationLayerVendor(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "is_storable": True, "standard_price": 100.0}
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "name": cls.product.name,
                            "product_qty": 10.0,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        cls.purchase_line = purchase_order.order_line

    def _create_move(self, purchase_line=False):
        return self.env["stock.move"].create(
            {
                "name": "Test move",
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "purchase_line_id": purchase_line.id if purchase_line else False,
            }
        )

    def _create_svl(self, stock_move=False):
        vals = {
            "product_id": self.product.id,
            "company_id": self.env.company.id,
            "quantity": 10.0,
            "value": 1000.0,
            "unit_cost": 100.0,
        }
        if stock_move:
            vals["stock_move_id"] = stock_move.id
        return self.env["stock.valuation.layer"].create(vals)

    def test_vendor_id_set_from_purchase_move(self):
        move = self._create_move(purchase_line=self.purchase_line)
        svl = self._create_svl(stock_move=move)
        self.assertEqual(svl.vendor_id, self.vendor)

    def test_vendor_id_empty_without_purchase(self):
        move = self._create_move()
        svl = self._create_svl(stock_move=move)
        self.assertFalse(svl.vendor_id)

    def test_vendor_id_empty_without_move(self):
        svl = self._create_svl()
        self.assertFalse(svl.vendor_id)

    def test_vendor_id_set_from_purchase_move_batch(self):
        vendor_2 = self.env["res.partner"].create({"name": "Test Vendor 2"})
        purchase_line_2 = self.purchase_line.order_id.copy(
            {"partner_id": vendor_2.id}
        ).order_line
        move_1 = self._create_move(purchase_line=self.purchase_line)
        move_2 = self._create_move(purchase_line=purchase_line_2)
        svl_1, svl_2 = self.env["stock.valuation.layer"].create(
            [
                {
                    "product_id": self.product.id,
                    "company_id": self.env.company.id,
                    "quantity": 10.0,
                    "value": 1000.0,
                    "unit_cost": 100.0,
                    "stock_move_id": move_1.id,
                },
                {
                    "product_id": self.product.id,
                    "company_id": self.env.company.id,
                    "quantity": 5.0,
                    "value": 500.0,
                    "unit_cost": 100.0,
                    "stock_move_id": move_2.id,
                },
            ]
        )
        self.assertEqual(svl_1.vendor_id, self.vendor)
        self.assertEqual(svl_2.vendor_id, vendor_2)
