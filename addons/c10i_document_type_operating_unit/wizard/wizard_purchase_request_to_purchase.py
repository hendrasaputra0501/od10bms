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
from odoo import api, fields, models, SUPERUSER_ID, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

class WizardPurchaseRequestToPurchase(models.TransientModel):
    _inherit    = "wizard.purchase.request.to.purchase"

    @api.multi
    def create_purchase(self):
        ctx = self.env.context.copy()
        ctx.update({'doc_type_id' : self.doc_type_id.id})
        if self.doc_type_id and self.doc_type_id.picking_type_id and self.doc_type_id.picking_type_id.warehouse_id.operating_unit_id:
            ctx.update({'operating_unit_id': self.doc_type_id.picking_type_id.warehouse_id.operating_unit_id.id})
        result      = super(WizardPurchaseRequestToPurchase, self.with_context(ctx)).create_purchase()
        return result