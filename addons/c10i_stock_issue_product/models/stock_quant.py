# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia <www.konsaltenindonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from collections import OrderedDict, defaultdict

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _account_entry_move(self, move):
        company_from = move.company_id
        if company_from and move.account_id and move.picking_id.picking_type_id.code == 'internal':
            if move.product_id.type != 'product' or move.product_id.valuation != 'real_time':
                return False

            if move.location_id.usage=='internal' and move.location_dest_id.usage!='internal':
                journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                if acc_dest != move.account_id.id:
                    acc_dest = move.account_id.id
                self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_valuation, acc_dest, journal_id)
            elif move.location_id.usage!='internal' and move.location_dest_id.usage=='internal':
                journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                if acc_src != move.account_id.id:
                    acc_src = move.account_id.id
                self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_src, acc_valuation, journal_id)
        else:
            return super(StockQuant, self)._account_entry_move(move)