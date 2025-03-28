# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch
from unittest.mock import DEFAULT
from werkzeug.urls import url_parse, url_decode

from odoo import exceptions
from odoo.addons.test_mail.models.test_mail_models import MailTestSimple
from odoo.addons.test_mail.tests.common import TestMailCommon, TestRecipients
from odoo.tests.common import tagged, HttpCase, users
from odoo.tools import mute_logger


@tagged('mail_thread')
class TestChatterTweaks(TestMailCommon, TestRecipients):

    @classmethod
    def setUpClass(cls):
        super(TestChatterTweaks, cls).setUpClass()
        cls.test_record = cls.env['mail.test.simple'].with_context(cls._test_context).create({'name': 'Test', 'email_from': 'ignasse@example.com'})

    def test_post_no_subscribe_author(self):
        original = self.test_record.message_follower_ids
        self.test_record.with_user(self.user_employee).with_context({'mail_create_nosubscribe': True}).message_post(
            body='Test Body', message_type='comment', subtype_xmlid='mail.mt_comment')
        self.assertEqual(self.test_record.message_follower_ids.mapped('partner_id'), original.mapped('partner_id'))

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_post_no_subscribe_recipients(self):
        original = self.test_record.message_follower_ids
        self.test_record.with_user(self.user_employee).with_context({'mail_create_nosubscribe': True}).message_post(
            body='Test Body', message_type='comment', subtype_xmlid='mail.mt_comment', partner_ids=[self.partner_1.id, self.partner_2.id])
        self.assertEqual(self.test_record.message_follower_ids.mapped('partner_id'), original.mapped('partner_id'))

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_post_subscribe_recipients(self):
        original = self.test_record.message_follower_ids
        self.test_record.with_user(self.user_employee).with_context({'mail_create_nosubscribe': True, 'mail_post_autofollow': True}).message_post(
            body='Test Body', message_type='comment', subtype_xmlid='mail.mt_comment', partner_ids=[self.partner_1.id, self.partner_2.id])
        self.assertEqual(self.test_record.message_follower_ids.mapped('partner_id'), original.mapped('partner_id') | self.partner_1 | self.partner_2)

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_chatter_context_cleaning(self):
        """ Test default keys are not propagated to message creation as it may
        induce wrong values for some fields, like parent_id. """
        parent = self.env['res.partner'].create({'name': 'Parent'})
        partner = self.env['res.partner'].with_context(default_parent_id=parent.id).create({'name': 'Contact'})
        self.assertFalse(partner.message_ids[-1].parent_id)

    def test_chatter_mail_create_nolog(self):
        """ Test disable of automatic chatter message at create """
        rec = self.env['mail.test.simple'].with_user(self.user_employee).with_context({'mail_create_nolog': True}).create({'name': 'Test'})
        self.flush_tracking()
        self.assertEqual(rec.message_ids, self.env['mail.message'])

        rec = self.env['mail.test.simple'].with_user(self.user_employee).with_context({'mail_create_nolog': False}).create({'name': 'Test'})
        self.flush_tracking()
        self.assertEqual(len(rec.message_ids), 1)

    def test_chatter_mail_notrack(self):
        """ Test disable of automatic value tracking at create and write """
        rec = self.env['mail.test.track'].with_user(self.user_employee).create({'name': 'Test', 'user_id': self.user_employee.id})
        self.flush_tracking()
        self.assertEqual(len(rec.message_ids), 1,
                         "A creation message without tracking values should have been posted")
        self.assertEqual(len(rec.message_ids.sudo().tracking_value_ids), 0,
                         "A creation message without tracking values should have been posted")

        rec.with_context({'mail_notrack': True}).write({'user_id': self.user_admin.id})
        self.flush_tracking()
        self.assertEqual(len(rec.message_ids), 1,
                         "No new message should have been posted with mail_notrack key")

        rec.with_context({'mail_notrack': False}).write({'user_id': self.user_employee.id})
        self.flush_tracking()
        self.assertEqual(len(rec.message_ids), 2,
                         "A tracking message should have been posted")
        self.assertEqual(len(rec.message_ids.sudo().mapped('tracking_value_ids')), 1,
                         "New tracking message should have tracking values")

    def test_chatter_tracking_disable(self):
        """ Test disable of all chatter features at create and write """
        rec = self.env['mail.test.track'].with_user(self.user_employee).with_context({'tracking_disable': True}).create({'name': 'Test', 'user_id': self.user_employee.id})
        self.flush_tracking()
        self.assertEqual(rec.sudo().message_ids, self.env['mail.message'])
        self.assertEqual(rec.sudo().mapped('message_ids.tracking_value_ids'), self.env['mail.tracking.value'])

        rec.write({'user_id': self.user_admin.id})
        self.flush_tracking()
        self.assertEqual(rec.sudo().mapped('message_ids.tracking_value_ids'), self.env['mail.tracking.value'])

        rec.with_context({'tracking_disable': False}).write({'user_id': self.user_employee.id})
        self.flush_tracking()
        self.assertEqual(len(rec.sudo().mapped('message_ids.tracking_value_ids')), 1)

        rec = self.env['mail.test.track'].with_user(self.user_employee).with_context({'tracking_disable': False}).create({'name': 'Test', 'user_id': self.user_employee.id})
        self.flush_tracking()
        self.assertEqual(len(rec.sudo().message_ids), 1,
                         "Creation message without tracking values should have been posted")
        self.assertEqual(len(rec.sudo().mapped('message_ids.tracking_value_ids')), 0,
                         "Creation message without tracking values should have been posted")

    def test_cache_invalidation(self):
        """ Test that creating a mail-thread record does not invalidate the whole cache. """
        # make a new record in cache
        record = self.env['res.partner'].new({'name': 'Brave New Partner'})
        self.assertTrue(record.name)

        # creating a mail-thread record should not invalidate the whole cache
        self.env['res.partner'].create({'name': 'Actual Partner'})
        self.assertTrue(record.name)


