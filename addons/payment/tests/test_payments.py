# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.payment.tests.common import PaymentCommon


@tagged('-at_install', 'post_install')
class TestPayments(PaymentCommon):

    def test_no_amount_available_for_refund_when_not_supported(self):
        self.acquirer.support_refund = False
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        self.assertEqual(
            tx.payment_id.amount_available_for_refund,
            0,
            msg="The value of `amount_available_for_refund` should be 0 when the acquirer doesn't "
                "support refunds."
        )

    def test_full_amount_available_for_refund_when_not_yet_refunded(self):
        self.acquirer.support_refund = 'full_only'  # Should simply not be False
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        self.assertAlmostEqual(
            tx.payment_id.amount_available_for_refund,
            tx.amount,
            places=2,
            msg="The value of `amount_available_for_refund` should be that of `total` when there "
                "are no linked refunds."
        )

    def test_full_amount_available_for_refund_when_refunds_are_pending(self):
        self.acquirer.write({
            'support_refund': 'full_only',  # Should simply not be False
            'support_authorization': True,  # To create transaction in the 'authorized' state
        })
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        for reference_index, state in enumerate(('draft', 'pending', 'authorized')):
            self.create_transaction(
                'dummy',
                amount=-tx.amount,
                reference=f'R-{tx.reference}-{reference_index + 1}',
                state=state,
                operation='refund',  # Override the computed flow
                source_transaction_id=tx.id,
            )
        self.assertAlmostEqual(
            tx.payment_id.amount_available_for_refund,
            tx.payment_id.amount,
            places=2,
            msg="The value of `amount_available_for_refund` should be that of `total` when all the "
                "linked refunds are pending (not in the state 'done')."
        )

    def test_no_amount_available_for_refund_when_fully_refunded(self):
        self.acquirer.support_refund = 'full_only'  # Should simply not be False
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        self.create_transaction(
            'dummy',
            amount=-tx.amount,
            reference=f'R-{tx.reference}',
            state='done',
            operation='refund',  # Override the computed flow
            source_transaction_id=tx.id,
        )._reconcile_after_done()
        self.assertEqual(
            tx.payment_id.amount_available_for_refund,
            0,
            msg="The value of `amount_available_for_refund` should be 0 when there is a linked "
                "refund of the full amount that is confirmed (state 'done')."
        )

    def test_no_full_amount_available_for_refund_when_partially_refunded(self):
        self.acquirer.support_refund = 'partial'
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        self.create_transaction(
            'dummy',
            amount=-(tx.amount / 10),
            reference=f'R-{tx.reference}',
            state='done',
            operation='refund',  # Override the computed flow
            source_transaction_id=tx.id,
        )._reconcile_after_done()
        self.assertAlmostEqual(
            tx.payment_id.amount_available_for_refund,
            tx.payment_id.amount - (tx.amount / 10),
            places=2,
            msg="The value of `amount_available_for_refund` should be equal to the total amount "
                "minus the sum of the absolute amount of the refunds that are confirmed (state "
                "'done')."
        )

    def test_refunds_count(self):
        self.acquirer.support_refund = 'full_only'  # Should simply not be False
        tx = self.create_transaction('redirect', state='done')
        tx._reconcile_after_done()  # Create the payment
        for reference_index, operation in enumerate(
            ('online_redirect', 'online_direct', 'online_token', 'validation', 'refund')
        ):
            self.create_transaction(
                'dummy',
                reference=f'R-{tx.reference}-{reference_index + 1}',
                state='done',
                operation=operation,  # Override the computed flow
                source_transaction_id=tx.id,
            )._reconcile_after_done()

        self.assertEqual(
            tx.payment_id.refunds_count,
            1,
            msg="The refunds count should only consider transactions with operation 'refund'."
        )

    def test_action_post_calls_send_payment_request_only_once(self):
        payment_token = self.create_token()
        payment_without_token = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'amount': 2000.0,
            'date': '2019-01-01',
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'journal_id': self.acquirer.journal_id.id,
            'payment_method_line_id': self.inbound_payment_method_line.id,
        })
        payment_with_token = payment_without_token.copy()
        payment_with_token.payment_token_id = payment_token.id

        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction'
            '._send_payment_request'
        ) as patched:
            payment_without_token.action_post()
            patched.assert_not_called()
            payment_with_token.action_post()
            patched.assert_called_once()

    def test_acquirer_journal_assignation(self):
        """ Test the computation of the 'journal_id' field and so, the link with the accounting side. """
        def get_payment_method_line(acquirer):
            return self.env['account.payment.method.line'].search([
                ('code', '=', acquirer.provider),
                ('payment_acquirer_id', '=', acquirer.id),
            ])

        with self.mocked_get_payment_method_information(), self.mocked_get_default_payment_method_id():
            journal = self.company_data['default_journal_bank']
            acquirer = self.acquirer
            self.assertRecordValues(acquirer, [{'journal_id': journal.id}])

            # Test changing the journal.
            copy_journal = journal.copy()
            acquirer.journal_id = copy_journal
            self.assertRecordValues(acquirer, [{'journal_id': copy_journal.id}])
            self.assertRecordValues(get_payment_method_line(acquirer), [{'journal_id': copy_journal.id}])

            # Test duplication of the acquirer.
            copy_acquirer = self.acquirer.copy()
            self.assertRecordValues(copy_acquirer, [{'journal_id': False}])
            copy_acquirer.state = 'test'
            self.assertRecordValues(copy_acquirer, [{'journal_id': journal.id}])

            # We are able to have both on the same journal...
            with self.assertRaises(ValidationError):
                # ...but not having both with the same name.
                acquirer.journal_id = journal
                journal._check_payment_method_line_ids_multiplicity()

            method_line = get_payment_method_line(copy_acquirer)
            method_line.name = "dummy (copy)"
            acquirer.journal_id = journal
