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
    account_asset_installment_line_id = fields.Many2one('account.asset.leasing', string="Account Asset Leasing")
    name = fields.Char(
        string='Number',
        related = 'account_asset_installment_line_id.number',
        readonly=1,
    )
    state = fields.Selection(selection=[('not_pay', 'Not Pay'),
                                        ('paid', 'Paid, Not Yet Post'),
                                        ('post', 'Post'),],
                             string='State', readonly=True, default='not_pay',
                             track_visibility='onchange')

    is_installment_payment = fields.Boolean(string="Is Installment Payment?", default=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

    voucher_id = fields.Many2one('account.voucher', string='Installment Details')


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

