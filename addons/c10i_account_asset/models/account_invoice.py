# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	def action_move_create(self):
		res = super(AccountInvoice, self).action_move_create()
		for inv in self:
			# FOR ASSET CREATION
			context = dict(self.env.context)
			# Within the context of an invoice,
			# this default value is for the type of the invoice, not the type of the asset.
			# This has to be cleaned from the context before creating the asset,
			# otherwise it tries to create the asset with the type of the invoice.
			context.pop('default_type', None)
			inv.invoice_line_ids.with_context(context).asset_create()

			# FOR CAPITALIZE
			for line in self.invoice_line_ids:
				if line.asset_id:
					asset_data = self.env['account.asset.asset'].search([('id','=',line.asset_id.id)])
					# asset_data.capitalize_value += line.price_subtotal
					capitalize_value = line.price_subtotal
					asset_data.with_context(ref=inv.name).update_asset_value(capitalize_value, inv.date_invoice)

		# FOR DISPOSAL
		AccountAsset = self.env['account.asset.asset']
		AccountAssetDeprLine = self.env['account.asset.depreciation.line']
		sold_assets = AccountAsset.search([('disposal_invoice_id','in',self.ids)])
		for asset in sold_assets:
			depr_line = asset.depreciation_line_ids.filtered(lambda x:x.disposal_method=='asset_sale')
			if depr_line:
				depr_line[0].write({'move_id': asset.disposal_invoice_id.move_id.id})
		
		return res

	@api.multi
	def action_cancel(self):
		res = super(AccountInvoice, self).action_cancel()
		for inv in self:
			for line in inv.invoice_line_ids:
				if line.asset_id:
					asset_data = self.env['account.asset.asset'].search([('id','=',line.asset_id.id)])
					# asset_data.capitalize_value += line.price_subtotal
					capitalize_value = line.price_subtotal
					asset_data.update_asset_value(-capitalize_value, inv.date_invoice)
		return res

class AccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"
	_description = "Invoice Line"

	asset_action_type = fields.Selection([('create', 'Create Asset'), ('capitalize', 'Capitalize Asset')], string='Action Asset Type', help='Information regarding how Asset Information was proceed if you input between Asset or Asset Category')
	asset_id = fields.Many2one('account.asset.asset', string='Add to Asset')