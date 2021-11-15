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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError

class MetroWeighbridgeRecapitulation(models.TransientModel):
    _name = 'wizard.weighbridge.recap.metro'
    _description = 'Rekapitulasi Timbangan Metro'

    wb_picking_type_id = fields.Many2one('weighbridge.picking.type', string='Tipe Transaksi', required=True)
    trans_type = fields.Selection([('purchase','Pembelian'),('sale','Penjualan')], string='Jenis Transaksi')
    partner_id = fields.Many2one('res.partner', 'Partner')
    sale_id = fields.Many2one('sale.order', 'Odoo Sale Order')
    purchase_id = fields.Many2one('purchase.order', 'Odoo Purchase Order')
    target_data = fields.Selection([('validated','Valid'),('draft','Belum Valid'),('all','Semua Data')], string='Target Data', required=True, default='all')
    line_ids = fields.One2many('weighbridge.recap.metro.line', 'wizard_id', 'Data Timbangan')
    start_date = fields.Date('Dari Tanggal')
    stop_date = fields.Date('Sampai Tanggal')
    vehicle_no = fields.Char('No. Kendaraan')

    @api.onchange('wb_picking_type_id')
    def _onchange_wb_picking_type_id(self):
        if self.wb_picking_type_id and self.wb_picking_type_id.trans_type:
            self.trans_type = self.wb_picking_type_id.trans_type
            self.partner_id = False
            self.sale_id = False
            self.purchase_id = False
            partner_domain = [('supplier','=',True)] if self.trans_type=='purchase' else [('customer','=',True)]
            return {'domain': {'partner_id': partner_domain}}

    @api.multi
    def generate_data_timbang(self):
        self.ensure_one()
        for x in self.line_ids:
            x.unlink()

        WeighbridgeScale = self.env['weighbridge.scale.metro'].sudo()
        WeighbridgeRecapLine = self.env['weighbridge.recap.metro.line']

        default_domain = [('wb_picking_type_id','=',self.wb_picking_type_id.id),('TIMBANG_RECSTS','=','F'),'|',('active','=',True),('active','=',False)]

        if self.partner_id:
            default_domain.extend([('wb_contract_id.related_partner_id','=',self.partner_id.id)])
        # else:
            # default_domain.extend([('wb_partner_id','!=',False)])
        
        if self.target_data=='validated':
            default_domain.extend([('valid','=',True)])
        elif self.target_data=='draft':
            default_domain.extend([('valid','=',False)])

        if self.purchase_id:
            default_domain.extend([('wb_contract_id.trans_type','=',self.trans_type), \
                    ('wb_contract_id.related_purchase_id','=',self.purchase_id.id)])
        elif self.sale_id:
            default_domain.extend([('wb_contract_id.trans_type','=',self.trans_type), \
                    ('wb_contract_id.related_sale_id','=',self.sale_id.id)])

        if self.vehicle_no and self.vehicle_no.strip():
            default_domain.extend([('TIMBANG_NOKENDARAAN','ilike',self.vehicle_no.strip())])

        if self.start_date:
            default_domain.extend([('TIMBANG_OUT_DATE','>=',self.start_date)])
        if self.stop_date:
            default_domain.extend([('TIMBANG_OUT_DATE','<=',self.stop_date)])

        if self._context.get('beacukai'):
            default_domain.extend([('picking_ids', '!=', False)])

        data_timbang = WeighbridgeScale.search(default_domain)
        for line in data_timbang:
            if self._context.get('beacukai'):
                if not line.picking_ids:
                    continue
                if not line.picking_ids.mapped('bea_cukai_ids'):
                    continue
            WeighbridgeRecapLine.create({
                'wizard_id': self.id,
                'weighbridge_id': line.id,
                'partner_id': line.wb_partner_id.id,
                'transporter_id': line.wb_transporter_id.id,
                'transporter_name': line.TIMBANG_TRANSPORTER,
                'contract_id': line.wb_contract_id.id,
                'driver_name': line.TIMBANG_SUPIR,
                'vehicle_number': line.TIMBANG_NOKENDARAAN,
                'partner_bruto': line.bruto_pks,
                'partner_tarra': line.tarra_pks,
                'partner_netto': line.TIMBANG_NETTOPKS,
                'valid': line.valid,

                'internal_quality_ffa': line.internal_quality_ffa,
                'internal_quality_ka': line.internal_quality_ka,
                'internal_quality_kk': line.internal_quality_kk,
                'vendor_quality_ffa': line.vendor_quality_ffa,
                'vendor_quality_ka': line.vendor_quality_ka,
                'vendor_quality_kk': line.vendor_quality_kk,
                })

    @api.multi
    def mark_as_valid(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError(_('Detail Data Timbangan tidak ditemukan.\nSilahkan tekan Generate Data Timbang terlebih dahulu'))

        for line in self.line_ids:
            line.weighbridge_id.valid = True

    @api.multi
    def print_internal_recap(self):
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : 'rekap_timbangan_internal_metro',
            'datas'         : {
                'model'         : 'wizard.weighbridge.recap.metro',
                'id'            : self.id,
                'ids'           : [self.id],
                'report_type'   : 'xlsx',
                'form'          : {
                    'wizard_metro_id' : self.id,
                },
            },
            'nodestroy': False
        }

    @api.multi
    def print_beacukai_recap(self):
        self.ensure_one()
        date_start = self.start_date or min(self.line_ids.mapped('weighbridge_id.TIMBANG_OUT_DATE'))
        date_stop = self.stop_date or max(self.line_ids.mapped('weighbridge_id.TIMBANG_OUT_DATE'))
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : 'rekap_timbangan_beacukai_metro',
            'datas'         : {
                'model'         : 'wizard.weighbridge.recap.metro',
                'id'            : self.id,
                'ids'           : [self.id],
                'report_type'   : 'pdf',
                'form'          : {
                    'wizard_metro_id' : self.id,
                    'start_date'    : date_start,
                    'stop_date'    : date_stop,
                },
            },
            'nodestroy': False
        }

