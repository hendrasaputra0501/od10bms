# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils
from collections import defaultdict


class StockMoveInsertAccount(models.Model):
	_inherit = "stock.move"


	# @api.multi
	# def _get_accounting_data_for_valuation(self):
	# 	""" Return the accounts and journal to use to post Journal Entries for
	# 	the real-time valuation of the quant. """
	# 	self.ensure_one()
	# 	accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
		
	# 	if self.location_id.valuation_out_account_id:
	# 		acc_src = self.location_id.valuation_out_account_id.id
	# 	else:
	# 		acc_src = accounts_data['stock_input'].id
		
	# 	if self.location_dest_id.valuation_in_account_id:
	# 		acc_dest = self.location_dest_id.valuation_in_account_id.id
	# 	else:
	# 		acc_dest = accounts_data['stock_output'].id
		
	# 	# attention: The below statement comment is default odoo. 
	# 	# acc_valuation = accounts_data.get('stock_valuation', False)

	# 	# Notes: The below expression logic for change account product default to be an account product in inventory adjustment 
	# 	# search stock_valuation_line
	# 	inventory_id, product_id= self.inventory_id.id , self.product_id.id
	# 	stock_inventory_line = self.env['stock.inventory.line'].search(['&',('inventory_id','=',inventory_id),('product_id','=',product_id)],limit=1)
	# 	acc_valuation_substitution = stock_inventory_line.account_id

	# 	if acc_valuation_substitution:
	# 		acc_valuation = acc_valuation_substitution
	# 	else:
	# 		acc_valuation = accounts_data.get('stock_valuation', False)
		
	# 	if acc_valuation:
	# 		acc_valuation = acc_valuation.id
	# 	if not accounts_data.get('stock_journal', False):
	# 		raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
	# 	if not acc_src:
	# 		raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
	# 	if not acc_dest:
	# 		raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
	# 	if not acc_valuation:
	# 		raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
	# 	journal_id = accounts_data['stock_journal'].id
	# 	return journal_id, acc_src, acc_dest, acc_valuation
