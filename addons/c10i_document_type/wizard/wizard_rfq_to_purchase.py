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

class WizardRfqToPurchase(models.TransientModel):
    _inherit	    = "wizard.rfq.to.purchase"
    _description 	= "RFQ To Purchase Order"

    doc_type_id         = fields.Many2one("res.document.type", "Type", required=True)

    @api.multi
    def create_purchase(self):
        po_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        request_ids = []
        self_ids = []
        values_header = {
            'partner_id': self.partner_id and self.partner_id.id or False,
            'partner_ref': self.partner_id and self.partner_id.ref or '',
            'currency_id': self.currency_id and self.currency_id.id or '',
            'purchase_request_ids': [(6, 0, list(set([rfq.request_id.id for rfq in self.line_ids])))],
            'purchase_rfq_ids': [(6, 0, list(set([rfq.rfq_id.id for rfq in self.line_ids])))],
            'picking_type_id': self.line_ids[-1] and self.line_ids[-1].rfq_id and self.line_ids[
                -1].rfq_id.picking_type_id and self.line_ids[-1].rfq_id.picking_type_id.id or False
        }
        if self.doc_type_id and self.doc_type_id.picking_type_id:
            values_header['picking_type_id'] = self.doc_type_id.picking_type_id.id
        if self.service_order:
            values_header.update({'service_order': True})
        new_purchase_id = po_obj.create(values_header)
        if new_purchase_id and not self.service_order:
            self_ids.append(new_purchase_id.id)
            for line in self.line_ids:
                if line.product_qty <= 0:
                    continue
                fpos = new_purchase_id.fiscal_position_id
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    taxes_ids = fpos.map_tax(
                        line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                else:
                    taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id)
                request_ids.append(line.request_id and line.request_id.id)
                if line.product_id.type <> 'service':
                    values_line = {
                        'order_id': new_purchase_id.id,
                        'product_id': line.product_id and line.product_id.id or False,
                        'request_id': line.request_id and line.request_id.id or False,
                        'request_line_id': line.request_line_id and line.request_line_id.id or False,
                        'rfq_id': line.rfq_id and line.rfq_id.id or False,
                        'rfq_line_id': line.rfq_line_id and line.rfq_line_id.id or False,
                        'name': line.request_line_id.name or '/',
                        'date_planned': line.scheduled_date or datetime.datetime.now().strftime('%Y-%m-%d'),
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom_id and line.product_uom_id.id or False,
                        'price_unit': line.unit_price,
                        'taxes_id': [(6, 0, taxes_ids.ids)],
                        'state': 'draft',
                    }
                    po_line_obj.create(values_line)
        if new_purchase_id and self.service_order:
            self_ids.append(new_purchase_id.id)
            for line in self.line_ids:
                if line.product_qty <= 0:
                    continue
                fpos = new_purchase_id.fiscal_position_id
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    taxes_ids = fpos.map_tax(
                        line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                else:
                    taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id)
                request_ids.append(line.request_id and line.request_id.id)
                if line.product_id.type == 'service':
                    values_line = {
                        'order_id': new_purchase_id.id,
                        'product_id': line.product_id and line.product_id.id or False,
                        'request_id': line.request_id and line.request_id.id or False,
                        'request_line_id': line.request_line_id and line.request_line_id.id or False,
                        'rfq_id': line.rfq_id and line.rfq_id.id or False,
                        'rfq_line_id': line.rfq_line_id and line.rfq_line_id.id or False,
                        'name': line.request_line_id.name or '/',
                        'date_planned': line.scheduled_date or datetime.datetime.now().strftime('%Y-%m-%d'),
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom_id and line.product_uom_id.id or False,
                        'price_unit': line.unit_price,
                        'taxes_id': [(6, 0, taxes_ids.ids)],
                        'state': 'draft',
                    }
                    po_line_obj.create(values_line)
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['context'] = {'search_default_purchase_request_ids': list(set(request_ids))}
        action['domain'] = [('id', 'in', self_ids)]
        return action