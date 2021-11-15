from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.multi
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        
        # tambahan
        cpo_qty = self.env['mill.lhp'].search([('state','=','approved')], order='id desc', limit=1)
        uom_qty = self.product_uom_qty
        if self.product_id.id == 9078:
            for record in cpo_qty:
                if uom_qty >= record.total_cpo_tangki:
                    warning_mess = {
                        'title': _('Stock Tidak cukup!'),
                        'message' : _('Stock Tidak cukup!') 
                    }
                    return {'warning': warning_mess}
            return {}
        if self.product_id.id == 9079:
            for record in cpo_qty:
                if uom_qty >= record.total_stock_kernel:
                    warning_mess = {
                        'title': _('Stock Tidak cukup!'),
                        'message' : _('Stock Tidak cukup!') 
                    }
                    return {'warning': warning_mess}
            return {}
        # tambahan

        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : _('You plan to sell %s %s but you only have %s %s available!\nThe stock on hand is %s %s.') % \
                            (self.product_uom_qty, self.product_uom.name, self.product_id.virtual_available, self.product_id.uom_id.name, self.product_id.qty_available, self.product_id.uom_id.name)
                    }
                    return {'warning': warning_mess}
        return {}