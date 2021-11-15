from odoo import models, fields, api

class BMOwner(models.Model):
	_name = 'bm.owner'
	_description = 'Master owner'

	company_id = fields.Many2one('res.company', string='Company', 
		default=lambda self: self.env.user.company_id)
	unit_id = fields.Many2one('bm.unit', string='Unit', required=True,)
	partner_id = fields.Many2one('res.partner', string='Partner', required=True,)
	start_date = fields.Datetime(string='Start Date',)
	end_date = fields.Datetime(string='End Date',)
	state = fields.Selection([('valid', 'Valid'), ('not_valid', 'Not Valid')], string="State",
		default='valid')

	@api.multi
	def button_not_valid(self):
		self.write({'state': 'not_valid'})