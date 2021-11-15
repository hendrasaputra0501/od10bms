# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ir_actions_report(models.Model):
    _inherit = 'ir.actions.report.xml'

    auto_print = fields.Boolean(string='Automatic printing')
    preview_print = fields.Boolean(string='Preview print')
