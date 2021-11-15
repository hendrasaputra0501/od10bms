# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountVoucher(models.Model):
	_inherit = 'account.voucher'

	account_voucher_ids = fields.One2many('account.asset.installment.line', 'voucher_id', string='Direct Payments', ondelete="restrict")
	account_lease_voucher_ids = fields.One2many('account.asset.leasing', 'lease_voucher_id', string='Direct Payments', ondelete="restrict")

	@api.multi
	def button_cancel(self):
		pass

	@api.one
	@api.multi
	def action_installment_update_state(self):
		if self.account_voucher_ids:
			self.account_voucher_ids.state = 'post'
			if self.account_voucher_ids and self.account_voucher_ids.account_asset_installment_line_id and self.account_voucher_ids.account_asset_installment_line_id.id:
				account_asset_lease_search = self.account_voucher_ids.account_asset_installment_line_id
				self.get_closed(account_asset_lease_search)

			
	# terms to call get_finished function from model: account.voucher --->doing in model: account.asset.leasingset, to be state = 'finished'
	@api.multi
	def get_closed(self, account_asset_lease_search):
		domain = ['&',('account_asset_installment_line_id','=',account_asset_lease_search.id),('state','in',['not_pay','paid'])]
		# is not there intallment with state = not_pay
		current_installment = self.env['account.asset.installment.line'].search(domain, order='installment_date asc')
		# if all installments have post 
		if not current_installment:
			current_search_header = self.env['account.asset.leasing'].search([('id','=',account_asset_lease_search.id)])
			# update account.asset.leasing state = finished to show Closed Button.
			current_search_header.write({'state':'finished'})



	@api.one
	@api.multi
	def action_dp_update_state(self):
		if self.account_lease_voucher_ids:
			self.account_lease_voucher_ids.is_down_payment_post = True
			if self.account_lease_voucher_ids.is_down_payment_post == True:
				current_search_installment_line = self.env['account.asset.installment.line'].search([('account_asset_installment_line_id','=',self.account_lease_voucher_ids.id)])
				# update first installment payment 
				current_search_installment_line.write({'is_installment_payment':True})


	@api.multi
	def action_move_line_create(self):
		res = super(AccountVoucher, self).action_move_line_create()
		self.action_installment_update_state()
		self.action_dp_update_state()
		return res