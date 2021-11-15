from odoo import models, fields, api

class Company(models.Model):
    _inherit = 'res.company'

    service_charge_product_id = fields.Many2one('product.product', string="Service charge")
    sinking_fund_product_id = fields.Many2one('product.product', string="Singking fund")
    tuition_schedule_date = fields.Integer(string="Date of Tuition Payment", default=1)

    electricity_cost_product_id = fields.Many2one('product.product', stirng="Electricity cost")
    water_cost_product_id = fields.Many2one('product.product', string="Water cost")