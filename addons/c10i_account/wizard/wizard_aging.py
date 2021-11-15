# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import base64
from openerp.tools.translate import _
import time
from datetime import datetime
from openerp.addons.jasper_reports import JasperDataParser

class wizard_aging(models.TransientModel):
    _name = "report.aging"
    _description = "Report Aging"
      
    from_date = fields.Date('As of date', required=True, default=lambda self: self._context.get('Date', fields.Date.context_today(self)))
    company = fields.Many2one("res.company","Company",required=1,default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    journal = fields.Many2many('account.journal','account_journal_aging_rel','aj_aging_id','aj_id',"Journal", domain=[('type', 'in', ('sale','sale_refund','purchase','purchase_refund'))])
    partner = fields.Many2many('res.partner','res_partner_aging_rel','rp_aging_id','aj_id',"Partner", domain=[('active', '=', True)])
    usia = fields.Integer('usia', default=30)
    invoice = fields.Selection([('summary','Summary'),('detail','Detail')],string='List Invoice',default='summary')
    Partner_type = fields.Selection([('receivable','Receivable Account'),('payable','Payable Account'),('all','Receivable and Payable Account')],string='Account_Type',default='receivable')
    report_type = fields.Selection([('xlsx','XLS'),('pdf','PDF')],string='Type',default='pdf')     
    
    @api.multi
    def create_report(self):
        data = self.read()[-1]
        if  data['report_type'] == 'xlsx':
            return {
                    'type'         : 'ir.actions.report.xml',
                    'report_name'   : 'report_aging_xls',
                    'datas': {
                            'model':'report.aging',
                            'id': self._context.get('active_ids') and self._context.get('active_ids')[0] or  self.id,
                            'ids': self._context.get('active_ids') and self._context.get('active_ids') or[],
                            'report_type': data['report_type'],
                            'form':data
                        },
                    'nodestroy': False
                    }        
        else:
            return {
                    'type'         : 'ir.actions.report.xml',
                    'report_name'   : 'report_aging',
                    'datas': {
                            'model':'report.aging',
                            'id': self._context.get('active_ids') and self._context.get('active_ids')[0] or  self.id,
                            'ids': self._context.get('active_ids') and self._context.get('active_ids') or[],
                            'report_type': data['report_type'],
                            'form':data
                        },
                    'nodestroy': False
                    }
        
wizard_aging()
