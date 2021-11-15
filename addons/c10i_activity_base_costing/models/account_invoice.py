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
        for line in res:
            if not line.get('invl_id', False):
                continue
            inv_line = self.env['account.invoice.line'].browse(line['invl_id'])
            line.update({
                'account_activity_id': inv_line.account_activity_id and inv_line.account_activity_id.id or False,
                })    
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res.update({
            'account_activity_id': line.get('account_activity_id', False),
        })
        return res

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    account_activity_id = fields.Many2one("account.activity", string="Activity", ondelete="restrict")