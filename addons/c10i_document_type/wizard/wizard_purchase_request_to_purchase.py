# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
import time
import datetime
from odoo import api, fields, models, SUPERUSER_ID, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

class WizardPurchaseRequestToPurchase(models.TransientModel):
    _inherit	    = "wizard.purchase.request.to.purchase"
    _description 	= "Purchase Request To Purchase Order"

    doc_type_id         = fields.Many2one("res.document.type", "Type", required=True)

    @api.multi
    def create_purchase(self):
        line_ids = self.line_ids.filtered(lambda r: r.is_select == True)
        if not line_ids:
            raise UserError(_("Please select item"))
        

        po_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        request_ids = []
        self_ids = []
        for header in self.partner_ids:
            values_header = {
                'partner_id': header and header.id or False,
                'partner_ref': header and header.ref or '',
                'purchase_request_ids': [(6, 0, [request.request_id.id for request in line_ids])],
                'picking_type_id': line_ids[-1] and line_ids[-1].request_id and line_ids[
                    -1].request_id.picking_type_id and line_ids[-1].request_id.picking_type_id.id or False
            }
            if self.doc_type_id and self.doc_type_id.picking_type_id:
                values_header['picking_type_id'] = self.doc_type_id.picking_type_id.id
            if self.service_order:
                values_header.update({'service_order': True})
            new_purchase_id = po_obj.create(values_header)
            self_ids.append(new_purchase_id.id)
            if new_purchase_id and not self.service_order:
                for line in line_ids:
                    if line.product_qty <= 0:
                        continue
                    request_ids.append(line.request_id and line.request_id.id)
                    fpos = new_purchase_id.fiscal_position_id
                    if self.env.uid == SUPERUSER_ID:
                        company_id = self.env.user.company_id.id
                        taxes_ids = fpos.map_tax(
                            line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                    else:
                        taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id)
                    if line.product_id.type != 'service':
                        values_line = {
                            'order_id': new_purchase_id.id,
                            'product_id': line.product_id and line.product_id.id or False,
                            'request_id': line.request_id and line.request_id.id or False,
                            'request_line_id': line.request_line_id and line.request_line_id.id or False,
                            'rfq_id': False,
                            'rfq_line_id': False,
                            'name': line.request_line_id.name or '/',
                            'date_planned': line.scheduled_date or datetime.datetime.now().strftime('%Y-%m-%d'),
                            'product_qty': line.product_qty,
                            'product_uom': line.product_uom_id and line.product_uom_id.id or False,
                            'price_unit': line.last_purchase_price,
                            'taxes_id': [(6, 0, taxes_ids.ids)],
                            'state': 'draft',
                        }
                        po_line_obj.create(values_line)
            if new_purchase_id and self.service_order:
                for line in line_ids:
                    if line.product_qty <= 0:
                        continue
                    request_ids.append(line.request_id and line.request_id.id)
                    fpos = new_purchase_id.fiscal_position_id
                    if self.env.uid == SUPERUSER_ID:
                        company_id = self.env.user.company_id.id
                        taxes_ids = fpos.map_tax(
                            line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                    else:
                        taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id)
                    if line.product_id.type == 'service':
                        values_line = {
                            'order_id': new_purchase_id.id,
                            'product_id': line.product_id and line.product_id.id or False,
                            'request_id': line.request_id and line.request_id.id or False,
                            'request_line_id': line.request_line_id and line.request_line_id.id or False,
                            'rfq_id': False,
                            'rfq_line_id': False,
                            'name': line.request_line_id.name or '/',
                            'date_planned': line.scheduled_date or datetime.datetime.now().strftime('%Y-%m-%d'),
                            'product_qty': line.product_qty,
                            'product_uom': line.product_uom_id and line.product_uom_id.id or False,
                            'price_unit': line.last_purchase_price,
                            'taxes_id': [(6, 0, taxes_ids.ids)],
                            'state': 'draft',
                        }
                        po_line_obj.create(values_line)
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['context'] = {'search_default_purchase_request_ids': list(set(request_ids))}
        action['domain'] = [('id', 'in', self_ids)]
        return action