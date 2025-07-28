# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestShipmentComposer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type_out = cls.wh.out_type_id
        cls.stock_loc = cls.wh.lot_stock_id
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {"name": "test", "type": "product"}
        )
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "warehouse_id": cls.wh.id,
                "note": "test terms",
            }
        )
        cls.sol = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so.id,
                "product_id": cls.product.id,
                "product_uom_qty": 5.0,
                "price_unit": 123.45,
            }
        )
        cls.so.action_confirm()
        cls.picking = cls.so.picking_ids[:1]
        cls.move = cls.picking.move_ids_without_package[:1]
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_loc, 5.0
        )
        cls.picking.action_assign()
        # Adjust scheduled_date to test compute
        cls.picking.scheduled_date = fields.Datetime.now() + timedelta(days=1)
        cls.composer1 = cls.create_composer()
        cls.line1 = cls.create_composer_line(cls.composer1, cls.move, quantity=5.0)

    @classmethod
    def create_composer(cls, partner=None, picking_type=None):
        partner = partner or cls.partner
        picking_type = picking_type or cls.picking_type_out
        return cls.env["stock.shipment.composer"].create(
            {"partner_id": partner.id, "picking_type_id": picking_type.id}
        )

    @classmethod
    def create_composer_line(cls, composer, move, quantity=1.0, price_declared=None):
        return cls.env["stock.shipment.composer.line"].create(
            {
                "composer_id": composer.id,
                "move_id": move.id,
                "quantity": quantity,
                "price_declared": price_declared or move.sale_line_id.price_unit,
            }
        )

    def test_compute_currency_and_amounts_and_note(self):
        self.assertEqual(self.composer1.currency_id, self.so.currency_id)
        self.assertEqual(self.composer1.amount_total, 617.25)
        self.assertEqual(self.composer1.amount_declared_total, 617.25)
        self.assertIn("test terms", self.composer1.note)
        self.assertTrue(all(self.composer1.line_ids.mapped("reserved_enough")))
        self.assertTrue(self.composer1.show_validate)

    def test_compute_scheduled_date(self):
        self.composer1._compute_scheduled_date()
        self.assertEqual(self.composer1.scheduled_date, self.picking.scheduled_date)

    def test_action_confirm_and_assign(self):
        self.assertEqual(self.composer1.state, "draft")
        self.composer1.action_confirm()
        self.assertEqual(self.composer1.state, "in_progress")
        self.picking.do_unreserve()
        self.assertEqual(self.picking.state, "confirmed")
        self.composer1.action_assign()
        self.assertEqual(self.picking.state, "assigned")

    def test_action_done_success_flow(self):
        self.composer1.action_confirm()
        res = self.composer1.action_done()
        self.assertEqual(res, True)
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.composer1.state, "done")
        self.assertTrue(self.composer1.date_done)
        self.assertEqual(self.move.quantity_done, 5.0)
        self.assertEqual(self.move.shipment_composer_id, self.composer1)

    def test_action_done_success_flow_with_backorder(self):
        self.line1.quantity = 3.0
        self.composer2 = self.create_composer()
        self.line2 = self.create_composer_line(self.composer2, self.move, quantity=2.0)
        self.composer1.action_confirm()
        # There should be a wizard asking to process picking without quantity done
        backorder_wizard_dict = self.composer1.action_done()
        self.assertTrue(backorder_wizard_dict)
        backorder_wizard = Form(
            self.env[(backorder_wizard_dict.get("res_model"))].with_context(
                **backorder_wizard_dict["context"]
            )
        ).save()
        self.assertEqual(len(backorder_wizard.pick_ids), 1)
        backorder_wizard.process()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.composer1.state, "done")
        self.assertTrue(self.composer1.date_done)
        self.assertEqual(self.move.quantity_done, 3.0)
        new_move = self.sol.move_ids - self.move
        self.assertEqual(self.line2.move_id, new_move)

    def test_action_done_quantity_zero_error(self):
        # set one line to zero and expect error
        self.line1.quantity = 0.0
        self.composer1.action_confirm()
        with self.assertRaises(UserError):
            self.composer1.action_done()

    def test_action_done_reserved_short_error(self):
        # Reduce availability to 2 (less than the move qty 3)
        # Remove 1 reserved by decreasing available stock and unassign/assign again
        self.picking.do_unreserve()
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_loc, -3.0
        )
        self.picking.action_assign()
        self.composer1.action_confirm()
        with self.assertRaises(UserError):
            self.composer1.action_done()

    def test_picking_button_validate_blocked_by_active_composer(self):
        self.composer1.action_confirm()
        with self.assertRaises(UserError):
            self.picking.button_validate()
        self.composer1.action_cancel()
        self.picking.button_validate()

    def test_write_propagates_actual_date_when_done(self):
        self.composer1.action_confirm()
        self.composer1.action_done()
        past_date = fields.Datetime.now() - timedelta(days=3)
        past_date = fields.Date.to_date(past_date)
        self.composer1.write({"actual_date": past_date})
        self.assertEqual(self.picking.actual_date, past_date)

    def test_quantity_constraint_against_move_qty(self):
        self.line1.quantity = 6.0
        with self.assertRaises(ValidationError):
            self.composer1.action_confirm()
        self.line1.quantity = 4.0
        self.composer2 = self.create_composer()
        self.line2 = self.create_composer_line(self.composer2, self.move, quantity=2.0)
        self.composer1.action_confirm()
        with self.assertRaises(ValidationError):
            self.composer2.action_confirm()
        self.line2.quantity = 1.0
        self.composer2.action_confirm()
        with self.assertRaises(ValidationError):
            self.line2.quantity = 2.0
