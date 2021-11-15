# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
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

import logging

class StockMove(models.Model):
    _inherit = 'stock.move'

    # @api.model
    # def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
    #     res = super(StockMove, self)._prepare_account_move_line(
    #         qty, cost, credit_account_id, debit_account_id)
    #     if res:
    #         debit_line_vals = res[0][2]
    #         credit_line_vals = res[1][2]
    #
    #         if self.account_location_type_id:
    #             debit_line_vals.update({'account_location_type_id': self.account_location_type_id.id})
    #             credit_line_vals.update({'account_location_type_id': self.account_location_type_id.id})
    #         if self.account_location_id:
    #             debit_line_vals.update({'account_location_id': self.account_location_id.id})
    #             credit_line_vals.update({'account_location_id': self.account_location_id.id})
    #         return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
    #     return res
    def action_done(self):
        res = super(StockMove,self).action_done()

        # for inter warehouse transfer
        pickings = self.env['stock.picking']
        for move in self:
            if not move.picking_id:
                continue
            if move.picking_id and move.picking_id.inter_warehouse \
                    and move.picking_id.inter_warehouse_type=='internal_out' and move.picking_id.dest_picking_type_id:
                pickings |= move.picking_id

        if pickings:
            for picking in pickings:
                print ">>>>>>>>>>>>>>>>>>>2 Ada coy", picking.id
                # create new picking for received products
                picking_type_id = picking.dest_picking_type_id.id
                new_picking = picking.copy({
                    'move_lines': [],
                    'picking_type_id': picking_type_id,
                    'inter_warehouse': True,
                    'inter_warehouse_type': 'internal_in',
                    'state': 'draft',
                    'origin': picking.name + (picking.origin and " (%s)" % picking.origin or ""),
                    'location_id': picking.location_dest_id.id,
                    'location_dest_id': picking.dest_picking_type_id.default_location_dest_id.id,
                    'backorder_id': picking.id,
                })
                print ">>>>>>>>>>>>>>>3 Ada coy", new_picking.id
                new_picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': new_picking, 'origin': picking},
                                                   subtype_id=self.env.ref('mail.mt_note').id)

                for move in picking.move_lines:
                    dict_product_cost_price = {}
                    if move.product_id.id not in dict_product_cost_price.keys():
                        dict_product_cost_price.update({move.product_id.id: {}})
                    for quant in move.quant_ids:
                        price = move.price_unit or quant.cost
                        if price not in dict_product_cost_price[move.product_id.id].keys():
                            dict_product_cost_price[move.product_id.id].update({price: 0.0})
                        dict_product_cost_price[move.product_id.id][price] += quant.qty
                    for product_id in dict_product_cost_price.keys():
                        for cost_price in dict_product_cost_price[product_id].keys():
                            dest_qty = dict_product_cost_price[product_id][cost_price]
                            move.copy({
                                'product_id': product_id,
                                'product_uom_qty': dest_qty,
                                'price_unit': cost_price,
                                'picking_id': new_picking.id,
                                'state': 'draft',
                                'location_id': move.location_dest_id.id,
                                'location_dest_id': picking.dest_picking_type_id.default_location_dest_id.id,
                                'picking_type_id': picking_type_id,
                                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                                'procure_method': 'make_to_stock',
                            })
                new_picking.action_confirm()
                new_picking.action_assign()