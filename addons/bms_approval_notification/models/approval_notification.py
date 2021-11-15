# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BmsApprovalNotification(models.Model):
    _name = 'bms.approval.notification'

    document_id = fields.Many2one("res.document.type", string="Document Type", required=True, domain=[('|'), ('name', 'ilike', 'Pembelian'), ('name', 'ilike', 'SPK')])
    document_state = fields.Selection([
                            ('to_approve_manager', 'To Approve Manager'),
                            ('to_approve_direktur', 'To Approve Direktur')
                        ], string='Document State', required=True)
    user_ids = fields.Many2many("res.users", string="Users", required=True)