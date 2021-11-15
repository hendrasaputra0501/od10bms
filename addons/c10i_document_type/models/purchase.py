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
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class PurchaseOrder(models.Model):
    _inherit        = 'purchase.order'

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

    doc_type_id         = fields.Many2one("res.document.type", "Type", ondelete="restrict", readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
    downpayment         = fields.Float("Down Payment", store=True, readonly=True, compute='_amount_downpayment', change_default=True, index=True, track_visibility='always', copy=False)
    downpayment_value   = fields.Float("Down Payment Amount", store=True, readonly=True, compute='_amount_downpayment', track_visibility='always')
    auto_downpayment    = fields.Boolean(related="doc_type_id.auto_downpayment", string="Auto Down Payment")
    user_id             = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    advance_invoice_ids = fields.One2many(comodel_name='account.invoice.advance', inverse_name='purchase_id', string='Advance Invoice', readonly=True, copy=False, track_visibility='onchange')
    advance_invoice_count = fields.Integer(compute="_compute_invoice_advance", string='# of Bills', copy=False, default=0)

    @api.depends('advance_invoice_ids.state')
    def _compute_invoice_advance(self):
        for order in self:
            order.advance_invoice_count = len(order.advance_invoice_ids.ids)

    @api.multi
    def print_report_purchase(self):
        if self.doc_type_id and self.doc_type_id.report_id:
            report_name = self.doc_type_id.report_id.report_name
        else:
            report_name = 'report_nota_purchase_order'
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : report_name,
            'datas'         : {
                'model'         : 'purchase.order',
                'id'            : self.id,
                'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or [],
                'name'          : self.name or "---",
                },
            'nodestroy'     : False
        }

    @api.onchange('partner_id', 'company_id', 'doc_type_id')
    def onchange_partner_id(self):
        if not self.partner_id and not self.doc_type_id:
            self.fiscal_position_id = False
            self.payment_term_id    = False
            self.currency_id        = False
            self.ref                = False
            self.incoterm_id        = False
            self.shipping_partner_id= False
            self.invoice_partner_id = False
            self.report_sign_1      = False
            self.report_sign_2      = False
            self.report_sign_3      = False
            self.report_sign_4      = False
            self.report_sign_5      = False
            self.report_sign_6      = False
        elif self.partner_id and not self.doc_type_id:
            self.fiscal_position_id = self.env['account.fiscal.position'].with_context(company_id=self.company_id.id).get_fiscal_position(self.partner_id.id)
            self.payment_term_id    = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id        = self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id
            self.partner_ref        = self.partner_id.ref
            self.incoterm_id        = False
            self.shipping_partner_id= False
            self.invoice_partner_id = False
            self.report_sign_1      = False
            self.report_sign_2      = False
            self.report_sign_3      = False
            self.report_sign_4      = False
            self.report_sign_5      = False
            self.report_sign_6      = False
        elif self.partner_id and self.doc_type_id:
            self.payment_term_id    = self.partner_id.property_supplier_payment_term_id.id or self.doc_type_id.payment_term_id.id
            self.currency_id        = self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id
            self.partner_ref        = self.partner_id.ref
            self.picking_type_id    = self.doc_type_id.picking_type_id and self.doc_type_id.picking_type_id.id or False
            self.incoterm_id        = self.doc_type_id.incoterm_id and self.doc_type_id.incoterm_id.id or False
            self.shipping_partner_id= self.doc_type_id.shipping_partner_id and self.doc_type_id.shipping_partner_id.id or False
            self.invoice_partner_id = self.doc_type_id.invoice_partner_id and self.doc_type_id.invoice_partner_id.id or False
            self.report_sign_1      = self.doc_type_id.purchase_report_sign_1 or "-"
            self.report_sign_2      = self.doc_type_id.purchase_report_sign_2 or "-"
            self.report_sign_3      = self.doc_type_id.purchase_report_sign_3 or "-"
            self.report_sign_4      = self.doc_type_id.purchase_report_sign_4 or "-"
            self.report_sign_5      = self.doc_type_id.purchase_report_sign_5 or "-"
            self.report_sign_6      = self.doc_type_id.purchase_report_sign_6 or "-"
            if self.auto_downpayment:
                self.downpayment        = self.doc_type_id.downpayment_default or 0.0
        elif self.doc_type_id and not self.partner_id:
            self.payment_term_id    = self.doc_type_id.payment_term_id and self.doc_type_id.payment_term_id.id or False
            self.picking_type_id    = self.doc_type_id.picking_type_id and self.doc_type_id.picking_type_id.id or False
            self.incoterm_id        = self.doc_type_id.incoterm_id and self.doc_type_id.incoterm_id.id or False
            self.shipping_partner_id= self.doc_type_id.shipping_partner_id and self.doc_type_id.shipping_partner_id.id or False
            self.invoice_partner_id = self.doc_type_id.invoice_partner_id and self.doc_type_id.invoice_partner_id.id or False
            self.report_sign_1      = self.doc_type_id.purchase_report_sign_1 or "-"
            self.report_sign_2      = self.doc_type_id.purchase_report_sign_2 or "-"
            self.report_sign_3      = self.doc_type_id.purchase_report_sign_3 or "-"
            self.report_sign_4      = self.doc_type_id.purchase_report_sign_4 or "-"
            self.report_sign_5      = self.doc_type_id.purchase_report_sign_5 or "-"
            self.report_sign_6      = self.doc_type_id.purchase_report_sign_6 or "-"
            if self.auto_downpayment:
                self.downpayment    = self.doc_type_id.downpayment_default or 0.0
        else:
            return {}
        return {}

    @api.model
    def create(self, vals):
        if self._context.get('doc_type_id') and self.env['res.document.type'].browse(self._context.get('doc_type_id')).id:
            document_type   = self._context.get('doc_type_id') and self.env['res.document.type'].browse(self._context.get('doc_type_id'))
            vals['doc_type_id']   = document_type.id
            vals['report_sign_1']   = document_type.purchase_report_sign_1
            vals['report_sign_2']   = document_type.purchase_report_sign_2
            vals['report_sign_3']   = document_type.purchase_report_sign_3
            vals['report_sign_4']   = document_type.purchase_report_sign_4
            vals['report_sign_5']   = document_type.purchase_report_sign_5
            vals['report_sign_6']   = document_type.purchase_report_sign_6
        if vals.get('doc_type_id') and self.env['res.document.type'].browse(vals['doc_type_id']) and self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id:
            if vals.get('name', _('New')) == _('New'):
                if 'company_id' in vals:
                    vals['name'] = self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id.with_context(force_company=vals['company_id']).next_by_id() or _('New')
                else:
                    vals['name'] = self.env['res.document.type'].browse(vals['doc_type_id']).sequence_id.next_by_id() or _('New')
        result = super(PurchaseOrder, self).create(vals)
        return result

    @api.multi
    def _create_picking(self):
        if self.doc_type_id.no_create_picking:
            return False
        else:
            result = super(PurchaseOrder, self)._create_picking()
            return result

    # @api.model
    # def _prepare_picking(self):
    #     picking_vals = super(PurchaseOrder, self)._prepare_picking()
    #     if self.doc_type_id and self.doc_type_id.picking_type_id and \
    #                 self.doc_type_id.picking_type_id.code=='incoming':
    #         picking_vals.update({
    #             'picking_type_id': self.doc_type_id.picking_type_id.id,
    #             'location_dest_id': self.doc_type_id.picking_type_id.default_location_dest_id.id,
    #         })
    #     return picking_vals

    @api.multi
    def action_view_advance_invoice(self):
        action = self.env.ref('c10i_account_invoice_advance.action_invoice_advance_tree2')
        result = action.read()[0]
        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_advance', 'default_purchase_id': self.id}
        if not self.advance_invoice_ids:
            # Choose a default account journal in the same currency in case a new invoice is created
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = self.advance_invoice_ids[0].journal_id.id

        # choose the view_mode accordingly
        if len(self.advance_invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.advance_invoice_ids.ids) + ")]"
        elif len(self.advance_invoice_ids) == 1:
            res = self.env.ref('c10i_account_invoice_advance.invoice_advance_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.advance_invoice_ids.id
        return result