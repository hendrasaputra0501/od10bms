from odoo import models, fields, api

class OfficeRentUnit(models.Model):
	_name = 'office.rent.unit'
	_inherit = 'bm.unit'
	_description = 'Office rent unit'

	block = fields.Char(string="Block")
	rent_ok = fields.Boolean(string="For Rent", default=True)
	product_id = fields.Many2one('product.product', string='Product')
	tenant_ids = fields.One2many('office.rent.unit.tenancy', 'unit_id', string="Tenant")

	@api.model
	def create(self, vals):
		prd = self.env['product.template'].create({'name': vals['name'],})
		vals['product_id']=prd.id
		print '=================', prd.id
		record = super(OfficeRentUnit, self).create(vals)
		return record