from dateutil.parser import parse
from odoo import api, fields, models, _
from datetime import datetime
import time

class WizardReportPPN(models.TransientModel):
    _name = 'wizard.report.ppn'
    _description = 'Laporan PPN Masukan-Keluaran'

    partner_ids = fields.Many2many('res.partner', string='Partner')
    account_group = fields.Many2one(comodel_name='tax.account.group', string="Account Group", required=True)
    account_ids = fields.Many2many(comodel_name='account.account', string='Account', compute="_onchange_account_group")
    date_from = fields.Date('Date From', required=True, default=lambda self:time.strftime('%Y-%m-%d'))
    date_to = fields.Date('Date To', required=True, default=lambda self:time.strftime('%Y-%m-%d'))

    @api.onchange('account_group')
    def _onchange_account_group(self):
        for record in self:
            if record.account_group:
                record.account_ids = record.account_group.account_ids
    
    @api.multi
    def print_report(self):
        data = self.read()[0]
        
        date_from = parse(data['date_from'])
        date_from_format = date_from.strftime('%d %B %Y')

        date_to = parse(data['date_to'])
        date_to_format = date_to.strftime('%d %B %Y')

        return {
            'type'          : 'ir.actions.report.xml',
            'name'          : 'Laporan PPN Masukan-Keluaran ' + date_from_format + ' - ' + date_to_format,
            'report_name'   : 'c10i_tax_payment.report_ppn_xlsx',
            'datas': {
                'id'            : self.id,
                'ids'           : [],
                'report_type'   : 'xlsx',
                'form'          : data
            },
            'nodestroy'     : False
        }
