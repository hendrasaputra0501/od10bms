# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tax_payment_id = fields.Many2one('tax.payment', 'Tax Payment Reference')
    tax_payment = fields.Boolean('Tax Payment')