class TestDiscuss(TestMailCommon, TestRecipients):

    @classmethod
    def setUpClass(cls):
        super(TestDiscuss, cls).setUpClass()
        cls.test_record = cls.env['mail.test.simple'].with_context(cls._test_context).create({
            'name': 'Test',
            'email_from': 'ignasse@example.com'
        })

    @mute_logger('openerp.addons.mail.models.mail_mail')
    def test_mark_all_as_read(self):
        def _employee_crash(*args, **kwargs):
            """ If employee is test employee, consider he has no access on document """
            recordset = args[0]
            if recordset.env.uid == self.user_employee.id and not recordset.env.su:
                if kwargs.get('raise_exception', True):
                    raise exceptions.AccessError('Hop hop hop Ernest, please step back.')
                return False
            return DEFAULT

        with patch.object(MailTestSimple, 'check_access_rights', autospec=True, side_effect=_employee_crash):
            with self.assertRaises(exceptions.AccessError):
                self.env['mail.test.simple'].with_user(self.user_employee).browse(self.test_record.ids).read(['name'])

            employee_partner = self.env['res.partner'].with_user(self.user_employee).browse(self.partner_employee.ids)

            # mark all as read clear needactions
            msg1 = self.test_record.message_post(body='Test', message_type='comment', subtype_xmlid='mail.mt_comment', partner_ids=[employee_partner.id])
            self._reset_bus()
            with self.assertBus(
                    [(self.cr.dbname, 'res.partner', employee_partner.id)],
                    message_items=[{
                        'type': 'mail.message/mark_as_read',
                        'payload': {
                            'message_ids': [msg1.id],
                            'needaction_inbox_counter': 0,
                        },
                    }]):
                employee_partner.env['mail.message'].mark_all_as_read(domain=[])
            na_count = employee_partner._get_needaction_count()
            self.assertEqual(na_count, 0, "mark all as read should conclude all needactions")

            # mark all as read also clear inaccessible needactions
            msg2 = self.test_record.message_post(body='Zest', message_type='comment', subtype_xmlid='mail.mt_comment', partner_ids=[employee_partner.id])
            needaction_accessible = len(employee_partner.env['mail.message'].search([['needaction', '=', True]]))
            self.assertEqual(needaction_accessible, 1, "a new message to a partner is readable to that partner")

            msg2.sudo().partner_ids = self.env['res.partner']
            employee_partner.env['mail.message'].search([['needaction', '=', True]])
            needaction_length = len(employee_partner.env['mail.message'].search([['needaction', '=', True]]))
            self.assertEqual(needaction_length, 1, "message should still be readable when notified")

            na_count = employee_partner._get_needaction_count()
            self.assertEqual(na_count, 1, "message not accessible is currently still counted")

            self._reset_bus()
            with self.assertBus(
                    [(self.cr.dbname, 'res.partner', employee_partner.id)],
                    message_items=[{
                        'type': 'mail.message/mark_as_read',
                        'payload': {
                            'message_ids': [msg2.id],
                            'needaction_inbox_counter': 0,
                        },
                    }]):
                employee_partner.env['mail.message'].mark_all_as_read(domain=[])
            na_count = employee_partner._get_needaction_count()
            self.assertEqual(na_count, 0, "mark all read should conclude all needactions even inacessible ones")

    def test_set_message_done_user(self):
        with self.assertSinglePostNotifications([{'partner': self.partner_employee, 'type': 'inbox'}], message_info={'content': 'Test'}):
            message = self.test_record.message_post(
                body='Test', message_type='comment', subtype_xmlid='mail.mt_comment',
                partner_ids=[self.user_employee.partner_id.id])
        message.with_user(self.user_employee).set_message_done()
        self.assertMailNotifications(message, [{'notif': [{'partner': self.partner_employee, 'type': 'inbox', 'is_read': True}]}])
        # TDE TODO: it seems bus notifications could be checked

    def test_set_star(self):
        msg = self.test_record.with_user(self.user_admin).message_post(body='My Body', subject='1')
        msg_emp = self.env['mail.message'].with_user(self.user_employee).browse(msg.id)

        # Admin set as starred
        msg.toggle_message_starred()
        self.assertTrue(msg.starred)

        # Employee set as starred
        msg_emp.toggle_message_starred()
        self.assertTrue(msg_emp.starred)

        # Do: Admin unstars msg
        msg.toggle_message_starred()
        self.assertFalse(msg.starred)
        self.assertTrue(msg_emp.starred)

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_mail_cc_recipient_suggestion(self):
        record = self.env['mail.test.cc'].create({'email_cc': 'cc1@example.com, cc2@example.com, cc3 <cc3@example.com>'})
        suggestions = record._message_get_suggested_recipients()[record.id]
        self.assertEqual(sorted(suggestions), [
            (False, '"cc3" <cc3@example.com>', 'CC Email'),
            (False, 'cc1@example.com', 'CC Email'),
            (False, 'cc2@example.com', 'CC Email'),
        ], 'cc should be in suggestions')

    def test_inbox_message_fetch_needaction(self):
        user1 = self.env['res.users'].create({'login': 'user1', 'name': 'User 1'})
        user1.notification_type = 'inbox'
        user2 = self.env['res.users'].create({'login': 'user2', 'name': 'User 2'})
        user2.notification_type = 'inbox'
        message1 = self.test_record.with_user(self.user_admin).message_post(body='Message 1', partner_ids=[user1.partner_id.id, user2.partner_id.id])
        message2 = self.test_record.with_user(self.user_admin).message_post(body='Message 2', partner_ids=[user1.partner_id.id, user2.partner_id.id])

        # both notified users should have the 2 messages in Inbox initially
        messages = self.env['mail.message'].with_user(user1)._message_fetch(domain=[['needaction', '=', True]])
        self.assertEqual(len(messages), 2)
        messages = self.env['mail.message'].with_user(user2)._message_fetch(domain=[['needaction', '=', True]])
        self.assertEqual(len(messages), 2)

        # first user is marking one message as done: the other message is still Inbox, while the other user still has the 2 messages in Inbox
        message1.with_user(user1).set_message_done()
        messages = self.env['mail.message'].with_user(user1)._message_fetch(domain=[['needaction', '=', True]])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].get('id'), message2.id)
        messages = self.env['mail.message'].with_user(user2)._message_fetch(domain=[['needaction', '=', True]])
        self.assertEqual(len(messages), 2)

    def test_notification_has_error_filter(self):
        """Ensure message_has_error filter is only returning threads for which
        the current user is author of a failed message."""
        message = self.test_record.with_user(self.user_admin).message_post(
            body='Test', message_type='comment', subtype_xmlid='mail.mt_comment',
            partner_ids=[self.user_employee.partner_id.id]
        )
        self.assertFalse(message.has_error)
        with self.mock_mail_gateway(sim_error='connect_smtp_notfound'):
            self.user_admin.notification_type = 'email'
            message2 = self.test_record.with_user(self.user_employee).message_post(
                body='Test', message_type='comment', subtype_xmlid='mail.mt_comment',
                partner_ids=[self.user_admin.partner_id.id]
            )
            self.assertTrue(message2.has_error)
        # employee is author of message which has a failure
        threads_employee = self.test_record.with_user(self.user_employee).search([('message_has_error', '=', True)])
        self.assertEqual(len(threads_employee), 1)
        # admin is also author of a message, but it doesn't have a failure
        # and the failure from employee's message should not be taken into account for admin
        threads_admin = self.test_record.with_user(self.user_admin).search([('message_has_error', '=', True)])
        self.assertEqual(len(threads_admin), 0)

    @users("employee")
    def test_unlink_notification_message(self):
        channel = self.env['mail.channel'].create({'name': 'testChannel'})
        channel.message_notify(
            body='test',
            message_type='user_notification',
            partner_ids=[self.partner_2.id],
            author_id=2
        )

        channel_message = self.env['mail.message'].sudo().search([('model', '=', 'mail.channel'), ('res_id', 'in', channel.ids)])
        self.assertEqual(len(channel_message), 1, "Test message should have been posted")

        channel.sudo().unlink()
        remaining_message = channel_message.exists()
        self.assertEqual(len(remaining_message), 0, "Test message should have been deleted")


