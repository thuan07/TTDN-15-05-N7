# -*- coding: utf-8 -*-
# pylint: disable=bad-whitespace
from freezegun import freeze_time
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import Form
from odoo.tests import tagged
from odoo import fields, Command
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

@tagged('post_install', '-at_install')
class TestAccountMoveInInvoiceOnchanges(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.invoice = cls.init_invoice('in_invoice', products=cls.product_a+cls.product_b)

        cls.product_line_vals_1 = {
            'name': cls.product_a.name,
            'product_id': cls.product_a.id,
            'account_id': cls.product_a.property_account_expense_id.id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': cls.product_a.uom_id.id,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 800.0,
            'price_subtotal': 800.0,
            'price_total': 920.0,
            'tax_ids': cls.product_a.supplier_taxes_id.ids,
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': 800.0,
            'debit': 800.0,
            'credit': 0.0,
            'date_maturity': False,
        }
        cls.product_line_vals_2 = {
            'name': cls.product_b.name,
            'product_id': cls.product_b.id,
            'account_id': cls.product_b.property_account_expense_id.id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': cls.product_b.uom_id.id,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 160.0,
            'price_subtotal': 160.0,
            'price_total': 208.0,
            'tax_ids': cls.product_b.supplier_taxes_id.ids,
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': 160.0,
            'debit': 160.0,
            'credit': 0.0,
            'date_maturity': False,
        }
        cls.tax_line_vals_1 = {
            'name': cls.tax_purchase_a.name,
            'product_id': False,
            'account_id': cls.company_data['default_account_tax_purchase'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 144.0,
            'price_subtotal': 144.0,
            'price_total': 144.0,
            'tax_ids': [],
            'tax_line_id': cls.tax_purchase_a.id,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': 144.0,
            'debit': 144.0,
            'credit': 0.0,
            'date_maturity': False,
        }
        cls.tax_line_vals_2 = {
            'name': cls.tax_purchase_b.name,
            'product_id': False,
            'account_id': cls.company_data['default_account_tax_purchase'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 24.0,
            'price_subtotal': 24.0,
            'price_total': 24.0,
            'tax_ids': [],
            'tax_line_id': cls.tax_purchase_b.id,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': 24.0,
            'debit': 24.0,
            'credit': 0.0,
            'date_maturity': False,
        }
        cls.term_line_vals_1 = {
            'name': '',
            'product_id': False,
            'account_id': cls.company_data['default_account_payable'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': -1128.0,
            'price_subtotal': -1128.0,
            'price_total': -1128.0,
            'tax_ids': [],
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': -1128.0,
            'debit': 0.0,
            'credit': 1128.0,
            'date_maturity': fields.Date.from_string('2019-01-01'),
        }
        cls.move_vals = {
            'partner_id': cls.partner_a.id,
            'currency_id': cls.company_data['currency'].id,
            'journal_id': cls.company_data['default_journal_purchase'].id,
            'date': fields.Date.from_string('2019-01-01'),
            'fiscal_position_id': False,
            'payment_reference': '',
            'invoice_payment_term_id': cls.pay_terms_a.id,
            'amount_untaxed': 960.0,
            'amount_tax': 168.0,
            'amount_total': 1128.0,
        }
        (cls.tax_armageddon + cls.tax_armageddon.children_tax_ids).write({'type_tax_use': 'purchase'})

    def setUp(self):
        super(TestAccountMoveInInvoiceOnchanges, self).setUp()
        self.assertInvoiceValues(self.invoice, [
            self.product_line_vals_1,
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

    def test_in_invoice_onchange_invoice_date(self):
        for tax_date, invoice_date, accounting_date in [
            ('2019-03-31', '2019-05-12', '2019-05-31'),
            ('2019-03-31', '2019-02-10', '2019-04-30'),
            ('2019-05-31', '2019-06-15', '2019-06-30'),
        ]:
            self.invoice.company_id.tax_lock_date = tax_date
            with Form(self.invoice) as move_form:
                move_form.invoice_date = invoice_date
            self.assertEqual(self.invoice.date, fields.Date.to_date(accounting_date))

    @freeze_time('2021-09-16')
    def test_in_invoice_onchange_invoice_date_2(self):
        invoice_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice', account_predictive_bills_disable_prediction=True))
        invoice_form.partner_id = self.partner_a
        invoice_form.invoice_payment_term_id = self.env.ref('account.account_payment_term_30days')
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
        invoice_form.invoice_date = fields.Date.from_string('2021-09-01')
        invoice = invoice_form.save()

        self.assertRecordValues(invoice, [{
            'date': fields.Date.from_string('2021-09-16'),
            'invoice_date': fields.Date.from_string('2021-09-01'),
            'invoice_date_due': fields.Date.from_string('2021-10-01'),
        }])

    def test_in_invoice_line_onchange_product_1(self):
        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.product_id = self.product_b
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'name': self.product_b.name,
                'product_id': self.product_b.id,
                'product_uom_id': self.product_b.uom_id.id,
                'account_id': self.product_b.property_account_expense_id.id,
                'price_unit': 160.0,
                'price_subtotal': 160.0,
                'price_total': 208.0,
                'tax_ids': self.product_b.supplier_taxes_id.ids,
                'amount_currency': 160.0,
                'debit': 160.0,
            },
            self.product_line_vals_2,
            {
                **self.tax_line_vals_1,
                'price_unit': 48.0,
                'price_subtotal': 48.0,
                'price_total': 48.0,
                'amount_currency': 48.0,
                'debit': 48.0,
            },
            {
                **self.tax_line_vals_2,
                'price_unit': 48.0,
                'price_subtotal': 48.0,
                'price_total': 48.0,
                'amount_currency': 48.0,
                'debit': 48.0,
            },
            {
                **self.term_line_vals_1,
                'price_unit': -416.0,
                'price_subtotal': -416.0,
                'price_total': -416.0,
                'amount_currency': -416.0,
                'credit': 416.0,
            },
        ], {
            **self.move_vals,
            'amount_untaxed': 320.0,
            'amount_tax': 96.0,
            'amount_total': 416.0,
        })

    def test_in_invoice_line_onchange_product_2_with_fiscal_pos(self):
        ''' Test mapping a price-included tax (10%) with a price-excluded tax (20%) on a price_unit of 110.0.
        The price_unit should be 100.0 after applying the fiscal position.
        '''
        tax_price_include = self.env['account.tax'].create({
            'name': '10% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10,
            'price_include': True,
            'include_base_amount': True,
        })
        tax_price_exclude = self.env['account.tax'].create({
            'name': '15% excl',
            'type_tax_use': 'purchase',
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

        product = self.env['product.product'].create({
            'name': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 110.0,
            'supplier_taxes_id': [(6, 0, tax_price_include.ids)],
        })

        move_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice'))
        move_form.partner_id = self.partner_a
        move_form.invoice_date = fields.Date.from_string('2019-01-01')
        move_form.currency_id = self.currency_data['currency']
        move_form.fiscal_position_id = fiscal_position
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = product
        invoice = move_form.save()

        self.assertInvoiceValues(invoice, [
            {
                'product_id': product.id,
                'price_unit': 200.0,
                'price_subtotal': 200.0,
                'price_total': 230.0,
                'tax_ids': tax_price_exclude.ids,
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 200.0,
                'debit': 100.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 30.0,
                'price_subtotal': 30.0,
                'price_total': 30.0,
                'tax_ids': [],
                'tax_line_id': tax_price_exclude.id,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 30.0,
                'debit': 15.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': -230.0,
                'price_subtotal': -230.0,
                'price_total': -230.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -230.0,
                'debit': 0.0,
                'credit': 115.0,
            },
        ], {
            'currency_id': self.currency_data['currency'].id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 200.0,
            'amount_tax': 30.0,
            'amount_total': 230.0,
        })

        uom_dozen = self.env.ref('uom.product_uom_dozen')
        with Form(invoice) as move_form:
            with move_form.invoice_line_ids.edit(0) as line_form:
                line_form.product_uom_id = uom_dozen

        self.assertInvoiceValues(invoice, [
            {
                'product_id': product.id,
                'product_uom_id': uom_dozen.id,
                'price_unit': 2400.0,
                'price_subtotal': 2400.0,
                'price_total': 2760.0,
                'tax_ids': tax_price_exclude.ids,
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 2400.0,
                'debit': 1200.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 360.0,
                'price_subtotal': 360.0,
                'price_total': 360.0,
                'tax_ids': [],
                'tax_line_id': tax_price_exclude.id,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 360.0,
                'debit': 180.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': -2760.0,
                'price_subtotal': -2760.0,
                'price_total': -2760.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -2760.0,
                'debit': 0.0,
                'credit': 1380.0,
            },
        ], {
            'currency_id': self.currency_data['currency'].id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 2400.0,
            'amount_tax': 360.0,
            'amount_total': 2760.0,
        })

    def test_in_invoice_line_onchange_product_2_with_fiscal_pos_2(self):
        ''' Test mapping a price-included tax (10%) with another price-included tax (20%) on a price_unit of 110.0.
        The price_unit should be 120.0 after applying the fiscal position.
        '''
        tax_price_include_1 = self.env['account.tax'].create({
            'name': '10% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10,
            'price_include': True,
            'include_base_amount': True,
        })
        tax_price_include_2 = self.env['account.tax'].create({
            'name': '20% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 20,
            'price_include': True,
            'include_base_amount': True,
        })

        fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'fiscal_pos_a',
            'tax_ids': [
                (0, None, {
                    'tax_src_id': tax_price_include_1.id,
                    'tax_dest_id': tax_price_include_2.id,
                }),
            ],
        })

        product = self.env['product.product'].create({
            'name': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 110.0,
            'supplier_taxes_id': [(6, 0, tax_price_include_1.ids)],
        })

        move_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice'))
        move_form.partner_id = self.partner_a
        move_form.invoice_date = fields.Date.from_string('2019-01-01')
        move_form.currency_id = self.currency_data['currency']
        move_form.fiscal_position_id = fiscal_position
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = product
        invoice = move_form.save()

        self.assertInvoiceValues(invoice, [
            {
                'product_id': product.id,
                'price_unit': 240.0,
                'price_subtotal': 200.0,
                'price_total': 240.0,
                'tax_ids': tax_price_include_2.ids,
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 200.0,
                'debit': 100.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 40.0,
                'price_subtotal': 40.0,
                'price_total': 40.0,
                'tax_ids': [],
                'tax_line_id': tax_price_include_2.id,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 40.0,
                'debit': 20.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': -240.0,
                'price_subtotal': -240.0,
                'price_total': -240.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -240.0,
                'debit': 0.0,
                'credit': 120.0,
            },
        ], {
            'currency_id': self.currency_data['currency'].id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 200.0,
            'amount_tax': 40.0,
            'amount_total': 240.0,
        })

        uom_dozen = self.env.ref('uom.product_uom_dozen')
        with Form(invoice) as move_form:
            with move_form.invoice_line_ids.edit(0) as line_form:
                line_form.product_uom_id = uom_dozen

        self.assertInvoiceValues(invoice, [
            {
                'product_id': product.id,
                'product_uom_id': uom_dozen.id,
                'price_unit': 2880.0,
                'price_subtotal': 2400.0,
                'price_total': 2880.0,
                'tax_ids': tax_price_include_2.ids,
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 2400.0,
                'debit': 1200.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 480.0,
                'price_subtotal': 480.0,
                'price_total': 480.0,
                'tax_ids': [],
                'tax_line_id': tax_price_include_2.id,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 480.0,
                'debit': 240.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': -2880.0,
                'price_subtotal': -2880.0,
                'price_total': -2880.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -2880.0,
                'debit': 0.0,
                'credit': 1440.0,
            },
        ], {
            'currency_id': self.currency_data['currency'].id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 2400.0,
            'amount_tax': 480.0,
            'amount_total': 2880.0,
        })

    def test_in_invoice_line_onchange_business_fields_1(self):
        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            # Current price_unit is 800.
            # We set quantity = 4, discount = 50%, price_unit = 400. The debit/credit fields don't change because (4 * 400) * 0.5 = 800.
            line_form.quantity = 4
            line_form.discount = 50
            line_form.price_unit = 400
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'quantity': 4,
                'discount': 50.0,
                'price_unit': 400.0,
            },
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

        move_form = Form(self.invoice)
        with move_form.line_ids.edit(2) as line_form:
            # Reset field except the discount that becomes 100%.
            # /!\ The modification is made on the accounting tab.
            line_form.quantity = 1
            line_form.discount = 100
            line_form.price_unit = 800
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'discount': 100.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'amount_currency': 0.0,
                'debit': 0.0,
            },
            self.product_line_vals_2,
            {
                **self.tax_line_vals_1,
                'price_unit': 24.0,
                'price_subtotal': 24.0,
                'price_total': 24.0,
                'amount_currency': 24.0,
                'debit': 24.0,
            },
            self.tax_line_vals_2,
            {
                **self.term_line_vals_1,
                'price_unit': -208.0,
                'price_subtotal': -208.0,
                'price_total': -208.0,
                'amount_currency': -208.0,
                'credit': 208.0,
            },
        ], {
            **self.move_vals,
            'amount_untaxed': 160.0,
            'amount_tax': 48.0,
            'amount_total': 208.0,
        })

    def test_in_invoice_line_onchange_accounting_fields_1(self):
        move_form = Form(self.invoice)
        with move_form.line_ids.edit(2) as line_form:
            # Custom debit on the first product line.
            line_form.debit = 3000
        with move_form.line_ids.edit(3) as line_form:
            # Custom credit on the second product line. Credit should be reset by onchange.
            # /!\ It's a negative line.
            line_form.credit = 500
        with move_form.line_ids.edit(0) as line_form:
            # Custom debit on the first tax line.
            line_form.debit = 800
        with move_form.line_ids.edit(4) as line_form:
            # Custom debit on the second tax line.
            line_form.debit = 250
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'price_unit': 3000.0,
                'price_subtotal': 3000.0,
                'price_total': 3450.0,
                'amount_currency': 3000.0,
                'debit': 3000.0,
            },
            {
                **self.product_line_vals_2,
                'price_unit': -500.0,
                'price_subtotal': -500.0,
                'price_total': -650.0,
                'amount_currency': -500.0,
                'debit': 0.0,
                'credit': 500.0,
            },
            {
                **self.tax_line_vals_1,
                'price_unit': 800.0,
                'price_subtotal': 800.0,
                'price_total': 800.0,
                'amount_currency': 800.0,
                'debit': 800.0,
            },
            {
                **self.tax_line_vals_2,
                'price_unit': 250.0,
                'price_subtotal': 250.0,
                'price_total': 250.0,
                'amount_currency': 250.0,
                'debit': 250.0,
            },
            {
                **self.term_line_vals_1,
                'price_unit': -3550.0,
                'price_subtotal': -3550.0,
                'price_total': -3550.0,
                'amount_currency': -3550.0,
                'credit': 3550.0,
            },
        ], {
            **self.move_vals,
            'amount_untaxed': 2500.0,
            'amount_tax': 1050.0,
            'amount_total': 3550.0,
        })

    def test_in_invoice_line_onchange_partner_1(self):
        move_form = Form(self.invoice)
        move_form.partner_id = self.partner_b
        move_form.payment_reference = 'turlututu'
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'partner_id': self.partner_b.id,
            },
            {
                **self.product_line_vals_2,
                'partner_id': self.partner_b.id,
            },
            {
                **self.tax_line_vals_1,
                'partner_id': self.partner_b.id,
            },
            {
                **self.tax_line_vals_2,
                'partner_id': self.partner_b.id,
            },
            {
                **self.term_line_vals_1,
                'name': 'turlututu',
                'partner_id': self.partner_b.id,
                'account_id': self.partner_b.property_account_payable_id.id,
                'price_unit': -789.6,
                'price_subtotal': -789.6,
                'price_total': -789.6,
                'amount_currency': -789.6,
                'credit': 789.6,
                'date_maturity': fields.Date.from_string('2019-02-28'),
            },
            {
                **self.term_line_vals_1,
                'name': 'turlututu',
                'partner_id': self.partner_b.id,
                'account_id': self.partner_b.property_account_payable_id.id,
                'price_unit': -338.4,
                'price_subtotal': -338.4,
                'price_total': -338.4,
                'amount_currency': -338.4,
                'credit': 338.4,
            },
        ], {
            **self.move_vals,
            'partner_id': self.partner_b.id,
            'payment_reference': 'turlututu',
            'fiscal_position_id': self.fiscal_pos_a.id,
            'invoice_payment_term_id': self.pay_terms_b.id,
            'amount_untaxed': 960.0,
            'amount_tax': 168.0,
            'amount_total': 1128.0,
        })

        # Remove lines and recreate them to apply the fiscal position.
        move_form = Form(self.invoice)
        move_form.invoice_line_ids.remove(0)
        move_form.invoice_line_ids.remove(0)
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_b
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'account_id': self.product_b.property_account_expense_id.id,
                'partner_id': self.partner_b.id,
                'tax_ids': self.tax_purchase_b.ids,
            },
            {
                **self.product_line_vals_2,
                'partner_id': self.partner_b.id,
                'price_total': 184.0,
                'tax_ids': self.tax_purchase_b.ids,
            },
            {
                **self.tax_line_vals_1,
                'name': self.tax_purchase_b.name,
                'partner_id': self.partner_b.id,
                'tax_line_id': self.tax_purchase_b.id,
            },
            {
                **self.term_line_vals_1,
                'name': 'turlututu',
                'account_id': self.partner_b.property_account_payable_id.id,
                'partner_id': self.partner_b.id,
                'price_unit': -772.8,
                'price_subtotal': -772.8,
                'price_total': -772.8,
                'amount_currency': -772.8,
                'credit': 772.8,
                'date_maturity': fields.Date.from_string('2019-02-28'),
            },
            {
                **self.term_line_vals_1,
                'name': 'turlututu',
                'account_id': self.partner_b.property_account_payable_id.id,
                'partner_id': self.partner_b.id,
                'price_unit': -331.2,
                'price_subtotal': -331.2,
                'price_total': -331.2,
                'amount_currency': -331.2,
                'credit': 331.2,
            },
        ], {
            **self.move_vals,
            'partner_id': self.partner_b.id,
            'payment_reference': 'turlututu',
            'fiscal_position_id': self.fiscal_pos_a.id,
            'invoice_payment_term_id': self.pay_terms_b.id,
            'amount_untaxed': 960.0,
            'amount_tax': 144.0,
            'amount_total': 1104.0,
        })

    def test_in_invoice_line_onchange_taxes_1(self):
        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 960
            line_form.tax_ids.add(self.tax_armageddon)
        move_form.save()

        child_tax_1 = self.tax_armageddon.children_tax_ids[0]
        child_tax_2 = self.tax_armageddon.children_tax_ids[1]

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'price_unit': 960.0,
                'price_subtotal': 800.0,
                'price_total': 1176.0,
                'tax_ids': (self.tax_purchase_a + self.tax_armageddon).ids,
            },
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            {
                'name': child_tax_1.name,
                'product_id': False,
                'account_id': self.company_data['default_account_tax_sale'].id,
                'partner_id': self.partner_a.id,
                'product_uom_id': False,
                'quantity': 1.0,
                'discount': 0.0,
                'price_unit': 64.0,
                'price_subtotal': 64.0,
                'price_total': 70.4,
                'tax_ids': child_tax_2.ids,
                'tax_line_id': child_tax_1.id,
                'currency_id': self.company_data['currency'].id,
                'amount_currency': 64.0,
                'debit': 64.0,
                'credit': 0.0,
                'date_maturity': False,
            },
            {
                'name': child_tax_1.name,
                'product_id': False,
                'account_id': self.company_data['default_account_expense'].id,
                'partner_id': self.partner_a.id,
                'product_uom_id': False,
                'quantity': 1.0,
                'discount': 0.0,
                'price_unit': 96.0,
                'price_subtotal': 96.0,
                'price_total': 105.6,
                'tax_ids': child_tax_2.ids,
                'tax_line_id': child_tax_1.id,
                'currency_id': self.company_data['currency'].id,
                'amount_currency': 96.0,
                'debit': 96.0,
                'credit': 0.0,
                'date_maturity': False,
            },
            {
                'name': child_tax_2.name,
                'product_id': False,
                'account_id': child_tax_2.cash_basis_transition_account_id.id,
                'partner_id': self.partner_a.id,
                'product_uom_id': False,
                'quantity': 1.0,
                'discount': 0.0,
                'price_unit': 96.0,
                'price_subtotal': 96.0,
                'price_total': 96.0,
                'tax_ids': [],
                'tax_line_id': child_tax_2.id,
                'currency_id': self.company_data['currency'].id,
                'amount_currency': 96.0,
                'debit': 96.0,
                'credit': 0.0,
                'date_maturity': False,
            },
            {
                **self.term_line_vals_1,
                'price_unit': -1384.0,
                'price_subtotal': -1384.0,
                'price_total': -1384.0,
                'amount_currency': -1384.0,
                'credit': 1384.0,
            },
        ], {
            **self.move_vals,
            'amount_untaxed': 960.0,
            'amount_tax': 424.0,
            'amount_total': 1384.0,
        })

    def test_compute_cash_rounding_lines(self):
        cash_rounding_add_invoice_line = self.env['account.cash.rounding'].create({
            'name': 'Add invoice line Rounding Down',
            'rounding': .1,
            'strategy': 'add_invoice_line',
            'profit_account_id': self.company_data['default_account_revenue'].id,
            'loss_account_id': self.company_data['default_account_expense'].id,
            'rounding_method': 'DOWN',
        })
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2019-01-01',
            'invoice_cash_rounding_id': cash_rounding_add_invoice_line.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'line',
                    'price_unit': 295,
                }),
                Command.create({
                    'name': 'cost',
                    'price_unit': 280.33,
                }),
                Command.create({
                    'name': 'cost neg',
                    'price_unit': -280.33,
                }),
            ],
        })
        self.assertFalse(move.line_ids.filtered(lambda line: line.is_rounding_line))

    def test_in_invoice_line_onchange_cash_rounding_1(self):
        # Test 'add_invoice_line' rounding
        move_form = Form(self.invoice)
        # Add a cash rounding having 'add_invoice_line'.
        move_form.invoice_cash_rounding_id = self.cash_rounding_a
        move_form.save()

        # The cash rounding does nothing as the total is already rounded.
        self.assertInvoiceValues(self.invoice, [
            self.product_line_vals_1,
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 799.99
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                'name': 'add_invoice_line',
                'product_id': False,
                'account_id': self.cash_rounding_a.loss_account_id.id,
                'partner_id': self.partner_a.id,
                'product_uom_id': False,
                'quantity': 1.0,
                'discount': 0.0,
                'price_unit': 0.01,
                'price_subtotal': 0.01,
                'price_total': 0.01,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.company_data['currency'].id,
                'amount_currency': 0.01,
                'debit': 0.01,
                'credit': 0.0,
                'date_maturity': False,
            },
            {
                **self.product_line_vals_1,
                'price_unit': 799.99,
                'price_subtotal': 799.99,
                'price_total': 919.99,
                'amount_currency': 799.99,
                'debit': 799.99,
            },
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

        # Test 'biggest_tax' rounding

        self.company_data['company'].country_id = self.env.ref('base.us')

        # Add a tag to product_a's default tax
        tax_line_tag = self.env['account.account.tag'].create({
            'name': "Tax tag",
            'applicability': 'taxes',
            'country_id': self.company_data['company'].country_id.id,
        })

        repartition_line = self.tax_purchase_a.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax')
        repartition_line.write({'tag_ids': [(4, tax_line_tag.id, 0)]})

        # Create the invoice
        biggest_tax_invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'invoice_date': '2019-01-01',
            'partner_id': self.partner_a.id,
            'invoice_cash_rounding_id': self.cash_rounding_b.id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 799.99,
                    'tax_ids': [(6, 0, self.product_a.supplier_taxes_id.ids)],
                    'product_uom_id':  self.product_a.uom_id.id,
                }),

                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': self.product_b.standard_price,
                    'tax_ids': [(6, 0, self.product_b.supplier_taxes_id.ids)],
                    'product_uom_id':  self.product_b.uom_id.id,
                }),
            ],
        })

        self.assertInvoiceValues(biggest_tax_invoice, [
            {
                **self.product_line_vals_1,
                'price_unit': 799.99,
                'price_subtotal': 799.99,
                'price_total': 919.99,
                'amount_currency': 799.99,
                'debit': 799.99,
                'tax_repartition_line_id': None,
                'tax_tag_ids': [],
            },
            {
                **self.product_line_vals_2,
                'tax_repartition_line_id': None,
                'tax_tag_ids': [],
            },
            {
                **self.tax_line_vals_1,
                'tax_repartition_line_id': repartition_line.id,
                'tax_tag_ids': tax_line_tag.ids,
            },
            {
                **self.tax_line_vals_2,
                'tax_repartition_line_id': self.tax_purchase_b.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax').id,
                'tax_tag_ids': [],
            },
            {
                'name': '%s (rounding)' % self.tax_purchase_a.name,
                'product_id': False,
                'account_id': self.company_data['default_account_tax_purchase'].id,
                'partner_id': self.partner_a.id,
                'product_uom_id': False,
                'quantity': 1.0,
                'discount': 0.0,
                'price_unit': -0.04,
                'price_subtotal': -0.04,
                'price_total': -0.04,
                'tax_ids': [],
                'tax_line_id': self.tax_purchase_a.id,
                'tax_repartition_line_id': repartition_line.id,
                'tax_tag_ids': tax_line_tag.ids,
                'currency_id': self.company_data['currency'].id,
                'amount_currency': -0.04,
                'debit': 0.0,
                'credit': 0.04,
                'date_maturity': False,
            },
            {
                **self.term_line_vals_1,
                'price_unit': -1127.95,
                'price_subtotal': -1127.95,
                'price_total': -1127.95,
                'amount_currency': -1127.95,
                'credit': 1127.95,
                'tax_repartition_line_id': None,
                'tax_tag_ids': [],
            },
        ], {
            **self.move_vals,
            'amount_untaxed': 959.99,
            'amount_tax': 167.96,
            'amount_total': 1127.95,
        })

    def test_in_invoice_line_onchange_currency_1(self):
        move_form = Form(self.invoice)
        move_form.currency_id = self.currency_data['currency']
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 800.0,
                'debit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 144.0,
                'debit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1128.0,
                'credit': 564.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })

        move_form = Form(self.invoice)
        # Change the date to get another rate: 1/3 instead of 1/2.
        move_form.date = fields.Date.from_string('2016-01-01')
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 800.0,
                'debit': 266.67,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 53.33,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 144.0,
                'debit': 48.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 8.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1128.0,
                'credit': 376.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
            'date': fields.Date.from_string('2016-01-01'),
        })

        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            # 0.045 * 0.1 = 0.0045. As the foreign currency has a 0.001 rounding,
            # the result should be 0.005 after rounding.
            line_form.quantity = 0.1
            line_form.price_unit = 0.045
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'quantity': 0.1,
                'price_unit': 0.05,
                'price_subtotal': 0.005,
                'price_total': 0.006,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 0.005,
                'debit': 0.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 53.33,
            },
            {
                **self.tax_line_vals_1,
                'price_unit': 24.0,
                'price_subtotal': 24.001,
                'price_total': 24.001,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.001,
                'debit': 8.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 8.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'price_unit': -208.01,
                'price_subtotal': -208.006,
                'price_total': -208.006,
                'amount_currency': -208.006,
                'credit': 69.33,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
            'date': fields.Date.from_string('2016-01-01'),
            'amount_untaxed': 160.005,
            'amount_tax': 48.001,
            'amount_total': 208.006,
        })

        # Exit the multi-currencies.
        move_form = Form(self.invoice)
        move_form.currency_id = self.company_data['currency']
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            {
                **self.product_line_vals_1,
                'quantity': 0.1,
                'price_unit': 0.05,
                'price_subtotal': 0.01,
                'price_total': 0.01,
                'amount_currency': 0.01,
                'debit': 0.01,
            },
            self.product_line_vals_2,
            {
                **self.tax_line_vals_1,
                'price_unit': 24.0,
                'price_subtotal': 24.0,
                'price_total': 24.0,
                'amount_currency': 24.0,
                'debit': 24.0,
            },
            self.tax_line_vals_2,
            {
                **self.term_line_vals_1,
                'price_unit': -208.01,
                'price_subtotal': -208.01,
                'price_total': -208.01,
                'amount_currency': -208.01,
                'credit': 208.01,
            },
        ], {
            **self.move_vals,
            'currency_id': self.company_data['currency'].id,
            'date': fields.Date.from_string('2016-01-01'),
            'amount_untaxed': 160.01,
            'amount_tax': 48.0,
            'amount_total': 208.01,
        })

    def test_in_invoice_onchange_past_invoice_1(self):
        copy_invoice = self.invoice.copy()

        move_form = Form(self.invoice)
        move_form.invoice_line_ids.remove(0)
        move_form.invoice_line_ids.remove(0)
        move_form.invoice_vendor_bill_id = copy_invoice
        move_form.save()

        self.assertInvoiceValues(self.invoice, [
            self.product_line_vals_1,
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

    def test_in_invoice_create_refund(self):
        self.invoice.action_post()

        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            'date': fields.Date.from_string('2019-02-01'),
            'reason': 'no reason',
            'refund_method': 'refund',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'not_paid', "Refunding with a draft credit note should keep the invoice 'not_paid'.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'debit': 0.0,
                'credit': 800.0,
                'tax_tag_invert': True,
                'tax_base_amount': 0.0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'debit': 0.0,
                'credit': 160.0,
                'tax_tag_invert': True,
                'tax_base_amount': 0.0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'debit': 0.0,
                'credit': 144.0,
                'tax_tag_invert': True,
                'tax_base_amount': 960.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'debit': 0.0,
                'credit': 24.0,
                'tax_tag_invert': True,
                'tax_base_amount': 160.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'debit': 1128.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
                'tax_tag_invert': False,
                'tax_base_amount': 0.0,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'date': move_reversal.date,
            'state': 'draft',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'not_paid',
        })

        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            'date': fields.Date.from_string('2019-02-01'),
            'reason': 'no reason again',
            'refund_method': 'cancel',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'reversed', "After cancelling it with a reverse invoice, an invoice should be in 'reversed' state.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'debit': 0.0,
                'credit': 800.0,
                'tax_tag_invert': True,
                'tax_base_amount': 0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'debit': 0.0,
                'credit': 160.0,
                'tax_tag_invert': True,
                'tax_base_amount': 0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'debit': 0.0,
                'credit': 144.0,
                'tax_tag_invert': True,
                'tax_base_amount': 960.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'debit': 0.0,
                'credit': 24.0,
                'tax_tag_invert': True,
                'tax_base_amount': 160.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'debit': 1128.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
                'tax_tag_invert': False,
                'tax_base_amount': 0,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'date': move_reversal.date,
            'state': 'posted',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'paid',
        })

    def test_in_invoice_create_refund_multi_currency(self):
        ''' Test the account.move.reversal takes care about the currency rates when setting
        a custom reversal date.
        '''
        move_form = Form(self.invoice)
        move_form.date = '2016-01-01'
        move_form.currency_id = self.currency_data['currency']
        move_form.save()

        self.invoice.action_post()

        # The currency rate changed from 1/3 to 1/2.
        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            'date': fields.Date.from_string('2017-01-01'),
            'reason': 'no reason',
            'refund_method': 'refund',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'not_paid', "Refunding with a draft credit note should keep the invoice 'not_paid'.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 564.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'currency_id': self.currency_data['currency'].id,
            'date': move_reversal.date,
            'state': 'draft',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'not_paid',
        })

        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            'date': fields.Date.from_string('2017-01-01'),
            'reason': 'no reason again',
            'refund_method': 'cancel',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'reversed', "After cancelling it with a reverse invoice, an invoice should be in 'reversed' state.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 564.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'currency_id': self.currency_data['currency'].id,
            'date': move_reversal.date,
            'state': 'posted',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'paid',
        })

    def test_in_invoice_create_1(self):
        # Test creating an account_move with the least information.
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
                }),
                Command.create({
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
                }),
            ],
        })

        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 800.0,
                'debit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 144.0,
                'debit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1128.0,
                'credit': 564.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })

    def test_in_invoice_write_1(self):
        # Test creating an account_move with the least information.
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
                }),
            ],
        })
        move.write({
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
                }),
            ],
        })

        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 800.0,
                'debit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 144.0,
                'debit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1128.0,
                'credit': 564.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })

    def test_in_invoice_duplicate_supplier_reference(self):
        ''' Ensure two vendor bills can't share the same vendor reference. '''
        self.invoice.ref = 'a supplier reference'
        invoice2 = self.invoice.copy(default={'invoice_date': self.invoice.invoice_date})
        invoice2.ref = 'a supplier reference'
        with self.assertRaises(ValidationError):
            invoice2.action_post()

    def test_in_invoice_switch_in_refund_1(self):
        # Test creating an account_move with an in_invoice_type and switch it in an in_refund.
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
                }),
                Command.create({
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
                }),
            ],
        })
        move.action_switch_invoice_into_refund_credit_note()

        self.assertRecordValues(move, [{'move_type': 'in_refund'}])
        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -800.0,
                'credit': 400.0,
                'debit': 0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -160.0,
                'credit': 80.0,
                'debit': 0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -144.0,
                'credit': 72.0,
                'debit': 0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -24.0,
                'credit': 12.0,
                'debit': 0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1128.0,
                'debit': 564.0,
                'credit': 0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })

    def test_in_invoice_switch_in_refund_2(self):
        # Test creating an account_move with an in_invoice_type and switch it in an in_refund and a negative quantity.
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'quantity': -self.product_line_vals_1['quantity'],
                    'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
                }),
                Command.create({
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'quantity': -self.product_line_vals_2['quantity'],
                    'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
                }),
            ],
        })

        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -800.0,
                'price_subtotal': -800.0,
                'price_total': -920.0,
                'credit': 400.0,
                'debit': 0,
                'quantity': -1.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -160.0,
                'price_subtotal': -160.0,
                'price_total': -208.0,
                'credit': 80.0,
                'debit': 0,
                'quantity': -1.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -144.0,
                'price_subtotal': -144.0,
                'price_total': -144.0,
                'price_unit': -144.0,
                'credit': 72.0,
                'debit': 0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -24.0,
                'price_subtotal': -24.0,
                'price_total': -24.0,
                'price_unit': -24.0,
                'credit': 12.0,
                'debit': 0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1128.0,
                'price_subtotal': 1128.0,
                'price_total': 1128.0,
                'price_unit': 1128.0,
                'debit': 564.0,
                'credit': 0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
            'amount_tax' : -self.move_vals['amount_tax'],
            'amount_total' : -self.move_vals['amount_total'],
            'amount_untaxed' : -self.move_vals['amount_untaxed'],
        })
        move.action_switch_invoice_into_refund_credit_note()

        self.assertRecordValues(move, [{'move_type': 'in_refund'}])
        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -800.0,
                'credit': 400.0,
                'debit': 0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -160.0,
                'credit': 80.0,
                'debit': 0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -144.0,
                'credit': 72.0,
                'debit': 0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -24.0,
                'credit': 12.0,
                'debit': 0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1128.0,
                'debit': 564.0,
                'credit': 0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
            'amount_tax' : self.move_vals['amount_tax'],
            'amount_total' : self.move_vals['amount_total'],
            'amount_untaxed' : self.move_vals['amount_untaxed'],
        })

    def test_in_invoice_change_period_accrual_1(self):
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'date': '2017-01-01',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2017-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, None, {
                    'name': self.product_line_vals_1['name'],
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'quantity': self.product_line_vals_1['quantity'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'tax_ids': self.product_line_vals_1['tax_ids'],
                }),
                (0, None, {
                    'name': self.product_line_vals_2['name'],
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'quantity': self.product_line_vals_2['quantity'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'tax_ids': self.product_line_vals_2['tax_ids'],
                }),
            ]
        })
        move.action_post()

        wizard = self.env['account.automatic.entry.wizard']\
            .with_context(active_model='account.move.line', active_ids=move.invoice_line_ids.ids).create({
            'action': 'change_period',
            'date': '2018-01-01',
            'percentage': 60,
            'journal_id': self.company_data['default_journal_misc'].id,
            'expense_accrual_account': self.env['account.account'].create({
                'name': 'Accrual Expense Account',
                'code': '234567',
                'user_type_id': self.env.ref('account.data_account_type_expenses').id,
                'reconcile': True,
            }).id,
            'revenue_accrual_account': self.env['account.account'].create({
                'name': 'Accrual Revenue Account',
                'code': '765432',
                'user_type_id': self.env.ref('account.data_account_type_expenses').id,
                'reconcile': True,
            }).id,
        })
        wizard_res = wizard.do_action()

        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 800.0,
                'debit': 400.0,
                'credit': 0.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 160.0,
                'debit': 80.0,
                'credit': 0.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 144.0,
                'debit': 72.0,
                'credit': 0.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 24.0,
                'debit': 12.0,
                'credit': 0.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1128.0,
                'debit': 0.0,
                'credit': 564.0,
                'date_maturity': fields.Date.from_string('2017-01-01'),
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
            'date': fields.Date.from_string('2017-01-01'),
        })

        accrual_lines = self.env['account.move'].browse(wizard_res['domain'][0][2]).line_ids.sorted('date')
        self.assertRecordValues(accrual_lines, [
            {'amount_currency': -480.0, 'debit': 0.0,   'credit': 240.0,    'account_id': self.product_line_vals_1['account_id'],   'reconciled': False},
            {'amount_currency': 480.0,  'debit': 240.0, 'credit': 0.0,      'account_id': wizard.expense_accrual_account.id,        'reconciled': True},
            {'amount_currency': -96.0,  'debit': 0.0,   'credit': 48.0,     'account_id': self.product_line_vals_2['account_id'],   'reconciled': False},
            {'amount_currency': 96.0,   'debit': 48.0,  'credit': 0.0,      'account_id': wizard.expense_accrual_account.id,        'reconciled': True},
            {'amount_currency': 480.0,  'debit': 240.0, 'credit': 0.0,      'account_id': self.product_line_vals_1['account_id'],   'reconciled': False},
            {'amount_currency': -480.0, 'debit': 0.0,   'credit': 240.0,    'account_id': wizard.expense_accrual_account.id,        'reconciled': True},
            {'amount_currency': 96.0,   'debit': 48.0,  'credit': 0.0,      'account_id': self.product_line_vals_2['account_id'],   'reconciled': False},
            {'amount_currency': -96.0,  'debit': 0.0,   'credit': 48.0,     'account_id': wizard.expense_accrual_account.id,        'reconciled': True},
        ])

    def test_in_invoice_reverse_caba(self):
        tax_waiting_account = self.env['account.account'].create({
            'name': 'TAX_WAIT',
            'code': 'TWAIT',
            'user_type_id': self.env.ref('account.data_account_type_current_liabilities').id,
            'reconcile': True,
            'company_id': self.company_data['company'].id,
        })
        tax_final_account = self.env['account.account'].create({
            'name': 'TAX_TO_DEDUCT',
            'code': 'TDEDUCT',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'company_id': self.company_data['company'].id,
        })
        tax_base_amount_account = self.env['account.account'].create({
            'name': 'TAX_BASE',
            'code': 'TBASE',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'company_id': self.company_data['company'].id,
        })
        self.env.company.account_cash_basis_base_account_id = tax_base_amount_account
        self.env.company.tax_exigibility = True
        tax_tags = defaultdict(dict)
        for line_type, repartition_type in [(l, r) for l in ('invoice', 'refund') for r in ('base', 'tax')]:
            tax_tags[line_type][repartition_type] = self.env['account.account.tag'].create({
                'name': '%s %s tag' % (line_type, repartition_type),
                'applicability': 'taxes',
                'country_id': self.env.ref('base.us').id,
            })
        tax = self.env['account.tax'].create({
            'name': 'cash basis 10%',
            'type_tax_use': 'purchase',
            'amount': 10,
            'tax_exigibility': 'on_payment',
            'cash_basis_transition_account_id': tax_waiting_account.id,
            'invoice_repartition_line_ids': [
                (0, 0, {
                    'factor_percent': 100,
                    'repartition_type': 'base',
                    'tag_ids': [(6, 0, tax_tags['invoice']['base'].ids)],
                }),
                (0, 0, {
                    'factor_percent': 100,
                    'repartition_type': 'tax',
                    'account_id': tax_final_account.id,
                    'tag_ids': [(6, 0, tax_tags['invoice']['tax'].ids)],
                }),
            ],
            'refund_repartition_line_ids': [
                (0, 0, {
                    'factor_percent': 100,
                    'repartition_type': 'base',
                    'tag_ids': [(6, 0, tax_tags['refund']['base'].ids)],
                }),
                (0, 0, {
                    'factor_percent': 100,
                    'repartition_type': 'tax',
                    'account_id': tax_final_account.id,
                    'tag_ids': [(6, 0, tax_tags['refund']['tax'].ids)],
                }),
            ],
        })
        # create invoice
        move_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice'))
        move_form.partner_id = self.partner_a
        move_form.invoice_date = fields.Date.from_string('2017-01-01')
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
            line_form.tax_ids.clear()
            line_form.tax_ids.add(tax)
        invoice = move_form.save()
        invoice.action_post()
        # make payment
        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
            'payment_date': invoice.date,
        })._create_payments()
        # check caba move
        partial_rec = invoice.mapped('line_ids.matched_debit_ids')
        caba_move = self.env['account.move'].search([('tax_cash_basis_rec_id', '=', partial_rec.id)])
        expected_values = [
            {
                'tax_line_id': False,
                'tax_repartition_line_id': False,
                'tax_ids': [],
                'tax_tag_ids': [],
                'account_id': tax_base_amount_account.id,
                'debit': 0.0,
                'credit': 800.0,
            },
            {
                'tax_line_id': False,
                'tax_repartition_line_id': False,
                'tax_ids': tax.ids,
                'tax_tag_ids': tax_tags['invoice']['base'].ids,
                'account_id': tax_base_amount_account.id,
                'debit': 800.0,
                'credit': 0.0,
            },
            {
                'tax_line_id': False,
                'tax_repartition_line_id': False,
                'tax_ids': [],
                'tax_tag_ids': [],
                'account_id': tax_waiting_account.id,
                'debit': 0.0,
                'credit': 80.0,
            },
            {
                'tax_line_id': tax.id,
                'tax_repartition_line_id': tax.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax').id,
                'tax_ids': [],
                'tax_tag_ids': tax_tags['invoice']['tax'].ids,
                'account_id': tax_final_account.id,
                'debit': 80.0,
                'credit': 0.0,
            },
        ]
        self.assertRecordValues(caba_move.line_ids, expected_values)
        # unreconcile
        credit_aml = invoice.line_ids.filtered('credit')
        credit_aml.remove_move_reconcile()
        # check caba move reverse is same as caba move with only debit/credit inverted
        reversed_caba_move = self.env['account.move'].search([('reversed_entry_id', '=', caba_move.id)])
        for value in expected_values:
            value.update({
                'debit': value['credit'],
                'credit': value['debit'],
            })
        self.assertRecordValues(reversed_caba_move.line_ids, expected_values)

    def test_in_invoice_line_tax_line_delete(self):
        with Form(self.invoice) as invoice_form:
            lines_count = len(invoice_form.line_ids)
            with invoice_form.line_ids.edit(0) as line_form:
                tax = line_form.tax_line_id
            invoice_form.line_ids.remove(0)
            # check that the tax line is recreated
            self.assertEqual(len(invoice_form.line_ids), lines_count)

        # Assert the tax line is recreated for the tax
        self.assertIn(tax, self.invoice.line_ids.tax_line_id)

    def test_invoice_sent_to_additional_partner(self):
        """
        Make sure that when an invoice is a partner to a partner who is not
        the invoiced customer, they receive a link containing an access token,
        allowing them to view the invoice without needing to log in.
        """

        invoice = self.init_invoice(
            'out_invoice', partner=self.partner_a, invoice_date='2023-04-17', amounts=[100])
        invoice.action_post()

        # add a follower to the invoice
        self.partner_b.email = 'partner_b@example.com'
        invoice.message_subscribe(self.partner_b.ids)

        # Create a partner not related to the invoice
        additional_partner = self.env['res.partner'].create({
            'name': "Additional Partner",
            'email': "additional@example.com",
        })

        # Send the invoice
        action = invoice.with_context(discard_logo_check=True).action_invoice_sent()
        action_context = action['context']

        # Create the email using the wizard and add the additional partner as a recipient
        invoice_send_wizard = self.env['account.invoice.send'].with_context(
            action_context,
            active_ids=[invoice.id]
        ).create({'is_print': False})
        invoice_send_wizard.partner_ids |= additional_partner

        # prevent mail.mail record from being deleted after being sent.
        invoice_send_wizard.template_id.auto_delete = False

        # send the invoice
        invoice_send_wizard.send_and_print_action()

        # Find the email sent to the additional partner
        additional_partner_mail = self.env['mail.mail'].search([
            ('res_id', '=', invoice.id),
            ('recipient_ids', '=', additional_partner.id)
        ])
        self.assertTrue(additional_partner_mail)
        self.assertIn('access_token=', additional_partner_mail.body_html,
                      "The additional partner should be sent the link including the token")

        # Find the email sent to the followers
        follower_mail = self.env['mail.mail'].search([
            ('res_id', '=', invoice.id),
            ('recipient_ids', '=', self.partner_b.id)
        ])
        self.assertTrue(follower_mail)
        self.assertNotIn('access_token=', follower_mail.body_html,
                      "The followers should not bet sent the access token by default")
