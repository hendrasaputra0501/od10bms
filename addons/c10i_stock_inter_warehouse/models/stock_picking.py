# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from collections import OrderedDict, defaultdict
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    inter_warehouse = fields.Boolean("Intra-Warehouse Transfer", readonly=True,
                                states={'draft': [('readonly',False)]})
    inter_warehouse_type = fields.Selection([('internal_out','Delivery Internal Transfer'),\
                                ('internal_in','Receive Internal Transfer')], string='Intra-Warehouse Type',
                                readonly=True, states={'draft': [('readonly',False)]})
    dest_picking_type_id = fields.Many2one('stock.picking.type', '(Intra) Picking Type Dest')

    @api.model
    def default_get(self, fields):
        res = super(StockPicking, self).default_get(fields)
        if res.get('inter_warehouse') and res.get('inter_warehouse_type'):
            if res['inter_warehouse_type'] == 'internal_out':
                picking_type_ids = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                              ('default_location_src_id.usage', '=', 'internal'),
                                              ('default_location_dest_id.usage', '=', 'transit')])
            else:
                picking_type_ids = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                ('default_location_src_id.usage', '=', 'transit'),
                                                ('default_location_dest_id.usage', '=', 'internal')])
            if picking_type_ids:
                res['picking_type_id'] = picking_type_ids[0].id
        return res

    # @api.multi
    # def print_report_picking(self):
    #     return {
    #         'type': 'ir.actions.report.xml',
    #         'report_name': 'report_stock_picking',
    #         'datas': {
    #             'model': 'stock.picking',
    #             'id': self._context.get('active_ids') and self._context.get('active_ids')[0] or self.id,
    #             'ids': self._context.get('active_ids') and self._context.get('active_ids') or [],
    #             'name': self.name or "---",
    #         },
    #         'nodestroy': False
    #     }