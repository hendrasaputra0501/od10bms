# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"
	_description = "Invoice Line"
	_order = "invoice_id,sequence,id"

	def _set_additional_fields(self, invoice):
		default_loc_type = self.env['account.location.type'].search([('name','=','-')])
		for line in self:
			line.update({
				'account_location_type_id': default_loc_type and default_loc_type[0].id or False,
				}) 