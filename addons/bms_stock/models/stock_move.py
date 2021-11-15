# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    account_id                          = fields.Many2one('account.account', string='Allocation Account', ondelete='restrict')
    account_location_type_id            = fields.Many2one(comodel_name="account.location.type", string="Tipe Lokasi", ondelete="restrict")
    account_location_id                 = fields.Many2one(comodel_name="account.location", string="Lokasi", ondelete="restrict")
    account_location_type_no_location   = fields.Boolean(string="Location Type No Account", related="account_location_type_id.no_location")
    account_account_location_ids        = fields.Many2many('account.account', string='Daftar Account')
    account_location_type_name          = fields.Char("Tipe Lokasi Name", related="account_location_type_id.name", required=True)
    account_location_name               = fields.Char("Lokasi Name", related="account_location_id.name", required=True)

    @api.onchange('account_location_type_id')
    def _onchange_account_location_type_id(self):
        if self.account_location_type_id:
            self.account_location_id = False
            if self.account_location_type_id.no_location and (self.account_location_type_id.general_charge):
                self.account_id = False
            else:
                self.account_id = self.account_location_type_id.account_id and self.account_location_type_id.account_id.id or False
            if self.account_location_type_id.account_ids:
                self.account_account_location_ids = self.account_location_type_id.account_ids.ids
            else:
                self.account_account_location_ids = self.env['account.account'].search([]).ids

    @api.onchange('account_location_id')
    def _onchange_account_location_id(self):
        if self.account_location_type_id.project and self.account_location_id:
            if self.account_location_type_id.project:
                project_data = self.env['mill.project'].search([('location_id', '=', self.account_location_id.id)])
                if project_data.categ_id.account_id:
                    self.account_account_location_ids = [(6, 0, [project_data.categ_id.account_id.id])]
                else:
                    self.account_account_location_ids = False

    @api.model
    def _prepare_account_move_line(self, qty, cost, credit_account_id,
                                   debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id)
        if res:
            debit_line_vals = res[0][2]
            credit_line_vals = res[1][2]

            if self.account_location_type_id:
                debit_line_vals.update({'account_location_type_id': self.account_location_type_id.id})
                credit_line_vals.update({'account_location_type_id': self.account_location_type_id.id})
            if self.account_location_id:
                debit_line_vals.update({'account_location_id': self.account_location_id.id})
                credit_line_vals.update({'account_location_id': self.account_location_id.id})
            return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        return res