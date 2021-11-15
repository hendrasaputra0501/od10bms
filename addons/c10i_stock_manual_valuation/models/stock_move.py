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
from odoo.addons import decimal_precision as dp
import time

class ProductCategory(models.Model):
    _inherit = 'product.category'

    # prev_balance_account_categ_id = fields.Many2one('account.account', 'Prev. Balance Account')
    purchase_account_categ_id = fields.Many2one('account.account', 'Purchase Account')
    cost_account_categ_ids = fields.One2many('account.account', 'product_cost_value_categ_id', 'Cost Account')
    cost_location_categ_ids = fields.One2many('account.location', 'product_cost_value_categ_id', 'Cost Account Location')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # prev_balance_account_id = fields.Many2one('account.account', 'Prev. Balance Account')
    purchase_account_id = fields.Many2one('account.account', 'Purchase Account')
    cost_account_ids = fields.One2many('account.account', 'product_tmpl_cost_value_id', 'Cost Account')
    cost_location_ids = fields.One2many('account.location', 'product_tmpl_cost_value_id', 'Cost Account Location')