@tagged('-at_install', 'post_install', 'multi_company')
class TestMultiCompany(TestMailCommon, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._activate_multi_company()

    def test_redirect_to_records(self):
        """ Test redirection and cids computation when involving multi company
        rules. """
        self.company_A = self.env['res.company'].create({
            'name': 'Company A',
            'user_ids': [(4, self.ref('base.user_admin'))],
        })

        self.company_B = self.env['res.company'].create({
            'name': 'Company B',
        })

        self.multi_company_record = self.env['mail.test.multi.company'].create({
            'name': 'Multi Company Record',
            'company_id': self.company_A.id,
        })

        # Test Case 0
        # Not logged, redirect to web/login
        response = self.url_open('/mail/view?model=%s&res_id=%s' % (
            self.multi_company_record._name,
            self.multi_company_record.id), timeout=15)

        path = url_parse(response.url).path
        self.assertEqual(path, '/web/login')

        decoded_fragment = url_decode(url_parse(response.url).fragment)
        self.assertTrue("cids" in decoded_fragment)
        self.assertEqual(decoded_fragment['cids'], str(self.multi_company_record.company_id.id))

        self.authenticate('admin', 'admin')

        # Test Case 1
        # Logged into company 1, try accessing record in company A
        # _redirect_to_record should add company A in allowed_company_ids
        response = self.url_open('/mail/view?model=%s&res_id=%s' % (
            self.multi_company_record._name,
            self.multi_company_record.id), timeout=15)

        self.assertEqual(response.status_code, 200)

        fragment = url_parse(response.url).fragment
        cids = url_decode(fragment)['cids']

        self.assertEqual(cids, '1,%s' % (self.company_A.id))

        # Test Case 2
        # Logged into company 1, try accessing record in company B
        # _redirect_to_record should redirect to messaging as the user
        # doesn't have any access for this company
        self.multi_company_record.company_id = self.company_B

        response = self.url_open('/mail/view?model=%s&res_id=%s' % (
            self.multi_company_record._name,
            self.multi_company_record.id), timeout=15)

        self.assertEqual(response.status_code, 200)

        fragment = url_parse(response.url).fragment
        action = url_decode(fragment)['action']

        self.assertEqual(action, 'mail.action_discuss')

    def test_redirect_to_records_nothread(self):
        """ Test no thread models and redirection """
        nothreads = self.env['mail.test.nothread'].create([
            {
                'company_id': company.id,
                'name': f'Test with {company.name}',
            }
            for company in (self.company_admin, self.company_2, self.env['res.company'])
        ])

        # when being logged, cids should be based on current user's company unless
        # there is an access issue (not tested here, see 'test_redirect_to_records')
        self.authenticate(self.user_admin.login, self.user_admin.login)
        for test_record in nothreads:
            for user_company in self.company_admin, self.company_2:
                with self.subTest(record_name=test_record.name, user_company=user_company):
                    self.user_admin.write({'company_id': user_company.id})
                    response = self.url_open(
                        f'/mail/view?model={test_record._name}&res_id={test_record.id}',
                        timeout=15
                    )
                    self.assertEqual(response.status_code, 200)

                    decoded_fragment = url_decode(url_parse(response.url).fragment)
                    self.assertTrue("cids" in decoded_fragment)
                    self.assertEqual(decoded_fragment['cids'], str(user_company.id))

        # when being not logged, cids should be added based on
        # '_get_mail_redirect_suggested_company'
        self.authenticate(None, None)
        for test_record in nothreads:
            with self.subTest(record_name=test_record.name, user_company=user_company):
                self.user_admin.write({'company_id': user_company.id})
                response = self.url_open(
                    f'/mail/view?model={test_record._name}&res_id={test_record.id}',
                    timeout=15
                )
                self.assertEqual(response.status_code, 200)

                decoded_fragment = url_decode(url_parse(response.url).fragment)
                if test_record.company_id:
                    self.assertIn('cids', decoded_fragment)
                    self.assertEqual(decoded_fragment['cids'], str(test_record.company_id.id))
                else:
                    self.assertNotIn('cids', decoded_fragment)
