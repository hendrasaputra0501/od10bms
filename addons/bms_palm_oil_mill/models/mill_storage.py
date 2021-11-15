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

class MillStorage(models.Model):
    _name = "mill.storage"
    _description = "Master Storage"

    name = fields.Char('Tangki', required=True)
    code = fields.Char('Kode', required=True)
    active = fields.Boolean('Active', default=True)
    type = fields.Selection([('CPO','CPO'),('CST','CST'),('SILO','SILO'),('OILTANK','OIL TANK'),('Kernel','Kernel'),('Nut','Nut'),('Bunker','Bunker')], required=True)
    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location')
    height = fields.Float('Ketinggian', required=True)

    _sql_constraints = [
       ('name_unique', 'unique(name)', 'Nama sudah pernah dipakai'),  
    ]

class MillStorageMeasurement(models.Model):
    _name = "mill.storage.measurement"
    _description = "Tabel Pengukuran Tangki"
    _rec_name = "mill_storage_id"

    mill_storage_id = fields.Many2one('mill.storage', string="Tangki", required=True)
    storage_type = fields.Selection(related='mill_storage_id.type')
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    mill_storage_measurement_cm = fields.One2many('mill.storage.measurement.cm','mill_storage_measurement_id', string='Tabel Pengukuran Tangki Cm')
    mill_storage_measurement_mm = fields.One2many('mill.storage.measurement.mm','mill_storage_measurement_id', string='Tabel Pengukuran Tangki mm')
    mill_storage_measurement_bunker_cm = fields.One2many('mill.storage.measurement.bunker.cm','mill_storage_measurement_id', string='Tabel Pengukuran Bunker Cm')

class MillStorageMeasurementCm(models.Model):
    _name = "mill.storage.measurement.cm"
    _description = "Tabel Pengukuran Tangki Cm"

    mill_storage_measurement_id = fields.Many2one('mill.storage.measurement')
    height = fields.Float('Ketinggian (Cm)', digits=dp.get_precision('Sounding Height Storage'), required=True)
    volume = fields.Float('Volume (L)', required=True)

    _sql_constraints = [
       ('mill_storage_measurement_height_unique', 'unique(mill_storage_measurement_id,height)', 'Ketinggian sudah pernah diinput'),  
    ]

class MillStorageMeasurementMm(models.Model):
    _name = "mill.storage.measurement.mm"
    _description = "Tabel Pengukuran Tangki mm"

    mill_storage_measurement_id = fields.Many2one('mill.storage.measurement')
    height_start = fields.Float('Ketinggian Dari (Cm)', required=True)
    height_end = fields.Float('Ketinggian Sampai (Cm)', required=True)
    height = fields.Float('Ketinggian mm', required=True)
    volume = fields.Float('Volume (L)', required=True)

    _sql_constraints = [
       ('mill_storage_measurement_height_start_end_unique', 'unique(mill_storage_measurement_id, height_start, height_end, height)', 'Ketinggian sudah pernah diinput'),  
    ]



class MillStorageMeasurementCm(models.Model):
    _name = "mill.storage.measurement.bunker.cm"
    _description = "Tabel Pengukuran Bunker Cm"

    mill_storage_measurement_id = fields.Many2one('mill.storage.measurement')
    height = fields.Float('Tinggi (Cm)', digits=dp.get_precision('Sounding Height Kernel'), required=True)
    volume = fields.Float('Volume (M3)', required=True, digits=dp.get_precision('Mill Bunker Volume'))
    density = fields.Float('Density', required=True, digits=dp.get_precision('Mill Bunker Density'))
    tonage = fields.Float('Tonage (MT)', required=True, digits=dp.get_precision('Mill Bunker Volume'))

    _sql_constraints = [
       ('mill_storage_measurement_height_unique', 'unique(mill_storage_measurement_id,height,volume,density,tonage)', 'Ketinggian sudah pernah diinput'),  
    ]
