# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import logging
import time
import datetime
import calendar
from odoo.tools.translate import _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import base64
import xlrd

###################################################### Master Utility #######################################################
class mill_utility(models.Model):
    _name           = 'mill.utility'
    _description    = 'Mill Utility'

    def _default_location_type(self):
        location_type_ids = self.env['account.location.type'].search([('utility', '=', True)])
        if location_type_ids:
            return location_type_ids[0].id
        else:
            return False

    name                = fields.Char("Name")
    code                = fields.Char("Code")
    location_id         = fields.Many2one(comodel_name="account.location", string="Lokasi")
    location_type_id    = fields.Many2one(comodel_name="account.location.type", string="Tipe Lokasi", ondelete="restrict", default=_default_location_type)
    type                = fields.Selection([('ws', 'Workshop'), ('vh', 'Vehicle'),
                                            ('ma', 'Machine'), ('lb','Laboratory'),
                                            ('he', 'Alat Berat'),]
                                           , string='Type')
    active              = fields.Boolean("Active", default=True)
    company_id          = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, values):
        location_name       = values.get('name', False)
        location_code       = values.get('code', False)
        location_type_id    = values.get('location_type_id', False)
        location_values     = {
            'name'      : location_name or "(NoName)",
            'code'      : location_code or "(NoCode)",
            'type_id'   : location_type_id or False,
        }
        new_location = False
        location = super(mill_utility, self).create(values)
        if location:
            new_location = self.env['account.location'].create(location_values)
        if new_location:
            location.location_id = new_location.id
        return location

    @api.multi
    def write(self, values):
        if 'name' in values and self.location_id:
            self.location_id.write({'name': values.get('name', False)})
        if 'code' in values and self.location_id:
            self.location_id.write({'code': values.get('code', False)})
        if 'location_type_id' in values and self.location_id:
            self.location_id.write({'type_id': values.get('location_type_id', False)})
        if 'active' in values and self.location_id:
            self.location_id.write({'active': values.get('active', False)})
        return super(mill_utility, self).write(values)

    @api.multi
    def unlink(self):
        for location in self:
            if location.location_id:
                location.location_id.unlink()
        location = super(mill_utility, self).unlink()
        return location

################################################### End Of Master Utility ###################################################

class mill_department(models.Model):
    _name           = 'mill.department'
    _description    = 'Mill Department'

    name                = fields.Char("Name")
    code                = fields.Char("Code")
    location_id         = fields.Many2one(comodel_name="account.location", string="Lokasi")
    location_type_id    = fields.Many2one(comodel_name="account.location.type", string="Tipe Lokasi", ondelete="restrict")
    active              = fields.Boolean("Active", default=True)
    company_id          = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)


    @api.model
    def create(self, values):
        location_name       = values.get('name', False)
        location_code       = values.get('code', False)
        location_type_id    = values.get('location_type_id', False)
        location_values     = {
            'name'      : location_name or "(NoName)",
            'code'      : location_code or "(NoCode)",
            'type_id'   : location_type_id or False,
        }
        new_location = False
        location = super(mill_department, self).create(values)
        if location:
            new_location = self.env['account.location'].create(location_values)
        if new_location:
            location.location_id = new_location.id
        return location

    @api.multi
    def write(self, values):
        if 'name' in values and self.location_id:
            self.location_id.write({'name': values.get('name', False)})
        if 'code' in values and self.location_id:
            self.location_id.write({'code': values.get('code', False)})
        if 'location_type_id' in values and self.location_id:
            self.location_id.write({'type_id': values.get('location_type_id', False)})
        if 'active' in values and self.location_id:
            self.location_id.write({'active': values.get('active', False)})
        return super(mill_department, self).write(values)

    @api.multi
    def unlink(self):
        for location in self:
            if location.location_id:
                location.location_id.unlink()
        location = super(mill_department, self).unlink()
        return location