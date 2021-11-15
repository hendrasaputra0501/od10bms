# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def print_report_picking(self):
        if self.is_issue == True:
            name = "report_spb"
        else:
            name = "report_stock_picking"
        return {
                'type'          : 'ir.actions.report.xml',
                'report_name'   : name,
                'datas'         : {
                    'model'         : 'stock.picking',
                    'id'            : self._context.get('active_ids') and self._context.get('active_ids')[0] or self.id,
                    'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or [],
                    'name'          : self.name or "---",
                    },
                'nodestroy'     : False
        }