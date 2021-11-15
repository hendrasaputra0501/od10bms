# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime


class AccountVoucher(models.Model):
	_inherit    = "account.voucher"
	_description = 'Accounting Voucher'

	@api.multi
	def create_report(self):
		report_name = 'report_voucher_cash_bank1'
		return {
				'type'          : 'ir.actions.report.xml',
				'report_name'   : report_name,
				'datas'         : {
					'model'         : 'account.voucher',
					'id'            : self._context.get('active_ids') and self._context.get('active_ids')[0] or self.id,
					'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or [],
					'name'          : (self.journal_report_type.capitalize() + " - " + self.number)or "---",
					},
				'nodestroy'     : False
		}

class AccountVoucherLine(models.Model):
	_inherit = 'account.voucher.line'

	account_account_location_ids        = fields.Many2many('account.account', string='Daftar Account')

	@api.onchange('account_location_type_id','account_location_id')
	def _onchange_account_location_id(self):
		if self.account_location_type_id.project and self.account_location_id:
			if self.account_location_type_id.project:
				project_data = self.env['mill.project'].search([('location_id', '=', self.account_location_id.id)])
				if project_data.categ_id.account_id:
					self.account_account_location_ids = [(6, 0, [project_data.categ_id.account_id.id])]
				else:
					self.account_account_location_ids = False
		if self.account_location_type_id:
			if self.account_location_type_id.account_ids:
				self.account_account_location_ids = self.account_location_type_id.account_ids.ids
			else:
				self.account_account_location_ids = self.env['account.account'].search([]).ids