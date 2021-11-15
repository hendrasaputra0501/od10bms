# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class WizardDownpaymentSale(models.TransientModel):
    _name	        = "wizard.downpayment.sale"
    _description 	= "Downpayment Sale"

    @api.model
    def default_get(self, fields):
        record_ids  = self._context.get('active_ids')
        result      = super(WizardDownpaymentSale, self).default_get(fields)
        if record_ids:
            downpayment_data        = self.env['sale.order'].browse(record_ids)
            downpayment_residual    = 100
            if downpayment_data:
                if 'doc_type_id' in fields:
                    result['doc_type_id'] = downpayment_data.doc_type_id.id
                if 'sale_id' in fields:
                    result['sale_id'] = downpayment_data.id
                if 'name' in fields:
                    result['name'] = downpayment_data.name
                if 'auto_downpayment' in fields:
                    result['auto_downpayment'] = downpayment_data.auto_downpayment
                if 'amount_total' in fields:
                    # result['amount_total'] = downpayment_data.amount_total
                    result['amount_total'] = downpayment_data.amount_untaxed
                if 'taxes_id' in fields:
                    tax_ids = []
                    for line in downpayment_data.order_line:
                        if line.tax_id:
                            tax_ids.extend(line.tax_id.ids)
                    if tax_ids:
                        result['taxes_id'] = [(6,0,list(set(tax_ids)))]
                if 'downpayment_residual' in fields:
                    if downpayment_data.advance_invoice_ids:
                        for advance in downpayment_data.advance_invoice_ids:
                            if advance.percentage_downpayment > 0 and advance.state not in ['cancel']:
                                downpayment_residual = downpayment_residual - advance.percentage_downpayment
                    result['downpayment_residual'] = downpayment_residual
                if 'downpayment' in fields:
                    result['downpayment'] = downpayment_residual
        return result

    name                = fields.Char("Name")
    doc_type_id         = fields.Many2one("res.document.type", "Type")
    downpayment         = fields.Float("Percentage",)
    downpayment_value   = fields.Float("Amount",)
    taxes_id            = fields.Many2many('account.tax', string='Taxes')
    amount_total        = fields.Float("Total Amount",)
    downpayment_residual= fields.Float("Residual ",)
    downpayment_date    = fields.Date("Date",)
    auto_downpayment    = fields.Boolean(string="Auto Down Payment")
    sale_id             = fields.Many2one('sale.order', string='Sale')
    user_id             = fields.Many2one('res.users', string='Responsible', readonly=True, default=lambda self: self.env.user)
    company_id          = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)

    @api.onchange('downpayment')
    def onchange_downpayment(self):
        if self.downpayment:
            self.downpayment_value = self.amount_total * ((self.downpayment or 0.0) / 100.0)
            if self.downpayment > self.downpayment_residual:
                self.downpayment = self.downpayment_residual

    @api.multi
    def create_downpayment(self):
        invoice_advance_obj         = self.env['account.invoice.advance']
        invoice_advance_line_obj    = self.env['account.invoice.advance.line']
        if self.doc_type_id.auto_downpayment:
            header_values = {
                'partner_id'                : self.sale_id.partner_id and self.sale_id.partner_id.id or False,
                'payment_term_id'           : self.sale_id.payment_term_id and self.sale_id.payment_term_id.id or False,
                'name'                      : self.sale_id.name or "",
                'date_invoice'              : self.downpayment_date or False,
                'type'                      : 'out_advance',
                'user_id'                   : self.env.user.id or self.user_id.id or False,
                'currency_id'               : self.sale_id.currency_id and self.sale_id.currency_id.id or False,
                'journal_id'                : self.sale_id.doc_type_id.downpayment_journal_id and self.sale_id.doc_type_id.journal_id.id or False,
                'account_id'                : self.sale_id.partner_id.property_account_receivable_id and self.sale_id.partner_id.property_account_receivable_id.id or False,
                'sale_id'                   : self.sale_id.id or False,
                'percentage_downpayment'    : self.downpayment,
            }
            new_invoice_advance = invoice_advance_obj.sudo().create(header_values)
            if new_invoice_advance:
                if new_invoice_advance:
                    lines_value     = {
                        'name'              : "Uang Muka " + self.name,
                        'quantity'          : 1,
                        'price_unit'        : self.downpayment_value,
                        'invoice_line_tax_ids': self.taxes_id and [(6,0,self.taxes_id.ids)] or False,
                        'price_subtotal'    : self.downpayment_value,
                        'account_id'        : self.doc_type_id.downpayment_account_id and self.doc_type_id.downpayment_account_id.id or False,
                        'invoice_id'        : new_invoice_advance.id
                    }
                    invoice_advance_line_obj.sudo().create(lines_value)
            new_invoice_advance.compute_taxes()
            if new_invoice_advance:
                return {
                    'name'          : ('Advance Invoice'),
                    'view_type'	    : 'form',
                    'view_mode'	    : 'form',
                    'res_model'	    : 'account.invoice.advance',
                    'res_id'	    : new_invoice_advance.id,
                    'type'		    : 'ir.actions.act_window',
                }

