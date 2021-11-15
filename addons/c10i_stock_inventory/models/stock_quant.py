# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _account_entry_move(self, move):
        company_from = move.company_id
        if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'inventory' and move.account_id:
            journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
            acc_dest = move.account_id.id
            self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_valuation,
                                                                                       acc_dest, journal_id)
        elif move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal' and move.account_id:
            journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
            acc_src = move.account_id.id
            self.with_context(force_company=company_from.id)._create_account_move_line(move, acc_src, acc_valuation,
                                                                                           journal_id)
        else:
            return super(StockQuant, self)._account_entry_move(move)