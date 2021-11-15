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

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _account_entry_move(self, move):
        company_from = move.company_id
        if move.picking_id and move.picking_id.inter_warehouse:
            if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                if move.product_id.categ_id.intra_warehouse_transfer_account_id:
                    acc_dest = move.product_id.categ_id.intra_warehouse_transfer_account_id.id
                self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_valuation,
                                                                                           acc_dest, journal_id)
            elif move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
                journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                if move.product_id.categ_id.intra_warehouse_transfer_account_id:
                    acc_src = move.product_id.categ_id.intra_warehouse_transfer_account_id.id
                self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_src, acc_valuation,
                                                                                           journal_id)
        else:
            return super(StockQuant, self)._account_entry_move(move)