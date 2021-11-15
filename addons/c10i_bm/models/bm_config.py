from odoo import models, fields, api

class BMConfig(models.TransientModel):
    _name = 'bm.config'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string="Company", required=True,
    	default=lambda self: self.env.user.company_id)
    service_charge_product_id = fields.Many2one(related='company_id.service_charge_product_id', string="Service Charge")
    sinking_fund_product_id = fields.Many2one(related='company_id.sinking_fund_product_id', string="Sinking Fund")
    tuition_schedule_date = fields.Integer(related='company_id.tuition_schedule_date', string="Schedule of Tuition Payment")

    electricity_cost_product_id = fields.Many2one(related='company_id.electricity_cost_product_id', string="Electricity Cost")
    water_cost_product_id = fields.Many2one(related='company_id.water_cost_product_id', string="Water Cost")