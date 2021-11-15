# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from odoo import api, fields, models
from odoo.addons.jasper_reports import JasperDataParser
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"
    
    report_type = fields.Selection([('xlsx','Excel Workbook'), ('pdf','PDF')], string="Document Type", default=lambda *a: 'xlsx')

    def check_report(self, data):
        if self.report_type != 'xlsx':
            res = super(AccountingReport, self).check_report()
            return res
        else:
            self.ensure_one()
            data = {}
            # data['ids'] = self.env.context.get('active_ids', [])
            # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
            # data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
            # used_context = self._build_contexts(data)
            # data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
            
            # data2 = {}
            # data2['form'] = self.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
            # for field in ['account_report_id']:
            #     if isinstance(data2['form'][field], tuple):
            #         data2['form'][field] = data2['form'][field][0]
            # comparison_context = self._build_comparison_context(data2)
            
            # data['form']['comparison_context'] = comparison_context
            # data['form'].update(self.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move'])[0])
            return self.env['report'].get_action(self, 'report_financial_xlsx', data=data)

class AccountLegalReport(models.TransientModel):
    _name = 'account.legal.report'
    _description = 'Legal Report'

    type = fields.Selection([('balance_sheet', 'Balance Sheet'),('profit_loss', 'Profit and Loss')], required=True, default=lambda self: self._context.get('type','balance_sheet'))
    date_start = fields.Date('Date Start', required=True)
    date_stop = fields.Date('Date Stop', required=True)
    target_move = fields.Selection([('posted','Posted Entries'),('all','All Entries')], 'Target Move', default='posted', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, required=True)

    @api.multi
    def print_report(self):
        self.ensure_one()
        if self.type=='balance_sheet':
            report_name = 'account_report_balance_sheet'
        else:
            report_name = 'account_report_profit_loss'

        if self.target_move=='posted':
            target_move_query = "am1.state='posted'"
        else:
            target_move_query = "am1.state in ('draft','posted')"
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : report_name,
            'datas'         : {
                'model'         : 'account.legal.report',
                'id'            : self.id,
                'ids'           : [self.id],
                'report_type'   : 'xlsx',
                'form'          : {
                        'target_move': target_move_query,
                        'date_start': self.date_start,
                        'date_stop': self.date_stop,
                        'year_start': (datetime.strptime(self.date_start, '%Y-%m-%d') + relativedelta(month=1, day=1)).strftime('%Y-%m-%d'),
                        'company_id': self.company_id.id,
                        'company_name': self.company_id.name,
                    },
                },
            'nodestroy': False
        }