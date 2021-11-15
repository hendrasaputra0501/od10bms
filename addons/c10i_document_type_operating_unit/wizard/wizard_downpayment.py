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
    _inherit        = "wizard.downpayment.sale"
    _description 	= "Downpayment Sale"

    @api.multi
    def create_downpayment(self):
        downpayment = super(WizardDownpaymentSale, self.sudo()).create_downpayment()
        advance_inv = self.env['account.invoice.advance'].browse(downpayment['res_id'])
        if self.doc_type_id and self.doc_type_id.journal_id and self.doc_type_id.journal_id.operating_unit_id:
            advance_inv.sudo().operating_unit_id = self.doc_type_id.journal_id.operating_unit_id.id
        else:
            advance_inv.sudo().operating_unit_id = self.env.user.default_operating_unit_id.id
        return downpayment

class WizardDownpaymentPurchase(models.TransientModel):
    _inherit        = "wizard.downpayment.purchase"
    _description 	= "Downpayment Purchase"

    @api.multi
    def create_downpayment(self):
        downpayment = super(WizardDownpaymentPurchase, self.sudo()).create_downpayment()
        advance_inv = self.env['account.invoice.advance'].browse(downpayment['res_id'])
        if self.doc_type_id and self.doc_type_id.journal_id and self.doc_type_id.journal_id.operating_unit_id:
            advance_inv.sudo().operating_unit_id = self.doc_type_id.journal_id.operating_unit_id.id
        else:
            advance_inv.sudo().operating_unit_id = self.env.user.default_operating_unit_id.id
        return downpayment