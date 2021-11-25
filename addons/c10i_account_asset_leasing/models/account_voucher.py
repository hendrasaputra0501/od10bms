# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountVoucher(models.Model):
	_inherit = 'account.voucher'

	# account_voucher_ids = fields.One2many('account.asset.installment.line', 'voucher_id', string='Direct Payments', ondelete="restrict")
	account_lease_voucher_ids = fields.One2many('account.asset.leasing', 'lease_voucher_id', string='Direct Payments', ondelete="restrict")
	asset_leasing_id = fields.Many2one('account.asset.leasing', string="Asset Leasing")

	@api.multi
	def button_cancel(self):
		pass

	@api.one
	@api.multi
	def action_installment_update_state(self):
		if self.asset_leasing_id:
			if 'not_paid' not in self.asset_leasing_id.account_asset_installment_line_ids.mapped('state') and self.asset_leasing_id.state == 'ongoing':
				self.asset_leasing_id.state='finished'

	@api.one
	@api.multi
	def action_dp_update_state(self):
		if self.account_lease_voucher_ids:
			self.account_lease_voucher_ids.is_down_payment_post = True
			if self.account_lease_voucher_ids.is_down_payment_post == True:
				current_search_installment_line = self.env['account.asset.installment.line'].search([('account_asset_installment_line_id','=',self.account_lease_voucher_ids.id)])
				# update first installment payment 
				current_search_installment_line.write({'is_installment_payment':True})

	@api.model
	def create(self, vals):
		journal = self.env['account.journal'].browse(vals['journal_id'])
		vals['account_id'] = journal.default_credit_account_id.id
		return super(AccountVoucher, self).create(vals)


	@api.multi
	def proforma_voucher(self):
		res = super(AccountVoucher, self).proforma_voucher()
		self.action_installment_update_state()
		self.action_dp_update_state()
		return res

class AccountVoucherLine(models.Model):
	_inherit = 'account.voucher.line'

	account_asset_installment_line_id = fields.Many2one("account.asset.installment.line", string="Asset Installment Line")