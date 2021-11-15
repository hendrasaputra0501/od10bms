# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report.xml'

    is_report_designer = fields.Boolean(string="Report created by Report Designer or not", default=False)
