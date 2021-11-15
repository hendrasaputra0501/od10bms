# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
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

class StockMoveValue(models.Model):
    _name = 'stock.move.value'

    move_id = fields.Many2one('stock.move', 'Move Reference')
    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure')
    product_qty = fields.Float('Quantity')
    amount = fields.Float('Value')
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')
    date = fields.Datetime('Date')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_value_move_line(self, qty, cost, location_from, location_to):
        self.ensure_one()
        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            if self.product_id.cost_method == 'average':
                valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
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
        res = {
            'move_id': self.id,
            'name': 'Stock Move %s'%str(self.id),
            'product_id': self.product_id.id,
            'product_qty': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'amount': stock_value,
            'location_id': location_from.id,
            'location_dest_id': location_to.id,
            'date': self.picking_id and self.picking_id.date_done or self.date,
            'company_id': self.company_id.id,
        }
        return res

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _create_value_move_line(self, move, location_from, location_to):
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        StockValueMove = self.env['stock.move.value']
        for cost, qty in quant_cost_qty.iteritems():
            value_move_vals = move._prepare_value_move_line(qty, cost, location_from, location_to)
            if value_move_vals:
                new_move = StockValueMove.create(value_move_vals)

    def _stock_value_move_enty(self, move):
        if move.product_id.type != 'product':
            return False
        if any(quant.owner_id or quant.qty <= 0 for quant in self):
            return False

        location_from = move.location_id
        location_to = self[0].location_id  # TDE FIXME: as the accounting is based on this value, should probably check all location_to to be the same
        company_from = location_from.usage == 'internal' and location_from.company_id or False
        company_to = location_to and (location_to.usage == 'internal') and location_to.company_id or False
        self._create_value_move_line(move, location_from, location_to)

    def _quant_create_from_move(self, qty, move, lot_id=False, owner_id=False, src_package_id=False, dest_package_id=False, force_location_from=False, force_location_to=False):
        quant = super(StockQuant, self)._quant_create_from_move(qty, move, lot_id=lot_id, owner_id=owner_id, src_package_id=src_package_id, dest_package_id=dest_package_id, force_location_from=force_location_from, force_location_to=force_location_to)
        quant._stock_value_move_enty(move)
        return quant

    def _quant_update_from_move(self, move, location_dest_id, dest_package_id, lot_id=False, entire_pack=False):
        res = super(StockQuant, self)._quant_update_from_move(move, location_dest_id, dest_package_id, lot_id=lot_id, entire_pack=entire_pack)
        self._stock_value_move_enty(move)
        return res