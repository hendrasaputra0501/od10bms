# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Dion Martin
#   @modifier Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WizardClosePurchaseRequest(models.TransientModel):
    _name 			= "wizard.close.purchase.request"
    _description 	= "Close Purchase Request"	   

    @api.model
    def view_init(self, fields):
        records = self.env['purchase.request'].browse(self._context.get('active_ids', []))
        if any(record.state != 'approved' for record in records):
            raise UserError(_("You can only close approved PBJ"))
    
    check_approved = fields.Boolean('Check Approved')

    @api.multi
    def button_done(self):
        records = self.env['purchase.request'].browse(self._context.get('active_ids', []))
        for record in records:
            record.state = 'done'