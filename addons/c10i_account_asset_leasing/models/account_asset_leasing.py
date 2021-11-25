# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, exceptions
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

import odoo.addons.decimal_precision as dp


class AccountAssetLeasing(models.Model):
	_name = 'account.asset.leasing'
	_description = "Account Asset Leasing"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = 'ongoing_date desc, id desc'


	number = fields.Char(
		string='',
		default='New',
		readonly=True,
	)
	# name = fields.Char(string='Lease Name')
	name = fields.Many2one('account.asset.asset',string='Asset')
	invoice_id = fields.Many2one('account.invoice', 'Bill')
	
	gross_value= fields.Float(string='Gross/Purchase Value', compute='', store=True, digits=dp.get_precision('Account'))
	deposite_value= fields.Float(string='Deposite Value/Uang Muka', compute='', store=True, digits=dp.get_precision('Account'))
	installment_period_numb = fields.Integer(string='Installment Periode Number/Jumlah Cicilan')
	state = fields.Selection(selection=[('draft', 'Draft'),
										('ongoing', 'Running'),
										('finished', 'Installment Finished'),
										('closed', 'Closed'),],
							 string='State', readonly=True, default='draft',
							 track_visibility='onchange')
	ongoing_date = fields.Date(string='Ongoing Date', default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
	account_asset_installment_line_ids = fields.One2many(comodel_name='account.asset.installment.line', inverse_name='asset_leasing_id', string='Account Asset Installment Lines', ondelete='cascade')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]},default=lambda self: self.env.user.company_id.currency_id.id)

	partner_id = fields.Many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft': [('readonly', False)]})
	is_down_payment = fields.Boolean(string="Is DP?", default=False)
	is_down_payment_post = fields.Boolean(string="is DP Posted?", default=False) 
	
	# entry_count = fields.Integer(compute='_entry_count', string='# Direct Payments')
	lease_voucher_id = fields.Many2one('account.voucher', string='Down Payments')
	voucher_ids = fields.One2many("account.voucher", 'asset_leasing_id')
	voucher_count = fields.Integer(string="Payment(s)", compute="_compute_voucher")

	@api.depends("voucher_ids")
	def _compute_voucher(self):
		for leasing in self:
			leasing.voucher_count = len(leasing.voucher_ids)

	@api.onchange('name')
	def get_gross(self):
		if self.name:
			self.gross_value = self.name.value
			self.invoice_id = self.name.invoice_id

	@api.onchange('invoice_id')
	def get_partner(self):
		if self.invoice_id:
			self.partner_id = self.invoice_id.partner_id and self.invoice_id.partner_id.id or False
	
	@api.multi
	def action_view_payments(self):
		return {
			'name': _('Payments'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.voucher',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', [x.id for x in self.voucher_ids])],
		}


	@api.multi
	def action_create_payment(self):
		if self.deposite_value>0:
			location_type=self.env['account.location.type'].search([('code', '=', 'NA')])
			res = {
				'name': _('Payments'),
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.voucher',
				'view_id': False,
				'type': 'ir.actions.act_window',
				'context': {
					'default_payment_type': 'purchase',
					'default_partner_id': self.partner_id.id,
					'default_asset_leasing_id': self.id,
					# 'default_account_id'	: self.invoice_id.account_id.id,
					'default_pay_now'	: 'pay_now',
					'default_line_ids': [{
							'name'			: 'DP Asset: %s'%(self.name.name),
							'account_id'	: self.invoice_id.account_id.id,
							'account_location_type_id' : location_type.id,
							'account_location_id': False,
							'account_location_type_no_location': location_type.no_location,
							'quantity'	: 1,
							'price_unit': self.deposite_value,
						}]
					},
				}
		return res

	@api.multi
	def get_leasing_number(self):
		self.number = self.env['ir.sequence'].next_by_code('account.asset.leasing') or 'New'

	@api.multi
	def action_ongoing(self):
		self.get_leasing_number()
		self.compute_installment()
		return self.write({'state':'ongoing'})

	@api.multi
	def action_close(self):
		if 'draft' in self.voucher_ids.mapped('state'):
			raise UserError('Not All Payments in Posted Status, Post it First!')
		ids = []
		# get id which is account.asset.leasing related to account.move model
		payments = self.voucher_ids.mapped('move_id').ids
		for rec in self:
			# get id which is account.invoice related to account.move model.
			# get id which is account.asset.installment.line related to account.move model.
			bill = [rec.invoice_id.move_id.id]
			ids.extend(payments + bill)
			move_lines = self.env['account.move.line'].search(['&',('move_id', 'in', ids),('account_id','=',rec.invoice_id.account_id.id)])
			# reconcile
			self.trans_rec_reconcile_full(move_lines)

		return self.write({'state':'closed'})


	@api.multi
	def trans_rec_reconcile_full(self, move_lines):
		currency = False
		for aml in move_lines:
			if not currency and aml.currency_id.id:
				currency = aml.currency_id.id
			elif aml.currency_id:
				if aml.currency_id.id == currency:
					continue
				raise UserError(_('Operation not allowed. You can only reconcile entries that share the same secondary currency or that don\'t have one. Edit your journal items or make another selection before proceeding any further.'))
		#Don't consider entrires that are already reconciled
		move_lines_filtered = move_lines.filtered(lambda aml: not aml.reconciled)
		#Because we are making a full reconcilition in batch, we need to consider use cases as defined in the test test_manual_reconcile_wizard_opw678153
		#So we force the reconciliation in company currency only at first
		move_lines_filtered.with_context(skip_full_reconcile_check='amount_currency_excluded', manual_full_reconcile_currency=currency).reconcile()

		#then in second pass the amounts in secondary currency, only if some lines are still not fully reconciled
		move_lines_filtered = move_lines.filtered(lambda aml: not aml.reconciled)
		if move_lines_filtered:
			move_lines_filtered.with_context(skip_full_reconcile_check='amount_currency_only', manual_full_reconcile_currency=currency).reconcile()
		move_lines.compute_full_after_batch_reconcile()
		# return {'type': 'ir.actions.act_window_close'}


	# @api.multi
	# def get_finished(self):
	# 	return self.write({'state':'finished'})

	@api.multi 
	def get_dp_post(self):
		if self:
				return {
					'name'          : ('Direct Payments'),
					'view_type'     : 'form',
					'view_mode'     : 'form',
					'res_model'     : 'account.voucher',
					'res_id'        : self.lease_voucher_id.id,
					'type'          : 'ir.actions.act_window',
				}
		return {}

	@api.multi
	def unlink(self):
		for leasing in self:
			if leasing.state not in ('draft'):
				raise exceptions.ValidationError('You cannot delete an Leasing which is Ongoing or Closed state.')
		return super(AccountAssetLeasing, self).unlink()

	
	@api.multi
	def compute_installment_amount(self, gross_value, deposite_value, installment_period_numb):
		temp_installment_amount = gross_value - deposite_value
		temp_installment_numb = temp_installment_amount/ installment_period_numb
		return temp_installment_numb


	@api.multi
	def warning_leasing(self):
		# pass
		if self.gross_value <= 0 or self.deposite_value <= 0 or self.installment_period_numb <= 0:
			raise exceptions.ValidationError('Warning, surely not zero or minus value for Gross Value or Deposite Value or Installment Periode Number !')

		if self.gross_value < self.deposite_value:
			raise exceptions.ValidationError('Warning, Purchase Value '+str(self.gross_value) +' must greater than Deposite Value ' +str(self.deposite_value))

		return True

	# show detail installment
	@api.multi
	def compute_installment(self):
		self.warning_leasing()
		installment_amount = self.compute_installment_amount(self.gross_value, self.deposite_value, self.installment_period_numb)
		if self.gross_value > 0 and self.deposite_value > 0 and self.installment_period_numb > 0:
			count = 0
			dt = fields.Datetime.from_string(self.ongoing_date)
			# dt = date_start_dt + relativedelta(months=+1)
			ongoing_date = datetime(dt.year, dt.month, 1)
			# dt = (datetime.strptime(str(self.ongoing_date),'%Y-%m-%d').date() + relativedelta(months=1)).strftime('%Y-%m-%d')
			if len([rec.id for rec in self.account_asset_installment_line_ids]) == 0: 
				for line in range(0,self.installment_period_numb):
					count += 1
					# dt = (datetime.strptime(str(self.ongoing_date),'%Y-%m-%d').date() + relativedelta(months=+count)).strftime('%Y-%m-%d')
					counter_date = (ongoing_date + relativedelta(months=+count)).strftime('%Y-%m-%d')
					vals = {'asset_leasing_id': self.id,'installment_amount':  installment_amount, 'name': self.name, 'installment_date':counter_date}
					temp = self.env['account.asset.installment.line'].create(vals)
			else:
				raise exceptions.ValidationError('Warning, please click Correction Button to make sure the data is empty !')

	# correction
	@api.multi
	def reset_leasing(self, vals):
		self.state = 'draft'
		self.env.cr.execute("""DELETE FROM account_asset_installment_line WHERE asset_leasing_id = '%s'""", (int(self.id),))
		self.env.cr.commit()

	# call ir.cron
	@api.multi
	def _cron_leasing(self):
		# find record account.asset.leasing with state == finished
		leasing = self.env['account.asset.leasing'].search([('state','in',['finished'])])
		for rec in leasing:
			ids = []
			# get id which is account.asset.leasing related to account.move model
			# get id which is account.invoice related to account.move model.
			# get id which is account.asset.installment.line related to account.move model.
			dp, bill, installment = [rec.lease_voucher_id.move_id.id], [rec.invoice_id.move_id.id], [line.voucher_id.move_id.id for line in rec.account_asset_installment_line_ids]
			ids.extend(dp + bill + installment)
			move_lines = self.env['account.move.line'].search(['&',('move_id', 'in', ids),('account_id','=',rec.invoice_id.account_id.id)])
			# reconcile
			rec.trans_rec_reconcile_full(move_lines)
			# change state from finished to closed state
			rec.write({'state':'closed'})

		return True