class MetroWeighbridgeRecapitulationLine(models.TransientModel):
    _name = 'weighbridge.recap.metro.line'
    _description = 'Data Timbangan'

    wizard_id = fields.Many2one('wizard.weighbridge.recap.metro', 'Wizard')
    weighbridge_id = fields.Many2one('weighbridge.scale.metro', 'Tiket', required=True)
    partner_id = fields.Many2one('weighbridge.partner', string='Relasi')
    transporter_id = fields.Many2one('weighbridge.partner', string='Transportir')
    transporter_name = fields.Char(string="Transportir")
    contract_id = fields.Many2one('weighbridge.contract', string='Kontrak')
    valid = fields.Boolean(string='Valid')
    vehicle_number = fields.Char(string='No. Plat')
    driver_name = fields.Char(string='Supir')
    bruto = fields.Float(string='Bruto', compute='_get_netto', store=True)
    tarra = fields.Float(string='Tarra', compute='_get_netto', store=True)
    netto = fields.Float(string='Netto', compute='_get_netto', store=True)
    partner_bruto = fields.Float(string='Partner Bruto')
    partner_tarra = fields.Float(string='Partner Tarra')
    partner_netto = fields.Float(string='Partner Netto')

    internal_quality_ffa = fields.Float(string='FFA')
    internal_quality_ka = fields.Float(string='KA')
    internal_quality_kk = fields.Float(string='KK')
    vendor_quality_ffa = fields.Float(string='Vendor FFA')
    vendor_quality_ka = fields.Float(string='Vendor KA')
    vendor_quality_kk = fields.Float(string='Vendor KK')

    @api.depends('weighbridge_id')
    def _get_netto(self):
        for line in self:
            if line.weighbridge_id.wb_picking_type_id.trans_type=='purchase':
                line.bruto = line.weighbridge_id.TIMBANG_IN_WEIGHT
                line.tarra = line.weighbridge_id.TIMBANG_OUT_WEIGHT
                line.netto = line.weighbridge_id.TIMBANG_BERATNETTO
            elif line.weighbridge_id.wb_picking_type_id.trans_type=='sale':
                line.bruto = line.weighbridge_id.TIMBANG_OUT_WEIGHT
                line.tarra = line.weighbridge_id.TIMBANG_IN_WEIGHT
                line.netto = line.weighbridge_id.TIMBANG_BERATNETTO

    @api.onchange('partner_bruto')
    def onchange_partner_bruto(self):
        self.ensure_one()
        self.partner_tarra = self.partner_bruto - self.partner_netto

    @api.onchange('partner_tarra')
    def onchange_partner_tarra(self):
        self.ensure_one()
        self.partner_bruto =  self.partner_netto + self.partner_tarra

    @api.multi
    def write(self, update_vals):
        for line in self:
            wb_to_update = {}
            if 'partner_bruto' in update_vals.keys() and line.partner_bruto!=update_vals['partner_bruto']:
                wb_to_update.update({'bruto_pks': update_vals['partner_bruto']})
            if 'partner_tarra' in update_vals.keys() and line.partner_tarra!=update_vals['partner_tarra']:
                wb_to_update.update({'tarra_pks': update_vals['partner_tarra']})
            if 'internal_quality_ffa' in update_vals.keys() and line.internal_quality_ffa!=update_vals['internal_quality_ffa']:
                wb_to_update.update({'internal_quality_ffa': update_vals['internal_quality_ffa']})
            if 'internal_quality_ka' in update_vals.keys() and line.internal_quality_ka!=update_vals['internal_quality_ka']:
                wb_to_update.update({'internal_quality_ka': update_vals['internal_quality_ka']})
            if 'internal_quality_kk' in update_vals.keys() and line.internal_quality_kk!=update_vals['internal_quality_kk']:
                wb_to_update.update({'internal_quality_kk': update_vals['internal_quality_kk']})
            if 'vendor_quality_ffa' in update_vals.keys() and line.vendor_quality_ffa!=update_vals['vendor_quality_ffa']:
                wb_to_update.update({'vendor_quality_ffa': update_vals['vendor_quality_ffa']})
            if 'vendor_quality_ka' in update_vals.keys() and line.vendor_quality_ka!=update_vals['vendor_quality_ka']:
                wb_to_update.update({'vendor_quality_ka': update_vals['vendor_quality_ka']})
            if 'vendor_quality_kk' in update_vals.keys() and line.vendor_quality_kk!=update_vals['vendor_quality_kk']:
                wb_to_update.update({'vendor_quality_kk': update_vals['vendor_quality_kk']})
            if 'valid' in update_vals.keys() and line.valid!=update_vals['valid']:
                wb_to_update.update({'valid': update_vals['valid']})

            line.weighbridge_id.sudo().write(wb_to_update)
        return super(MetroWeighbridgeRecapitulationLine, self).write(update_vals)