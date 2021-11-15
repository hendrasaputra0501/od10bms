# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia <www.konsaltenindonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from odoo import models, api, fields, _
from odoo.exceptions import UserError

class AssetInvoice(models.TransientModel):
    _name = "wizard.asset.from.invoice"
    _description = "Add or Capitalize Asset"

    action_type = fields.Selection([('create', 'Create Asset'), ('capitalize', 'Capitalize Asset')], string='Type', required=True, default='capitalize')
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice Line', required=True)
    asset_category_id = fields.Many2one('account.asset.category', 'Asset Category')
    asset_id = fields.Many2one('account.asset.asset', 'Add to Asset')

    @api.model
    def default_get(self, default_fields):
        LineObj = self.env['account.invoice.line']
        context = self._context
        
        data = super(AssetInvoice, self).default_get(default_fields)
        if context.get('active_id'):
            invoice_line = LineObj.browse(context['active_id'])
            if invoice_line.invoice_id.state!='draft':
                raise UserError(_("Invoice must be in draft or Pro-forma state in order to create or capitalize asset it."))
            data['invoice_line_id'] = invoice_line.id
            data['action_type'] = invoice_line.asset_action_type or 'capitalize'
            data['asset_category_id'] = invoice_line.asset_category_id.id
            data['asset_id'] = invoice_line.asset_id.id
        return data

    @api.multi
    def confirm(self):
        self.ensure_one()
        to_write = {'asset_action_type': self.action_type, 'asset_id': False, 'asset_category_id': False}
        if self.action_type=='create':
            to_write['asset_category_id'] = self.asset_category_id.id
        else:
            to_write['asset_id'] = self.asset_id.id

        self.invoice_line_id.write(to_write)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def remove(self):
        self.ensure_one()
        self.invoice_line_id.write({
                'asset_action_type': False, 'asset_id': False, 'asset_category_id': False,
            })
        return {'type': 'ir.actions.act_window_close'}