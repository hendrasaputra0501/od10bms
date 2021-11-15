# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Chaidar Aji Nugroho <chaidaraji@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning

class purchase_rfq(models.Model):
    _inherit 			= 'purchase.rfq'

class purchase_rfq_line(models.Model):
    _inherit = 'purchase.rfq.line'

    note  = fields.Char('Note')