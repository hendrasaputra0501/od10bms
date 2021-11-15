# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BMTower(models.Model):
    _name = 'bm.tower'
    _description = 'Master data tower'

    name = fields.Char(string='Name', required=True,)
    code = fields.Char(string='Code', required=True,)
    floor_ids = fields.One2many('bm.floor', 'tower_id', string='Floor')
    company_id = fields.Many2one('res.company', string='Company',
    	default=lambda self: self.env.user.company_id)