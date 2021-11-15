# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('advance_invoice_ids.amount_total','advance_invoice_ids.state')
    def _amount_downpayment(self):
        for order in self:
            amount_total        = 0.0
            percentage_total    = 0.0
            for line in order.advance_invoice_ids:
                if line.state not in ['cancel']:
                    amount_total        += line.amount_total
                    percentage_total    += line.percentage_downpayment
            order.update({
                'downpayment'       : percentage_total,
                'downpayment_value' : amount_total,
            })

    doc_type_id         = fields.Many2one("res.document.type", "Type", ondelete="restrict", readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always', copy=True)
    downpayment         = fields.Float("Down Payment", store=True, readonly=True, compute='_amount_downpayment', change_default=True, index=True, track_visibility='always', copy=False)
    downpayment_value   = fields.Float("Down Payment Amount", store=True, readonly=True, compute='_amount_downpayment', track_visibility='always', copy=False)
    auto_downpayment    = fields.Boolean(related="doc_type_id.auto_downpayment", string="Auto Down Payment", copy=False)
    user_id             = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    advance_invoice_ids = fields.One2many(comodel_name='account.invoice.advance', inverse_name='sale_id', string='Advance Invoice', readonly=True, copy=False, track_visibility='onchange')

    @api.multi
    def print_report_sale(self):
        if self.doc_type_id and self.doc_type_id.report_id:
            report_name = self.doc_type_id.report_id.report_name
        else:
            raise ValidationError(_("Terjadi kesalahan (T.T). \n"
                                        "Report Tidak Ditemukan!"))
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : report_name,
            'datas'         : {
                'model'         : 'sale.order',
                'id'            : self._context.get('active_ids') and self._context.get('active_ids')[0] or self.id,
                'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or [],
                'name'          : self.name or "---",
                },
            'nodestroy'     : False
        }

    @api.model
    def create(self, vals):
        if vals.get('doc_type_id') and self.env['res.document.type'].browse(vals['doc_type_id']) and self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id:
            if vals.get('name', _('New')) == _('New'):
                if 'company_id' in vals:
                    vals['name'] = self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id.with_context(force_company=vals['company_id']).next_by_id() or _('New')
                else:
                    vals['name'] = self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id.next_by_id() or _('New')
        result = super(SaleOrder, self).create(vals)
        return result

    @api.onchange('doc_type_id')
    def onchange_doc_type(self):
        if self.doc_type_id and self.doc_type_id.picking_type_id and self.doc_type_id.picking_type_id.warehouse_id:
            self.warehouse_id = self.doc_type_id.picking_type_id.warehouse_id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_procurement_create(self):
        for sale_line in self:
            if sale_line.order_id.doc_type_id.no_create_picking:
                return False
            else:
                result = super(SaleOrderLine, self)._action_procurement_create()
                return result

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(group_id=group_id)
        if self.order_id.doc_type_id and self.order_id.doc_type_id.picking_type_id \
                and self.order_id.doc_type_id.picking_type_id.code=='outgoing' \
                and self.order_id.doc_type_id.picking_type_id.warehouse_id:
            vals.update({
                'warehouse_id': self.order_id.doc_type_id.picking_type_id.warehouse_id.id,
            })
        return vals