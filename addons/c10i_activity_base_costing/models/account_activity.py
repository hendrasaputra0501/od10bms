# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################


from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

# import time
# import calendar
# from datetime import datetime
# from dateutil.relativedelta import relativedelta

class AccountActivity(models.Model):
    _name = 'account.activity'
    _description = 'Account Activity'

    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    type_id = fields.Many2one("account.location.type", string="Tipe Lokasi", ondelete="restrict")
    parent_id = fields.Many2one("account.activity", string="Parent Activity", ondelete="restrict")
    # parent_code = fields.Char(related="parent_id.code", string="Parent Activity", readonly=True, store=True)
    child_ids = fields.One2many('account.activity', 'parent_id', 'Child Activity')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    level = fields.Integer("Level", compute="_compute_level", readonly=True, store=True)
    
    active = fields.Boolean("Active", default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)

    account_id = fields.Many2one("account.account", string="Account Allocation", ondelete="restrict")

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'code, name'
    _order = 'parent_left'

    _sql_constraints = [
        ('activity_code_company_uniq', 'unique (code,company_id)', 'The code of the Activity must be unique per company !')
    ]

    @api.depends('parent_id')
    def _compute_level(self):
        for level in self:
            self.level = len(self.search([('id', 'parent_of', [self.id])]))

    @api.multi
    def _name_get(self):
        result = []
        for record in self:
            if record.name and record.code:
                result.append((record.id, record.code + " - " + record.name))
            if record.name and not record.code:
                result.append((record.id, record.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        AccountActivity = self.search(domain + args, limit=limit)
        return AccountActivity._name_get()