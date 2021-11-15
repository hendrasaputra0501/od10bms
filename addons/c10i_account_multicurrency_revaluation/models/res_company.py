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

class Company(models.Model):
    _inherit = 'res.company'

    revaluation_loss_account_id = fields.Many2one('account.account', 'Revaluation loss account', domain=[('deprecated', '=', False)])
    revaluation_gain_account_id = fields.Many2one('account.account', 'Revaluation gain account', domain=[('deprecated', '=', False)])
    default_currency_reval_journal_id = fields.Many2one('account.journal', 'Default Revaluation Journal')

    @api.multi
    def write(self, update_vals):
        if 'revaluation_loss_account_id' in update_vals.keys():
            update_vals.update({'expense_currency_exchange_account_id': update_vals['revaluation_loss_account_id']})
        if 'revaluation_loss_account_id' in update_vals.keys():
            update_vals.update({'income_currency_exchange_account_id': update_vals['revaluation_loss_account_id']})
        res = super(Company, self).write(update_vals)
        return res

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    revaluation_loss_account_id = fields.Many2one('account.account', related='company_id.revaluation_loss_account_id', string='Revaluation loss account', domain=[('deprecated', '=', False)])
    revaluation_gain_account_id = fields.Many2one('account.account', related='company_id.revaluation_gain_account_id', string='Revaluation gain account', domain=[('deprecated', '=', False)])
    default_currency_reval_journal_id = fields.Many2one('account.journal', related='company_id.default_currency_reval_journal_id', string='Default Revaluation Journal', domain=[('type', '=', 'general')])

    @api.multi
    def write(self, update_vals):
        company_to_update = {}
        if 'revaluation_loss_account_id' in update_vals.keys():
            company_to_update.update({'expense_currency_exchange_account_id': update_vals['revaluation_loss_account_id']})
        if 'revaluation_loss_account_id' in update_vals.keys():
            company_to_update.update({'income_currency_exchange_account_id': update_vals['revaluation_loss_account_id']})
        self.company_id.write(company_to_update)
        res = super(AccountConfigSettings, self).write(update_vals)
        return res
