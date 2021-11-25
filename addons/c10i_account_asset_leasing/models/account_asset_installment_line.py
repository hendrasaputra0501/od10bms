# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

import odoo.addons.decimal_precision as dp


class AccountAssetLeasing(models.Model):
    _name = 'account.asset.installment.line'
    _description = "Account Asset Installment Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'installment_date desc, id desc'


    
    installment_amount= fields.Float(string='Installment Amount', compute='', store=True, digits=dp.get_precision('Account'))
    installment_date = fields.Date(string='Installment Date', readonly=True)
    asset_leasing_id = fields.Many2one('account.asset.leasing', string="Account Asset Leasing")
    name = fields.Char(
        string='Number',
        related = 'asset_leasing_id.number',
        readonly=1,
    )
    state = fields.Selection(selection=[('not_paid', 'Not Paid'),
                                        ('paid', 'Paid')],
                             string='State', readonly=True, default='not_pay',
                             track_visibility='onchange', compute="_get_status")

    is_installment_payment = fields.Boolean(string="Is Installment Payment?", default=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

    voucher_line_ids = fields.One2many('account.voucher.line', 'account_asset_installment_line_id',string='Payment Lines')

    @api.depends('asset_leasing_id.voucher_ids')
    def _get_status(self):
        for line in self:
            value = sum(line.voucher_line_ids.filtered(lambda l: l.voucher_id.state=='posted').mapped('price_subtotal'))
            line.state= 'paid' if line.installment_amount==value else 'not_paid'

    @api.multi
    def action_create_payment(self):
        res = {
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.voucher',
            'view_id': False,
            'type': 'ir.actions.act_window',
            }
        # voucher_id = self.env['account.voucher.line'].search([('account_asset_installment_line_id', '=', self.id)]).voucher_id
        if not self.voucher_line_ids:
            location_type=self.env['account.location.type'].search([('code', '=', 'NA')])
            res['context'] = {
                'default_payment_type': 'purchase',
                'default_partner_id': self.asset_leasing_id.partner_id.id,
                'default_asset_leasing_id': self.asset_leasing_id.id,
                # 'default_account_id'    : self.asset_leasing_id.invoice_id.account_id.id,
                'default_pay_now'   : 'pay_now',
                'default_line_ids': [{
                        'name'          : 'Installment Asset [%s]: %s'%(self.installment_date, self.asset_leasing_id.name.name),
                        'account_id'    : self.asset_leasing_id.invoice_id.account_id.id,
                        'account_location_type_id' : location_type.id,
                        'account_location_id': False,
                        'account_location_type_no_location': location_type.no_location,
                        'quantity'  : 1,
                        'price_unit': self.installment_amount-sum(self.voucher_line_ids.filtered(lambda l: l.voucher_id.state=='posted').mapped('price_subtotal')),
                        'account_asset_installment_line_id': self.id,
                    }]
                }
        else:
            res.update({
                    'view_mode': 'tree',
                    'domain' : [('id', 'in', self.voucher_line_ids.mapped('voucher_id').ids)]
                })
        return res

    @api.multi
    def post_installment(self):
        # redirect to DP form because installment state is paid should be post state
        if self.state == 'paid':
            return {
                    'name'          : ('Direct Payments'),
                    'view_type'     : 'form',
                    'view_mode'     : 'form',
                    'res_model'     : 'account.voucher',
                    'res_id'        : self.voucher_id.id,
                    'type'          : 'ir.actions.act_window',
                    }

