# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Anggar Bagus Kurniawan <anggar.bagus@gmail.com>
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

class MillDensityChart(models.Model):
    _name = "mill.density.chart"
    _description = "CRUDE PALM OIL DENSITY CHART"
    _rec_name = "temperature"

    temperature = fields.Float('Temperature', required=True)
    density = fields.Float('Density', required=True, digits=dp.get_precision('Density'))

    _sql_constraints = [
       ('temperature_unique', 'unique(temperature)', 'Temperature sudah pernah diinput'),  
    ]

class MillKoreksiSuhu(models.Model):
    _name = "mill.koreksi.suhu"
    _description = "Faktor Koreksi Suhu"
    _rec_name = 'mill_storage_id'

    mill_storage_id = fields.Many2one('mill.storage', string="Tangki", required=True)
    temperature_calibrated = fields.Float('Suhu Kalibrasi BMKG', required=True)
    uom_id = fields.Many2one('product.uom', string='UoM', required=True)
    faktor_koreksi = fields.Float('Faktor Koreksi', required=True, digits=dp.get_precision('Koreksi Suhu'))

    _sql_constraints = [
       ('mill_storage_id_unique', 'unique(mill_storage_id)', 'Tangki sudah pernah diinput'),  
    ]