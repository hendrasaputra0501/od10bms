# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia <www.konsaltenindonesia.com>
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

class AccountInvoice(models.Model):
    _inherit        = "account.invoice"

    @api.multi
    def print_report_invoice(self):
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : 'report_nota_invoice',
            'datas'         : {
                'model'         : 'account.invoice',
                'id'            : self.id,
                'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or [],
                'name'          : self.number or "Report Nota Invoice",
                },
            'nodestroy'     : False
        }

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        seq = 8
        for line in res:
            if self.type in ('out_invoice', 'in_refund'):
                if line[2]['inv_line_type']=='dest':
                    line[2].update({'sequence': 5})
                else:
                    line[2].update({'sequence': seq})
            else:
                if line[2]['inv_line_type']=='dest':
                    line[2].update({'sequence': 999})
                else:
                    line[2].update({'sequence': seq})
            seq+=1
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res.update({'inv_line_type': line['type']})
        return res

class AccountTax(models.Model):
    _inherit    = "account.tax"

    report_name = fields.Char("Name Reporting")

class AccountJournal(models.Model):
    _inherit = "account.journal"

    receipt_sequence = fields.Boolean('Dedicated Cash/Bank Receipt Sequence', 
        help="Check this box if you don't want to share the same sequence for "
            "payment and receipt made from this journal", default=False)
    receipt_sequence_id = fields.Many2one('ir.sequence', string='Receipt Entry Sequence',
        help="This field contains the information related to the numbering of the journal"
            " entries of this journal.", required=False, copy=False)
    type = fields.Selection(selection_add=[('closing', 'Closing')])

    @api.model
    def _get_sequence_prefix(self, code, refund=False, receipt=False):
        prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        elif receipt:
            prefix = 'IN' + prefix
        return prefix + '/%(range_year)s/'

    @api.model
    def _create_sequence(self, vals, refund=False, receipt=False):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix = self._get_sequence_prefix(vals['code'], refund, receipt)
        seq = {
            'name': refund and vals['name'] + _(': Refund') or vals['name'],
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq)

    @api.model
    def create(self, vals):
        if vals.get('type') in ('cash', 'bank') and vals.get('receipt_sequence') and not vals.get('refund_sequence_id'):
            vals.update({'receipt_sequence_id': self.sudo()._create_sequence(vals, receipt=True).id})
        journal = super(AccountJournal, self).create(vals)
        return journal

    @api.multi
    def write(self, vals):
        result = super(AccountJournal, self).write(vals)
        if vals.get('receipt_sequence'):
            for journal in self.filtered(lambda j: j.type in ('cash', 'bank') and not j.receipt_sequence_id):
                journal_vals = {
                    'name': journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code
                }
                journal.receipt_sequence_id = self.sudo()._create_sequence(journal_vals, receipt=True).id
        return result


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True
        prec = self.env['decimal.precision'].precision_get('Account')

        self._cr.execute("""\
                SELECT      move_id
                FROM        account_move_line
                WHERE       move_id in %s
                GROUP BY    move_id
                HAVING      abs(sum(debit) - sum(credit)) > %s
                """, (tuple(self.ids), 10 ** (-prec)))
        if len(self._cr.fetchall()) != 0:
            raise UserError(_("Cannot create unbalanced journal entry."))
        return True

    @api.model
    def create(self, vals):
        move_date = vals.get('date',time.strftime('%Y-%m-%d'))
        AccountPeriod = self.env['account.period'].sudo()

        closed_period_domain = [('date_start','<=',move_date),('date_stop','>=',move_date),('state','=','done')]
        if not self._context.get('closing',False) and AccountPeriod.search(closed_period_domain):
            raise UserError(_('Journal Creation Failed!\nYou cannot create journal entries in a closed period.'))
        period_id = self.env['account.period'].search([('date_start','<=',move_date),('date_stop','>=',move_date), ('special', '=', False)])
        vals.update({'period_id':period_id.id})
        return super(AccountMove, self).create(vals)

    @api.multi
    def write(self, update_vals):
        AccountPeriod = self.env['account.period'].sudo()
        for move in self:
            move_date = update_vals.get('date', move.date)
            closed_period_domain = [('date_start', '<=', move_date), ('date_stop', '>=', move_date),('state', '=', 'done')]
            if not (self._context.get('closing', False) or move.journal_id.type == 'closing') and AccountPeriod.search(closed_period_domain):
                raise UserError(_('Journal Modification Failed!\nYou cannot modify journal entries in a closed period.'))
        return super(AccountMove, self).write(update_vals)

    @api.multi
    def button_cancel(self):
        AccountPeriod = self.env['account.period'].sudo()
        for move in self:
            move_date = move.date
            closed_period_domain = [('date_start', '<=', move_date), ('date_stop', '>=', move_date),('state', '=', 'done')]
            if not (self._context.get('closing', False) or move.journal_id.type == 'closing') and AccountPeriod.search(closed_period_domain):
                raise UserError(_('Journal Cancelation Failed!\nYou cannot cancel journal entries in a closed period.'))
        return super(AccountMove, self).button_cancel()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sequence = fields.Integer('Sequence')
    _order = "date desc, move_id desc, sequence asc, id asc"