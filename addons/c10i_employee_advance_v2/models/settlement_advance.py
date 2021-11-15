import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_compare, float_is_zero
import odoo.addons.decimal_precision as dp

class AccountSettlementAdvance(models.Model):
	_inherit = 'account.settlement.advance'

	settlement_advance_line_ids = fields.One2many('settlement.advance.line', 'settlement_id', 'Detail Settlement', required=True, readonly=True, states={'draft': [('readonly', False)]})
	reference_notes = fields.Text("Reference Notes")

	@api.depends('settlement_line_ids', 'settlement_line_ids.residual', 'settlement_line_ids.amount')
	def amount_total(self):
		for data in self:
			settle_amount = 0.0
			return_amount = 0.0
			for line in data.settlement_line_ids:
				settle_amount += line.amount
				return_amount += line.residual - line.amount

			data.settlement_amount_total = settle_amount
			data.return_amount_total = return_amount

	@api.multi
	def settle(self):
		'''
		Confirm the advances given in ids and create the journal entries for each of them
		'''
		MoveLine = self.env['account.move.line']
		for settlement in self:
			local_context = dict(self._context, force_company=settlement.journal_id.company_id.id)
			#validation lines
			valid = False
			for line in settlement.settlement_line_ids:
				if line.amount:
					valid = True
			if not valid:
				raise UserError(_('There should be at least one Advance that need to be settled.'))
			if settlement.return_amount_total and settlement.return_account_id:
				total_detail_settlement = sum(settlement.settlement_advance_line_ids.mapped('amount'))
				if (total_detail_settlement+settlement.return_amount_total) != settlement.settlement_amount_total:
					raise UserError(_('Total amount detail settlement + return amount must same with settlement amount.'))
			else:
				total_detail_settlement = sum(settlement.settlement_advance_line_ids.mapped('amount'))
				if total_detail_settlement!=settlement.settlement_amount_total:
					raise UserError(_('Total amount detail settlement must same with settlement amount.'))


			if settlement.move_id:
				continue
			ctx = local_context.copy()
			ctx['date'] = settlement.date
			ctx['check_move_validity'] = False
			
			move = self.env['account.move'].create(settlement.account_move_get())
			seq = 5
			for line in settlement.settlement_line_ids:
				if not line.amount:
					line.unlink()
					continue
				# if line.residual!=line.amount:
				#     raise UserError(_('This settlemenet (%s) is not Valid. Residual Amount is %s while you \
				#         were about to settle for only %s. \nSettlement Amount must be same with \
				#         Residual Amount')%(str(line.move_line_id.move_id.name),str(line.residual), str(line.amount)))
				# if line.split_line_ids:
				#     for split_line in line.split_line_ids:
				#         move_line_vals = split_line.with_context(sequence=seq)._prepare_expense_split_move_line(line, move)
				#         MoveLine.with_context(ctx).create(move_line_vals)
				# else:
				#     move_line_vals = line.with_context(sequence=seq)._prepare_expense_move_line(move)
				#     MoveLine.with_context(ctx).create(move_line_vals)
				
				seq+=1
				# amount_line = line.amount
				amount_line = line.amount
				new_move_line = MoveLine.with_context(ctx).create(line.with_context(sequence=seq)._prepare_settlement_move_line(move, amount_line))
				(line.move_line_id + new_move_line).reconcile()
				seq+=1

			if settlement.return_amount_total and settlement.return_account_id:
				move_line_vals = settlement.with_context(sequence=seq)._prepare_return_move_line(move)
				MoveLine.with_context(ctx).create(move_line_vals)

			for detail in settlement.settlement_advance_line_ids:
					move_line_vals = detail.with_context(sequence=seq)._prepare_expense_settlement_move_line(detail,move)
					MoveLine.with_context(ctx).create(move_line_vals)
			settlement.write({
				'move_id': move.id,
				'state': 'posted',
			})
			move.post()
		return True

class AccountSettlementAdvanceLine(models.Model):
	_inherit = 'account.settlement.advance.line'
	_description = 'Detail Settlement Advance'

	pull_settle = fields.Boolean("Pull Settle")

class SettlementAdvanceLine(models.Model):
	_name = 'settlement.advance.line'
	_description = 'Split Settlement Advance'

	settlement_id = fields.Many2one('account.settlement.advance', 'Settlement Ref', required=True, ondelete='cascade')
	account_id = fields.Many2one('account.account', 'Account')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
	name = fields.Char('Description')
	amount = fields.Float('Settlement Amount', digits=dp.get_precision('Account'))

	def _prepare_expense_settlement_move_line(self, settlement_line, move):
		seq = self._context.get('sequence', 5)
		company_currency = move.journal_id.company_id.currency_id
		current_currency = company_currency
		debit = credit = 0.0
		amount = current_currency!=company_currency and \
			current_currency.with_context({'date': move.date}).compute(self.amount, company_currency) \
			or self.amount
		sign = 1
		if settlement_line.amount>0.0:
			if amount>0.0:
				debit = amount
			else:
				credit = abs(amount)
		else:
			sign = -1
			if amount>0.0:
				credit = amount
			else:
				debit = abs(amount)
		return {
			'sequence': seq,
			'move_id': move.id,
			'account_id': self.account_id.id,
			'analytic_account_id': self.analytic_account_id.id,
			'partner_id': self.settlement_id.employee_partner_id.id,
			'name': self.name,
			'journal_id': move.journal_id.id,
			'date': move.date,
			'debit': debit,
			'credit': credit,
			'amount_currency': current_currency!=company_currency and sign*self.amount or 0.0,
			'currency_id': current_currency!=company_currency and current_currency.id or False,
		}