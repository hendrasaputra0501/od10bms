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
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
import time

class MillLhp(models.Model):
	_name = "mill.lhp"
	_description = "Laporan Harian Produksi"
	_rec_name = "date"

	# @api.depends('tanpa_produksi')
	# def _compute_computed(self):
	# 	res = 'yes' if self.tanpa_produksi == False else 'no'
	# 	print '==============', res
	# 	self.computed = res
		
	@api.depends('saldo_awal_tbs_brutto','saldo_awal_tbs_netto','tbs_in_netto', 'tbs_in_brutto','tbs_in_brutto', 'tanpa_produksi')
	def _compute_tbs(self):
		for lhp in self:
			total_tbs_netto = lhp.saldo_awal_tbs_netto+lhp.tbs_in_netto
			total_tbs_brutto = lhp.saldo_awal_tbs_brutto+lhp.tbs_in_brutto

			# Lori dihitung hanya ketika ada produksi
			per_lori_netto = lhp.total_lori and total_tbs_netto/lhp.total_lori or 0.0
			per_lori_brutto = lhp.total_lori and total_tbs_brutto/lhp.total_lori or 0.0
			tbs_ramp_brutto = per_lori_brutto*lhp.restan_loading_ramp
			tbs_ramp_netto = per_lori_netto*lhp.restan_loading_ramp
			tbs_lori_brutto = per_lori_brutto*lhp.restan_lori
			tbs_lori_netto = per_lori_netto*lhp.restan_lori
			tbs_rebusan_brutto = per_lori_brutto*lhp.restan_rebusan
			tbs_rebusan_netto = per_lori_netto*lhp.restan_rebusan

			if lhp.tanpa_produksi:
				saldo_akhir_tbs_netto = total_tbs_netto
				saldo_akhir_tbs_brutto = total_tbs_brutto
				computed = "belum"
			else:
				saldo_akhir_tbs_netto = tbs_ramp_netto+tbs_lori_netto+tbs_rebusan_netto
				saldo_akhir_tbs_brutto = tbs_ramp_brutto+tbs_lori_brutto+tbs_rebusan_brutto
				computed = "sudah"
			
			tbs_proses_brutto = per_lori_brutto*lhp.proses_tbs
			tbs_proses_netto = per_lori_netto*lhp.proses_tbs
			lhp.update({
				'total_tbs_netto': total_tbs_netto,
				'total_tbs_brutto': total_tbs_brutto,
				'per_lori_netto': per_lori_netto,
				'per_lori_brutto': per_lori_brutto,
				'tbs_ramp_brutto': tbs_ramp_brutto,
				'tbs_ramp_netto': tbs_ramp_netto,
				'tbs_lori_brutto': tbs_lori_brutto,
				'tbs_lori_netto': tbs_lori_netto,
				'tbs_rebusan_brutto': tbs_rebusan_brutto,
				'tbs_rebusan_netto': tbs_rebusan_netto,
				'saldo_akhir_tbs_netto': saldo_akhir_tbs_netto,
				'saldo_akhir_tbs_brutto': saldo_akhir_tbs_brutto,
				'tbs_proses_brutto': tbs_proses_brutto,
				'tbs_proses_netto': tbs_proses_netto,
				'computed' : computed

				})


	state = fields.Selection([('draft','Draft'),('approved','Approved')], default='draft')
	date = fields.Date('Tanggal')
	tanpa_produksi = fields.Boolean('Tanpa Produksi')
	lhp_tbs_line = fields.One2many('mill.lhp.tbs.line','lhp_id', string='TBS')
	lhp_cpo_line = fields.One2many('mill.lhp.cpo.line','lhp_id', string='CPO')
	proses_tbs = fields.Float('PROSES TBS')
	proses_tbs_brutto_rel = fields.Float(related='proses_tbs')
	proses_tbs_netto_rel = fields.Float(related='proses_tbs')
	restan_rebusan = fields.Float()
	restan_lori = fields.Float()
	restan_loading_ramp = fields.Float()
	restan_lantai = fields.Float()
	total_restan = fields.Float()
	total_lori = fields.Float()
	total_lori_brutto_rel = fields.Float(related='total_lori')
	total_lori_netto_rel = fields.Float(related='total_lori')
	per_lori_netto = fields.Float(compute='_compute_tbs', store=True)
	per_lori_brutto = fields.Float(compute='_compute_tbs', store=True)
	per_lori_netto_rel = fields.Float(related='per_lori_netto')
	per_lori_brutto_rel = fields.Float(related='per_lori_brutto')
	saldo_awal_tbs_brutto = fields.Float()
	saldo_awal_tbs_netto = fields.Float()
	tbs_proses_brutto = fields.Float(compute='_compute_tbs', store=True)
	tbs_proses_netto = fields.Float(compute='_compute_tbs', store=True)
	tbs_in_brutto = fields.Float()
	tbs_in_netto = fields.Float(compute='_computre_tbs_in')
	tbs_in_plasma = fields.Float()
	tbs_in_ptpn = fields.Float()
	total_tbs_netto = fields.Float(compute='_compute_tbs', store=True)
	total_tbs_brutto = fields.Float(compute='_compute_tbs', store=True)
	tbs_ramp_brutto = fields.Float(compute='_compute_tbs', store=True)
	tbs_ramp_netto = fields.Float(compute='_compute_tbs', store=True)
	tbs_lori_netto = fields.Float(compute='_compute_tbs', store=True)
	tbs_lori_brutto = fields.Float(compute='_compute_tbs', store=True)
	tbs_rebusan_brutto = fields.Float(compute='_compute_tbs', store=True)
	tbs_rebusan_netto = fields.Float(compute='_compute_tbs', store=True)
	saldo_akhir_tbs_netto = fields.Float(compute='_compute_tbs', store=True)
	saldo_akhir_tbs_brutto = fields.Float(compute='_compute_tbs', store=True)
	computed = fields.Char(compute='_compute_tbs', store=True)
	sounding_id = fields.Many2one('mill.daily.sounding')

	lhp_kernel_line = fields.One2many('mill.lhp.kernel.line','lhp_id', string='Kernel')

	total_penjualan_cpo = fields.Float('Penjualan CPO')
	selisih_timbang_penjualan_cpo = fields.Float('Selisih Timbang Penjualan CPO')
	saldo_awal_cpo = fields.Float('Saldo Awal CPO')
	total_produksi_cpo = fields.Float('Produksi CPO')
	total_pengiriman_cpo = fields.Float('Pengiriman CPO')
	total_penyesuaian_cpo = fields.Float('Penyesuaian CPO')
	total_cpo_tangki = fields.Float('Stock CPO dalam Tangki')

	saldo_awal_cpo_palopo = fields.Float('Stok Kemarin')
	total_penjualan_cpo_palopo = fields.Float('Penjualan CPO')
	selisih_timbang_penjualan_cpo_palopo = fields.Float('Selisih Timbang Penjualan CPO')
	total_penyesuaian_cpo_palopo = fields.Float('Penyesuaian CPO')
	total_cpo_tangki_palopo = fields.Float('Stok CPO dalam Tangki')

	saldo_awal_cpo_ptpn = fields.Float('Stok Kemarin')
	total_produksi_cpo_ptpn = fields.Float('Produksi CPO',compute="_compute_produksi_cpo_ptpn", store=True)
	total_penyerahan_cpo_ptpn = fields.Float('Penyerahan CPO')
	total_cpo_tangki_ptpn = fields.Float('Stok CPO dalam Tangki', compute='_compute_cpo_tangki_ptpn')

	saldo_awal_kernel = fields.Float('Total Stock Kernel kemarin (saldo awal)')
	total_penjualan_kernel = fields.Float('Total Penjualan Kernel')
	selisih_timbang_penjualan_kernel = fields.Float('Selisih Timbang Penjualan Kernel')
	total_produksi_kernel = fields.Float('Total Produksi Kernel hari ini')
	total_pengiriman_kernel = fields.Float('Pengiriman Kernel')
	total_penyesuaian_kernel = fields.Float('Penyesuaian Kernel')
	total_stock_kernel = fields.Float('Total Stock Kernel')
	
	saldo_awal_kernel_mpa = fields.Float('Stok Kemarin')
	total_penjualan_kernel_mpa = fields.Float('Penjualan Kernel')
	selisih_timbang_penjualan_kernel_mpa = fields.Float('Selisih Timbang Penjualan Kernel')
	total_penyesuaian_kernel_mpa = fields.Float('Penyesuaian Kernel')
	total_stock_kernel_mpa = fields.Float('Total Stok Kernel')

	saldo_awal_kernel_ptpn = fields.Float('Stok Kemarin')
	total_produksi_kernel_ptpn = fields.Float('Total Produksi Kernel hari ini',compute="_compute_produksi_cpo_ptpn", store=True)
	total_penyerahan_kernel_ptpn = fields.Float('Penyerahan Kernel')
	total_penyesuaian_kernel_ptpn = fields.Float('Penyesuaian Kernel')
	total_stock_kernel_ptpn = fields.Float('Total Stok Kernel', compute='_compute_kernel_tangki_ptpn')
	
	oer = fields.Float("OER", compute='_compute_oer')
	ker = fields.Float("KER", compute='_compute_ker')
	throughput = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'), compute='_compute_throughput')
	hm_ebc = fields.Float(digits=dp.get_precision('Kernel Lossess Precentage'))
	# restan_ptpn = fields.Float("Restan PTPN",)
	company_id = fields.Many2one('res.company', string='Company', required=True,
		default=lambda self: self.env['res.company']._company_default_get('mill.lhp'))

	lhp_type_id = fields.Many2one("mill.lhp.type", string="LHP Type")
	move_tbs_proses_ids = fields.Many2many("stock.move", "tbs_proses_lhp_move_rel", string="Stock Move TBS")
	move_tbs_proses_id = fields.Many2one("stock.move", string="Stock Move TBS")
	move_cpo_produksi_ids = fields.Many2many("stock.move", "cpo_produksi_lhp_move_rel", string="Stock Move CPO Produksi")
	move_cpo_produksi_id = fields.Many2one("stock.move", string="Stock Move CPO Produksi")
	move_cpo_penyesuaian_ids = fields.Many2many("stock.move", "cpo_penyesuaian_lhp_move_rel", string="Stock Move CPO Penyesuaian")
	move_cpo_penyesuaian_id = fields.Many2one("stock.move", string="Stock Move CPO Penyesuaian")
	move_kernel_produksi_ids = fields.Many2many("stock.move", "kernel_produksi_lhp_move_rel", string="Stock Move Kernel Produksi")
	move_kernel_produksi_id = fields.Many2one("stock.move", string="Stock Move Kernel Produksi")
	move_kernel_penyesuaian_ids = fields.Many2many("stock.move", "kernel_penyesuaian_lhp_move_rel", string="Stock Move Kernel Penyesuaian")
	move_kernel_penyesuaian_id = fields.Many2one("stock.move", string="Stock Move Kernel Penyesuaian")

	_order = "date desc, id desc"

	@api.depends('tbs_in_plasma', 'tbs_in_ptpn')
	def _computre_tbs_in(self):
		self.tbs_in_netto = self.tbs_in_ptpn+self.tbs_in_plasma

	def generate_move_from_lhp(self, data):
		return self.env['stock.move'].create({
			'name': "LHP tanggal " + data['sounding'].date,
			'date': datetime.now(),
			'product_id': data['product_id'].id,
			'product_uom_qty': data['qty'],
			'product_uom': data['product_id'].uom_id.id,
			'procure_method': 'make_to_stock',
			'location_dest_id': data['location_dest_id'].id,
			'location_id': data['location_id'].id,
		})

	@api.multi
	def action_approve(self):
		for sounding in self:
			data = {}
				# Create Stock Move TBS Olah
			if sounding.tbs_proses_netto:
				if not sounding.move_tbs_proses_ids:
					qty = sounding.tbs_proses_netto
					location_id = sounding.lhp_type_id.location_id
					location_dest_id = sounding.lhp_type_id.product_tbs_id.property_stock_production
				else:
					qty_src = sum(sounding.move_tbs_proses_ids.filtered(lambda x: x.location_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					qty_return = sum(sounding.move_tbs_proses_ids.filtered(lambda x: x.location_dest_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					total = abs(qty_src - qty_return)
					if total<sounding.tbs_proses_netto:
						qty = sounding.tbs_proses_netto - total
						location_id = sounding.lhp_type_id.location_id
						location_dest_id = sounding.lhp_type_id.product_tbs_id.property_stock_production
					else:
						qty = total - sounding.tbs_proses_netto
						location_id = sounding.lhp_type_id.product_tbs_id.property_stock_production
						location_dest_id = sounding.lhp_type_id.location_id
				data = {
						'sounding' : sounding,
						'qty' : qty,
						'location_id' : location_id,
						'location_dest_id' : location_dest_id,
						'product_id' : sounding.lhp_type_id.product_tbs_id,
				}
				move_tbs_proses_id = self.generate_move_from_lhp(data)
				self.move_tbs_proses_ids = [(4,move_tbs_proses_id.id)]
				self.move_tbs_proses_id = move_tbs_proses_id.id
				move_tbs_proses_id.action_done()
				move_tbs_proses_id.date = sounding.date

				# Create Stock Move CPO Produksi
			if sounding.total_produksi_cpo:
				if not sounding.move_cpo_produksi_ids:
					qty = sounding.total_produksi_cpo
					location_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
					location_dest_id = sounding.lhp_type_id.location_dest_id
				else:
					qty_src = sum(sounding.move_cpo_produksi_ids.filtered(lambda x: x.location_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					qty_return = sum(sounding.move_cpo_produksi_ids.filtered(lambda x: x.location_dest_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					total = abs(qty_src - qty_return)
					if total<sounding.total_produksi_cpo:
						qty = sounding.total_produksi_cpo - total
						location_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
						location_dest_id = sounding.lhp_type_id.location_dest_id
					else:
						qty = total - sounding.total_produksi_cpo
						location_id = sounding.lhp_type_id.location_dest_id
						location_dest_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
				data = {
						'sounding' : sounding,
						'qty' : qty,
						'location_id' : location_id,
						'location_dest_id' : location_dest_id,
						'product_id' : sounding.lhp_type_id.product_cpo_id,
				}
				move_cpo_produksi_id = self.generate_move_from_lhp(data)
				self.move_cpo_produksi_ids = [(4,move_cpo_produksi_id.id)]
				self.move_cpo_produksi_id = move_cpo_produksi_id.id
				move_cpo_produksi_id.action_done()
				move_cpo_produksi_id.date = sounding.date
				for quant in move_cpo_produksi_id.quant_ids:
					quant.sudo().in_date = sounding.date

				# Create Stock Move CPO Penyesuaian
			if sounding.total_penyesuaian_cpo:
				if not sounding.move_cpo_penyesuaian_ids:
					qty = sounding.total_penyesuaian_cpo
					location_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
					location_dest_id = sounding.lhp_type_id.location_dest_id
				else:
					qty_src = sum(sounding.move_cpo_penyesuaian_ids.filtered(lambda x: x.location_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					qty_return = sum(sounding.move_cpo_penyesuaian_ids.filtered(lambda x: x.location_dest_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					total = abs(qty_src - qty_return)
					if total<sounding.total_penyesuaian_cpo:
						qty = sounding.total_penyesuaian_cpo - total
						location_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
						location_dest_id = sounding.lhp_type_id.location_dest_id
					else:
						qty = total - sounding.total_penyesuaian_cpo
						location_id = sounding.lhp_type_id.location_dest_id
						location_dest_id = sounding.lhp_type_id.product_cpo_id.property_stock_production
				data = {
						'sounding' : sounding,
						'qty' : qty,
						'location_id' : location_id,
						'location_dest_id' : location_dest_id,
						'product_id' : sounding.lhp_type_id.product_cpo_id,
				}
				move_cpo_penyesuaian_id = self.generate_move_from_lhp(data)
				self.move_cpo_penyesuaian_ids = [(4,move_cpo_penyesuaian_id.id)]
				self.move_cpo_penyesuaian_id = move_cpo_penyesuaian_id.id
				move_cpo_penyesuaian_id.action_done()
				move_cpo_penyesuaian_id.date = sounding.date
				for quant in move_cpo_penyesuaian_id.quant_ids:
					quant.sudo().in_date = sounding.date

				# Create Stock Move Kernel Produksi
			if sounding.total_produksi_kernel:
				if not sounding.move_kernel_produksi_ids:
					qty = sounding.total_produksi_kernel
					location_id = sounding.lhp_type_id.product_kernel_id.property_stock_production
					location_dest_id = sounding.lhp_type_id.location_dest_id
				else:
					qty_src = sum(sounding.move_kernel_produksi_ids.filtered(lambda x: x.location_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					qty_return = sum(sounding.move_kernel_produksi_ids.filtered(lambda x: x.location_dest_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					total = abs(qty_src - qty_return)
					if total<sounding.total_produksi_kernel:
						qty = sounding.total_produksi_kernel - total
						location_id = sounding.lhp_type_id.product_kernel_id.property_stock_production
						location_dest_id = sounding.lhp_type_id.location_dest_id
					else:
						qty = total - sounding.total_produksi_kernel
						location_id = sounding.lhp_type_id.location_dest_id
						location_dest_id = sounding.lhp_type_id.product_kernel_id.property_stock_production
				data = {
						'sounding' : sounding,
						'qty' : qty,
						'location_id' : location_id,
						'location_dest_id' : location_dest_id,
						'product_id' : sounding.lhp_type_id.product_kernel_id,
				}
				move_kernel_produksi_id = self.generate_move_from_lhp(data)
				self.move_kernel_produksi_ids = [(4,move_kernel_produksi_id.id)]
				self.move_kernel_produksi_id = move_kernel_produksi_id.id
				move_kernel_produksi_id.action_done()
				move_kernel_produksi_id.date = sounding.date
				for quant in move_kernel_produksi_id.quant_ids:
					quant.sudo().in_date = sounding.date

				# Create Stock Move Kernel Penyesuaian
			if sounding.total_penyesuaian_kernel:
				if not sounding.move_kernel_penyesuaian_ids:
					qty = sounding.total_penyesuaian_kernel
					location_id = sounding.lhp_type_id.location_id
					location_dest_id = sounding.lhp_type_id.location_dest_id
				else:
					qty_src = sum(sounding.move_kernel_penyesuaian_ids.filtered(lambda x: x.location_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					qty_return = sum(sounding.move_kernel_penyesuaian_ids.filtered(lambda x: x.location_dest_id == sounding.lhp_type_id.location_id).mapped('product_uom_qty'))
					total = abs(qty_src - qty_return)
					if total<sounding.total_penyesuaian_kernel:
						qty = sounding.total_penyesuaian_kernel - total
						location_id = sounding.lhp_type_id.location_id
						location_dest_id = sounding.lhp_type_id.location_dest_id
					else:
						qty = total - sounding.total_penyesuaian_kernel
						location_id = sounding.lhp_type_id.location_dest_id
						location_dest_id = sounding.lhp_type_id.location_id
				data = {
						'sounding' : sounding,
						'qty' : qty,
						'location_id' : location_id,
						'location_dest_id' : location_dest_id,
						'product_id' : sounding.lhp_type_id.product_kernel_id,
				}
				move_kernel_penyesuaian_id = self.generate_move_from_lhp(data)
				self.move_kernel_penyesuaian_ids = [(4,move_kernel_penyesuaian_id.id)]
				self.move_kernel_penyesuaian_id - move_kernel_penyesuaian_id.id
				move_kernel_penyesuaian_id.action_done()
				move_kernel_penyesuaian_id.date = sounding.date
				for quant in move_kernel_penyesuaian_id.quant_ids:
					quant.sudo().in_date = sounding.date

			sounding.state='approved'

	@api.multi
	def action_draft(self):
		for lhp in self:
			#Return
			if lhp.move_cpo_produksi_id:
				data = {
					'location_id' : lhp.move_cpo_produksi_id.location_dest_id,
					'location_dest_id' : lhp.move_cpo_produksi_id.location_id,
					'sounding' : lhp,
					'qty' : lhp.move_cpo_produksi_id.product_uom_qty,
					'product_id' : lhp.lhp_type_id.product_cpo_id,
					}
				move_cpo_produksi_ret = self.generate_move_from_lhp(data)
				lhp.move_cpo_produksi_ids = [(4,move_cpo_produksi_ret.id)]
				move_cpo_produksi_ret.action_done()
			if lhp.move_cpo_penyesuaian_id:
				data = {
					'location_id' : lhp.move_cpo_penyesuaian_id.location_dest_id,
					'location_dest_id' : lhp.move_cpo_penyesuaian_id.location_id,
					'sounding' : lhp,
					'qty' : lhp.move_cpo_penyesuaian_id.product_uom_qty,
					'product_id' : lhp.lhp_type_id.product_cpo_id,
					}
				move_cpo_penyesuaian_ret = self.generate_move_from_lhp(data)
				lhp.move_cpo_penyesuaian_ids = [(4,move_cpo_penyesuaian_ret.id)]
				move_cpo_penyesuaian_ret.action_done()
			if lhp.move_kernel_produksi_id:
				data = {
					'location_id' : lhp.move_kernel_produksi_id.location_dest_id,
					'location_dest_id' : lhp.move_kernel_produksi_id.location_id,
					'sounding' : lhp,
					'qty' : lhp.move_kernel_produksi_id.product_uom_qty,
					'product_id' : lhp.lhp_type_id.product_kernel_id,
					}
				move_kernel_produksi_ret = self.generate_move_from_lhp(data)
				lhp.move_kernel_produksi_ids = [(4,move_kernel_produksi_ret.id)]
				move_kernel_produksi_ret.action_done()
			if lhp.move_kernel_penyesuaian_id:
				data = {
					'location_id' : lhp.move_kernel_penyesuaian_id.location_dest_id,
					'location_dest_id' : lhp.move_kernel_penyesuaian_id.location_id,
					'sounding' : lhp,
					'qty' : lhp.move_kernel_penyesuaian_id.product_uom_qty,
					'product_id' : lhp.lhp_type_id.product_kernel_id,
					}
				move_kernel_penyesuaian_ret = self.generate_move_from_lhp(data)
				lhp.move_kernel_penyesuaian_ids = [(4,move_kernel_penyesuaian_ret.id)]
				move_kernel_penyesuaian_ret.action_done()
			if lhp.move_tbs_proses_id:
				data = {
					'location_id' : lhp.move_tbs_proses_id.location_dest_id,
					'location_dest_id' : lhp.move_tbs_proses_id.location_id,
					'sounding' : lhp,
					'qty' : lhp.move_tbs_proses_id.product_uom_qty,
					'product_id' : lhp.lhp_type_id.product_tbs_id,
					}
				move_tbs_proses_ret = self.generate_move_from_lhp(data)
				lhp.move_tbs_proses_ids = [(4,move_tbs_proses_ret.id)]
				move_tbs_proses_ret.action_done()
			lhp.state="draft"

	@api.multi
	def unlink(self):
		for lhp in self:
			if lhp.move_cpo_produksi_ids or lhp.move_cpo_penyesuaian_ids or lhp.move_kernel_produksi_ids or lhp.move_kernel_penyesuaian_ids or lhp.move_tbs_proses_ids:
				raise ValidationError("Dokumen %s tidak dapat dihapus" %(lhp.date))
		return super(MillLhp, self).unlink()

	@api.onchange('saldo_awal_cpo', 'total_penjualan_cpo', 'total_pengiriman_cpo', 'total_cpo_tangki', 'total_penyesuaian_cpo', 'selisih_timbang_penjualan_cpo')
	def onchange_qty_cpo(self):
		total_penyesuaian_cpo = self.total_penyesuaian_cpo + self.selisih_timbang_penjualan_cpo
		self.total_penyesuaian_cpo = total_penyesuaian_cpo
		self.total_produksi_cpo = self.total_cpo_tangki - (self.saldo_awal_cpo - self.selisih_timbang_penjualan_cpo - self.total_penjualan_cpo - self.total_pengiriman_cpo)
		if self.total_pengiriman_cpo:
			self.total_cpo_tangki_palopo+=self.total_pengiriman_cpo

	@api.depends('total_produksi_cpo','tbs_proses_netto')
	def _compute_oer(self):
		for data in self:
			if data.total_produksi_cpo and data.tbs_proses_netto:
				data.oer = (data.total_produksi_cpo/data.tbs_proses_netto)*100

	@api.depends('oer','ker','tbs_in_ptpn')
	def _compute_produksi_cpo_ptpn(self):
		for lhp in self:
			last_lhp = self.env['mill.lhp'].search([('date','<',lhp.date),('computed','=','sudah')], order='date desc',limit=1)
			if last_lhp:
				last_lhp_belum = self.env['mill.lhp'].search([('date','<',lhp.date),('date','>',last_lhp.date),('computed','=','belum')], order='date desc',)
				last_tbs_ptpn = sum(last_lhp_belum.mapped('tbs_in_ptpn')) if last_lhp_belum else 0.0
			else:
				last_tbs_ptpn = 0
			tbs_ptpn = lhp.tbs_in_ptpn+last_tbs_ptpn
			# print '===============================', tbs_ptpn, lhp.oer, lhp.tbs_in_ptpn
			lhp.total_produksi_cpo_ptpn = (lhp.oer/100)*(tbs_ptpn)
			lhp.total_produksi_kernel_ptpn = (lhp.ker/100)*(tbs_ptpn)

	@api.depends('saldo_awal_cpo_ptpn', 'total_produksi_cpo_ptpn', 'total_penyerahan_cpo_ptpn')
	def _compute_cpo_tangki_ptpn(self):
		self.total_cpo_tangki_ptpn = self.saldo_awal_cpo_ptpn+self.total_produksi_cpo_ptpn-self.total_penyerahan_cpo_ptpn

	@api.depends('saldo_awal_kernel_ptpn', 'total_produksi_kernel_ptpn', 'total_penyerahan_kernel_ptpn', 'total_penyesuaian_kernel_ptpn')
	def _compute_kernel_tangki_ptpn(self):
		self.total_stock_kernel_ptpn = self.saldo_awal_kernel_ptpn + self.total_penyesuaian_kernel_ptpn + self.total_produksi_kernel_ptpn - self.total_penyerahan_kernel_ptpn

	@api.depends('total_produksi_kernel','tbs_proses_netto')
	def _compute_ker(self):
		for data in self:
			if data.total_produksi_kernel and data.tbs_proses_netto:
				data.ker = (data.total_produksi_kernel/data.tbs_proses_netto)*100

	@api.depends('tbs_proses_netto', 'hm_ebc')
	def _compute_throughput(self):
		if self.hm_ebc and self.tbs_proses_netto:
			self.throughput = ((self.tbs_proses_netto/1000)/self.hm_ebc)


	@api.onchange('saldo_awal_cpo_palopo','total_penjualan_cpo_palopo','total_penyesuaian_cpo_palopo', 'selisih_timbang_penjualan_cpo_palopo')
	def onchange_qty_tangki_palopo(self):
		total_penyesuaian_cpo_palopo = self.total_penyesuaian_cpo_palopo + self.selisih_timbang_penjualan_cpo_palopo
		self.total_penyesuaian_cpo_palopo = total_penyesuaian_cpo_palopo
		self.total_cpo_tangki_palopo = (self.saldo_awal_cpo_palopo+self.total_pengiriman_cpo+total_penyesuaian_cpo_palopo)-self.total_penjualan_cpo_palopo

	@api.onchange('saldo_awal_kernel', 'total_penjualan_kernel', 'total_pengiriman_kernel', 'total_stock_kernel', 'selisih_timbang_penjualan_kernel')
	def onchange_qty_kernel(self):
		total_penyesuaian_kernel = self.total_penyesuaian_kernel + self.selisih_timbang_penjualan_kernel
		self.total_penyesuaian_kernel = total_penyesuaian_kernel
		self.total_produksi_kernel = self.total_stock_kernel - (self.saldo_awal_kernel - self.selisih_timbang_penjualan_kernel - self.total_penjualan_kernel - self.total_pengiriman_kernel)
		if self.total_pengiriman_kernel:
			self.total_stock_kernel_mpa+=self.total_pengiriman_kernel

	@api.onchange('saldo_awal_kernel_mpa','total_penjualan_kernel_mpa', 'total_penyesuaian_kernel_mpa', 'selisih_timbang_penjualan_kernel_mpa')
	def onchange_qty_stock_mpa(self):
		total_penyesuaian_kernel_mpa = self.total_penyesuaian_kernel_mpa + self.selisih_timbang_penjualan_kernel_mpa
		self.total_penyesuaian_kernel_mpa = total_penyesuaian_kernel_mpa
		self.total_stock_kernel_mpa = (self.saldo_awal_kernel_mpa + total_penyesuaian_kernel_mpa + self.total_pengiriman_kernel) - self.total_penjualan_kernel_mpa

	@api.multi
	def print_lhp(self):
		res = self.env['report'].get_action(self, 'bms_palm_oil_mill.report_lhp_qweb')
		# res.update({'preview_print': True})
		return res

	def print_lhp_kumulatif(self):
		return self.env['report'].get_action(self, 'report_lhp_kumulatif_xlsx')

class MillLhpTbs(models.Model):
	_name = "mill.lhp.tbs.line"
	_description = "Laporan Harian Produksi TBS"

	sequence = fields.Integer()
	lhp_id = fields.Many2one('mill.lhp')
	name = fields.Char('Description')
	brutto = fields.Float('Brutto')
	netto = fields.Float('Netto')
	uom_id = fields.Many2one('product.uom', string='UoM')
	type = fields.Selection([('total','total'),('normal','normal')], string='Type')

class MillLhpCpo(models.Model):
	_name = "mill.lhp.cpo.line"
	_description = "Laporan Harian Produksi CPO"

	sequence = fields.Integer()
	lhp_id = fields.Many2one('mill.lhp')
	name = fields.Char('Description')
	storage_id = fields.Many2one('mill.storage')
	height = fields.Float('Ketinggian', digits=0)
	temperature = fields.Float('Suhu/Temperature')
	uom_height_id = fields.Many2one('product.uom', string='UoM')
	uom_temperature_id = fields.Many2one('product.uom', string='UoM')
	type = fields.Selection([('cm','cm'),('mm','mm'),('total','total')], string='Type')
	density = fields.Float('Density', digits=dp.get_precision('Density'))
	volume_liter = fields.Float('Volume Liter')
	uom_volume_liter_id = fields.Many2one('product.uom', string='UoM')
	koreksi_suhu = fields.Float('Faktor Koreksi', digits=dp.get_precision('Koreksi Suhu'))
	jumlah_setelah_koreksi = fields.Float()
	jumlah = fields.Float()
	uom_jumlah_id = fields.Many2one('product.uom', string='UoM')
	ffa = fields.Float(digits=dp.get_precision('Sounding FFA'))
	

class MillLhpKernel(models.Model):
	_name = "mill.lhp.kernel.line"
	_description = "Laporan Harian Produksi Kernel"

	sequence = fields.Integer()
	lhp_id = fields.Many2one('mill.lhp')
	name = fields.Char('Description')
	storage_id = fields.Many2one('mill.storage')
	height = fields.Float('Ketinggian', digits=(15,0))
	sample_height = fields.Float('Sample', digits=(15,2))
	real_height = fields.Float('Tinggi Bersih', digits=(15,0))
	desc_1 = fields.Char('Ket. 1')
	type = fields.Selection([('detail','detail'),('total','total'),('bunker','bunker')], string='Type')
	kg_cm = fields.Float('kg/cm')
	desc_2 = fields.Char('Ket. 2')
	density = fields.Float('Densitas', digits=dp.get_precision('Mill Bunker Density'))
	jumlah = fields.Float()
	desc_3 = fields.Char('Ket. 3')
