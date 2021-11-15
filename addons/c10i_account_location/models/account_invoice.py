# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
import urllib3
from lxml import etree
import time

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        default_loc_type = self.env['account.location.type'].search([('name','=','-')])
        for line in res:
            if not line.get('invl_id', False):
                continue
            inv_line = self.env['account.invoice.line'].browse(line['invl_id'])
            line.update({
                'account_location_type_id': inv_line.account_location_type_id and inv_line.account_location_type_id.id or (default_loc_type and default_loc_type[0].id or False),
                'account_location_id': inv_line.account_location_id and inv_line.account_location_id.id or False,
                })    
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        default_loc_type = self.env['account.location.type'].search([('name','=','-')])
        res.update({
            'account_location_type_id': line.get('account_location_type_id', default_loc_type and default_loc_type[0].id or False),
            'account_location_id': line.get('account_location_id', False),
        })
        return res
        
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    account_location_type_id = fields.Many2one(comodel_name="account.location.type", string="Tipe Lokasi", ondelete="restrict")
    account_location_id = fields.Many2one(comodel_name="account.location", string="Lokasi", ondelete="restrict")
    account_location_type_no_location = fields.Boolean(string="Location Type No Account", related="account_location_type_id.no_location")

    @api.onchange('account_location_type_id')
    def _onchange_account_location_type_id(self):
        if self.account_location_type_id:
            self.account_location_id = False
            if self.account_location_type_id.no_location and (self.account_location_type_id.general_charge):
                self.account_id = False
            else:
                self.account_id = self.account_location_type_id.account_id and self.account_location_type_id.account_id.id or False