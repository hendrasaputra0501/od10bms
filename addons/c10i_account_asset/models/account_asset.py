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
from odoo.tools import float_compare, float_is_zero


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    writeoff_sale_account_asset_id = fields.Many2one('account.account', 'Write-off Sale Account')

class AccountAssetCapitalizeHistory(models.Model):
    _name = 'account.asset.capitalize.history'

    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    date = fields.Date('Date', required=True)
    value = fields.Float('Value', digits=0, required=True)
    ref = fields.Char('Reference')

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    date_accrue = fields.Date('Date Accrue')
    account_depreciation_expense_id = fields.Many2one('account.account', 'Depreciation Expense Acccount', help='If you fill this, then this Asset will use this account as Expense Depreciation')
    prev_accumulated_depr = fields.Float(string='Prev. Accumulated Depreciation', digits=0, readonly=True, states={'draft': [('readonly', False)]},
        help="It is the acculumated depreciation amount of the Opening Asset Entry.")
    disposal_reason = fields.Text(string='Disposal Reason', readonly=True)
    disposal_method = fields.Selection(selection=[('asset_sale', 'Sold'), ('asset_dispose', 'Disposed')], string='Disposal Method', readonly=True)
    disposal_move_id = fields.Many2one('account.move', 'Disposal Entry', readonly=True)
    disposal_invoice_id = fields.Many2one('account.invoice', 'Sales Invoice Asset', readonly=True)
    disposal_move_line_ids = fields.One2many('account.move.line', related='disposal_move_id.line_ids', string='Disposal Asset', readonly=True)
    capitalize_line_ids = fields.One2many('account.asset.capitalize.history', 'asset_id', string='Capitalize Value History', digits=0)
    capitalize_value = fields.Float(string='Capitalize Value', digits=0, compute='_amount_capitalize')

    @api.depends('capitalize_line_ids.value')
    def _amount_capitalize(self):
        for asset in self:
            capitalize_value = 0.0
            for cap in asset.capitalize_line_ids:
                capitalize_value += cap.value
            asset.capitalize_value = capitalize_value

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'disposal_reason': '',
            'disposal_method': False,
            'disposal_move_id': False,
            'disposal_invoice_id': False,
        })
        return super(AccountAssetAsset, self).copy(default)
    
    @api.multi
    def validate(self):
        self.write({'state': 'open'})
        fields = [
            'method',
            'method_number',
            'method_period',
            'method_end',
            'method_progress_factor',
            'method_time',
            'salvage_value',
            'prev_accumulated_depr',
            'invoice_id',
        ]
        ref_tracked_fields = self.env['account.asset.asset'].fields_get(fields)
        for asset in self:
            tracked_fields = ref_tracked_fields.copy()
            if asset.method == 'linear':
                del(tracked_fields['method_progress_factor'])
            if asset.method_time != 'end':
                del(tracked_fields['method_end'])
            else:
                del(tracked_fields['method_number'])
            dummy, tracking_value_ids = asset._message_track(tracked_fields, dict.fromkeys(fields))
            asset.message_post(subject=_('Asset created'), tracking_value_ids=tracking_value_ids)

    @api.one
    @api.depends('value', 'prev_accumulated_depr', 'salvage_value', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount', 'disposal_move_id.state', 'capitalize_value')
    def _amount_residual(self):
        total_amount = 0.0
        for line in self.depreciation_line_ids:
            if line.move_check:
                total_amount += line.amount
        if self.disposal_move_id and self.disposal_move_id.state=='posted':
            self.value_residual = 0.0
        else:
            self.value_residual = (self.value + self.capitalize_value) - total_amount - (self.prev_accumulated_depr + self.salvage_value)

    @api.multi
    def update_asset_value(self, capitalize_value, date):
        self.ensure_one()
        context = self.env.context
        if context.get('cancel'):
            self.env['account.asset.capitalize.history'].create({
                'asset_id': self.id, 
                'ref': context.get('ref', ''), 
                'value': capitalize_value, 
                'date': date
                })
        else:
            self.env['account.asset.capitalize.history'].create({
                'asset_id': self.id, 
                'ref': context.get('ref', ''), 
                'value': capitalize_value,
                'date': date
                })
        self.compute_depreciation_board()

    @api.multi
    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            print 
            if self.prorata:
                # if we already have some previous validated entries, starting date is last entry + method perio
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date()
            else:
                # depreciation_date = 1st of January of purchase year if annual valuation, 1st of
                # purchase month in other cases
                if self.method_period >= 12:
                    asset_date = datetime.strptime(self.date[:4] + '-01-01', DF).date()
                else:
                    asset_date = datetime.strptime(self.date[:7] + '-01', DF).date()
                # if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = asset_date
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)

            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                sequence = x + 1
                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
                amount = self.currency_id.round(amount)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + self.capitalize_value + residual_amount),
                    'depreciation_date': depreciation_date.strftime(DF),
                }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                depreciation_date = date(year, month, day) + relativedelta(months=+self.method_period)
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year

        self.write({'depreciation_line_ids': commands})

        return True

# class AccountAssetCapitalizeDepreciation(models.Model):
#     _name = 'account.asset.capitalize.depreciation'

#     depr_id = fields.Many2one('account.asset.depreciation.line', string='Depreciation')
#     capitalize_history_id = fields.Many2one('account.asset.capitalize.history', string='Capitalize Ref')
#     value = fields.Float('Additional Value')

class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    # @api.depends('capitalize_line_ids.value')
    # def _amount_depr_capitalize(self):
    #     for depr in self:
    #         depr_capitalize_value = 0.0
    #         for cap in depr.depr_capitalize_line_ids
    #             depr_capitalize_value += cap.value
    #         depr.depr_capitalize_value = depr_capitalize_value

    disposal_method = fields.Selection([('asset_sale', 'Sold'), ('asset_dispose', 'Disposed')], string='Disposal Method')
    disposal_reason = fields.Text(string='Disposal Reason')

    # depr_capitalize_line_ids = fields.One2many('account.asset.capitalize.depreciation', string='Depr. Capitalize Value History', digits=0)
    # depr_capitalize_value = fields.Float('Depr. Capitalize Addition', compute='_amount_depr_capitalize')

    @api.model
    def _cron_depreciate(self):
        to_depreciate = self.search([('depreciation_date','<=',fields.Date.context_today(self)), ('asset_id.state','=','open'), ('move_id','=',False)])
        to_depreciate.create_move(datetime.today())

    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        for line in self:
            if line.move_id:
                raise UserError(_('This depreciation is already linked to a journal entry! Please post or delete it.'))
            category_id = line.asset_id.category_id
            depreciation_date = self.env.context.get(
                'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
            asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
            move_line_1 = {
                'name': asset_name,
                'account_id': category_id.account_depreciation_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': category_id.journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
            }
            move_line_2 = {
                'name': asset_name,
                'account_id': line.asset_id.account_depreciation_expense_id and line.asset_id.account_depreciation_expense_id.id or category_id.account_depreciation_expense_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': category_id.journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.amount or 0.0,
            }
            move_vals = {
                'ref': line.asset_id.code,
                'date': depreciation_date or False,
                'journal_id': category_id.journal_id.id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            }
            move = self.env['account.move'].create(move_vals)
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move

        if post_move and created_moves:
            created_moves.filtered(
                lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
        return [x.id for x in created_moves]