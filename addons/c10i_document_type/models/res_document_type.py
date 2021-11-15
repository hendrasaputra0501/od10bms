# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Users(models.Model):
    _inherit = 'res.users'

    document_type_ids = fields.Many2many('res.document.type', 'document_user_rel', 'user_id', 'document_id', string='Access Document Type(s)')

class res_document_type(models.Model):
    _name           = 'res.document.type'
    _description    = 'Document Type'
    _inherit        = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('company_id')
    def _get_company_partner(self):
        for doc in self:
            if doc.company_id:
                doc.partner_company_id = doc.company_id.partner_id.id

    name                    = fields.Char("Name")
    sales                   = fields.Boolean("Is Sales?")
    purchase                = fields.Boolean("Is Purchase?")
    spk                     = fields.Boolean("Is SPK?")
    no_create_picking       = fields.Boolean("No Create Picking?")
    auto_downpayment        = fields.Boolean("Auto Downpayment")
    sequence_id             = fields.Many2one("ir.sequence", "Sequence", ondelete="restrict")
    report_id               = fields.Many2one("ir.actions.report.xml", "Report", ondelete="restrict")
    journal_id              = fields.Many2one("account.journal", "Journal", ondelete="restrict")
    account_id              = fields.Many2one("account.account", "Account", ondelete="restrict")
    downpayment_journal_id  = fields.Many2one("account.journal", "Down Payment Journal", ondelete="restrict")
    downpayment_account_id  = fields.Many2one("account.account", "Down Payment Account", ondelete="restrict")
    downpayment_default     = fields.Float("Default Down Payment", default=15)
    payment_term_id         = fields.Many2one("account.payment.term", "Payment Term", ondelete="restrict")
    incoterm_id             = fields.Many2one("stock.incoterms", "Incoterm", ondelete="restrict")
    picking_type_id         = fields.Many2one("stock.picking.type", "Picking Type", ondelete="restrict")
    tolerance               = fields.Float("Tolerance")
    shipping_partner_id     = fields.Many2one('res.partner', 'Delivery Address')
    invoice_partner_id 	    = fields.Many2one('res.partner', 'Invoice Address')
    company_id              = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    partner_company_id      = fields.Many2one('res.partner', compute='_get_company_partner', string='Partner Company')
    user_ids                = fields.Many2many('res.users', 'document_user_rel', 'document_id', 'user_id', string='Users')
    purchase_report_sign_1  = fields.Char("Sign 1", default="Purchasing")
    purchase_report_sign_2  = fields.Char("Sign 2", default="Accounting")
    purchase_report_sign_3  = fields.Char("Sign 3", default="Accounting")
    purchase_report_sign_4  = fields.Char("Sign 4", default="Accounting")
    purchase_report_sign_5  = fields.Char("Sign 5", default="Finance")
    purchase_report_sign_6  = fields.Char("Sign 6", default="Finance")

class InvoiceAdvance(models.Model):
    _inherit = 'account.invoice.advance'

    sale_id                 = fields.Many2one(comodel_name='sale.order', string="Sale")
    purchase_id             = fields.Many2one(comodel_name='purchase.order', string="Purchase")
    percentage_downpayment  = fields.Float("Down Payment Percentage")

    @api.onchange('purchase_id')
    def onchange_purchase(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id
        self.origin = self.purchase_id.partner_ref or self.purchase_id.name
        new_lines = self.env['account.invoice.advance.line']
        tax_ids = []
        for x in self.purchase_id.order_line:
            if x.taxes_id:
                tax_ids.extend(x.taxes_id.ids)
        data = {
            'name'              : "Uang Muka " + self.purchase_id.name,
            'quantity'          : 1,
            'price_unit'        : self.purchase_id.amount_untaxed,
            'invoice_line_tax_ids': tax_ids and [(6,0,list(set(tax_ids)))] or False,
            'account_id'        : self.purchase_id.doc_type_id.downpayment_account_id and self.purchase_id.doc_type_id.downpayment_account_id.id or False,
        }
        new_line = new_lines.new(data)
        new_line._set_additional_fields(self)
        new_lines += new_line

        self.invoice_line_ids += new_lines
        return {}