from odoo import models, fields, api

class BMFloor(models.Model):
    _name = 'bm.floor'
    _description = 'Master data floor'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    tower_id = fields.Many2one('bm.tower', string='Tower')
    company_id = fields.Many2one('res.company', string='Company',
    	default=lambda self: self.env.user.company_id)