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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
import urllib3
from lxml import etree
import time

import logging
_logger = logging.getLogger(__name__)

class WeighbridgeScaleMetro(models.Model):
    _name = "weighbridge.scale.metro"
    _description = "Timbangan"
    _order = "id desc"

    create_to_odoo_model = fields.Boolean('Need Odoo Model', default=False, help='Flag that indicate this data need to be created as Odoo Picking')
    update_to_odoo_model = fields.Boolean('Update Odoo Model', default=False, help='Flag that indicate the Picking should be updated based on this data')
    delete_to_odoo_model = fields.Boolean('Deletion Update Odoo Model', default=False, help='Flag that indicate the Picking should be updated by canceling it based on this data')
    cannot_be_updated = fields.Boolean('Cannot Update Odoo Model', default=False, help='Flag that indicate the Picking should be updated by canceling it based on this data')
    state = fields.Selection([('to_create', 'To be Created'),
        ('to_update', 'To be Updated'),('cannot_be_updated', 'Need Manual Update'),
        ('to_delete', 'To be Deleted'),('done','Synchronized')], compute='_get_state', string='State', store=True)

    wb_picking_type_id = fields.Many2one('weighbridge.picking.type', 'Converter Picking Type')
    picking_type_id = fields.Many2one('stock.picking.type', related='wb_picking_type_id.related_picking_type_id', string='Picking Type')
    wb_product_id = fields.Many2one('weighbridge.product', 'Converter Product')
    product_id = fields.Many2one('product.product', related='wb_product_id.related_product_id', string='Product', domain=[('product_type','=','stockable')])
    wb_partner_id = fields.Many2one('weighbridge.partner', 'Converter Partner')
    partner_id = fields.Many2one('res.partner', related='wb_partner_id.related_partner_id', string='Partner')
    wb_transporter_id = fields.Many2one('weighbridge.partner', 'Converter Transporter')
    transporter_id = fields.Many2one('res.partner', related='wb_transporter_id.related_partner_id', string='Transporter', required=True)
    wb_contract_id = fields.Many2one('weighbridge.contract', 'Converter Contract')
    # partner_id = fields.Many2one('res.partner', related='wb_contract_id.related_partner_id', string='Partner')
    
    picking_ids = fields.Many2many('stock.picking', 'weighbridge_metro_picking_rel', 'weighbridge_id', 'picking_id', string='Pickings')
    invoiced = fields.Boolean('Invoiced')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

    name = fields.Char(related='TIMBANG_NO', readonly=True)
    src_machine = fields.Char('Source Machine', required=True)
    TIMBANG_NO = fields.Char(string='TIMBANG NO', required=True)
    TIMBANG_RECSTS = fields.Char(string='TIMBANG RECSTS')
    TIMBANG_NOKENDARAAN = fields.Char(string='TIMBANG NOKENDARAAN')
    TIMBANG_JENISTIMBANG = fields.Char(string='TIMBANG JENISTIMBANG')
    TIMBANG_TIPETRANS = fields.Char(string='TIMBANG TIPETRANS')
    TIMBANG_PRODUK = fields.Char(string='TIMBANG PRODUK')
    TIMBANG_RELASI = fields.Char(string='TIMBANG RELASI')
    TIMBANG_TRANSPORTER = fields.Char(string='TIMBANG TRANSPORTER')
    TIMBANG_SUPIR = fields.Char(string='TIMBANG SUPIR')
    TIMBANG_KONTRAK = fields.Char(string='TIMBANG KONTRAK')
    TIMBANG_DO = fields.Char(string='TIMBANG DO')
    TIMBANG_NETTOPKS = fields.Float(string='TIMBANG NETTOPKS', digits=(15,2))
    TIMBANG_SORTASI = fields.Float(string='TIMBANG SORTASI', digits=(15,2))
    TIMBANG_NOSEGEL = fields.Char(string='TIMBANG NOSEGEL')
    TIMBANG_FFA = fields.Float(string='TIMBANG FFA', digits=(15,2))
    TIMBANG_MOISTURE = fields.Float(string='TIMBANG MOISTURE', digits=(15,2))
    TIMBANG_DIRTY = fields.Float(string='TIMBANG DIRTY', digits=(15,2))
    TIMBANG_SUHU = fields.Float(string='TIMBANG SUHU', digits=(15,2))
    TIMBANG_IN_WEIGHT = fields.Float(string='TIMBANG IN WEIGHT', digits=(15,2))
    TIMBANG_IN_DATE = fields.Date(string='TIMBANG IN DATE')
    # TIMBANG_IN_TIME = fields.Time(string='TIMBANG IN TIME')
    TIMBANG_IN_TIMESTAMP = fields.Datetime(string='TIMBANG IN TIMESTAMP')
    TIMBANG_IN_USERLOG = fields.Char(string='TIMBANG IN USERLOG')
    TIMBANG_OUT_WEIGHT = fields.Float(string='TIMBANG OUT WEIGHT', digits=(15,2))
    TIMBANG_OUT_DATE = fields.Date(string='TIMBANG OUT DATE')
    # TIMBANG_OUT_TIME = fields.Time(string='TIMBANG OUT TIME')
    TIMBANG_OUT_TIMESTAMP = fields.Datetime(string='TIMBANG OUT TIMESTAMP')
    TIMBANG_OUT_USERLOG = fields.Char(string='TIMBANG OUT USERLOG')
    TIMBANG_BERATNETTO = fields.Float(string='TIMBANG BERATNETTO', digits=(15,2))
    TIMBANG_POTONGAN = fields.Float(string='TIMBANG POTONGAN', digits=(15,2))
    TIMBANG_TOTALBERAT = fields.Float(string='TIMBANG TOTALBERAT', digits=(15,2))
    prev_totalberat = fields.Float(string='Prev. Total Berat', digits=(15,2))
    TIMBANG_TIMESTAMPDELETE = fields.Datetime(string='TIMBANG TIMESTAMPDELETE')
    TIMBANG_USERLOGDELETE = fields.Char(string='TIMBANG USERLOGDELETE')
    TIMBANG_KETERANGAN = fields.Char(string='TIMBANG KETERANGAN')
    TIMBANG_GUID = fields.Char(string='TIMBANG GUID')
    TIMBANG_TIMESTAMPEDIT = fields.Datetime(string='TIMBANG TIMESTAMPEDIT')
    TIMBANG_USERLOGEDIT = fields.Char(string='TIMBANG USERLOGEDIT')
    TIMBANG_ISGENERATED = fields.Char(string='TIMBANG ISGENERATED')
    TIMBANG_OUT_BERAPAKALI_AUDIT = fields.Integer(string='TIMBANG OUT BERAPAKALI AUDIT')
    TIMBANG_IN_WEIGHT_AUDIT = fields.Float(string='TIMBANG IN WEIGHT AUDIT', digits=(15,2))
    TIMBANG_OUT_WEIGHT_AUDIT = fields.Float(string='TIMBANG OUT WEIGHT AUDIT', digits=(15,2))
    TIMBANG_BERATNETTO_AUDIT = fields.Float(string='TIMBANG BERATNETTO AUDIT', digits=(15,2))
    TIMBANG_POTONGAN_AUDIT = fields.Float(string='TIMBANG POTONGAN AUDIT', digits=(15,2))
    TIMBANG_TOTALBERAT_AUDIT = fields.Float(string='TIMBANG TOTALBERAT AUDIT', digits=(15,2))
    TIMBANG_OUT_TIMESTAMP_AUDIT = fields.Datetime(string='TIMBANG OUT TIMESTAMP AUDIT')
    TIMBANG_OUT_USERLOG_AUDIT = fields.Char(string='TIMBANG OUT USERLOG AUDIT')
    TIMBANG_CETAK = fields.Integer(string='TIMBANG CETAK')
    TIMBANG_PECAHKONTRAKDO = fields.Integer(string='TIMBANG PECAHKONTRAKDO')
    TIMBANG_ASALKONTRAK = fields.Char(string='TIMBANG ASALKONTRAK')
    TIMBANG_ASALDO = fields.Char(string='TIMBANG ASALDO')
    TIMBANG_ASALTOTALBERAT = fields.Float(string='TIMBANG ASALTOTALBERAT', digits=(15,2))
    TIMBANG_ASALKELEBIHANBERAT = fields.Float(string='TIMBANG ASALKELEBIHANBERAT', digits=(15,2))
    TIMBANG_LASTUPLOAD = fields.Datetime(string='TIMBANG LASTUPLOAD')
    # CONTRACT INFORMATION
    KONTRAK_NO = fields.Char(string='KONTRAK NO')
    KONTRAK_RECSTS = fields.Char(string='KONTRAK RECSTS')
    KONTRAK_TANGGAL = fields.Date(string='KONTRAK TANGGAL')
    KONTRAK_PRODUK = fields.Char(string='KONTRAK PRODUK')
    KONTRAK_KUALITAS = fields.Char(string='KONTRAK KUALITAS')
    KONTRAK_RELASI = fields.Char(string='KONTRAK RELASI')
    KONTRAK_QUANTITY = fields.Float(string='KONTRAK QUANTITY', digits=(15,2))
    KONTRAK_EXTRAQTY = fields.Float(string='KONTRAK EXTRAQTY', digits=(15,2))
    KONTRAK_EXTRAPROSEN = fields.Float(string='KONTRAK EXTRAPROSEN', digits=(15,2))
    KONTRAK_KETERANGAN = fields.Char(string='KONTRAK KETERANGAN')
    KONTRAK_TIMESTAMP = fields.Datetime(string='KONTRAK TIMESTAMP')
    KONTRAK_USERLOG = fields.Char(string='KONTRAK USERLOG')
    KONTRAK_TIMESTAMPUPDATE = fields.Datetime(string='KONTRAK TIMESTAMPUPDATE')
    KONTRAK_USERLOGUPDATE = fields.Char(string='KONTRAK USERLOGUPDATE')
    KONTRAK_TIMESTAMPDELETE = fields.Datetime(string='KONTRAK TIMESTAMPDELETE')
    KONTRAK_USERLOGDELETE = fields.Char(string='KONTRAK USERLOGDELETE')
    KONTRAK_GUID = fields.Char(string='KONTRAK GUID')
    KONTRAK_TIMESTAMPFINISH = fields.Datetime(string='KONTRAK TIMESTAMPFINISH')
    KONTRAK_USERLOGFINISH = fields.Char(string='KONTRAK USERLOGFINISH')
    KONTRAK_LASTUPLOAD = fields.Datetime(string='KONTRAK LASTUPLOAD')
    KONTRAK_BC_MTU = fields.Char(string='KONTRAK BC MTU')
    KONTRAK_BC_HARGA = fields.Float(string='KONTRAK_BC_HARGA', digits=(15,2))
    KONTRAK_BC_JENISDOKUMEN = fields.Char(string='KONTRAK_BC_JENISDOKUMEN')
    KONTRAK_BC_NOMORPABEAN = fields.Char(string='KONTRAK_BC_NOMORPABEAN')
    KONTRAK_BC_TANGGALPABEAN = fields.Date(string='KONTRAK_BC_TANGGALPABEAN')
    KONTRAK_BC_NOMORBUKTI = fields.Char(string='KONTRAK_BC_NOMORBUKTI')
    KONTRAK_BC_TANGGALBUKTI = fields.Date(string='KONTRAK_BC_TANGGALBUKTI')
    KONTRAK_BC_USERLOG = fields.Char(string='KONTRAK_BC_USERLOG')
    KONTRAK_BC_TIMESTAMP = fields.Datetime(string='KONTRAK_BC_TIMESTAMP')
    KONTRAK_BC_FLAG = fields.Integer(string='KONTRAK_BC_FLAG')
    
    valid = fields.Boolean('Valid', default=False, help='Already Checked from recapitulation')
    internal_quality_ffa = fields.Float('Free Fatid Acid (FFA)')
    internal_quality_ka = fields.Float('Kadar Air (KA)')
    internal_quality_kk = fields.Float('Kadar Kotor (KK)')
    vendor_quality_ffa = fields.Float('Free Fatid Acid (FFA)')
    vendor_quality_ka = fields.Float('Kadar Air (KA)')
    vendor_quality_kk = fields.Float('Kadar Kotor (KK)')
    bruto_pks = fields.Float('Partner Bruto')
    tarra_pks = fields.Float('Partner Tarra')

    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('TIMBANG_NO', 'unique("TIMBANG_NO",src_machine,company_id)', 'Tiket Timbang already Exist')
    ]

    @api.multi
    @api.depends('create_to_odoo_model', 'update_to_odoo_model', 'delete_to_odoo_model', 'cannot_be_updated')
    def _get_state(self):
        for timbang in self:
            if timbang.create_to_odoo_model:
                timbang.state='to_create'
            elif timbang.update_to_odoo_model:
                timbang.state='to_update'
            elif timbang.delete_to_odoo_model:
                timbang.state='to_delete'
            elif timbang.cannot_be_updated:
                timbang.state='cannot_be_updated'
            else:
                timbang.state='done'

    @api.model
    def create(self, vals):
        if 'TIMBANG_IN_TIMESTAMP' in vals.keys():
            try:
                vals['TIMBANG_IN_TIMESTAMP'] = (datetime.strptime(vals['TIMBANG_IN_TIMESTAMP'],"%Y-%m-%d %H:%M:%S.%f") - relativedelta(hours=+7)).strftime(DT)
            except:
                vals['TIMBANG_IN_TIMESTAMP'] = (datetime.strptime(vals['TIMBANG_IN_TIMESTAMP'], "%Y-%m-%d %H:%M:%S") - relativedelta(hours=+7)).strftime(DT)
        if 'TIMBANG_OUT_TIMESTAMP' in vals.keys():
            try:
                vals['TIMBANG_OUT_TIMESTAMP'] = (datetime.strptime(vals['TIMBANG_OUT_TIMESTAMP'],"%Y-%m-%d %H:%M:%S.%f") - relativedelta(hours=+7)).strftime(DT)
            except:
                vals['TIMBANG_OUT_TIMESTAMP'] = (datetime.strptime(vals['TIMBANG_OUT_TIMESTAMP'],"%Y-%m-%d %H:%M:%S") - relativedelta(hours=+7)).strftime(DT)
        return super(WeighbridgeScaleMetro, self).create(vals)

    @api.multi
    def force_update_contract(self, new_contract):
        self.ensure_one()
        _logger.info('::::::::::::::::::: Update Kontrak dari Synchronized Timbang No. %s'%self.TIMBANG_NO)
        if self.picking_type_id.code=='outgoing':
            prev_sale_order = self.wb_contract_id.related_sale_id
            sale_order = new_contract.related_sale_id
            if not sale_order or sale_order.state not in ('sale','done'):
                return False
            procurement_group = sale_order.procurement_group_id
            if not procurement_group:
                proc_vals = sale_order._prepare_procurement_group()
                procurement_group = self.env["procurement.group"].create(proc_vals)
                sale_order.procurement_group_id = procurement_group.id
            sale_order_line = False
            for x in sale_order.order_line:
                if x.product_id.id==self.product_id.id:
                    sale_order_line = x
                    break
            if not sale_order_line:
                return False
            sale_line = sale_order_line.ensure_one()
            procurement_line_id = self.env['procurement.order'].search([('sale_line_id','=',sale_line.id)], order='id desc', limit=1)
            if not procurement_line_id:
                vals = sale_line._prepare_order_line_procurement(group_id=sale_line.order_id.procurement_group_id.id)
                vals['product_qty'] = sale_line.product_uom_qty
                procurement_line_id = self.env["procurement.order"].create(vals)

            try:
                for move in self.picking_ids.mapped('move_lines'):
                    move.sudo().write({
                        'procurement_id':procurement_line_id and procurement_line_id.id or False,
                        'group_id': procurement_group.id,
                        })
                for pick in self.picking_ids:
                    pick.sudo().write({
                        'partner_id': sale_order.partner_id.id,
                        'group_id': procurement_group.id,
                        'bea_cukai_ids': self.wb_picking_type_id.kawasan_berikat and sale_order.bea_cukai_id and [(6,0,[sale_order.bea_cukai_id.id])] or [],
                        })
            except:
                return False
            for xsol in prev_sale_order.order_line:
                xsol.sudo().qty_delivered = xsol._get_delivered_qty()
            sale_line.sudo().qty_delivered = sale_line._get_delivered_qty()
        elif self.picking_type_id.code=='incoming':
            prev_purchase_order = self.wb_contract_id.related_purchase_id
            purchase_order = new_contract.related_purchase_id
            if not purchase_order or purchase_order.state not in ('purchase','done'):
                return False
            purchase_line = False
            for x in purchase_order.order_line:
                if x.product_id.id==self.product_id.id:
                    purchase_line = x
                    break
            if not purchase_line:
                return False
            purchase_line = purchase_line.ensure_one()
            try:
                for move in self.picking_ids.mapped('move_lines'):
                    move.purchase_line_id.sudo().qty_received = move.purchase_line_id.qty_received - move.product_uom_qty
                    purchase_line.sudo().qty_received = purchase_line.qty_received + move.product_uom_qty

                    new_price = purchase_line._get_stock_move_price_unit()
                    move.sudo().write({
                        'purchase_line_id': purchase_line.id,
                        'price_unit': new_price,
                        })
                    for amove in move.sudo().mapped('account_move_line_ids').mapped('move_id'):
                        if True:
                            if amove.state!='draft':
                                amove.sudo().button_cancel()
                                amove.sudo().partner_id = purchase_order.partner_id.id
                                for m in amove.line_ids:
                                    if m.debit > 0.0:
                                        m.with_context(check_move_validity=False).sudo().write({
                                            'debit': new_price*m.quantity,
                                            'partner_id': purchase_order.partner_id.id,
                                            })
                                    elif m.credit > 0.0:
                                        m.with_context(check_move_validity=False).sudo().write({
                                            'credit': new_price*m.quantity,
                                            'partner_id': purchase_order.partner_id.id,
                                            })
                                amove.sudo().post()
                            else:
                                amove.sudo().partner_id = purchase_order.partner_id.id
                                for m in amove.line_ids:
                                    if m.debit > 0.0:
                                        m.with_context(check_move_validity=False).sudo().write({
                                            'debit': new_price*m.quantity,
                                            'partner_id': purchase_order.partner_id.id,
                                            })
                                    elif m.credit > 0.0:
                                        m.with_context(check_move_validity=False).sudo().write({
                                            'credit': new_price*m.quantity,
                                            'partner_id': purchase_order.partner_id.id,
                                            })
                        else:
                            _logger.warning('Failed to update Journal')
                for pick in self.picking_ids:
                    pick.sudo().write({
                        'partner_id': purchase_order.partner_id.id,
                        'origin': purchase_order.name,
                        'bea_cukai_ids': self.wb_picking_type_id.kawasan_berikat and purchase_order.bea_cukai_id and [(6,0,[purchase_order.bea_cukai_id.id])] or [],
                        })
            except:
                return False
        self.wb_contract_id = new_contract.id
        return True

    @api.multi
    def write(self, update_vals):
        WbPickingType = self.env['weighbridge.picking.type'].sudo()
        WbProduct = self.env['weighbridge.product'].sudo()
        for timbang in self:
            if 'TIMBANG_IN_TIMESTAMP' in update_vals.keys():
                try:
                    update_vals['TIMBANG_IN_TIMESTAMP'] = (datetime.strptime(update_vals['TIMBANG_IN_TIMESTAMP'], "%Y-%m-%d %H:%M:%S.%f") - relativedelta(hours=+7)).strftime(DT)
                except:
                    update_vals['TIMBANG_IN_TIMESTAMP'] = (datetime.strptime(update_vals['TIMBANG_IN_TIMESTAMP'], "%Y-%m-%d %H:%M:%S") - relativedelta(hours=+7)).strftime(DT)
            if 'TIMBANG_OUT_TIMESTAMP' in update_vals.keys():
                try:
                    update_vals['TIMBANG_OUT_TIMESTAMP'] = (datetime.strptime(update_vals['TIMBANG_OUT_TIMESTAMP'], "%Y-%m-%d %H:%M:%S.%f") - relativedelta(hours=+7)).strftime(DT)
                except:
                    update_vals['TIMBANG_OUT_TIMESTAMP'] = (datetime.strptime(update_vals['TIMBANG_OUT_TIMESTAMP'], "%Y-%m-%d %H:%M:%S") - relativedelta(hours=+7)).strftime(DT)

            if 'TIMBANG_TIPETRANS' in update_vals.keys() and timbang.TIMBANG_TIPETRANS != update_vals.get(
                    'TIMBANG_TIPETRANS'):
                if timbang.picking_ids:
                    update_vals.update({'cannot_be_updated': True, 'update_to_odoo_model': False})
                else:
                    wb_picking_type = WbPickingType.search([('name', '=', update_vals.get('TIMBANG_TIPETRANS'))])
                    if wb_picking_type:
                        update_vals.update({'wb_picking_type_id': wb_picking_type.id})
                    else:
                        update_vals.update({'wb_picking_type_id': False})
            if 'TIMBANG_PRODUK' in update_vals.keys() and timbang.TIMBANG_PRODUK != update_vals.get('TIMBANG_PRODUK'):
                if timbang.picking_ids:
                    update_vals.update({'cannot_be_updated': True, 'update_to_odoo_model': False})
                else:
                    wb_product = WbProduct.search([('name', '=', update_vals.get('TIMBANG_PRODUK'))])
                    if wb_product:
                        update_vals.update({'wb_product_id': wb_product.id})
                    else:
                        update_vals.update({'wb_product_id': False})

            if timbang.picking_ids:
                picking_to_update = {}
                ########## Perubahan Informasi Penting ############
                # >> Update Kontrak
                if 'TIMBANG_KONTRAK' in update_vals.keys() and timbang.TIMBANG_KONTRAK!=update_vals.get('TIMBANG_KONTRAK'):
                    # proses update link kontrak
                    wb_kontrak = WbContract.search([('name','=',update_vals.get('TIMBANG_KONTRAK'))])
                    if not wb_kontrak:
                        update_vals.update({'cannot_be_updated': True, 'update_to_odoo_model': False})
                    else:
                        res = timbang.force_update_contract(wb_kontrak)
                        if not res:
                            update_vals.update({'cannot_be_updated': True, 'update_to_odoo_model': False})
                # >> Update Quantity
                if 'TIMBANG_TOTALBERAT' in update_vals.keys() and timbang.TIMBANG_TOTALBERAT!=update_vals.get('TIMBANG_TOTALBERAT'):
                    update_vals.update({'prev_totalberat': timbang.TIMBANG_TOTALBERAT})
                # >> Update Tanggal
                if 'TIMBANG_OUT_TIMESTAMP' in update_vals.keys() and timbang.TIMBANG_OUT_TIMESTAMP!=update_vals.get('TIMBANG_OUT_TIMESTAMP'):
                    picking_to_update.update({'date_done': update_vals['TIMBANG_OUT_TIMESTAMP']})
                    timbang.picking_ids.mapped('move_lines').sudo().write({'date': update_vals['TIMBANG_OUT_TIMESTAMP']})
                    if timbang.picking_type_id.code=='incoming':
                        timbang.picking_ids.mapped('move_lines').mapped('quant_ids').sudo().write({'in_date' : update_vals['TIMBANG_OUT_TIMESTAMP']})
                        if 'TIMBANG_OUT_DATE' in update_vals.keys() and timbang.TIMBANG_OUT_DATE != update_vals.get('TIMBANG_OUT_DATE'):
                            for amove in timbang.picking_ids.mapped('move_lines').sudo().mapped('account_move_line_ids').mapped('move_id'):
                                try:
                                    if amove.state!='draft':
                                        amove.sudo().button_cancel()
                                        amove.sudo().write({'date' : update_vals['TIMBANG_OUT_DATE']})
                                        amove.sudo().post()
                                    else:
                                        amove.sudo().write({'date' : update_vals['TIMBANG_OUT_DATE']})
                                except:
                                    _logger.warning('Failed to update Journal')
                
                ########## Perubahan Informasi Tambahan saja ############
                # >> Ganti Transporter, ganti linknya Transporternya, ganti Transporter di Pickingnya
                if 'TIMBANG_TRANSPORTER' in update_vals.keys() and timbang.TIMBANG_TRANSPORTER!=update_vals.get('TIMBANG_TRANSPORTER'):
                    transporter = self.env['weighbridge.partner'].search([('name','=',update_vals['TIMBANG_TRANSPORTER'])])
                    if transporter:
                        timbang.wb_transporter_id = transporter[0].id
                        picking_to_update.update({'transporter_id': transporter[0].related_partner_id.id})
                elif ('wb_transporter_id' in update_vals.keys() and timbang.wb_transporter_id.id!=update_vals.get('wb_transporter_id')):
                    transporter = self.env['weighbridge.partner'].browse(update_vals['wb_transporter_id'])
                    if transporter:
                        picking_to_update.update({'transporter_id': transporter.related_partner_id.id})
                
                # >> Ganti Nomer Kendaraan dan Supir, langsung eksekusi
                if 'TIMBANG_SUPIR' in update_vals.keys() and timbang.TIMBANG_SUPIR!=update_vals.get('TIMBANG_SUPIR'):
                    picking_to_update.update({'driver_name': update_vals['TIMBANG_SUPIR']})
                if 'TIMBANG_NOKENDARAAN' in update_vals.keys() and timbang.TIMBANG_NOKENDARAAN!=update_vals.get('TIMBANG_NOKENDARAAN'):
                    picking_to_update.update({'vehicle_number': update_vals['TIMBANG_NOKENDARAAN']})
                # >> Ganti Bruto Tarra QC, lansung eksekusi di Pickingnya
                if 'internal_quality_ffa' in update_vals.keys() and timbang.internal_quality_ffa!=update_vals.get('internal_quality_ffa'):
                    picking_to_update.update({'internal_quality_ffa': update_vals['internal_quality_ffa']})
                if 'internal_quality_kk' in update_vals.keys() and timbang.internal_quality_kk!=update_vals.get('internal_quality_kk'):
                    picking_to_update.update({'internal_quality_kk': update_vals['internal_quality_kk']})
                if 'internal_quality_ka' in update_vals.keys() and timbang.internal_quality_ka!=update_vals.get('internal_quality_ka'):
                    picking_to_update.update({'internal_quality_ka': update_vals['internal_quality_ka']})
                if 'vendor_quality_ffa' in update_vals.keys() and timbang.vendor_quality_ffa!=update_vals.get('vendor_quality_ffa'):
                    picking_to_update.update({'vendor_quality_ffa': update_vals['vendor_quality_ffa']})
                if 'vendor_quality_kk' in update_vals.keys() and timbang.vendor_quality_kk!=update_vals.get('vendor_quality_kk'):
                    picking_to_update.update({'vendor_quality_kk': update_vals['vendor_quality_kk']})
                if 'vendor_quality_ka' in update_vals.keys() and timbang.vendor_quality_ka!=update_vals.get('vendor_quality_ka'):
                    picking_to_update.update({'vendor_quality_ka': update_vals['vendor_quality_ka']})

                for picking in timbang.picking_ids:
                    picking.write(picking_to_update)
        return super(WeighbridgeScaleMetro, self).write(update_vals)

    @api.multi
    def set_weighbridge_picking_type(self):
        WbPickingType = self.env['weighbridge.picking.type'].sudo()
        PickingType = self.env['stock.picking.type'].sudo()

        for tipe_transaksi in self.mapped('TIMBANG_TIPETRANS'):
            wb_picking_type = WbPickingType.search([('name','=',tipe_transaksi)])
            if wb_picking_type:
                self.filtered(lambda x: x.TIMBANG_TIPETRANS==tipe_transaksi).write({'wb_picking_type_id': wb_picking_type.id})
            else:
                continue

    @api.multi
    def set_weighbridge_product(self):
        Product = self.env['product.product'].sudo()
        WbProduct = self.env['weighbridge.product'].sudo()

        for product_name in self.mapped('TIMBANG_PRODUK'):
            wb_product = WbProduct.search([('name','=',product_name)])
            if wb_product:
                self.filtered(lambda x: x.TIMBANG_PRODUK==product_name).write({'wb_product_id': wb_product.id})
            else:
                continue

    @api.multi
    def set_weighbridge_partner(self):
        Partner = self.env['res.partner'].sudo()
        WbPartner = self.env['weighbridge.partner'].sudo()

        for relasi_name in self.mapped('TIMBANG_RELASI'):
            wb_partner = WbPartner.search([('name','=',relasi_name)])
            if wb_partner:
                self.filtered(lambda x: x.TIMBANG_RELASI==relasi_name).write({'wb_partner_id': wb_partner.id})
            else:
                continue
    
    @api.multi
    def set_weighbridge_transporter(self):
        Partner = self.env['res.partner'].sudo()
        WbPartner = self.env['weighbridge.partner'].sudo()
        
        for relasi_name in self.mapped('TIMBANG_TRANSPORTER'):
            wb_partner = WbPartner.search([('name','=',relasi_name)])
            if wb_partner:
                self.filtered(lambda x: x.TIMBANG_TRANSPORTER==relasi_name).write({'wb_transporter_id': wb_partner.id})
            else:
                continue

    @api.multi
    def set_weighbridge_contract(self):
        WbContract = self.env['weighbridge.contract'].sudo()

        for kontrak in self.mapped('TIMBANG_KONTRAK'):
            wb_kontrak = WbContract.search([('name','=',kontrak)])
            if wb_kontrak:
                self.filtered(lambda x: x.TIMBANG_KONTRAK==kontrak).write({'wb_contract_id': wb_kontrak.id})
            else:
                continue

    @api.model
    def _sync_timbang_to_master(self):
        #################################### FILL ODOO FIELD #################################
        _logger.info('================START: Converting Field Timbang to Odoo')
        empty_picking_type = self.search([('wb_picking_type_id','=',False)], limit=40)
        # empty_picking_type = self.search([('wb_picking_type_id','=',False)])
        empty_picking_type.set_weighbridge_picking_type()

        empty_product = self.search([('wb_product_id','=',False)], limit=40)
        # empty_product = self.search([('wb_product_id','=',False)])
        empty_product.set_weighbridge_product()
        
        empty_partner = self.search([('wb_partner_id','=',False)], limit=40)
        # empty_partner = self.search([('wb_partner_id','=',False)])
        empty_partner.set_weighbridge_partner()
        
        empty_transporter = self.search([('wb_transporter_id','=',False)], limit=40)
        # empty_transporter = self.search([('wb_transporter_id','=',False)])
        empty_transporter.set_weighbridge_transporter()
        
        # empty_contract = self.search([('wb_contract_id','=',False)], limit=40)
        # empty_contract = self.search([('wb_contract_id','=',False)])
        # empty_contract.set_weighbridge_contract()
        _logger.info('================END: Converting Field Timbang to Odoo')

    def _prepare_sale_move(self, timbang, sale_line, picking):
        procurement_line_id = False
        if sale_line:
            procurement_line_id = self.env['procurement.order'].search([('sale_line_id','=',sale_line.id)], order='id desc', limit=1)
            if not procurement_line_id:
                vals = sale_line._prepare_order_line_procurement(group_id=sale_line.order_id.procurement_group_id.id)
                vals['product_qty'] = sale_line.product_uom_qty
                procurement_line_id = self.env["procurement.order"].create(vals)
        return {
            'picking_id': picking.id,
            'name': sale_line and sale_line.name or timbang.product_id.name,
            'company_id': timbang.company_id.id,
            'product_id': timbang.product_id.id,
            'product_uom_qty': timbang.TIMBANG_TOTALBERAT,
            'product_uom': timbang.product_id.uom_id.id,
            'warehouse_id': timbang.picking_type_id.warehouse_id.id,
            'location_id': timbang.picking_type_id.default_location_src_id.id,
            'location_dest_id': timbang.partner_id.property_stock_customer.id,
            'procurement_id': procurement_line_id and procurement_line_id.id or False,
            'group_id': sale_line and sale_line.order_id.procurement_group_id.id or False,
            'picking_type_id': procurement_line_id and procurement_line_id.rule_id.picking_type_id.id or False,
            'state': 'draft',

            'netto_pks': timbang.TIMBANG_NETTOPKS,
            'gross_weight': timbang.TIMBANG_IN_WEIGHT,
            'tara_weight': timbang.TIMBANG_OUT_WEIGHT,
            'net_weight': timbang.TIMBANG_BERATNETTO,
            'potongan_weight': timbang.TIMBANG_POTONGAN,
            }

    def _prepare_purchase_move(self, timbang, purchase_line, picking):
        return {
            'company_id': timbang.company_id.id,
            'name': purchase_line and purchase_line.name or timbang.product_id.name,
            'picking_id': picking.id,
            'product_id': timbang.product_id.id,
            'product_uom_qty': timbang.TIMBANG_TOTALBERAT,
            'product_uom': timbang.product_id.uom_id.id,
            'warehouse_id': timbang.picking_type_id.warehouse_id.id,
            'location_id': timbang.partner_id.property_stock_supplier.id,
            'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
            'picking_type_id': timbang.picking_type_id.id,
            'partner_id': timbang.partner_id.id,
            'state': 'draft',

            'netto_pks': timbang.TIMBANG_NETTOPKS,
            'gross_weight': timbang.TIMBANG_IN_WEIGHT,
            'tara_weight': timbang.TIMBANG_OUT_WEIGHT,
            'net_weight': timbang.TIMBANG_BERATNETTO,
            'potongan_weight': timbang.TIMBANG_POTONGAN,

            'purchase_line_id': purchase_line and purchase_line.id or False,
            'price_unit': purchase_line and purchase_line._get_stock_move_price_unit() or 0.0,
            'procurement_id': False,
            }

    def _prepare_transfer_move(self, timbang, picking):
        return {
            'company_id': picking.company_id.id,
            'name': timbang.product_id.name,
            'picking_id': picking.id,
            'product_id': timbang.product_id.id,
            'product_uom_qty': timbang.TIMBANG_TOTALBERAT,
            'product_uom': timbang.product_id.uom_id.id,
            'warehouse_id': timbang.picking_type_id.warehouse_id.id,
            'location_id': timbang.picking_type_id.default_location_src_id.id,
            'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
            'picking_type_id': timbang.picking_type_id.id,
            'partner_id': timbang.partner_id.id,
            'state': 'draft',

            'netto_pks': timbang.TIMBANG_NETTOPKS,
            'gross_weight': timbang.TIMBANG_IN_WEIGHT,
            'tara_weight': timbang.TIMBANG_OUT_WEIGHT,
            'net_weight': timbang.TIMBANG_BERATNETTO,
            'potongan_weight': timbang.TIMBANG_POTONGAN,

            'purchase_line_id': False,
            'price_unit': timbang.product_id.standard_price,
            'procurement_id': False,
            }

    @api.multi
    def do_create_new_picking_without_contract(self):
        Picking = self.env['stock.picking']
        res = self.env['stock.picking']
        StockMove = self.env['stock.move']
        for timbang in sorted(self, key=lambda x: (x.picking_type_id.code=='incoming' and 0 or 1, x.TIMBANG_OUT_TIMESTAMP)):
            if timbang.picking_ids:
                continue
            if timbang.TIMBANG_RECSTS=='D':
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'delete_to_odoo_model': False})
                continue

            try:
            # if True:
                if timbang.picking_type_id.code=='incoming':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Receipt'%timbang.TIMBANG_NO)
                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.partner_id.property_stock_supplier.id,
                        'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'company_id': timbang.company_id.id,
                        'state': 'draft',

                        'transporter_id': timbang.transporter_id.id,
                        'tiket_timbang': timbang.TIMBANG_NO,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                        })
                    StockMove.create(self._prepare_purchase_move(timbang, False, new_picking))
                elif timbang.picking_type_id.code=='outgoing':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Delivery'%timbang.TIMBANG_NO)
                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.picking_type_id.default_location_src_id.id,
                        'location_dest_id': timbang.partner_id.property_stock_customer.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'group_id': False,
                        'company_id': timbang.company_id.id,
                        'state': 'draft',

                        'tiket_timbang': timbang.TIMBANG_NO,
                        'transporter_id': timbang.transporter_id.id,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                        })
                    new_move = StockMove.create(self._prepare_sale_move(timbang, False, new_picking))
                elif timbang.picking_type_id.code=='internal':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Transfer' % timbang.TIMBANG_NO)
                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.picking_type_id.default_location_src_id.id,
                        'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'origin': False,
                        'company_id': timbang.company_id.id,
                        'state': 'draft',

                        'transporter_id': timbang.transporter_id.id,
                        'tiket_timbang': timbang.TIMBANG_NO,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                    })
                    StockMove.create(self._prepare_transfer_move(timbang, new_picking))

                new_picking.action_done()
                res |= new_picking
                # UPDATE TANGGAL TRANSAKSI
                for move in new_picking.move_lines:
                    move.sudo().date = timbang.TIMBANG_OUT_TIMESTAMP
                    if timbang.picking_type_id.code=='incoming':
                        move.quant_ids.sudo().write({'in_date' : timbang.TIMBANG_OUT_TIMESTAMP})
                        for amove in move.sudo().account_move_line_ids.mapped('move_id'):
                            try:
                                if amove.sudo().state!='draft':
                                    amove.sudo().button_cancel()
                                    amove.sudo().write({'date': timbang.TIMBANG_OUT_DATE})
                                    amove.sudo().post()
                                else:
                                    amove.sudo().write({'date': timbang.TIMBANG_OUT_DATE})
                            except:
                                _logger.warning('Failed to update Journal')
                new_picking.date_done = timbang.TIMBANG_OUT_TIMESTAMP
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'picking_ids': [(4,new_picking.id)]})
            except:
                _logger.warning('================Fail to Convert Timbang %s'%timbang.TIMBANG_NO)
                continue

        return res

    @api.multi
    def do_create_new_picking(self):
        Picking = self.env['stock.picking']
        res = self.env['stock.picking']
        StockMove = self.env['stock.move']
        for timbang in sorted(self, key=lambda x: (x.picking_type_id.code=='incoming' and 0 or 1, x.TIMBANG_OUT_TIMESTAMP)):
            if timbang.picking_ids:
                continue
            if timbang.TIMBANG_RECSTS=='D':
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'delete_to_odoo_model': False})
                continue

            try:
            # if True:
                if timbang.picking_type_id.code=='incoming':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Receipt'%timbang.TIMBANG_NO)
                    purchase_order = timbang.wb_contract_id.related_purchase_id
                    if not purchase_order or purchase_order.state not in ('purchase','done'):
                        continue
                    purchase_line = purchase_order.order_line.filtered(lambda x: x.product_id.id==timbang.product_id.id)
                    purchase_line = False
                    for x in purchase_order.order_line:
                        if x.product_id.id==timbang.product_id.id:
                            purchase_line = x
                            break
                    if not purchase_line:
                        continue
                    purchase_line = purchase_line.ensure_one()

                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.partner_id.property_stock_supplier.id,
                        'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'origin': purchase_order.name,
                        'company_id': timbang.company_id.id,
                        'state': 'draft',

                        'transporter_id': timbang.transporter_id.id,
                        'tiket_timbang': timbang.TIMBANG_NO,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                        })
                    StockMove.create(self._prepare_purchase_move(timbang, purchase_line, new_picking))
                elif timbang.picking_type_id.code=='outgoing':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Delivery'%timbang.TIMBANG_NO)
                    sale_order = timbang.wb_contract_id.related_sale_id
                    if not sale_order or sale_order.state not in ('sale','done'):
                        continue
                    procurement_group = sale_order.procurement_group_id
                    if not procurement_group:
                        proc_vals = sale_order._prepare_procurement_group()
                        procurement_group = self.env["procurement.group"].create(proc_vals)
                        sale_order.procurement_group_id = procurement_group.id
                    # sale_order_line = sale_order.order_line.filtered(lambda x: x.product_id.id==timbang.product_id.id)
                    sale_order_line = False
                    for x in sale_order.order_line:
                        if x.product_id.id==timbang.product_id.id:
                            sale_order_line = x
                            break
                    if not sale_order_line:
                        continue
                    sale_order_line = sale_order_line.ensure_one()

                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.picking_type_id.default_location_src_id.id,
                        'location_dest_id': timbang.partner_id.property_stock_customer.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'group_id': procurement_group.id,
                        'company_id': sale_order.company_id.id,
                        'state': 'draft',

                        'tiket_timbang': timbang.TIMBANG_NO,
                        'transporter_id': timbang.transporter_id.id,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                        })
                    new_move = StockMove.create(self._prepare_sale_move(timbang, sale_order_line, new_picking))
                elif timbang.picking_type_id.code=='internal':
                    _logger.info('::::::::::::::::::: Converting Timbang %s to Transfer' % timbang.TIMBANG_NO)
                    new_picking = Picking.create({
                        'partner_id': timbang.partner_id.id,
                        'picking_type_id': timbang.picking_type_id.id,
                        'location_id': timbang.picking_type_id.default_location_src_id.id,
                        'location_dest_id': timbang.picking_type_id.default_location_dest_id.id,
                        'date_done': timbang.TIMBANG_OUT_TIMESTAMP,
                        'origin': False,
                        'company_id': timbang.company_id.id,
                        'state': 'draft',

                        'transporter_id': timbang.transporter_id.id,
                        'tiket_timbang': timbang.TIMBANG_NO,
                        'driver_name': timbang.TIMBANG_SUPIR,
                        'vehicle_number': timbang.TIMBANG_NOKENDARAAN,
                    })
                    StockMove.create(self._prepare_transfer_move(timbang, new_picking))

                new_picking.action_done()
                res |= new_picking
                # UPDATE TANGGAL TRANSAKSI
                for move in new_picking.move_lines:
                    move.sudo().date = timbang.TIMBANG_OUT_TIMESTAMP
                    if timbang.picking_type_id.code=='incoming':
                        move.quant_ids.sudo().write({'in_date' : timbang.TIMBANG_OUT_TIMESTAMP})
                        for amove in move.sudo().account_move_line_ids.mapped('move_id'):
                            try:
                                if amove.sudo().state!='draft':
                                    amove.sudo().button_cancel()
                                    amove.sudo().write({'date': timbang.TIMBANG_OUT_DATE})
                                    amove.sudo().post()
                                else:
                                    amove.sudo().write({'date': timbang.TIMBANG_OUT_DATE})
                            except:
                                _logger.warning('Failed to update Journal')
                new_picking.date_done = timbang.TIMBANG_OUT_TIMESTAMP
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'picking_ids': [(4,new_picking.id)]})
            except:
                _logger.warning('================Fail to Convert Timbang %s'%timbang.TIMBANG_NO)
                continue
        return res

    @api.multi
    def do_update_picking(self):
        Picking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        Quant = self.env['stock.quant']
        for timbang in sorted(self, key=lambda x: (x.picking_type_id.code == 'incoming' and 0 or 1, x.TIMBANG_OUT_TIMESTAMP)):
            # karena sudah dibuat diatas, maka di skip saja
            if timbang.create_to_odoo_model:
                continue
            if timbang.TIMBANG_RECSTS=='D':
                continue
            if not timbang.picking_ids:
                continue
            picking = timbang.picking_ids[0]
            move_line = False
            for x in picking.move_lines:
                if x.product_id.id==timbang.product_id.id:
                    move_line = x
            if not move_line:
                continue
            # 1. perubahan qty
            # qty jadi lebih kecil
            try:
                _logger.info('::::::::::::::::::: Update Timbang %s Pickings'%timbang.TIMBANG_NO)
                # 1. perubahan qty
                # qty jadi lebih kecil
                if timbang.prev_totalberat and timbang.TIMBANG_TOTALBERAT<timbang.prev_totalberat:
                    diff_qty = timbang.prev_totalberat - timbang.TIMBANG_TOTALBERAT
                    if timbang.picking_type_id.code=='incoming':
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT, 'state': 'done'})
                        # cari di quant yg ada sekarang
                        quant_available = move_line.quant_ids.filtered(lambda x: x.location_id.usage=='internal' and x.qty>0)
                        quants_move_sudo = self.env['stock.quant'].sudo()
                        if quant_available:
                            for quant in quant_available:
                                quant._quant_split(diff_qty)
                                quants_move_sudo |= quant
                                diff_qty -= quant.qty
                        if diff_qty:
                            preferred_domain_list = [[('reservation_id', '=', move_line.id)], [('reservation_id', '=', False)], \
                                                     ['&', ('reservation_id', '!=', move_line.id), ('reservation_id', '!=', False)]]
                            quants = Quant.quants_get_preferred_domain(
                                diff_qty, move_line, domain=[('qty', '>', 0)],
                                preferred_domain_list=preferred_domain_list)
                            for quant, qty in quants:
                                if not quant:
                                    #If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                                    quant = Quant.with_context(force_reverse_move=True)._quant_create_from_move(
                                        qty, move_line, lot_id=False, owner_id=False, 
                                        src_package_id=False, dest_package_id=False, 
                                        force_location_from=False, force_location_to=move_line.location_id)
                                    # create negative move
                                    neg_vals = {
                                        'product_id': move_line.product_id.id,
                                        'location_id': move_line.location_dest_id.id,
                                        'qty': -qty,
                                        'cost': move_line.get_price_unit(),
                                        'history_ids': [(4, move_line.id)],
                                        'in_date': datetime.now().strftime(DF),
                                        'company_id': move_line.company_id.id,
                                        'negative_move_id': move_line.id,
                                    }
                                    quant_negative = Quant.sudo().create(neg_vals)
                                    quant.propagated_from_id = quant_negative.id
                                else:
                                    quant._quant_split(qty)
                                    quants_move_sudo |= quant
                                quants_reconcile_sudo |= quant
                        if quants_move_sudo:
                            quants_move_sudo.with_context(force_reverse_move=True)._quant_update_from_move(move_line, \
                                            move_line.location_id, False, lot_id=False, entire_pack=False)
                    elif timbang.picking_type_id.code=='outgoing':
                        # bikin stock quant baru untuk memasukkan barang yg tadi dikembalikan
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT})
                        move_line.procurement_id.sale_line_id.qty_delivered = move_line.procurement_id.sale_line_id._get_delivered_qty()
                        reservation = [(False, diff_qty)]
                        quant = self.env['stock.quant']._quant_create_from_move(
                            diff_qty, move_line, lot_id=False, owner_id=False, 
                            src_package_id=False, dest_package_id=False, 
                            force_location_from=move_line.location_dest_id, 
                            force_location_to=move_line.location_id)
                        ######## ketika membuat quant pemasukan tambahan, 
                        ######## otomatis jurnal tambahannya jg terbuat
                        quants_reconcile_sudo |= quant
                # qty jadi lebih besar
                elif timbang.prev_totalberat and timbang.TIMBANG_TOTALBERAT>timbang.prev_totalberat:
                    diff_qty = timbang.TIMBANG_TOTALBERAT - timbang.prev_totalberat
                    if timbang.picking_type_id.code=='incoming':
                        # bikin stock quant baru yg blom teralokasikan
                        quant = self.env['stock.quant']._quant_create_from_move(
                            diff_qty, move_line, lot_id=False, owner_id=False, 
                            src_package_id=False, dest_package_id=False, 
                            force_location_from=move_line.location_id, 
                            force_location_to=move_line.location_dest_id)
                        ######## ketika membuat quant pemasukan tambahan, 
                        ######## otomatis jurnal tambahannya jg terbuat
                        quants_reconcile_sudo |= quant
                        # update stok move, quantity nya dinaikin
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT, 'state': 'done'})
                    elif timbang.picking_type_id.code=='outgoing':
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT})
                        move_line.procurement_id.sale_line_id.qty_delivered = move_line.procurement_id.sale_line_id._get_delivered_qty()
                        # cari di quant yg ada sekarang
                        preferred_domain_list = [[('reservation_id', '=', move_line.id)], [('reservation_id', '=', False)], \
                                    ['&', ('reservation_id', '!=', move_line.id), ('reservation_id', '!=', False)]]
                        quants = Quant.quants_get_preferred_domain(
                            diff_qty, move_line, domain=[('qty', '>', 0)],
                            preferred_domain_list=preferred_domain_list)
                        Quant.quants_move(
                            quants, move_line, move_line.location_dest_id,
                            lot_id=move_line.restrict_lot_id.id, owner_id=move_line.restrict_partner_id.id)

                if quants_reconcile_sudo and move_line.location_dest_id.usage=='internal':
                    self._cr.execute("""
                        SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                        ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                    """, (move_line.product_id.id, move_line.location_dest_id.parent_left,
                          move_line.location_dest_id.parent_right, move_line.location_dest_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)
                elif quants_reconcile_sudo and move_line.location_id.usage=='internal':
                    self._cr.execute("""
                        SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                        ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                    """, (move_line.product_id.id, move_line.location_id.parent_left,
                          move_line.location_id.parent_right, move_line.location_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)

                if timbang.picking_type_id.code=='incoming':
                    move_line.quant_ids.sudo().write({'in_date' : timbang.TIMBANG_OUT_TIMESTAMP})
                    for amove in move_line.sudo().account_move_line_ids.mapped('move_id'):
                        try:
                            if amove.state!='draft':
                                amove.button_cancel()
                                amove.write({'date': timbang.TIMBANG_OUT_DATE})
                                amove.post()
                            else:
                                amove.write({'date': timbang.TIMBANG_OUT_DATE})
                        except:
                            _logger.warning('Failed to update Journal')

                # 3. perubahan kontrak dan partner
                timbang.write({'update_to_odoo_model': False, 'prev_totalberat': 0.0})
            except:
                _logger.info('::::::::::::::::::: Fail to Update Timbang %s Pickings'%timbang.TIMBANG_NO)
                continue

    @api.multi
    def do_update_picking_without_contract(self):
        Picking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        Quant = self.env['stock.quant']
        for timbang in sorted(self, key=lambda x: (x.picking_type_id.code == 'incoming' and 0 or 1, x.TIMBANG_OUT_TIMESTAMP)):
            # karena sudah dibuat diatas, maka di skip saja
            if timbang.create_to_odoo_model:
                continue
            if timbang.TIMBANG_RECSTS=='D':
                continue
            if not timbang.picking_ids:
                continue
            picking = timbang.picking_ids[0]
            move_line = False
            for x in picking.move_lines:
                if x.product_id.id==timbang.product_id.id:
                    move_line = x
            if not move_line:
                continue
            # 1. perubahan qty
            # qty jadi lebih kecil
            try:
                _logger.info('::::::::::::::::::: Update Timbang %s Pickings'%timbang.TIMBANG_NO)
                # 1. perubahan qty
                # qty jadi lebih kecil
                if timbang.prev_totalberat and timbang.TIMBANG_TOTALBERAT<timbang.prev_totalberat:
                    diff_qty = timbang.prev_totalberat - timbang.TIMBANG_TOTALBERAT
                    if timbang.picking_type_id.code=='incoming':
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT, 'state': 'done'})
                        # cari di quant yg ada sekarang
                        quant_available = move_line.quant_ids.filtered(lambda x: x.location_id.usage=='internal' and x.qty>0)
                        quants_move_sudo = self.env['stock.quant'].sudo()
                        if quant_available:
                            for quant in quant_available:
                                quant._quant_split(diff_qty)
                                quants_move_sudo |= quant
                                diff_qty -= quant.qty
                        if diff_qty:
                            preferred_domain_list = [[('reservation_id', '=', move_line.id)], [('reservation_id', '=', False)], \
                                                     ['&', ('reservation_id', '!=', move_line.id), ('reservation_id', '!=', False)]]
                            quants = Quant.quants_get_preferred_domain(
                                diff_qty, move_line, domain=[('qty', '>', 0)],
                                preferred_domain_list=preferred_domain_list)
                            for quant, qty in quants:
                                if not quant:
                                    #If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                                    quant = Quant.with_context(force_reverse_move=True)._quant_create_from_move(
                                        qty, move_line, lot_id=False, owner_id=False, 
                                        src_package_id=False, dest_package_id=False, 
                                        force_location_from=False, force_location_to=move_line.location_id)
                                    # create negative move
                                    neg_vals = {
                                        'product_id': move_line.product_id.id,
                                        'location_id': move_line.location_dest_id.id,
                                        'qty': -qty,
                                        'cost': move_line.get_price_unit(),
                                        'history_ids': [(4, move_line.id)],
                                        'in_date': datetime.now().strftime(DF),
                                        'company_id': move_line.company_id.id,
                                        'negative_move_id': move_line.id,
                                    }
                                    quant_negative = Quant.sudo().create(neg_vals)
                                    quant.propagated_from_id = quant_negative.id
                                else:
                                    quant._quant_split(qty)
                                    quants_move_sudo |= quant
                                quants_reconcile_sudo |= quant
                        if quants_move_sudo:
                            quants_move_sudo.with_context(force_reverse_move=True)._quant_update_from_move(move_line, \
                                            move_line.location_id, False, lot_id=False, entire_pack=False)
                    elif timbang.picking_type_id.code=='outgoing':
                        # bikin stock quant baru untuk memasukkan barang yg tadi dikembalikan
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT})
                        # move_line.procurement_id.sale_line_id.qty_delivered = move_line.procurement_id.sale_line_id._get_delivered_qty()
                        reservation = [(False, diff_qty)]
                        quant = self.env['stock.quant']._quant_create_from_move(
                            diff_qty, move_line, lot_id=False, owner_id=False, 
                            src_package_id=False, dest_package_id=False, 
                            force_location_from=move_line.location_dest_id, 
                            force_location_to=move_line.location_id)
                        ######## ketika membuat quant pemasukan tambahan, 
                        ######## otomatis jurnal tambahannya jg terbuat
                        quants_reconcile_sudo |= quant
                # qty jadi lebih besar
                elif timbang.prev_totalberat and timbang.TIMBANG_TOTALBERAT>timbang.prev_totalberat:
                    diff_qty = timbang.TIMBANG_TOTALBERAT - timbang.prev_totalberat
                    if timbang.picking_type_id.code=='incoming':
                        # bikin stock quant baru yg blom teralokasikan
                        quant = self.env['stock.quant']._quant_create_from_move(
                            diff_qty, move_line, lot_id=False, owner_id=False, 
                            src_package_id=False, dest_package_id=False, 
                            force_location_from=move_line.location_id, 
                            force_location_to=move_line.location_dest_id)
                        ######## ketika membuat quant pemasukan tambahan, 
                        ######## otomatis jurnal tambahannya jg terbuat
                        quants_reconcile_sudo |= quant
                        # update stok move, quantity nya dinaikin
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT, 'state': 'done'})
                    elif timbang.picking_type_id.code=='outgoing':
                        move_line.write({'product_uom_qty': timbang.TIMBANG_TOTALBERAT})
                        # move_line.procurement_id.sale_line_id.qty_delivered = move_line.procurement_id.sale_line_id._get_delivered_qty()
                        # cari di quant yg ada sekarang
                        preferred_domain_list = [[('reservation_id', '=', move_line.id)], [('reservation_id', '=', False)], \
                                    ['&', ('reservation_id', '!=', move_line.id), ('reservation_id', '!=', False)]]
                        quants = Quant.quants_get_preferred_domain(
                            diff_qty, move_line, domain=[('qty', '>', 0)],
                            preferred_domain_list=preferred_domain_list)
                        Quant.quants_move(
                            quants, move_line, move_line.location_dest_id,
                            lot_id=move_line.restrict_lot_id.id, owner_id=move_line.restrict_partner_id.id)

                if quants_reconcile_sudo and move_line.location_dest_id.usage=='internal':
                    self._cr.execute("""
                        SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                        ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                    """, (move_line.product_id.id, move_line.location_dest_id.parent_left,
                          move_line.location_dest_id.parent_right, move_line.location_dest_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)
                elif quants_reconcile_sudo and move_line.location_id.usage=='internal':
                    self._cr.execute("""
                        SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                        ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                    """, (move_line.product_id.id, move_line.location_id.parent_left,
                          move_line.location_id.parent_right, move_line.location_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)

                if timbang.picking_type_id.code=='incoming':
                    move_line.quant_ids.sudo().write({'in_date' : timbang.TIMBANG_OUT_TIMESTAMP})
                    for amove in move_line.sudo().account_move_line_ids.mapped('move_id'):
                        try:
                            if amove.state!='draft':
                                amove.button_cancel()
                                amove.write({'date': timbang.TIMBANG_OUT_DATE})
                                amove.post()
                            else:
                                amove.write({'date': timbang.TIMBANG_OUT_DATE})
                        except:
                            _logger.warning('Failed to update Journal')

                # 3. perubahan kontrak dan partner
                timbang.write({'update_to_odoo_model': False, 'prev_totalberat': 0.0})
            except:
                _logger.info('::::::::::::::::::: Fail to Update Timbang %s Pickings'%timbang.TIMBANG_NO)
                continue

    @api.multi
    def do_cancel_picking(self):
        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        Quant = self.env['stock.quant']
        for timbang in self:
            if not timbang.picking_ids:
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'delete_to_odoo_model': False})
                continue

            picking = timbang.picking_ids[0]
            move_line = False
            for x in picking.move_lines:
                if x.product_id.id == timbang.product_id.id:
                    move_line = x
            if not move_line:
                continue
            if (not move_line.product_uom_qty) or move_line.product_uom_qty==0.0:
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False,
                        'delete_to_odoo_model': False})
                continue

            try:
                _logger.info('::::::::::::::::::: Return Timbang %s Pickings'%timbang.TIMBANG_NO)
                cancel_qty = timbang.TIMBANG_TOTALBERAT
                if timbang.picking_type_id.code == 'incoming':
                    move_line.write({'product_uom_qty': 0.0, 'state': 'done'})
                    # cari di quant yg ada sekarang
                    quant_available = move_line.quant_ids.filtered(
                        lambda x: x.location_id.usage == 'internal' and x.qty > 0)
                    quants_move_sudo = self.env['stock.quant'].sudo()
                    if quant_available:
                        for quant in quant_available:
                            quant._quant_split(cancel_qty)
                            quants_move_sudo |= quant
                            cancel_qty -= quant.qty
                    if cancel_qty:
                        preferred_domain_list = [[('reservation_id', '=', move_line.id)],
                                                 [('reservation_id', '=', False)],
                                                 ['&', ('reservation_id', '!=', move_line.id),
                                                  ('reservation_id', '!=', False)]]
                        quants = Quant.quants_get_preferred_domain(
                            cancel_qty, move_line, domain=[('qty', '>', 0)],
                            preferred_domain_list=preferred_domain_list)
                        for quant, qty in quants:
                            if not quant:
                                # If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                                quant = Quant.with_context(force_reverse_move=True)._quant_create_from_move(
                                    qty, move_line, lot_id=False, owner_id=False,
                                    src_package_id=False, dest_package_id=False,
                                    force_location_from=False, force_location_to=move_line.location_id)
                                # create negative move
                                neg_vals = {
                                    'product_id': move_line.product_id.id,
                                    'location_id': move_line.location_dest_id.id,
                                    'qty': -qty,
                                    'cost': move_line.get_price_unit(),
                                    'history_ids': [(4, move_line.id)],
                                    'in_date': datetime.now().strftime(DF),
                                    'company_id': move_line.company_id.id,
                                    'negative_move_id': move_line.id,
                                }
                                quant_negative = Quant.sudo().create(neg_vals)
                                quant.propagated_from_id = quant_negative.id
                            else:
                                quant._quant_split(qty)
                                quants_move_sudo |= quant
                            quants_reconcile_sudo |= quant
                    if quants_move_sudo:
                        quants_move_sudo.with_context(force_reverse_move=True)._quant_update_from_move(move_line,
                                    move_line.location_id, False, lot_id=False, entire_pack=False)
                elif timbang.picking_type_id.code == 'outgoing':
                    # bikin stock quant baru untuk memasukkan barang yg tadi dikembalikan
                    move_line.write({'product_uom_qty': 0.0})
                    quant = self.env['stock.quant']._quant_create_from_move(
                        cancel_qty, move_line, lot_id=False, owner_id=False,
                        src_package_id=False, dest_package_id=False,
                        force_location_from=move_line.location_dest_id,
                        force_location_to=move_line.location_id)
                    ######## ketika membuat quant pemasukan tambahan,
                    ######## otomatis jurnal tambahannya jg terbuat
                    quants_reconcile_sudo |= quant

                    self._cr.execute("""
                            SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                            ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                        """, (move_line.product_id.id, move_line.location_id.parent_left,
                              move_line.location_id.parent_right, move_line.location_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)
                timbang.write({'delete_to_odoo_model': False, 'prev_totalberat': 0.0})
            except:
                _logger.info('::::::::::::::::::: Fail to Return Timbang %s Pickings'%timbang.TIMBANG_NO)

    @api.multi
    def do_cancel_picking_without_contract(self):
        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        Quant = self.env['stock.quant']
        for timbang in self:
            if not timbang.picking_ids:
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False, 
                    'delete_to_odoo_model': False})
                continue

            picking = timbang.picking_ids[0]
            move_line = False
            for x in picking.move_lines:
                if x.product_id.id == timbang.product_id.id:
                    move_line = x
            if not move_line:
                continue
            if (not move_line.product_uom_qty) or move_line.product_uom_qty==0.0:
                timbang.write({'create_to_odoo_model': False, 'update_to_odoo_model': False,
                        'delete_to_odoo_model': False})
                continue

            try:
                _logger.info('::::::::::::::::::: Return Timbang %s Pickings'%timbang.TIMBANG_NO)
                cancel_qty = timbang.TIMBANG_TOTALBERAT
                if timbang.picking_type_id.code == 'incoming':
                    move_line.write({'product_uom_qty': 0.0, 'state': 'done'})
                    # cari di quant yg ada sekarang
                    quant_available = move_line.quant_ids.filtered(
                        lambda x: x.location_id.usage == 'internal' and x.qty > 0)
                    quants_move_sudo = self.env['stock.quant'].sudo()
                    if quant_available:
                        for quant in quant_available:
                            quant._quant_split(cancel_qty)
                            quants_move_sudo |= quant
                            cancel_qty -= quant.qty
                    if cancel_qty:
                        preferred_domain_list = [[('reservation_id', '=', move_line.id)],
                                                 [('reservation_id', '=', False)],
                                                 ['&', ('reservation_id', '!=', move_line.id),
                                                  ('reservation_id', '!=', False)]]
                        quants = Quant.quants_get_preferred_domain(
                            cancel_qty, move_line, domain=[('qty', '>', 0)],
                            preferred_domain_list=preferred_domain_list)
                        for quant, qty in quants:
                            if not quant:
                                # If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                                quant = Quant.with_context(force_reverse_move=True)._quant_create_from_move(
                                    qty, move_line, lot_id=False, owner_id=False,
                                    src_package_id=False, dest_package_id=False,
                                    force_location_from=False, force_location_to=move_line.location_id)
                                # create negative move
                                neg_vals = {
                                    'product_id': move_line.product_id.id,
                                    'location_id': move_line.location_dest_id.id,
                                    'qty': -qty,
                                    'cost': move_line.get_price_unit(),
                                    'history_ids': [(4, move_line.id)],
                                    'in_date': datetime.now().strftime(DF),
                                    'company_id': move_line.company_id.id,
                                    'negative_move_id': move_line.id,
                                }
                                quant_negative = Quant.sudo().create(neg_vals)
                                quant.propagated_from_id = quant_negative.id
                            else:
                                quant._quant_split(qty)
                                quants_move_sudo |= quant
                            quants_reconcile_sudo |= quant
                    if quants_move_sudo:
                        quants_move_sudo.with_context(force_reverse_move=True)._quant_update_from_move(move_line,
                                    move_line.location_id, False, lot_id=False, entire_pack=False)
                elif timbang.picking_type_id.code == 'outgoing':
                    # bikin stock quant baru untuk memasukkan barang yg tadi dikembalikan
                    move_line.write({'product_uom_qty': 0.0})
                    quant = self.env['stock.quant']._quant_create_from_move(
                        cancel_qty, move_line, lot_id=False, owner_id=False,
                        src_package_id=False, dest_package_id=False,
                        force_location_from=move_line.location_dest_id,
                        force_location_to=move_line.location_id)
                    ######## ketika membuat quant pemasukan tambahan,
                    ######## otomatis jurnal tambahannya jg terbuat
                    quants_reconcile_sudo |= quant

                    self._cr.execute("""
                            SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                            ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                        """, (move_line.product_id.id, move_line.location_id.parent_left,
                              move_line.location_id.parent_right, move_line.location_id.id))
                    if self._cr.fetchone():
                        quants_reconcile_sudo._quant_reconcile_negative(move_line)
                timbang.write({'delete_to_odoo_model': False, 'prev_totalberat': 0.0})
            except:
                _logger.info('::::::::::::::::::: Fail to Return Timbang %s Pickings'%timbang.TIMBANG_NO)

    @api.model
    def _sync_timbang_to_picking(self):
        _logger.info('================START: Converting Timbang to Picking')
        ################################ TIMBANG TO PICKING ##################################
        # CREATE NEW PICKING
        # untuk pembelian TBS, tidak pakai PO, 
        # jadi untuk sementara smua Purchase via timbangan langsung masuk tanpa link ke PO
        timbang_to_create1 = self.search([('create_to_odoo_model','=',True), \
            ('wb_picking_type_id','!=',False), ('wb_picking_type_id.without_contract','=',True), \
            ('wb_partner_id','!=',False),('wb_product_id','!=',False)], limit=20, order='TIMBANG_OUT_TIMESTAMP asc')
        timbang_to_create1.do_create_new_picking_without_contract()
        # sedangkan ini untuk handling penjualan
        timbang_to_create2 = self.search([('create_to_odoo_model', '=', True), \
             ('wb_picking_type_id', '!=', False), ('wb_picking_type_id.without_contract','=',False), \
             ('wb_partner_id','!=',False), ('wb_product_id', '!=', False)], limit=20, order='TIMBANG_OUT_TIMESTAMP asc')
        timbang_to_create2.do_create_new_picking()

        # UPDATE CURRENT PICKING
        # ini untuk handling revisi timbangan atas transaksi pembelian yg mana POnya tidak ada
        timbang_to_update1 = self.search([('update_to_odoo_model','=',True), ('wb_picking_type_id.without_contract','=',True), \
            ('create_to_odoo_model','=',False), ('wb_contract_id','=',False)], limit=50, order='TIMBANG_OUT_TIMESTAMP asc')
        timbang_to_update1.do_update_picking_without_contract()
        # ini untuk handling revisi timbangan penjualan
        timbang_to_update2 = self.search([('update_to_odoo_model','=',True), ('wb_picking_type_id.without_contract','=',False), \
            ('create_to_odoo_model','=',False)], limit=50, order='TIMBANG_OUT_TIMESTAMP asc')
        timbang_to_update2.do_update_picking()

        # CREATE CANCEL PICKING
        timbang_to_cancel1 = self.search([('delete_to_odoo_model','=',True), ('wb_picking_type_id.without_contract','=',True), \
            ('wb_contract_id','=',False)])
        timbang_to_cancel1.do_cancel_picking_without_contract()
        timbang_to_cancel2 = self.search([('delete_to_odoo_model','=',True), ('wb_picking_type_id.without_contract','=',False)])
        timbang_to_cancel2.do_cancel_picking()
        _logger.info('================END: Converting Timbang to Picking')