# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TaxAccountGroup(models.Model):
    _name = 'tax.account.group'

    name = fields.Char(string="Group Name", required=True)
    account_ids = fields.Many2many("account.account", string="Account", required=True)