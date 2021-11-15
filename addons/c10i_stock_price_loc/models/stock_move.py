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
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

from datetime import datetime
import time
from collections import defaultdict

import logging

class StockMove(models.Model):
    _inherit = 'stock.move'

    def get_price_unit(self):
        price_unit = super(StockMove, self).get_price_unit()
        
        average_cost_type = self.product_id.average_cost_type or self.product_id.categ_id.average_cost_type
        if average_cost_type=='by_location' and self.location_id.usage=='internal' and self.location_dest_id.usage!='internal':
            return self.with_context(location_id=self.location_id.id).get_price_unit_per_location()
        else:
            return price_unit

    def get_price_unit_per_location(self):
        location_id = False
        if self.env.context.get('location_id'):
            check_usage = self.env['stock.location'].search([('usage','=','internal'),('id','=',self.env.context['location_id'])])
            if not check_usage:
                raise UserError(_('You cannot search for product price at non-Physical Location'))
            location_id = self.env.context['location_id']
        elif self.location_dest_id.usage=='internal':
            location_id = self.location_dest_id
        if not location_id:
            raise UserError(_('Please input spesific Physical Location'))
        price_data = self.env['product.location.price'].search([('product_id','=',self.product_id.id),('location_id','=',location_id)])
        return price_data and price_data.standard_price or 0.0

    @api.multi
    def product_price_update_before_done(self):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        std_price_location_update = {}
        for move in self.filtered(lambda move: move.location_id.usage in ('supplier', 'production', 'transit') and move.product_id.cost_method == 'average'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            product_tot_qty_available2 = move.product_id.with_context(location=move.location_dest_id.id).qty_available + tmpl_dict[move.product_id.id]
            print ">>>>>>>>>>>>>>>>>>>>>>>>>", product_tot_qty_available2
            
            # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
            if product_tot_qty_available <= 0:
                new_std_price = move.get_price_unit()
            else:
                # Get the standard price
                amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                new_std_price = ((amount_unit * product_tot_qty_available) + (move.get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)

            tmpl_dict[move.product_id.id] += move.product_qty
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

            price_data = False
            average_cost_type = move.product_id.average_cost_type or move.product_id.categ_id.average_cost_type
            if average_cost_type=='by_location':
                if (move.location_dest_id.id, move.product_id.id) not in std_price_location_update.keys():
                    price_data = self.env['product.location.price'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id)])
                    if not price_data:
                        price_data = self.env['product.location.price'].create({'location_id': move.location_dest_id.id, 'product_id': move.product_id.id, 'standard_price': 0.0})
                    std_price_location_update.update({(move.location_dest_id.id, move.product_id.id): price_data})
                else:
                    price_data = std_price_location_update[(move.location_dest_id.id, move.product_id.id)]

                # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                print ">>>>>>>>>>>>>>>", price_data
                if product_tot_qty_available2 <= 0:
                    new_std_price2 = move.get_price_unit()
                    print ">>>>>>>>>>>>>>>ambil dari get price", new_std_price2
                else:
                    # Get the standard price
                    amount_unit2 = price_data.standard_price
                    print ">>>>>>>>>>>>>>>ambil dari price data", amount_unit2, move.get_price_unit()
                    new_std_price2 = ((amount_unit2 * product_tot_qty_available2) + (move.get_price_unit() * move.product_qty)) / (product_tot_qty_available2 + move.product_qty)

                price_data.sudo().write({'standard_price': new_std_price2})

    def _store_average_cost_price(self):
        """ Store the average price of the move on the move and product form (costing method 'real')"""
        super(StockMove, self)._store_average_cost_price()
        for move in self.filtered(lambda move: move.product_id.cost_method != 'real' and not move.origin_returned_move_id):
            # jika productnya pake average cost type by location, maka price unit ngambil dari standard price di price location
            average_cost_type = move.product_id.average_cost_type or move.product_id.categ_id.average_cost_type
            if average_cost_type=='by_location' and move.location_id.usage=='internal':
                price_data = self.env['product.location.price'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)])
                move.write({'price_unit': price_data.standard_price})

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id)
        
        average_cost_type = self.product_id.average_cost_type or self.product_id.categ_id.average_cost_type
        # dijalankan jika dan hanya jika pengeluaran barang
        # print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> JALAN NDAK?", asd
        if res and self.product_id.cost_method == 'average' and average_cost_type=='by_location':
            location_to_check = self.location_id if self.location_id.usage=='internal' else self.location_dest_id
            if location_to_check.usage!='internal':
                return res
            if self._context.get('force_valuation_amount'):
                valuation_amount = self._context.get('force_valuation_amount')
                valuation_correction_amt = self._context.get('force_valuation_amount')
            else:
                if self.product_id.cost_method == 'average':
                    valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
                    valuation_correction_amt = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.with_context(location_id=location_to_check.id).get_price_unit_per_location()
                else:
                    valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
                    valuation_correction_amt = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
            # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
            # the company currency... so we need to use round() before creating the accounting entries.
            debit_value = self.company_id.currency_id.round(valuation_amount * qty)
            debit_correction_amt = self.company_id.currency_id.round(valuation_correction_amt * qty)

            # check that all data is correct
            if self.company_id.currency_id.is_zero(debit_value):
                if self.product_id.cost_method == 'standard':
                    raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
                return []
            credit_value = debit_value
            credit_correction_amt = debit_correction_amt

            if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
                # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
                # account books the real purchase price, while the stock account books the average price. The difference is
                # booked in the dedicated price difference account.
                if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                    debit_value = self.origin_returned_move_id.price_unit * qty
                    debit_correction_amt = self.origin_returned_move_id.price_unit * qty
                # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
                # is made using the original average price to negate the delivery effect.
                if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                    debit_value = self.origin_returned_move_id.price_unit * qty
                    debit_correction_amt = self.origin_returned_move_id.price_unit * qty
                    credit_value = debit_value
                    credit_correction_amt = debit_correction_amt

                if self.location_id.usage == 'procurement' and self.origin_returned_move_id:
                    credit_correction_amt = self.origin_returned_move_id.price_unit * qty
                    
            if len(res) > 2:
                debit_line_vals = res[0][2]
                credit_line_vals = res[1][2]
                diff_line_vals = res[2][2]

                if debit_value!=debit_correction_amt:
                    debit_line_vals.update({
                        'debit': debit_correction_amt if debit_correction_amt > 0 else 0,
                        'credit': -debit_correction_amt if debit_correction_amt < 0 else 0,
                    })

                if credit_value!=credit_correction_amt:
                    credit_line_vals.update({
                        'credit': credit_correction_amt if credit_correction_amt > 0 else 0,
                        'debit': -credit_correction_amt if credit_correction_amt < 0 else 0,
                    })

                diff_amount = debit_value - credit_value
                diff_correction_amount = debit_correction_amt - credit_correction_amt
                if diff_correction_amount!=diff_amount:
                    if diff_correction_amount:
                        diff_line_vals.update({
                            'credit': diff_correction_amount if diff_correction_amount > 0 else 0,
                            'debit': -diff_correction_amount if diff_correction_amount < 0 else 0,
                        })
                        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
                    else:
                        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals), (0, 0, diff_line_vals)]
                
                return [(0, 0, debit_line_vals), (0, 0, credit_line_vals), (0, 0, diff_line_vals)]
            else:
                debit_line_vals = res[0][2]
                credit_line_vals = res[1][2]

                if debit_value!=debit_correction_amt:
                    debit_line_vals.update({
                        'debit': debit_correction_amt if debit_correction_amt > 0 else 0,
                        'credit': -debit_correction_amt if debit_correction_amt < 0 else 0,
                    })

                if credit_value!=credit_correction_amt:
                    credit_line_vals.update({
                        'credit': credit_correction_amt if credit_correction_amt > 0 else 0,
                        'debit': -credit_correction_amt if credit_correction_amt < 0 else 0,
                    })

                diff_amount = debit_value - credit_value
                diff_correction_amount = debit_correction_amt - credit_correction_amt
                if diff_correction_amount!=diff_amount:
                    if diff_correction_amount:
                        price_diff_account = self.product_id.property_account_creditor_price_difference
                        if not price_diff_account:
                            price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
                        if not price_diff_account:
                            raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
                        price_diff_line = {
                            'name': self.name,
                            'product_id': self.product_id.id,
                            'quantity': qty,
                            'product_uom_id': self.product_id.uom_id.id,
                            'ref': self.picking_id.name,
                            'partner_id': self.picking_id.partner_id.id,
                            'credit': diff_correction_amount > 0 and diff_correction_amount or 0,
                            'debit': diff_correction_amount < 0 and -diff_correction_amount or 0,
                            'account_id': price_diff_account.id,
                        }
                        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals), (0, 0, price_diff_line)]
                    else:
                        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

                return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        return res

    def _prepare_value_move_line(self, qty, cost, location_from, location_to):
        self.ensure_one()
        res = super(StockMove, self)._prepare_value_move_line(qty, cost, location_from, location_to)
        average_cost_type = self.product_id.average_cost_type or self.product_id.categ_id.average_cost_type
        if res and self.product_id.cost_method == 'average' and average_cost_type=='by_location':
            location_to_check = location_from if location_from.usage=='internal' else (location_to if location_to.usage=='internal' else False)
            if not location_to_check:
                return res
            if self._context.get('force_valuation_amount'):
                valuation_amount = self._context.get('force_valuation_amount')
            else:
                if self.product_id.cost_method == 'average':
                    valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.with_context(location_id=location_to_check.id).get_price_unit_per_location()
                else:
                    valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
            # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
            # the company currency... so we need to use round() before creating the accounting entries.
            stock_value = self.company_id.currency_id.round(valuation_amount * qty)

            # check that all data is correct
            if self.company_id.currency_id.is_zero(stock_value):
                if self.product_id.cost_method == 'standard':
                    raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
                return {}

            if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
                # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
                # account books the real purchase price, while the stock account books the average price. The difference is
                # booked in the dedicated price difference account.
                if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                    stock_value = self.origin_returned_move_id.price_unit * qty
                # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
                # is made using the original average price to negate the delivery effect.
                if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                    stock_value = self.origin_returned_move_id.price_unit * qty
            res.update({'amount': stock_value})
        return res
