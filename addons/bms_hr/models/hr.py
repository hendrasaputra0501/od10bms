# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Department(models.Model):

    _inherit = "hr.department"

    code = fields.Char(string='Code', required=True)
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit')