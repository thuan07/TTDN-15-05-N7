# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields,api, models, _
from odoo.exceptions import UserError, ValidationError


class CrmTeam(models.Model):
    _inherit = "crm.team"

    website_ids = fields.One2many('website', 'salesteam_id', string='Websites', help="Websites using this Sales Team")
    abandoned_carts_count = fields.Integer(
        compute='_compute_abandoned_carts',
        string='Number of Abandoned Carts', readonly=True)
    abandoned_carts_amount = fields.Integer(
        compute='_compute_abandoned_carts',
        string='Amount of Abandoned Carts', readonly=True)

    def _compute_abandoned_carts(self):
        # abandoned carts to recover are draft sales orders that have no order lines,
        # a partner other than the public user, and created over an hour ago
        # and the recovery mail was not yet sent
        counts = {}
        amounts = {}
        website_teams = self.filtered(lambda team: team.website_ids)
        if website_teams:
            abandoned_carts_data = self.env['sale.order'].read_group([
                ('is_abandoned_cart', '=', True),
                ('cart_recovery_email_sent', '=', False),
                ('team_id', 'in', website_teams.ids),
            ], ['amount_total', 'team_id'], ['team_id'])
            counts = {data['team_id'][0]: data['team_id_count'] for data in abandoned_carts_data}
            amounts = {data['team_id'][0]: data['amount_total'] for data in abandoned_carts_data}
        for team in self:
            team.abandoned_carts_count = counts.get(team.id, 0)
            team.abandoned_carts_amount = amounts.get(team.id, 0)

    def get_abandoned_carts(self):
        self.ensure_one()
        return {
            'name': _('Abandoned Carts'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': [('is_abandoned_cart', '=', True)],
            'search_view_id': [self.env.ref('sale.sale_order_view_search_inherit_sale').id],
            'context': {
                'search_default_team_id': self.id,
                'default_team_id': self.id,
                'search_default_recovery_email': 1,
                'create': False
            },
            'res_model': 'sale.order',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        You can find all abandoned carts here, i.e. the carts generated by your website's visitors from over an hour ago that haven't been confirmed yet.</p>
                        <p>You should send an email to the customers to encourage them!</p>
                    '''),
        }
