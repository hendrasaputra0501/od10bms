# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia <www.konsaltenindonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import float_is_zero
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

from datetime import datetime
import time

import logging

class ProductLocationPrice(models.Model):
	_name = 'product.location.price'

	location_id = fields.Many2one('stock.location',string='Location')
	product_id = fields.Many2one('product.product',string='Product')
	standard_price = fields.Float('Cost Price')

class ProductCategory(models.Model):
    _inherit = 'product.category'

    average_cost_type = fields.Selection([('by_company','By Company'),('by_location','By Stock Location')], default='by_company', string='Average Cost Store By')

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    average_cost_type = fields.Selection([('by_company','By Company'),('by_location','By Stock Location')], string='Average Cost Store By')

    @api.multi
    def do_change_standard_price(self, new_price, account_id):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        AccountMove = self.env['account.move']

        quant_locs = self.env['stock.quant'].sudo().read_group([('product_id', 'in', self.ids)], ['location_id'], ['location_id'])
        quant_loc_ids = [loc['location_id'][0] for loc in quant_locs]
        locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.env.user.company_id.id), ('id', 'in', quant_loc_ids)])

        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}

        average_cost_type = self.average_cost_type or self.categ_id.average_cost_type
        cost_method = self.cost_method or self.categ_id.cost_method
        if cost_method=='average' and average_cost_type=='by_location' and not self.env.context.get('location_id'):
        	return False

        if average_cost_type=='by_location':
        	locations = self.env['stock.location'].browse([self.env.context.get('location_id')])

        for location in locations:
            for product in self.with_context(location=location.id, compute_child=False).filtered(lambda r: r.valuation == 'real_time'):
            	price_data = False
            	if cost_method=='average' and average_cost_type=='by_location':
            		price_data = self.env['product.location.price'].search([('product_id','=',product.id),('location_id','=',location.id)])
                	diff = price_data.standard_price - new_price
            	else:
                	diff = product.standard_price - new_price

                if float_is_zero(diff, precision_rounding=product.currency_id.rounding):
                    # raise UserError(_("No difference between standard price and new price!"))
                    continue
                if not product_accounts[product.id].get('stock_valuation', False):
                    raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
                qty_available = product.qty_available
                if qty_available:
                    # Accounting Entries
                    if diff * qty_available > 0:
                        debit_account_id = account_id
                        credit_account_id = product_accounts[product.id]['stock_valuation'].id
                        if cost_method=='average' and average_cost_type=='by_location':
                            self.env['stock.move.value'].create({
                                    'move_id': False,
                                    'name': 'Standard Price changed',
                                    'product_id': product.id,
                                    'product_qty': 0.0,
                                    'product_uom_id': product.uom_id.id,
                                    'amount': abs(diff * qty_available),
                                    'location_id': location.id,
                                    'location_dest_id': product.property_stock_inventory.id,
                                    'date': self.env.context.get('force_date', datetime.now()),
                                    'company_id': product.company_id.id,
                                })
                    else:
                        debit_account_id = product_accounts[product.id]['stock_valuation'].id
                        credit_account_id = account_id
                        if cost_method=='average' and average_cost_type=='by_location':
                            self.env['stock.move.value'].create({
                                    'move_id': False,
                                    'name': 'Standard Price changed',
                                    'product_id': product.id,
                                    'product_qty': 0.0,
                                    'product_uom_id': product.uom_id.id,
                                    'amount': abs(diff * qty_available),
                                    'location__id': product.property_stock_inventory.id,
                                    'location_dest_id': location.id,
                                    'date': self.env.context.get('force_date', datetime.now()),
                                    'company_id': product.company_id.id,
                                })

                    move_vals = {
                        'journal_id': product_accounts[product.id]['stock_journal'].id,
                        'company_id': location.company_id.id,
                        'line_ids': 
                        [(0, 0, {
                            'name': _('Standard Price changed'),
                            'account_id': debit_account_id,
                            'debit': abs(diff * qty_available),
                            'credit': 0,
                            'product_id': self.id,
                        }), (0, 0, {
                            'name': _('Standard Price changed'),
                            'account_id': credit_account_id,
                            'debit': 0,
                            'credit': abs(diff * qty_available),
                            'product_id': self.id,
                        })],
                    }
                    move = AccountMove.create(move_vals)
                    move.post()

                if cost_method=='average' and average_cost_type=='by_location' and price_data:
                	price_data.write({'standard_price': new_price})
        self.write({'standard_price': new_price})
        return True