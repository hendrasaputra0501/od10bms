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
from odoo.exceptions import UserError, ValidationError

class Currency(models.Model):
    _inherit = 'res.currency'

    # Define currency name, ex: IDR = Rupiah, etc.
    alias_currency_name = fields.Char("Currency Name", default='')

    @api.multi
    def _get_permission_inverse_currency(self):
        self.ensure_one()
        self.allow_inverse_currency_rate = self.env.user.company_id.allow_inverse_currency_rate

    allow_inverse_currency_rate = fields.Boolean('Allow Inverse Currency Rate', compute=_get_permission_inverse_currency)
    inverse_rate = fields.Boolean('Inverse Currency Rate')

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)
        from_rate = (1.0/from_currency.rate if from_currency.inverse_rate else from_currency.rate)
        to_rate = (1.0/to_currency.rate if to_currency.inverse_rate else to_currency.rate)
        return to_rate / from_rate

    @api.multi
    def compute(self, from_amount, to_currency, round=True):
        if not self._context.get('force_rate', False):
            return super(Currency, self).compute(from_amount, to_currency, round=round)
        else:
            """ Convert `from_amount` from currency `self` to `to_currency`. """
            self, to_currency = self or to_currency, to_currency or self
            assert self, "compute from unknown currency"
            assert to_currency, "compute to unknown currency"
            # apply conversion rate
            if self == to_currency:
                to_amount = from_amount
            else:
                to_amount = from_amount * self._context['force_rate']
            # apply rounding
            return to_currency.round(to_amount) if round else to_amount

class CurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    allow_inverse_currency_rate = fields.Boolean(related='currency_id.allow_inverse_currency_rate', string='Allow Inverse Currency Rate')
    inverse_rate = fields.Boolean('Inverse Currency Rate')

    @api.multi
    @api.onchange('currency_id')
    def onchange_currency_id(self):
        self.ensure_one()
        if self.currency_id:
            self.inverse_rate = self.currency_id.inverse_rate
        else:
            self.inverse_rate = False