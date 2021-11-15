# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Anggar Bagus Kurniawan <anggar.bagus@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
import time
import math

class MillDailySounding(models.Model):
    _name = "mill.daily.sounding"
    _description = "Laporan harian Sounding"
    _rec_name = "date"

    date = fields.Date('Tanggal', required=True)
    tanpa_produksi = fields.Boolean('Tanpa Produksi')
    state = fields.Selection([('draft','Draft'),('approved','Approved')], default='draft')
    sounding_cpo_lines = fields.One2many('mill.daily.sounding.cpo.line', 'sounding_id', string='CPO', copy=True)
    sounding_kernel_lines = fields.One2many('mill.daily.sounding.kernel.line', 'sounding_id', string='Kernel', copy=True)
    oil_losses_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    oil_losses_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    solid_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    solid_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_cake_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_cake_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    wet_nut_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    wet_nut_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    final_effluent_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    final_effluent_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    empty_bunch_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    empty_bunch_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    empty_bunch_ffb_show = fields.Float(related='empty_bunch_ffb',digits=dp.get_precision('Oil Lossess Precentage'))
    total_oil_losses_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'), compute='_compute_total_oil_losses_ffb', store=True)
    total_oil_losses_ffb_show = fields.Float(related='total_oil_losses_ffb', digits=dp.get_precision('Kernel Lossess Precentage'))
    press_1_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_1_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_2_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_2_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_3_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_3_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_4_sample = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    press_4_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'))
    total_press_ffb = fields.Float(digits=dp.get_precision('Oil Lossess Precentage'), compute='_compute_total_press_ffb', store=True)

    # Kernel Losses
    kernel_losses_sample = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    kernel_losses_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    claybath_sample = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    claybath_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    ltds_1_sample = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    ltds_1_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    ltds_2_sample = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    ltds_2_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    f_cyclone_sample = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    f_cyclone_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    total_kernel_losses_ffb = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'), compute='_compute_total_kernel_losses_ffb', store=True)
    total_kernel_losses_ffb_show = fields.Float(related='total_kernel_losses_ffb',digits=dp.get_precision('Kernel Lossess Precentage'))
    moist = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))

    ffa_average = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'), compute='_compute_ffa_average', store=True)
    effective_rippler_mill_1 = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    effective_rippler_mill_2 = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    kotoran_produksi = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    kotoran_bunker = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    kotoran_silo_1 = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    kotoran_silo_2 = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
 

    #TBS
    tbs_in = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    restan = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    total_in_restan = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))

    lori_olah = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    restan_dalam_stelizer = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    restan_depan_stelizer = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    restan_belakang_stelizer = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    loading_ramp = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    total_stelizer = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'), compute='_compute_total_stelizer', store=True)

    kapasitas_lori = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    tbs_olah = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
    hm_ebc = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'),compute='_compute_durasi')
    # throughput = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'), compute='_compute_throughput')

    start_olah_date = fields.Date()
    start_olah_time = fields.Float()
    stop_olah_date = fields.Date()
    stop_olah_time = fields.Float()
    durasi_olah = fields.Integer('Durasi Olah', compute='_compute_durasi')
    karbonat = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))

    keterangan = fields.Text()

    _order = "date desc, id desc"

    @api.depends('start_olah_date', 'start_olah_time', 'stop_olah_date', 'stop_olah_time')
    def _compute_durasi(self):
        for data in self:
            if data.start_olah_date and data.stop_olah_time:
                start_time = datetime.strptime(
                    data.start_olah_date + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(data.start_olah_time * 60, 60))),
                    DT)
                stop_time = datetime.strptime(
                    data.stop_olah_date + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(data.stop_olah_time * 60, 60))),
                    DT)
                diff = stop_time - start_time
                # diff = float(diff.time().hour)+float(diff.time().minute)/60
                hours, seconds = divmod(diff.days * 3600 + diff.seconds, 3600)
                data.durasi_olah = hours
                data.hm_ebc = float(hours)+float((seconds/60)/60.0) 

    # @api.depends('tbs_olah','hm_ebc')
    # def _compute_throughput(self):
    #     if self.tbs_olah and self.durasi_olah:
    #         self.throughput = self.tbs_olah/self.durasi_olah

    @api.depends('solid_ffb','press_cake_ffb','wet_nut_ffb','final_effluent_ffb','empty_bunch_ffb')
    def _compute_total_oil_losses_ffb(self):
        for data in self:
            data.total_oil_losses_ffb = data.solid_ffb + data.press_cake_ffb + data.wet_nut_ffb + data.final_effluent_ffb + data.empty_bunch_ffb

    @api.depends('press_1_ffb','press_2_ffb','press_3_ffb','press_4_ffb')
    def _compute_total_press_ffb(self):
        for data in self:
            data.total_press_ffb = data.press_1_ffb + data.press_2_ffb + data.press_3_ffb + data.press_4_ffb

    @api.depends('claybath_ffb','ltds_1_ffb','ltds_2_ffb','f_cyclone_ffb')
    def _compute_total_kernel_losses_ffb(self):
        for data in self:
            data.total_kernel_losses_ffb = data.claybath_ffb + data.ltds_1_ffb + data.ltds_2_ffb + data.f_cyclone_ffb
            data.total_kernel_losses_ffb_show = data.claybath_ffb + data.ltds_1_ffb + data.ltds_2_ffb + data.f_cyclone_ffb

    @api.depends('sounding_cpo_lines.ffa')
    def _compute_ffa_average(self):
        for data in self:
            if data.sounding_cpo_lines:
                ffa_list = list(data.sounding_cpo_lines.mapped('ffa'))
                data.ffa_average = sum(ffa_list) / len(ffa_list)
            else:
                data.ffa_average = 0.0

    @api.depends('restan_dalam_stelizer','restan_depan_stelizer','restan_belakang_stelizer','loading_ramp')
    def _compute_total_stelizer(self):
        for data in self:
            data.total_stelizer = data.restan_dalam_stelizer + data.restan_depan_stelizer +  data.restan_belakang_stelizer + data.loading_ramp

    @api.multi
    def prepare_cpo_line(self):
        for sounding in self:
            if sounding.state=='approved':
                total_cpo = 0
                lhp_cpo_line = []
                jumlah_real_cm = 0
                jumlah_real_mm = 0
                obj_uom = self.env['product.uom']
                uom_height_cm_id = obj_uom.search([('name','=','cm')])
                uom_height_mm_id = obj_uom.search([('name','=','mm')])
                uom_temperature_id = obj_uom.search([('name','=','Celcius')])
                uom_volume_liter_id = obj_uom.search([('name','=','Kg/Liter')])
                uom_jumlah_id = obj_uom.search([('name','=','Kg')])
                sequence = 1
            
                lhp_ids = self.env['mill.lhp'].search([('sounding_id','=',self.id)])
                if lhp_ids:
                    lhp_ids.lhp_cpo_line.unlink()
                #CPO
                for line in sounding.sounding_cpo_lines.filtered(lambda r: r.storage_id.type=='CPO'):
                    jumlah_real_cm = 0
                    jumlah_real_mm = 0
                    ketinggian = math.modf((line.height+line.storage_id.height))
                    density = self.env['mill.density.chart'].search([('temperature','=', line.temperature)])
                    if not density:
                        raise Warning('Density suhu %s belum di setting' % (line.temperature))

                    table_pengukuran = self.env['mill.storage.measurement'].search([('mill_storage_id','=',line.storage_id.id),
                        ('start_date','<=',sounding.date),
                        ('end_date','>=',sounding.date)])
                    if not table_pengukuran:
                        raise Warning('Table Pengukuran Tangki %s tanggal %s belum di setting!' % (line.storage_id.name, sounding.date))

                    volume_cm = self.env['mill.storage.measurement.cm'].search([('mill_storage_measurement_id','=',table_pengukuran.id),('height','=',ketinggian[1])])
                    if not volume_cm:
                        raise Warning('Volume Cm ketinggian %s tidak ditemukan pada master tabel pengukuran!' % (ketinggian[1]))


                    koreksi_suhu = self.env['mill.koreksi.suhu'].search([('mill_storage_id','=',line.storage_id.id)])
                    if not koreksi_suhu:
                        raise Warning('Koreksi suhu pada tangki %s belum disetting!' % (line.storage_id.name))

                    faktor_koreksi_suhu = ((line.temperature - koreksi_suhu.temperature_calibrated)*koreksi_suhu.faktor_koreksi)+1
                    volume_cm_calibrated = volume_cm.volume*faktor_koreksi_suhu
                    jumlah_real_cm = volume_cm_calibrated*density.density
                    

                
                    # volume cm
                    lhp_cpo_line.append([0,0,{
                        'sequence': sequence,
                        'name': line.storage_id.name,
                        'storage_id': line.storage_id.id,
                        'height': ketinggian[1],
                        'temperature': line.temperature,
                        'uom_height_id': uom_height_cm_id.id,
                        'uom_temperature_id': uom_temperature_id.id,
                        'type': 'cm',
                        'density': density.density,
                        'volume_liter': volume_cm.volume,
                        'uom_volume_liter_id': uom_volume_liter_id.id,
                        'koreksi_suhu': faktor_koreksi_suhu,
                        'jumlah_setelah_koreksi': volume_cm_calibrated,
                        'jumlah': jumlah_real_cm,
                        'uom_jumlah_id': uom_jumlah_id.id,
                        'ffa':line.ffa,
                        }])

                    # volume mm
                    if ketinggian[0]>0.00:
                        volume_mm = self.env['mill.storage.measurement.mm'].search([('mill_storage_measurement_id','=',table_pengukuran.id),
                            ('height_start','<=',ketinggian[1]),
                            ('height_end','>=',ketinggian[1]),
                            ('height','=', round(ketinggian[0]*10,1)),
                            ])
                        if not volume_mm:
                            raise Warning('Volume mm ketinggian cm %s pada ketinggian mm %s tidak ditemukan pada master tabel pengukuran!' % (ketinggian[1], ketinggian[0]))
                        
                        volume_mm_calibrated = volume_mm.volume*faktor_koreksi_suhu
                        jumlah_real_mm = volume_mm_calibrated*density.density
                        lhp_cpo_line.append([0,0,{
                            'sequence': sequence,
                            'name': line.storage_id.name,
                            'storage_id': line.storage_id.id,
                            'height': round(ketinggian[0]*10,1),
                            'temperature': line.temperature,
                            'uom_height_id': uom_height_mm_id.id,
                            'uom_temperature_id': uom_temperature_id.id,
                            'type': 'mm',
                            'density': density.density,
                            'volume_liter': volume_mm.volume,
                            'uom_volume_liter_id': uom_volume_liter_id.id,
                            'koreksi_suhu': faktor_koreksi_suhu,
                            'jumlah_setelah_koreksi': volume_mm_calibrated,
                            'jumlah': jumlah_real_mm,
                            'uom_jumlah_id': uom_jumlah_id.id,
                            'ffa':line.ffa,
                            }])

                    # jumlah
                    lhp_cpo_line.append([0,0,{
                        'sequence': sequence,
                        'type': 'total',
                        'jumlah': jumlah_real_mm+jumlah_real_cm,
                        'uom_jumlah_id': uom_jumlah_id.id,
                        }])
                    total_cpo+=jumlah_real_mm+jumlah_real_cm
                    sequence+=1
                #CST
                for line in sounding.sounding_cpo_lines.filtered(lambda r: r.storage_id.type=='CST'):
                    kg_cm   = 255.04
                    jumlah = (line.height-15)*kg_cm*0.8783
                    lhp_cpo_line.append([0,0,{
                        'sequence': sequence,
                        'name': line.storage_id.name,
                        'storage_id': line.storage_id.id,
                        'height': line.height,
                        'temperature': False,
                        'uom_height_id': uom_height_cm_id.id,
                        'uom_temperature_id':False,
                        'type': 'cm',
                        'density': False,
                        'volume_liter': False,
                        'uom_volume_liter_id': False,
                        'koreksi_suhu': faktor_koreksi_suhu,
                        'jumlah_setelah_koreksi': False,
                        'jumlah': jumlah,
                        'uom_jumlah_id': uom_jumlah_id.id,
                        }])

                    total_cpo+=jumlah
                    sequence+=1
                #OILTANK
                for line in sounding.sounding_cpo_lines.filtered(lambda r: r.storage_id.type=='OILTANK'):
                    kg_cm   = 67.85
                    jumlah = (line.height)*kg_cm*0.8783
                    lhp_cpo_line.append([0,0,{
                        'sequence': sequence,
                        'name': line.storage_id.name,
                        'storage_id': line.storage_id.id,
                        'height': line.height,
                        'temperature': False,
                        'uom_height_id': uom_height_cm_id.id,
                        'uom_temperature_id':False,
                        'type': 'cm',
                        'density': False,
                        'volume_liter': False,
                        'uom_volume_liter_id': False,
                        'koreksi_suhu': faktor_koreksi_suhu,
                        'jumlah_setelah_koreksi': False,
                        'jumlah': jumlah,
                        'uom_jumlah_id': uom_jumlah_id.id,
                        }])

                    total_cpo+=jumlah
                    sequence+=1
                return lhp_cpo_line, total_cpo

    @api.multi
    def prepare_tbs_line(self):
        for sounding in self:
            if sounding.state=='approved':
                lhp_tbs_line = {}
                obj_lhp = self.env['mill.lhp']
                obj_timbangan = self.env['weighbridge.scale.metro']
                tbs_in_brutto = 0
                tbs_in_plasma = 0
                tbs_in_ptpn_netto = 0

                saldo_awal_tbs = obj_lhp.search([('date','<',sounding.date)], order='date desc', limit=1)
                tbs_in = obj_timbangan.search([('TIMBANG_OUT_DATE','=',sounding.date),('TIMBANG_TIPETRANS','=','PEMBELIAN TBS'),('TIMBANG_RECSTS','=','F')])
                tbs_in_ptpn = obj_timbangan.search([('TIMBANG_OUT_DATE','=',sounding.date),('TIMBANG_TIPETRANS','=','TBS PTPN'),('TIMBANG_RECSTS','=','F')])
                for tbs in tbs_in:
                    tbs_in_brutto+=tbs.TIMBANG_BERATNETTO
                    tbs_in_plasma+=tbs.TIMBANG_TOTALBERAT
                
                for tbs_ptpn in tbs_in_ptpn:
                    tbs_in_ptpn_netto+=tbs_ptpn.TIMBANG_TOTALBERAT

                lhp_tbs_line = {
                                'tbs_in_brutto' : tbs_in_brutto,
                                'tbs_in_plasma' : tbs_in_plasma,
                                'saldo_awal_tbs_netto' : saldo_awal_tbs.saldo_akhir_tbs_netto,
                                'saldo_awal_tbs_brutto' : saldo_awal_tbs.saldo_akhir_tbs_brutto,
                                'tbs_in_ptpn' : tbs_in_ptpn_netto,
                }

                return lhp_tbs_line

    @api.multi
    def prepare_kernel_line(self):
        for sounding in self:
            if sounding.state=='approved':
                lhp_kernel_line = []
                sequence = 1
                stock_akhir_gudang = 0
                kernel_in_progress = 0
                total_kernel = 0

                lhp_ids = self.env['mill.lhp'].search([('sounding_id','=',self.id)])
                if lhp_ids:
                    lhp_ids.lhp_kernel_line.unlink()               

                #Kernel-Silo
                for bunker in sounding.sounding_kernel_lines.filtered(lambda r: r.storage_id.type=='SILO'):
                    height = bunker.storage_id.height
                    sample_height = (bunker.height_1+bunker.height_2+bunker.height_3)/3
                    real_height = height - sample_height
                    kg_cm = 39.37
                    density = 1333
                    jumlah = (real_height*kg_cm*0.9)+density
                    lhp_kernel_line.append([0,0,{
                        'sequence': sequence,
                        'name': bunker.storage_id.name,
                        'storage_id': bunker.storage_id.id,
                        'height': height,
                        'sample_height': sample_height,
                        'real_height': real_height,
                        'desc_1': 'cm x',
                        'type': 'bunker',
                        'kg_cm': kg_cm,
                        'desc_2': 'Kg/cm +',
                        'density': density,
                        'jumlah': jumlah,
                        'desc_3': 'Kg',
                        }])
                    total_kernel+=jumlah
                    sequence+=1

                #Bulk-Silo
                for bunker in sounding.sounding_kernel_lines.filtered(lambda r: r.storage_id.type=='Bunker'):
                    height = bunker.storage_id.height
                    sample_height = (bunker.height_1+bunker.height_2+bunker.height_3)/3
                    real_height = height - sample_height
                    kg_cm = (56790*0.67/501)
                    density = 1814
                    jumlah = (real_height*kg_cm)+density
                    lhp_kernel_line.append([0,0,{
                        'sequence': sequence,
                        'name': bunker.storage_id.name,
                        'storage_id': bunker.storage_id.id,
                        'height': height,
                        'sample_height': sample_height,
                        'real_height': real_height,
                        'desc_1': 'cm x',
                        'type': 'bunker',
                        'kg_cm': kg_cm,
                        'desc_2': 'Kg/cm +',
                        'density': density,
                        'jumlah': jumlah,
                        'desc_3': 'Kg',
                        }])
                    total_kernel+=jumlah
                    sequence+=1

                #Kernel
                for bunker in sounding.sounding_kernel_lines.filtered(lambda r: r.storage_id.type=='Kernel'):
                    kg_cm = 42.38
                    density = 1836
                    height = bunker.storage_id.height
                    sample_height = (bunker.height_1+bunker.height_2+bunker.height_3)/3
                    real_height = height - sample_height
                    jumlah = real_height*kg_cm+density

                    lhp_kernel_line.append([0,0,{
                        'sequence': sequence,
                        'name': bunker.storage_id.name,
                        'storage_id': bunker.storage_id.id,
                        'height': height,
                        'sample_height': sample_height,
                        'real_height': real_height,
                        'desc_1': 'cm x',
                        'type': 'bunker',
                        'kg_cm': kg_cm,
                        'desc_2': 'Kg/cm +',
                        'density': density,
                        'jumlah': jumlah,
                        'desc_3': 'Kg',
                        }])
                    total_kernel+=jumlah
                    sequence+=1

                #Karung
                for bunker in sounding.sounding_kernel_lines.filtered(lambda r: r.storage_id.type=='Nut'):
                    # kg_cm = 50.50
                    kg_karung = 70
                    # density = 0.4
                    height = bunker.storage_id.height
                    sample_height = bunker.height_1
                    real_height = height - sample_height
                    jumlah = (sample_height*kg_karung*1)

                    lhp_kernel_line.append([0,0,{
                        'sequence': sequence,
                        'name': bunker.storage_id.name,
                        'storage_id': bunker.storage_id.id,
                        'height': False,
                        'sample_height': sample_height,
                        'real_height': False,
                        'desc_1': 'cm x',
                        'type': 'bunker',
                        'kg_cm': kg_karung,
                        'desc_2': 'Kg/cm +',
                        'density': False,
                        'jumlah': jumlah,
                        'desc_3': 'Kg',
                        }])
                    total_kernel+=jumlah
                    sequence+=1
                    
                return lhp_kernel_line,total_kernel        


    @api.multi
    def action_approve(self):
        for sounding in self:
            sounding.state='approved'

    @api.multi
    def view_lhp(self):
        lhp_ids = self.env['mill.lhp'].search([('sounding_id','=',self.id)])
        action = self.env.ref('bms_palm_oil_mill.action_mill_lhp')
        result = action.read()[0]
        result['context'] = {}
       
        if len(lhp_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, [lhp.id for lhp in lhp_ids])) + "])]"
        else:
            res = self.env.ref('bms_palm_oil_mill.mill_lhp_form_view', False)
            result['res_id'] = lhp_ids and lhp_ids.id or False
            result['views'] = [(res and res.id or False, 'form')]
        return result

    @api.model
    def get_saldo_awal_cpo(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        if last_lhp:
            prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','in',['PENJUALAN CPO','PENGIRIMAN CPO']),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','>',last_lhp.date),('TIMBANG_OUT_DATE','<',self.date)])
            prev_move_qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
            qty = (last_lhp.total_cpo_tangki + last_lhp.total_penyesuaian_cpo) - prev_move_qty
        return qty

    @api.model
    def get_saldo_awal_cpo_palopo(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        qty = last_lhp.total_cpo_tangki_palopo
        return qty

    @api.model
    def get_saldo_awal_cpo_ptpn(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        qty = last_lhp.total_cpo_tangki_ptpn
        return qty

    @api.model
    def get_penjualan_cpo(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENJUALAN CPO'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty

    @api.model
    def get_penjualan_cpo_palopo(self):
        qty = 0
        picking_type = self.env['stock.picking.type'].search([('name','=', 'Delivery Orders Palopo')])
        prev_move_out = self.env['stock.picking'].search([('picking_type_id','=',picking_type.id),('state','=','done')])
        for move in prev_move_out:
            date_time = datetime.strptime(move.date_done, "%Y-%m-%d %H:%M:%S")# convert into datetime fromat
            date = date_time.date()
            if str(date) == self.date:
                qty+=move.pack_operation_product_ids['qty_done']
                ret_move_out = self.env['stock.picking'].search([('origin','=',move.name),('state','=','done')])
                if ret_move_out:
                    qty-=move.pack_operation_product_ids['qty_done']
        return qty
    
    @api.model
    def get_pengiriman_cpo(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENGIRIMAN CPO'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty    


    @api.model
    def get_saldo_awal_kernel(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        if last_lhp:
            prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','in',['PENJUALAN KER','PENGIRIMAN KER']),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','>',last_lhp.date),('TIMBANG_OUT_DATE','<',self.date)])
            prev_move_qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
            qty = (last_lhp.total_stock_kernel + last_lhp.total_penyesuaian_kernel) - prev_move_qty
        return qty

    @api.model
    def get_saldo_awal_kernel_mpa(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        qty = last_lhp.total_stock_kernel_mpa
        return qty

    @api.model
    def get_saldo_awal_kernel_ptpn(self):
        last_lhp = self.env['mill.lhp'].search([('date','<',self.date)], order='date desc', limit=1)
        qty = 0.0
        qty = last_lhp.total_stock_kernel_ptpn
        return qty

    @api.model
    def get_penjualan_kernel(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENJUALAN KER'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty

    @api.model
    def get_penjualan_kernel_mpa(self):
        qty = 0
        picking_type = self.env['stock.picking.type'].search([('name','=', 'Delivery Orders MPA')])
        prev_move_out = self.env['stock.picking'].search([('picking_type_id','=',picking_type.id),('state','=','done')])
        for move in prev_move_out:
            date_time = datetime.strptime(move.date_done, "%Y-%m-%d %H:%M:%S")# convert into datetime fromat
            date = date_time.date()
            if str(date) == self.date:
                qty+=move.pack_operation_product_ids['qty_done']
                ret_move_out = self.env['stock.picking'].search([('origin','=',move.name),('state','=','done')])
                if ret_move_out:
                    qty-=move.pack_operation_product_ids['qty_done']
        return qty

    @api.model
    def get_pengiriman_kernel(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENGIRIMAN KER'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty
        
    @api.model
    def get_penyerahan_cpo(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENYERAHAN CPO'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty

    @api.model
    def get_penyerahan_kernel(self):
        prev_move_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENYERAHAN KER'),('TIMBANG_RECSTS','=','F'),\
                ('TIMBANG_OUT_DATE','=',self.date)])
        qty = sum(prev_move_out.mapped('TIMBANG_TOTALBERAT')) if prev_move_out else 0.0
        return qty

    @api.multi
    def action_create_view_lhp(self):
        for sounding in self:
            total_cpo_tangki = 0
            total_produksi_cpo = 0
            total_penjualan_cpo = 0
            total_pengiriman_cpo = 0
            saldo_awal_cpo = 0

            total_cpo_tangki_palopo = 0
            saldo_awal_cpo_palopo = 0
            total_penjualan_cpo_palopo = 0

            total_stock_kernel = 0
            total_penjualan_kernel = 0
            total_pengiriman_kernel = 0
            saldo_awal_kernel = 0
            total_produksi_kernel = 0

            total_stock_kernel_mpa = 0
            total_penjualan_kernel_mpa = 0
            saldo_awal_kernel_mpa = 0

            prev_lhp = self.env['mill.lhp'].search([('date', '<', self.date)], order='date desc', limit=1)

            cpo_lines, total_cpo_tangki = sounding.prepare_cpo_line()
            tbs_lines = sounding.prepare_tbs_line()
            kernel_lines, total_stock_kernel = sounding.prepare_kernel_line()
            obj_lhp = self.env['mill.lhp']
            total_restan = sounding.restan_dalam_stelizer+sounding.restan_depan_stelizer+sounding.restan_belakang_stelizer+sounding.loading_ramp
            total_lori = sounding.lori_olah+sounding.restan_dalam_stelizer+sounding.restan_depan_stelizer+sounding.restan_belakang_stelizer+sounding.loading_ramp
            saldo_awal_cpo = sounding.get_saldo_awal_cpo()
            total_selisih_penyesuaian_cpo = sum(sounding.sounding_cpo_lines.mapped('penyesuaian_qty_tangki_cpo')) if sounding.sounding_cpo_lines else 0.0
            # total_cpo_tangki += total_selisih_penyesuaian_cpo
            total_penjualan_cpo = sounding.get_penjualan_cpo()
            total_pengiriman_cpo = sounding.get_pengiriman_cpo()
            saldo_awal_cpo_palopo = sounding.get_saldo_awal_cpo_palopo()
            total_penjualan_cpo_palopo = sounding.get_penjualan_cpo_palopo()
            total_cpo_tangki_palopo = (saldo_awal_cpo_palopo + total_pengiriman_cpo) -total_penjualan_cpo_palopo
            saldo_awal_cpo_ptpn = sounding.get_saldo_awal_cpo_ptpn()
            total_penyerahan_cpo_ptpn = sounding.get_penyerahan_cpo()
            saldo_awal_kernel = sounding.get_saldo_awal_kernel()
            total_penjualan_kernel = sounding.get_penjualan_kernel()
            total_pengiriman_kernel = sounding.get_pengiriman_kernel()
            saldo_awal_kernel_mpa = sounding.get_saldo_awal_kernel_mpa()
            total_selisih_penyesuaian_kernel = sum(sounding.sounding_kernel_lines.mapped('penyesuaian_qty_stock_kernel')) if sounding.sounding_kernel_lines else 0.0
            # total_stock_kernel += total_selisih_penyesuaian_kernel
            total_penjualan_kernel_mpa = sounding.get_penjualan_kernel_mpa()
            total_stock_kernel_mpa = (saldo_awal_kernel_mpa + total_pengiriman_kernel) - total_penjualan_kernel_mpa
            saldo_awal_kernel_ptpn = sounding.get_saldo_awal_kernel_ptpn()
            total_penyerahan_kernel_ptpn = sounding.get_penyerahan_kernel()
            total_produksi_cpo = (total_cpo_tangki+total_penjualan_cpo+total_pengiriman_cpo+total_penyerahan_cpo_ptpn)-(saldo_awal_cpo)
            total_produksi_kernel = (total_stock_kernel+total_pengiriman_kernel+total_penjualan_kernel+total_penyerahan_kernel_ptpn)-(saldo_awal_kernel)

            lhp_ids = self.env['mill.lhp'].search([('sounding_id','=',self.id)])
            if lhp_ids:
                if lhp_ids.state != "draft":
                    sounding.view_lhp()
                else:
                    lhp_ids.write({
                        'date': sounding.date,
                        'tanpa_produksi': sounding.tanpa_produksi,
                        'lhp_type_id': prev_lhp.lhp_type_id.id,
                        'lhp_cpo_line': cpo_lines,
                        'proses_tbs': sounding.lori_olah,
                        'restan_rebusan': sounding.restan_dalam_stelizer,
                        'restan_lori': sounding.restan_depan_stelizer+sounding.restan_belakang_stelizer,
                        'restan_loading_ramp': sounding.loading_ramp,
                        'restan_lantai': 0,
                        'total_restan': total_restan,
                        'total_lori': total_lori,
                        'saldo_awal_tbs_netto': tbs_lines['saldo_awal_tbs_netto'],
                        'saldo_awal_tbs_brutto': tbs_lines['saldo_awal_tbs_brutto'],
                        'tbs_in_brutto': tbs_lines['tbs_in_brutto'],
                        'tbs_in_plasma': tbs_lines['tbs_in_plasma'],
                        'tbs_in_ptpn': tbs_lines['tbs_in_ptpn'],
                        'sounding_id': sounding.id,
                        'lhp_kernel_line': kernel_lines,
                        'total_cpo_tangki': total_cpo_tangki,
                        'total_produksi_cpo': total_produksi_cpo,
                        'total_penjualan_cpo': total_penjualan_cpo,
                        'total_pengiriman_cpo': total_pengiriman_cpo,
                        'saldo_awal_cpo': saldo_awal_cpo,
                        'total_penyesuaian_cpo': total_selisih_penyesuaian_cpo,
                        'total_penyesuaian_kernel': total_selisih_penyesuaian_kernel,
                        'saldo_awal_cpo_palopo' : saldo_awal_cpo_palopo,
                        'saldo_awal_cpo_ptpn' : saldo_awal_cpo_ptpn,
                        'total_penyerahan_cpo_ptpn' : total_penyerahan_cpo_ptpn,
                        'total_penjualan_cpo_palopo' : total_penjualan_cpo_palopo,
                        'total_cpo_tangki_palopo' : total_cpo_tangki_palopo+lhp_ids.total_penyesuaian_cpo_palopo,
                        'total_stock_kernel': total_stock_kernel,
                        'total_penjualan_kernel': total_penjualan_kernel,
                        'total_pengiriman_kernel': total_pengiriman_kernel,
                        'saldo_awal_kernel': saldo_awal_kernel,
                        'saldo_awal_kernel_mpa': saldo_awal_kernel_mpa,
                        'total_penjualan_kernel_mpa' : total_penjualan_kernel_mpa,
                        'total_stock_kernel_mpa' : total_stock_kernel_mpa+lhp_ids.total_penyesuaian_kernel_mpa,
                        'total_produksi_kernel': total_produksi_kernel,
                        'saldo_awal_kernel_ptpn': saldo_awal_kernel_ptpn,
                        'total_penyerahan_kernel_ptpn' : total_penyerahan_kernel_ptpn,
                        'hm_ebc': self.hm_ebc,
                        # 'throughput': self.throughput,

                        })
            else:
                obj_lhp.create({
                    'date': sounding.date,
                    'tanpa_produksi': sounding.tanpa_produksi,
                    'lhp_type_id': prev_lhp.lhp_type_id.id,
                    'lhp_cpo_line': cpo_lines,
                    'proses_tbs': sounding.lori_olah,
                    'restan_rebusan': sounding.restan_dalam_stelizer,
                    'restan_lori': sounding.restan_depan_stelizer+sounding.restan_belakang_stelizer,
                    'restan_loading_ramp': sounding.loading_ramp,
                    'restan_lantai': 0,
                    'total_restan': total_restan,
                    'total_lori': total_lori,
                    'saldo_awal_tbs_netto': tbs_lines['saldo_awal_tbs_netto'],
                    'saldo_awal_tbs_brutto': tbs_lines['saldo_awal_tbs_brutto'],
                    'tbs_in_brutto': tbs_lines['tbs_in_brutto'],
                    'tbs_in_plasma': tbs_lines['tbs_in_plasma'],
                    'tbs_in_ptpn': tbs_lines['tbs_in_ptpn'],
                    'sounding_id': sounding.id,
                    'lhp_kernel_line': kernel_lines,
                    'total_cpo_tangki': total_cpo_tangki,
                    'total_produksi_cpo': total_produksi_cpo,
                    'total_penjualan_cpo': total_penjualan_cpo,
                    'total_pengiriman_cpo': total_pengiriman_cpo,
                    'saldo_awal_cpo': saldo_awal_cpo,
                    'total_penyesuaian_cpo': total_selisih_penyesuaian_cpo,
                    'total_penyesuaian_kernel': total_selisih_penyesuaian_kernel,
                    'saldo_awal_cpo_palopo' : saldo_awal_cpo_palopo,
                    'saldo_awal_cpo_ptpn' : saldo_awal_cpo_ptpn,
                    'total_penyerahan_cpo_ptpn' : total_penyerahan_cpo_ptpn,
                    'total_penjualan_cpo_palopo' : total_penjualan_cpo_palopo,
                    'total_cpo_tangki_palopo' : total_cpo_tangki_palopo,
                    'total_stock_kernel': total_stock_kernel,
                    'total_penjualan_kernel': total_penjualan_kernel,
                    'total_pengiriman_kernel': total_pengiriman_kernel,
                    'saldo_awal_kernel': saldo_awal_kernel,
                    'saldo_awal_kernel_mpa': saldo_awal_kernel_mpa,
                    'total_penjualan_kernel_mpa' : total_penjualan_kernel_mpa,
                    'total_stock_kernel_mpa' : total_stock_kernel_mpa,
                    'total_produksi_kernel': total_produksi_kernel,
                    'saldo_awal_kernel_ptpn': saldo_awal_kernel_ptpn,
                    'total_penyerahan_kernel_ptpn' : total_penyerahan_kernel_ptpn,
                    'hm_ebc': self.hm_ebc,
                    # 'throughput': self.throughput,

                    })                
            return sounding.view_lhp()

    @api.multi
    def action_set_to_draft(self):
        for sounding in self:
            lhp_ids = self.env['mill.lhp'].search([('sounding_id','=',sounding.id)])
            for lhp in lhp_ids:
                lhp.action_draft()
            sounding.state='draft'



class MillDailySoundingCPO(models.Model):
    _name = "mill.daily.sounding.cpo.line"
    _description = "Laporan harian Sounding CPO"

    sounding_id = fields.Many2one('mill.daily.sounding', required=True)
    storage_id = fields.Many2one('mill.storage', required=True, string='Lokasi')
    height = fields.Float(digits=0)
    temperature = fields.Float()
    ffa = fields.Float(digits=dp.get_precision('Sounding FFA'))
    penyesuaian_qty_tangki_cpo = fields.Float('Selisih Penyesuaian (kg)')

class MillDailySoundingKernel(models.Model):
    _name = "mill.daily.sounding.kernel.line"
    _description = "Laporan harian Sounding Kernel"

    sounding_id = fields.Many2one('mill.daily.sounding', required=True)
    storage_id = fields.Many2one('mill.storage', required=True, string='Lokasi')
    height_1 = fields.Float('Ketinggian 1', digits=(15,2))
    height_2 = fields.Float('Ketinggian 2', digits=(15,2))
    height_3 = fields.Float('Ketinggian 3', digits=(15,2))
    penyesuaian_qty_stock_kernel = fields.Float('Selisih Penyesuaian (kg)')

