# -*- coding: utf-8 -*-
# Copyright 2017-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportKpi(models.Model):

    _inherit = 'mis.report.kpi'

    budgetable = fields.Boolean(
        default=False,
    )
