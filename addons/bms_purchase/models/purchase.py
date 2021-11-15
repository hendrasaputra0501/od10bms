from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sign_city = fields.Char(string='Kota')    


    #AWAL tambahan DIKI
    approved_manager = fields.Many2one('res.users','Approved By Manager')
    approved_direktur = fields.Many2one('res.users','Approved By Direktur')

    state_approv = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve_manager', 'To Approve Manager'),
        ('to_approve_direktur', 'To Approve Direktur'),
        ('approved', 'Approved')
        ], string='Status', default='draft')

    @api.multi
    def set_to_approve_manager(self):
        for doc in self:
            doc.state_approv = 'to_approve_manager'

    @api.multi
    def set_to_approve_direktur(self):
        for doc in self:
            manager = self.env.uid
            doc.approved_manager = manager
            doc.state_approv = 'to_approve_direktur'

    @api.multi
    def set_approved(self):
        for doc in self:
            direktur = self.env.uid
            doc.approved_direktur = direktur
            doc.state_approv = 'approved'

    @api.onchange('purchase_request_ids')
    def onchange_purchase_request(self):
        detail_lines = []
        for each in self.purchase_request_ids.filtered(lambda x: x.line_ids.ids not in self.order_line.ids):
            purchase_request = self.env['purchase.request'].search([('id','=',each.id)])
            for x in purchase_request:
                for lines in x.line_ids.filtered(lambda x: x.residual!=0):
                    vals = {
                        'order_id'          : self.id,
                        'name'              : lines.product_id.display_name,
                        'product_id'        : lines.product_id.id,
                        'scheduled_date'    : lines.scheduled_date,
                        'price_unit'        : lines.product_id.last_purchase_price,
                        'product_qty'       : lines.product_qty,
                        'product_uom'       : lines.product_uom_id.id,
                        'date_planned'      : lines.scheduled_date or self.date_planned,
                        'request_line_id'   : lines.id,
                        'request_id'        : x.id,
                    }
                    detail_lines.append((0,0,vals))
                self.order_line = detail_lines
            
    #AHIR tambahan DIKI