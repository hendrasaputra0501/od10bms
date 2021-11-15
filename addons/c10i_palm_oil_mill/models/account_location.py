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

class AccountLocationType(models.Model):
    _inherit    = 'account.location.type'

    project         = fields.Boolean("Project")
    utility         = fields.Boolean("Utility")
    infrastructure  = fields.Boolean("Infrastructure")

class AccountLocation(models.Model):
    _inherit = 'account.location'

    mill_costing_categ_id = fields.Many2many('mill.valuation.category', 'mill_costing_account_location_rel', 'account_location_id', 'mill_costing_categ_id', string='Mill Valuation Category')