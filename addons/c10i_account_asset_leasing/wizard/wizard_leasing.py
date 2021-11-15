# -*- coding: utf-8 -*-
import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression



class WizardLeasing(models.TransientModel):
	_name           = "wizard.leasing"
	_description    = "Leasing"


	@api.model
	def _default_journal(self):
		record_ids  = self._context.get('active_ids', False)
		active_model = str(self._context.get('active_model'))
		company_id = self._context.get('company_id', self.env.user.company_id.id)

		if active_model == 'account.asset.leasing':
			# domain = [('company_id', '=', company_id),]
			current_search_header = self.env['account.asset.leasing'].search([('id','in',record_ids)])
			domain = [('id', '=', current_search_header.invoice_id.journal_id.id)]
		else:
			current_search_line = self.env['account.asset.installment.line'].search([('id','in',record_ids)], limit=1)
			current_search_header = self.env['account.asset.leasing'].search([('id','=',current_search_line.account_asset_installment_line_id.id)])
			# domain = [('company_id', '=', company_id),('id','=', current_search_header.invoice_id.journal_id.id)]
			domain = [('id','=', current_search_header.invoice_id.journal_id.id)]
		
		return self.env['account.journal'].search(domain, limit=1)

	# @api.model
	def _default_partner(self):
		record_ids  = self._context.get('active_ids', False)
		active_model = str(self._context.get('active_model'))
		if active_model == 'account.asset.leasing':
			current_search_header = self.env['account.asset.leasing'].search([('id','in',record_ids)])
			domain = [('id', '=', current_search_header.partner_id.id)]
		else:
			current_search_line = self.env['account.asset.installment.line'].search([('id','in',record_ids)], limit=1)
			current_search_header = self.env['account.asset.leasing'].search([('id','=',current_search_line.account_asset_installment_line_id.id)])
			domain = [('id','=', current_search_header.partner_id.id)]
		
		return self.env['res.partner'].search(domain, limit=1)

	def _default_account(self):
		record_ids  = self._context.get('active_ids', False)
		active_model = str(self._context.get('active_model'))
		# company_id = self._context.get('company_id', self.env.user.company_id.id)
		if active_model == 'account.asset.leasing':
			current_search_header = self.env['account.asset.leasing'].search([('id','in',record_ids)])
			domain = [('id', '=', current_search_header.invoice_id.account_id.id)]

		if active_model == 'account.asset.installment.line':
			current_search_line = self.env['account.asset.installment.line'].search([('id','in',record_ids)], limit=1)
			current_search_header = self.env['account.asset.leasing'].search([('id','=',current_search_line.account_asset_installment_line_id.id)])
			domain = [('id','=', current_search_header.invoice_id.account_id.id)]
		
		return self.env['account.account'].search(domain, limit=1)


	
	account_id = fields.Many2one('account.account', string='Asset Account', default=_default_account)
	# journal_id = fields.Many2one('account.journal', string='Journal', ondelete='restrict')
	journal_id = fields.Many2one('account.journal', 'Journal', required=True, default=_default_journal)
	description = fields.Char(string='Description')
	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True, default=_default_partner)


	@api.model
	def default_get(self, fields):
		record_ids  = self._context.get('active_ids', False)
		active_model = str(self._context.get('active_model'))
		# call function related things to note
		self.validation_info(record_ids, active_model)
		result      = super(WizardLeasing, self).default_get(fields)
		return result

	@api.multi
	def validation_info(self, record_ids, active_model):
		# selection active model: account.asset.leasing or account.asset.installment.line  
		if active_model == 'account.asset.leasing':
			current_search_header = self.env['account.asset.leasing'].search([('id','in',record_ids)])
			if len(current_search_header.account_asset_installment_line_ids) <= 0:
				raise ValidationError('Warning, please click Compute Button to avoid Detail Installment Periode Data is empty.')

		if active_model == 'account.asset.installment.line':
			current_search_line = self.env['account.asset.installment.line'].search([('id','in',record_ids)])

			if current_search_line.account_asset_installment_line_id.state == 'draft':
				raise ValidationError('Warning, make sure running state before !.')

			if current_search_line.state == 'post':
				raise ValidationError('Warning, you can not post more than one!.')
			# check state: paid 
			domain = ['&',('account_asset_installment_line_id','=',current_search_line.account_asset_installment_line_id.id),('state','=','paid')]
			temp_outstanding = self.env['account.asset.installment.line'].search(domain, order='installment_date asc')
			if temp_outstanding:
				raise ValidationError('Warning, you have still outstanding, state: Paid, Not yet Post !.')

			# check state:not Pay
			domain = ['&',('account_asset_installment_line_id','=',current_search_line.account_asset_installment_line_id.id),('state','=','not_pay')]
			temp = self.env['account.asset.installment.line'].search(domain, order='installment_date asc')
			if temp:
				temp_date = temp.mapped('installment_date')
				validate_sequence_payment = [date for date in temp_date if current_search_line.installment_date > date]
				# For payment must sequence date
				if len(validate_sequence_payment) > 0:
					raise ValidationError('Attention, you should to pay in order time!. See there are still smaller date: ' + ' '.join(map(str,validate_sequence_payment)))
				
		# return True


	# update installment payment current
	@api.multi
	def set_update_installment_state(self):
		record_ids  = self._context.get('active_ids', False)
		current_search_line = self.env['account.asset.installment.line'].search([('id','in',record_ids)])
		# redirect to DP form because installment state is paid should be post state
		if current_search_line.state == 'paid':
			return {
					'name'          : ('Direct Payments'),
					'view_type'     : 'form',
					'view_mode'     : 'form',
					'res_model'     : 'account.voucher',
					'res_id'        : current_search_line.voucher_id.id,
					'type'          : 'ir.actions.act_window',
					}
			
		# update first installment payment current that state is paid 
		if current_search_line.state == 'not_pay':
			current_search_line.write({'state': 'paid'})
			# self.get_closed(current_search_line)

		# return self.env['account.asset.leasing'].search([('id','=',current_search_line.account_asset_installment_line_id.id)])
		return current_search_line

	# to know that down payment is current
	@api.multi
	def set_update_down_payment(self):
		record_ids  = self._context.get('active_ids', False)
		current_search_header = self.env['account.asset.leasing'].search([('id','in',record_ids)])
		current_search_header.is_down_payment = True


		return current_search_header


	# create payment what if down payment or installment payment
	@api.multi
	def create_payment(self):
		# record_ids  = self._context.get('active_ids')
		active_model = str(self._context.get('active_model'))
		data = self.read()[0]
		# surely to know active model
		if active_model == 'account.asset.leasing':
			temp = self.set_update_down_payment()
		else:
			# active_model == 'account.asset.installment.line':
			temp = self.set_update_installment_state()

		account_voucher_obj = self.env['account.voucher']
		account_voucher_obj_line = self.env['account.voucher.line']
		if self:
			values = {
				'voucher_type': 'purchase',
				'partner_id': data.get('partner_id')[0] if data.get('partner_id') else False,
				'pay_now':'pay_now',
				'journal_id': data.get('journal_id')[0] if data.get('journal_id') else False,
				'date': fields.Date.today(),
				'account_date': fields.Date.today(),
				'name':temp.number if active_model == 'account.asset.leasing' else temp.name,
				# 'account_id': data.get('account_id')[0] if data.get('account_id') else False,
				'account_id': self.journal_id.default_credit_account_id.id or False,
				# 'account_id': self.journal_id.default_debit_account_id if self.voucher_type == 'sale' else self.journal_id.default_credit_account_id
				'check_number': False,
				'check_date': False
			}
			new_account_voucher = account_voucher_obj.sudo().create(values)

			if new_account_voucher:
				values_lines = {
					'name': data.get('description') if data.get('description') else '',
					'account_id': data.get('account_id')[0] if data.get('account_id') else False,
					'account_analytic_id': False,
					'quantity': 1,
					'price_unit': temp.deposite_value if active_model == 'account.asset.leasing' else temp.installment_amount,
					'tax_ids': False,
					'price_subtotal': 1 * temp.deposite_value if active_model == 'account.asset.leasing' else temp.installment_amount,
					'currency_id': temp.currency_id and temp.currency_id.id or False,
					'company_id': self.env.user.company_id and self.env.user.company_id.id or False,
					'voucher_id': new_account_voucher.id 
				}
				account_voucher_obj_line.sudo().create(values_lines)
				# update field lease_voucher_id in model: account.asset.installment for reference with account.voucher model
				if active_model == 'account.asset.leasing':
					# temp.write({'lease_voucher_id': new_account_voucher.id})
					temp.lease_voucher_id = new_account_voucher.id
				# update field voucher_id in model: account.asset.installment.line for reference with account.voucher model
				else: 
					# active_model == 'account.asset.installment.line':
					temp.write({'voucher_id': new_account_voucher.id})
			
			if new_account_voucher:
				return {
					'name'          : ('Direct Payments'),
					'view_type'     : 'form',
					'view_mode'     : 'form',
					'res_model'     : 'account.voucher',
					'res_id'        : new_account_voucher.id,
					'type'          : 'ir.actions.act_window',
				}

		return {}