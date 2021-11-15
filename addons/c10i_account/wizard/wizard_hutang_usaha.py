# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from dateutil.parser import parse
from odoo import api, fields, models, _
from datetime import datetime
import time

class wizard_hutang_usaha(models.TransientModel):
    _name = 'wizard.hutang.usaha'
    _description = 'Laporan Hutang Usaha'

    partner_ids = fields.Many2many('res.partner', string='Vendor')
    account_ids = fields.Many2many('account.account', string='Account', required=True, default=lambda self: self.env['account.account'].search([('internal_type', '=', "payable")]))
    date_from = fields.Date('Date From', required=True, default=lambda self:time.strftime('%Y-%m-%d'))
    date_to = fields.Date('Date To', required=True, default=lambda self:time.strftime('%Y-%m-%d'))
    
    @api.multi
    def print_report(self):
        data = self.read()[0]
        
        date_from = parse(data['date_from'])
        date_from_format = date_from.strftime('%d %B %Y')

        date_to = parse(data['date_to'])
        date_to_format = date_to.strftime('%d %B %Y')

        return {
            'type'          : 'ir.actions.report.xml',
            'name'          : 'Laporan Hutang Usaha ' + date_from_format + ' - ' + date_to_format,
            'report_name'   : 'c10i_account.report_hutang_usaha_xlsx',
            'datas': {
                'id'            : self.id,
                'ids'           : [],
                'report_type'   : 'xlsx',
                'form'          : data
            },
            'nodestroy'     : False
        }

wizard_hutang_usaha()