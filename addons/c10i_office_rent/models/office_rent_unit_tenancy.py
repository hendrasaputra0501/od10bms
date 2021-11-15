from odoo import models, fields, api

class OfficeRentUnitTenancy(models.Model):
    _name = 'office.rent.unit.tenancy'
    _inherit = 'bm.unit.tenancy'
    _description = 'Master data office rent tenancy'

    unit_id = fields.Many2one('office.rent.unit', string="Unit")
    rent_order_ids = fields.Many2many('office.rent.order', 'relasi_tenancy_order', 'tenancy_id', 'order_id', string='Rent Order')