class WizardDownpaymentPurchase(models.TransientModel):
    _name	        = "wizard.downpayment.purchase"
    _description 	= "Downpayment Purchase"

    @api.model
    def default_get(self, fields):
        record_ids  = self._context.get('active_ids')
        result      = super(WizardDownpaymentPurchase, self).default_get(fields)
        if record_ids:
            downpayment_data        = self.env['purchase.order'].browse(record_ids)
            downpayment_residual    = 100
            if downpayment_data:
                if 'doc_type_id' in fields:
                    result['doc_type_id'] = downpayment_data.doc_type_id.id
                if 'purchase_id' in fields:
                    result['purchase_id'] = downpayment_data.id
                if 'name' in fields:
                    result['name'] = downpayment_data.name
                if 'auto_downpayment' in fields:
                    result['auto_downpayment'] = downpayment_data.auto_downpayment
                if 'amount_total' in fields:
                    # result['amount_total'] = downpayment_data.amount_total
                    result['amount_total'] = downpayment_data.amount_untaxed
                if 'taxes_id' in fields:
                    tax_ids = []
                    for line in downpayment_data.order_line:
                        if line.taxes_id:
                            tax_ids.extend(line.taxes_id.ids)
                    if tax_ids:
                        result['taxes_id'] = [(6,0,list(set(tax_ids)))]
                if 'downpayment_residual' in fields:
                    if downpayment_data.advance_invoice_ids:
                        for advance in downpayment_data.advance_invoice_ids:
                            if advance.percentage_downpayment > 0 and advance.state not in ['cancel']:
                                downpayment_residual = downpayment_residual - advance.percentage_downpayment
                    result['downpayment_residual'] = downpayment_residual
                if 'downpayment' in fields:
                    result['downpayment'] = downpayment_residual
        return result

    name                = fields.Char("Name")
    doc_type_id         = fields.Many2one("res.document.type", "Type")
    downpayment         = fields.Float("Percentage",)
    downpayment_value   = fields.Float("Amount",)
    amount_total        = fields.Float("Total Amount",)
    downpayment_residual= fields.Float("Residual ",)
    downpayment_date    = fields.Date("Date",)
    taxes_id            = fields.Many2many('account.tax', string='Taxes')
    auto_downpayment    = fields.Boolean(string="Auto Down Payment")
    purchase_id         = fields.Many2one('purchase.order', string='Purchase')
    user_id             = fields.Many2one('res.users', string='Responsible', readonly=True, default=lambda self: self.env.user)
    company_id          = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)

    @api.onchange('downpayment')
    def onchange_downpayment(self):
        if self.downpayment:
            self.downpayment_value = self.amount_total * ((self.downpayment or 0.0) / 100.0)
            if self.downpayment > self.downpayment_residual:
                self.downpayment = self.downpayment_residual

    @api.multi
    def create_downpayment(self):
        invoice_advance_obj         = self.env['account.invoice.advance']
        invoice_advance_line_obj    = self.env['account.invoice.advance.line']
        if self.doc_type_id.auto_downpayment:
            header_values = {
                'partner_id'                : self.purchase_id.partner_id and self.purchase_id.partner_id.id or False,
                'payment_term_id'           : self.purchase_id.payment_term_id and self.purchase_id.payment_term_id.id or False,
                'name'                      : self.purchase_id.name or "",
                'date_invoice'              : self.downpayment_date or False,
                'type'                      : 'in_advance',
                'origin'                    : self.purchase_id.partner_ref or self.purchase_id.name,
                'user_id'                   : self.env.user.id or self.user_id.id or False,
                'currency_id'               : self.purchase_id.currency_id and self.purchase_id.currency_id.id or False,
                'journal_id'                : self.purchase_id.doc_type_id.downpayment_journal_id and self.purchase_id.doc_type_id.journal_id.id or False,
                'account_id'                : self.purchase_id.partner_id.property_account_payable_id and self.purchase_id.partner_id.property_account_payable_id.id or False,
                'purchase_id'               : self.purchase_id.id or False,
                'percentage_downpayment'    : self.downpayment,
                # 'reference'                 : self.purchase_id.partner_ref,
            }
            new_invoice_advance = invoice_advance_obj.sudo().create(header_values)
            if new_invoice_advance:
                if new_invoice_advance:
                    lines_value     = {
                        'name'              : "Uang Muka " + self.name,
                        'quantity'          : 1,
                        'price_unit'        : self.downpayment_value,
                        'invoice_line_tax_ids': self.taxes_id and [(6,0,self.taxes_id.ids)] or False,
                        'price_subtotal'    : self.downpayment_value,
                        'account_id'        : self.doc_type_id.downpayment_account_id and self.doc_type_id.downpayment_account_id.id or False,
                        'invoice_id'        : new_invoice_advance.id
                    }
                    invoice_advance_line_obj.sudo().create(lines_value)
            new_invoice_advance.compute_taxes()
            if new_invoice_advance:
                return {
                    'name'          : ('Advance Bills'),
                    'view_type'	    : 'form',
                    'view_mode'	    : 'form',
                    'res_model'	    : 'account.invoice.advance',
                    'res_id'	    : new_invoice_advance.id,
                    'type'		    : 'ir.actions.act_window',
                }