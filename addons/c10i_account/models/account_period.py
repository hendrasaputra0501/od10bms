# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
import urllib3
from lxml import etree
import time

class AccountPeriod(models.Model):
    _inherit = 'account.period'

    # earning_account_id = fields.Many2one('account.account', related='company_id.monthly_earning_account_id', string='Earning Account', store=True)
    # counterpart_earning_account_id = fields.Many2one('account.account', related='company_id.counterpart_monthly_earning_account_id', string='Counter-part Earning Account', store=True)

    def close_period(self):
        AccountMove = self.env['account.move']
        for period in self:
            unposted_moves = AccountMove.search([('state','=','draft'),('date','>=',period.date_start),('date','<=',period.date_stop)])
            if unposted_moves:
                raise UserError(_('Closing Period Failed!\nIn order to close a period, you must Post Journal Entries in this period.'))
            period.state = 'done'

    def reopen_period(self):
        for period in self:
            if period.fiscalyear_id.state=='done':
                raise UserError(_('ReOpen Period Failed!\nYou cannot re-open Period in Closed Fiscal Year'))
            period.state = 'draft'

    def periodical_post_entries(self):
        AccountMove = self.env['account.move']
        for period in self:
            unposted_moves = AccountMove.search(
                [('state', '=', 'draft'), ('date', '>=', period.date_start), ('date', '<=', period.date_stop)])
            unposted_moves.post()