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

class AccountFiscalyear(models.Model):
    _inherit = 'account.fiscalyear'

    name = fields.Char('Fiscal Year', required=True, readonly=True, states={'draft': [('readonly',False)]})
    code = fields.Char('Code', size=6, required=True, readonly=True, states={'draft': [('readonly',False)]})
    date_start = fields.Date('Start Date', required=True, readonly=True, states={'draft': [('readonly',False)]})
    date_stop = fields.Date('End Date', required=True, readonly=True, states={'draft': [('readonly',False)]})
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods', readonly=True, states={'draft': [('readonly',False)]})
    journal_id = fields.Many2one('account.journal', 'Closing Journal', readonly=True, states={'draft': [('readonly',False)]})
    # fiscalyear_toclose_id = fields.Many2one('account.fiscalyear', 'Fiscal Year to Close')
    move_id = fields.Many2one('account.move', 'Closing Journal Entry')

    @api.multi
    def close_fiscalyear(self):
        AccountPeriod = self.env['account.period']
        self.ensure_one()
        period_open = AccountPeriod.search([('fiscalyear_id','=',self.id),('state','=','draft')])
        if period_open:
            raise UserError(_('Cannot Close!\nIn order to close a Fiscal Year, you must Close all periods in this Fiscal Year.'))
        self.state = 'done'

    @api.multi
    def reopen_fiscalyear(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def create_closing_entry(self):
        self.ensure_one()
        AccountPeriod = self.env['account.period']
        # if not self.fiscalyear_toclose_id:
        #     raise UserError(_('Cannot Create Opening!\nPlease input Fiscal Year to Close.'))
        # check_period_open = AccountPeriod.search([('fiscalyear_id', '=', self.fiscalyear_toclose_id.id), ('state', '=', 'draft')])
        check_period_open = self.period_ids.filtered(lambda x: x.state=='draft')
        if check_period_open:
            raise UserError(_('Cannot Create Closing!\nPlease close all periods in this Fiscal Year.'))
        AccountMoveLine = self.env['account.move.line']
        AccountMove = self.env['account.move']
        pl_accounts = self.env['account.account'].search([('user_type_id.include_initial_balance','=',False)])
        profit_loss_moves = AccountMoveLine.search([('account_id','in',pl_accounts.ids),
                ('journal_id.type','!=','closing'),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_stop)])
        #create journal closing
        if not self.journal_id:
            raise UserError(_('Cannot Close!\nPlease input Closing Journal.'))
        pl_amount = sum(profit_loss_moves.mapped('balance'))

        AccountMove = self.env['account.move']
        AccountMoveLineCr = self.env['account.move.line'].with_context(check_move_validity=False)

        earning_account = self.company_id.earning_account_id
        if not earning_account:
            raise UserError(_('Earning Account not Found in this Company!\nPlease Input Earning Account in Configuration.'))

        counterpart_earning_account = self.company_id.counterpart_earning_account_id
        if not counterpart_earning_account:
            raise UserError(_('Counter-part Earning Account not Found in this Company!\nPlease Input Counter-part Earning Account in Configuration.'))

        closing_move = AccountMove.with_context(closing=True).create({
            'date': self.date_stop,
            'journal_id': self.journal_id.id,
        })
        move_line_dict = {
            'date': self.date_stop,
            'journal_id': self.journal_id.id,
            'name': ('Earning of Fiscal Year %s'%self.code) if pl_amount<0 \
                else ('Closing Fiscal Year %s'%self.code),
            'account_id': earning_account.id if pl_amount<0 else counterpart_earning_account.id,
            'debit': pl_amount if pl_amount>0 else 0.0,
            'credit': abs(pl_amount) if pl_amount<0 else 0.0,
            'move_id': closing_move.id
        }
        AccountMoveLineCr.create(move_line_dict)

        ct_move_line_dict = {
            'date': self.date_stop,
            'journal_id': self.journal_id.id,
            'name': ('Earning of Fiscal Year %s'%self.code) if pl_amount>0 \
                else ('Closing Fiscal Year %s'%self.code),
            'account_id': earning_account.id if pl_amount>0 else counterpart_earning_account.id,
            'debit': abs(pl_amount) if pl_amount<0 else 0.0,
            'credit': pl_amount if pl_amount>0 else 0.0,
            'move_id': closing_move.id
        }
        AccountMoveLineCr.create(ct_move_line_dict)

        self.move_id = closing_move.id
        closing_move.with_context(closing=True).post()
        return self.close_fiscalyear()

    @api.multi
    def cancel_closing_entry(self):
        self.ensure_one()
        if self.move_id:
            self.with_context(closing=True).move_id.button_cancel()
            self.with_context(closing=True).move_id.unlink()
        return self.reopen_fiscalyear()

    # Override versi Konsalten : by Hendra
    @api.one
    def create_period(self):
        if not hasattr(self, 'interval'):
            self.interval = 1
        period_obj = self.env['account.period']
        for fy in self.browse(self.ids):
            if fy.period_ids:
                continue
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create({
                'name': "%s %s" % (_('Closing Period'), ds.strftime('%Y')),
                'code': ds.strftime('13/%Y'),
                'date_start': fy.date_stop,
                'date_stop': fy.date_stop,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=self.interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=self.interval)
        return True