# -*- coding: utf-8 -*-

from odoo.tests import common, Form
from odoo.tools import float_compare


@common.tagged('post_install', '-at_install')
class TestDeliveryCost(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.company.write({
            'country_id': self.env.ref('base.us').id,
        })
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.AccountAccount = self.env['account.account']
        self.SaleConfigSetting = self.env['res.config.settings']
        self.Product = self.env['product.product']

        self.partner_18 = self.env['res.partner'].create({'name': 'My Test Customer'})
        self.pricelist = self.env.ref('product.list0')
        self.product_4 = self.env['product.product'].create({'name': 'A product to deliver', 'weight': 1.0})
        self.product_uom_unit = self.env.ref('uom.product_uom_unit')
        self.product_delivery_normal = self.env['product.product'].create({
            'name': 'Normal Delivery Charges',
            'type': 'service',
            'list_price': 10.0,
            'categ_id': self.env.ref('delivery.product_category_deliveries').id,
        })
        self.normal_delivery = self.env['delivery.carrier'].create({
            'name': 'Normal Delivery Charges',
            'fixed_price': 10,
            'delivery_type': 'fixed',
            'product_id': self.product_delivery_normal.id,
        })
        self.partner_4 = self.env['res.partner'].create({'name': 'Another Customer'})
        self.partner_address_13 = self.env['res.partner'].create({
            'name': "Another Customer's Address",
            'parent_id': self.partner_4.id,
        })
        self.product_uom_hour = self.env.ref('uom.product_uom_hour')
        self.account_data = self.env.ref('account.data_account_type_revenue')
        self.account_tag_operating = self.env.ref('account.account_tag_operating')
        self.product_2 = self.env['product.product'].create({'name': 'Zizizaproduct', 'weight': 1.0})
        self.product_category = self.env.ref('product.product_category_all')
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
        # as the tests hereunder assume all the prices in USD, we must ensure
        # that the company actually uses USD
        # We do an invalidate_cache so the cache is aware of it too.
        self.env.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = %s",
            [self.env.ref('base.USD').id, self.env.company.id])
        self.env.company.invalidate_cache()
        self.pricelist.currency_id = self.env.ref('base.USD').id

    def test_00_delivery_cost(self):
        # In order to test Carrier Cost
        # Create sales order with Normal Delivery Charges

        self.sale_normal_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750.00,
            })],
        })
        # I add delivery cost in Sales order

        self.a_sale = self.AccountAccount.create({
            'code': 'X2020',
            'name': 'Product Sales - (test)',
            'user_type_id': self.account_data.id,
            'tag_ids': [(6, 0, {
                self.account_tag_operating.id
            })]
        })

        self.product_consultant = self.Product.create({
            'sale_ok': True,
            'list_price': 75.0,
            'standard_price': 30.0,
            'uom_id': self.product_uom_hour.id,
            'uom_po_id': self.product_uom_hour.id,
            'name': 'Service',
            'categ_id': self.product_category.id,
            'type': 'service'
        })

        # I add delivery cost in Sales order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.sale_normal_delivery_charges.id,
            'default_carrier_id': self.normal_delivery.id
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

        # I check sales order after added delivery cost

        line = self.SaleOrderLine.search([('order_id', '=', self.sale_normal_delivery_charges.id),
            ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost is not Added")

        zin = str(delivery_wizard.display_price) + " " + str(delivery_wizard.delivery_price) + ' ' + line.company_id.country_id.code + line.company_id.name
        self.assertEqual(float_compare(line.price_subtotal, 10.0, precision_digits=2), 0,
            "Delivery cost does not correspond to 10.0. %s %s" % (line.price_subtotal, zin))

        # I confirm the sales order

        self.sale_normal_delivery_charges.action_confirm()

        # Create one more sales order with Free Delivery Charges

        self.delivery_sale_order_cost = self.SaleOrder.create({
            'partner_id': self.partner_4.id,
            'partner_invoice_id': self.partner_address_13.id,
            'partner_shipping_id': self.partner_address_13.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'Service on demand',
                'product_id': self.product_consultant.id,
                'product_uom_qty': 24,
                'product_uom': self.product_uom_hour.id,
                'price_unit': 75.00,
            }), (0, 0, {
                'name': 'On Site Assistance',
                'product_id': self.product_2.id,
                'product_uom_qty': 30,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 38.25,
            })],
        })

        # I add free delivery cost in Sales order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.delivery_sale_order_cost.id,
            'default_carrier_id': self.free_delivery.id
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

        # I check sales order after adding delivery cost
        line = self.SaleOrderLine.search([('order_id', '=', self.delivery_sale_order_cost.id),
            ('product_id', '=', self.free_delivery.product_id.id)])

        self.assertEqual(len(line), 1, "Delivery cost is not Added")
        self.assertEqual(float_compare(line.price_subtotal, 0, precision_digits=2), 0,
            "Delivery cost is not correspond.")

        # I set default delivery policy

        self.default_delivery_policy = self.SaleConfigSetting.create({})

        self.default_delivery_policy.execute()

    def test_01_delivery_cost_from_pricelist(self):
        """ This test aims to validate the use of a pricelist to compute the delivery cost in the case the associated
            product of the shipping method is defined in the pricelist """

        # Create pricelist with a custom price for the standard shipping method
        my_pricelist = self.env['product.pricelist'].create({
            'name': 'shipping_cost_change',
            'item_ids': [(0, 0, {
                'compute_price': 'fixed',
                'fixed_price': 5,
                'applied_on': '0_product_variant',
                'product_id': self.normal_delivery.product_id.id,
            })],
        })

        # Create sales order with Normal Delivery Charges
        sale_pricelist_based_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'pricelist_id': my_pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750.00,
            })],
        })

        # Add of delivery cost in Sales order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': sale_pricelist_based_delivery_charges.id,
            'default_carrier_id': self.normal_delivery.id
        }))
        self.assertEqual(delivery_wizard.delivery_price, 5.0, "Delivery cost does not correspond to 5.0 in wizard")
        delivery_wizard.save().button_confirm()

        line = self.SaleOrderLine.search([('order_id', '=', sale_pricelist_based_delivery_charges.id),
                                          ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost hasn't been added to SO")
        self.assertEqual(line.price_subtotal, 5.0, "Delivery cost does not correspond to 5.0")

    def test_02_delivery_cost_from_different_currency(self):
        """ This test aims to validate the use of a pricelist using a different currency to compute the delivery cost in
            the case the associated product of the shipping method is defined in the pricelist """

        # Create pricelist with a custom price for the standard shipping method
        my_pricelist = self.env['product.pricelist'].create({
            'name': 'shipping_cost_change',
            'item_ids': [(0, 0, {
                'compute_price': 'fixed',
                'fixed_price': 5,
                'applied_on': '0_product_variant',
                'product_id': self.normal_delivery.product_id.id,
            })],
            'currency_id': self.env.ref('base.EUR').id,
        })

        # Create sales order with Normal Delivery Charges
        sale_pricelist_based_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'pricelist_id': my_pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750.00,
            })],
        })

        # Add of delivery cost in Sales order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': sale_pricelist_based_delivery_charges.id,
            'default_carrier_id': self.normal_delivery.id
        }))
        self.assertEqual(delivery_wizard.delivery_price, 5.0, "Delivery cost does not correspond to 5.0 in wizard")
        delivery_wizard.save().button_confirm()

        line = self.SaleOrderLine.search([('order_id', '=', sale_pricelist_based_delivery_charges.id),
                                          ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost hasn't been added to SO")
        self.assertEqual(line.price_subtotal, 5.0, "Delivery cost does not correspond to 5.0")

    def test_01_taxes_on_delivery_cost(self):

        # Creating taxes and fiscal position

        tax_price_include = self.env['account.tax'].create({
            'name': '10% inc',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 10,
            'price_include': True,
            'include_base_amount': True,
        })
        tax_price_exclude = self.env['account.tax'].create({
            'name': '15% exc',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 15,
        })

        fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'fiscal_pos_a',
            'tax_ids': [
                (0, None, {
                    'tax_src_id': tax_price_include.id,
                    'tax_dest_id': tax_price_exclude.id,
                }),
            ],
        })

        # Setting tax on delivery product
        self.normal_delivery.product_id.taxes_id = tax_price_include

        # Create sales order
        order_form = Form(self.env['sale.order'].with_context(tracking_disable=True))
        order_form.partner_id = self.partner_18
        order_form.pricelist_id = self.pricelist
        order_form.fiscal_position_id = fiscal_position

        # Try adding delivery product as a normal product
        with order_form.order_line.new() as line:
            line.product_id = self.normal_delivery.product_id
            line.product_uom_qty = 1.0
            line.product_uom = self.product_uom_unit
        sale_order = order_form.save()

        self.assertRecordValues(sale_order.order_line, [{'price_subtotal': 9.09, 'price_total': 10.45}])

        # Now trying to add the delivery line using the delivery wizard, the results should be the same as before
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context(default_order_id=sale_order.id,
                          default_carrier_id=self.normal_delivery.id))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

        line = self.SaleOrderLine.search([
            ('order_id', '=', sale_order.id),
            ('product_id', '=', self.normal_delivery.product_id.id),
            ('is_delivery', '=', True)
        ])

        self.assertRecordValues(line, [{'price_subtotal': 9.09, 'price_total': 10.45}])

    def test_add_carrier_on_picking(self):
        """
        A user confirms a SO, then adds a carrier on the picking. The invoicing
        policy of the carrier is set to "Real Cost". He then confirms the
        picking: a line with the carrier cost should be added to the SO
        """
        self.normal_delivery.invoice_policy = 'real'

        so_form = Form(self.env['sale.order'])
        so_form.partner_id = self.partner_4
        with so_form.order_line.new() as line:
            line.product_id = self.product_2
        so = so_form.save()
        so.action_confirm()

        picking = so.picking_ids
        picking.carrier_id = self.normal_delivery
        picking.move_lines.quantity_done = 1
        picking.button_validate()

        so.order_line.invalidate_cache(ids=so.order_line.ids)

        self.assertEqual(picking.state, 'done')
        self.assertRecordValues(so.order_line, [
            {'product_id': self.product_2.id, 'is_delivery': False, 'product_uom_qty': 1, 'qty_delivered': 1},
            {'product_id': self.normal_delivery.product_id.id, 'is_delivery': True, 'product_uom_qty': 1, 'qty_delivered': 0},
        ])


    def test_delivery_cost_gift_card(self):
        """
        A customer has a carrier with the amount greater than the one to have
        free shipping cost, then uses a gift card that lowers that amount to less
        than the threshold: the shipping cost should still be 0.0
        """

        if "gift.card" not in self.env:
            return

        product_delivery_free = self.env['product.product'].create({
            'name': 'Free Delivery Charges',
            'type': 'service',
            'list_price': 40.0,
            'categ_id': self.env.ref('delivery.product_category_deliveries').id,
        })
        free_delivery = self.env['delivery.carrier'].create({
            'name': 'Delivery Now Free Over 100',
            'fixed_price': 40,
            'delivery_type': 'fixed',
            'product_id': product_delivery_free.id,
            'free_over': True,
            'amount': 100,
        })


        sale_normal_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 120.00,
            })],
        })
        gift_card = self.env['gift.card'].create({
            'initial_amount': 40,
        })
        sale_normal_delivery_charges._pay_with_gift_card(gift_card)

        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': sale_normal_delivery_charges.id,
            'default_carrier_id': free_delivery.id
        }))
        delivery_wizard.save().button_confirm()

        self.assertEqual(len(sale_normal_delivery_charges.order_line), 3)
        self.assertEqual(sale_normal_delivery_charges.amount_untaxed, 80.0, "Delivery cost is not Added")

    def test_estimated_weight(self):
        """
        Test that negative qty SO lines are not included in the estimated weight calculation
        of delivery carriers (since it's used when calculating their rates).
        """
        sale_order = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'name': 'SO - neg qty',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_4.id,
                    'product_uom_qty': 1,
                    'product_uom': self.product_uom_unit.id,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': -1,
                    'product_uom': self.product_uom_unit.id,
                })],
        })
        shipping_weight = sale_order._get_estimated_weight()
        self.assertEqual(shipping_weight, self.product_4.weight, "Only positive quantity products' weights should be included in estimated weight")

    def test_price_with_weight_volume_variable(self):
        """ Test that the price is correctly computed when the variable is weight*volume. """
        qty = 3
        list_price = 2
        volume = 2.5
        weight = 1.5
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_18.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.env['product.product'].create({
                        'name': 'wv',
                        'weight': weight,
                        'volume': volume,
                    }).id,
                    'product_uom_qty': qty,
                    'product_uom': self.product_uom_unit.id,
                }),
            ],
        })
        delivery = self.env['delivery.carrier'].create({
            'name': 'Delivery Charges',
            'delivery_type': 'base_on_rule',
            'product_id': self.product_delivery_normal.id,
            'price_rule_ids': [(0, 0, {
                'variable': 'price',
                'operator': '>=',
                'max_value': 0,
                'list_price': list_price,
                'variable_factor': 'wv',
            })]
        })
        self.assertEqual(
            delivery._get_price_available(sale_order),
            qty * list_price * weight * volume,
            "The shipping price is not correctly computed with variable weight*volume.",
        )
