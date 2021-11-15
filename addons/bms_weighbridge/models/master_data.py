# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
import urllib3
from lxml import etree
import time

############### RES.PARTNER ####################
class WbPartner(models.Model):
    _name = 'weighbridge.partner'
    _description = "Partner"
    _order = "id desc"

    name = fields.Char('TIMBANG RELASI / TIMBANG TRANSPORTER')
    related_partner_id = fields.Many2one('res.partner', 'Odoo Partner')
    tbs_pricelist_ids = fields.One2many('tbs.pricelist', 'partner_id', 'TBS Pricelist')
    cpo_ongkir_ids = fields.One2many('cpo.ongkir', 'partner_id', string="Ongkos Kirim CPO")

class Partner(models.Model):
    _inherit = 'res.partner'

    referensi_timbang = fields.Char('Kode Reference di Timbangan')
    referensi_timbang_id = fields.Many2one('weighbridge.partner', 'Weighbridge Partner')

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if 'referensi_timbang' in vals and vals.get('referensi_timbang',''):
            if vals['referensi_timbang'].strip():
                new_ref = self.env['weighbridge.partner'].create({'name': vals['referensi_timbang'].strip(), 
                    'related_partner_id': res.id})
                res.referensi_timbang_id = new_ref.id
        return res

    @api.multi
    def write(self, vals):
        for partner in self:
            if 'referensi_timbang' in vals:
                ref = vals.get('referensi_timbang','') or ''
                if not ref.strip() and partner.referensi_timbang_id:
                    raise UserError(_('You cannot make edit Referensi Timbang into NULL unless you delete Related Partner in Weighbridge'))
                elif ref.strip():
                    if partner.referensi_timbang_id:
                        partner.referensi_timbang_id.write({'name': ref.strip()})
                    else:
                        ref_new = self.env['weighbridge.partner'].create({'name': ref.strip(), 
                                'related_partner_id': partner.id})
                        partner.referensi_timbang_id = ref_new.id
        return super(Partner, self).write(vals)

class WbProduct(models.Model):
    _name = 'weighbridge.product'
    _description = "Product"
    _order = "id desc"

    name = fields.Char('TIMBANG PRODUK')
    related_product_id = fields.Many2one('product.product', 'Odoo Product', domain=[('type','=','product')])
    transport_account_id = fields.Many2one('account.account', "Transport Account")

class Product(models.Model):
    _inherit = 'product.product'

    referensi_timbang = fields.Char('Kode Reference di Timbangan')
    referensi_timbang_id = fields.Many2one('weighbridge.product', 'Weighbridge Product')

    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        if 'referensi_timbang' in vals and vals.get('referensi_timbang',''):
            if vals['referensi_timbang'].strip():
                new_ref =  self.env['weighbridge.product'].create({'name': vals['referensi_timbang'].strip(), 
                    'related_product_id': res.id})
                res.referensi_timbang_id = new_ref.id
        return res

    @api.multi
    def write(self, vals):
        for product in self:
            if 'referensi_timbang' in vals:
                ref = vals.get('referensi_timbang','') or ''
                if not ref.strip() and product.referensi_timbang_id:
                    raise UserError(_('You cannot make edit Referensi Timbang into NULL unless you delete Related Product in Weighbridge'))
                elif ref.strip():
                    if product.referensi_timbang_id:
                        product.referensi_timbang_id.write({'name': ref.strip()})
                    else:
                        new_ref = self.env['weighbridge.product'].create({'name': ref.strip(), 
                                'related_product_id': product.id})
                        product.referensi_timbang_id = new_ref.id
        return super(Product, self).write(vals)

class Contract(models.Model):
    _name = 'weighbridge.contract'
    _description = "Contract"
    _order = "id desc"

    name = fields.Char('TIMBANG SO')
    trans_type = fields.Selection([('purchase','Pembelian'),('sale','Penjualan')], string='Jenis Transaksi')
    related_sale_id = fields.Many2one('sale.order', 'Odoo Sale Order')
    related_purchase_id = fields.Many2one('purchase.order', 'Odoo Purchase Order')
    related_partner_id = fields.Many2one('res.partner', compute='_get_partner', string='Partner', store=True)

    @api.depends('trans_type', 'related_sale_id', 'related_purchase_id')
    def _get_partner(self):
        for wbc in self:
            if wbc.trans_type=='purchase' and wbc.related_purchase_id:
                wbc.related_partner_id = wbc.related_purchase_id.partner_id.id
            elif wbc.trans_type=='sale' and wbc.related_sale_id:
                wbc.related_partner_id = wbc.related_sale_id.partner_id.id

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    referensi_timbang_id = fields.Many2one('weighbridge.contract', 'Weighbridge Contract')

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if 'order_line' in vals:
            product_timbang = self.sudo().env['weighbridge.product'].search([])
            if product_timbang and product_timbang.mapped('related_product_id').ids:
                product_timbang = product_timbang.mapped('related_product_id').ids
                sale_product = res.order_line.mapped('product_id').ids
                if (res.name or res.client_order_ref) and list(set(product_timbang) & set(sale_product)):
                    new_ref =  self.sudo().env['weighbridge.contract'].create({'name': res.client_order_ref or res.name,
                            'related_sale_id': res.id, 'trans_type': 'sale'})
                    res.referensi_timbang_id = new_ref.id
        return res

    @api.multi
    def write(self, update_vals):
        res = super(SaleOrder, self).write(update_vals)
        for so in self:
            if 'client_order_ref' in update_vals.keys() and so.referensi_timbang_id:
                if update_vals['client_order_ref'] == '':
                    so.referensi_timbang_id.name = so.name
                else:
                    so.referensi_timbang_id.name = so.client_order_ref
        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    referensi_timbang_id = fields.Many2one('weighbridge.contract', 'Weighbridge Contract')

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if 'order_line' in vals:
            product_timbang = self.sudo().env['weighbridge.product'].search([])
            if product_timbang and product_timbang.mapped('related_product_id').ids:
                product_timbang = product_timbang.mapped('related_product_id').ids
                purchase_product = res.order_line.mapped('product_id').ids
                if (res.name or res.partner_ref) and list(set(product_timbang) & set(purchase_product)):
                    new_ref =  self.sudo().env['weighbridge.contract'].create({'name': res.partner_ref or res.name, 
                            'related_purchase_id': res.id, 'trans_type': 'purchase'})
                    res.referensi_timbang_id = new_ref.id
        return res

    @api.multi
    def write(self, update_vals):
        res = super(PurchaseOrder, self).write(update_vals)
        for po in self:
            if 'partner_ref' in update_vals.keys() and po.referensi_timbang_id:
                if update_vals['partner_ref'] == '':
                    po.referensi_timbang_id.name = po.name
                else:
                    po.referensi_timbang_id.name = po.partner_ref
        return res


class PickingType(models.Model):
    _name = 'weighbridge.picking.type'
    _description = "Picking Type"
    _order = "id desc"

    name = fields.Char('TIMBANG TIPETRANS')
    trans_type = fields.Selection([('purchase','Pembelian'),('sale','Penjualan'),('internal', 'Internal')], string='Jenis Transaksi')
    related_picking_type_id = fields.Many2one('stock.picking.type', 'Odoo Picking Type')
    without_contract = fields.Boolean('Tanpa Link ke Kontrak')