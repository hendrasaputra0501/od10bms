from odoo import api, models, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from calendar import monthrange

class LHPkumulatifXlsx(ReportXlsx):

	def generate_xlsx_report(self, workbook, data, objects):
		print("objects", objects)

		sheet = workbook.add_worksheet('LHP')
		sheet.set_column(0,0,3)
		sheet.set_column(1,1,3)
		sheet.set_column(2,2,20)
		sheet.set_column(4,6,20)
		bold = workbook.add_format({'bold': True, 'font_size':12})
		header = workbook.add_format({'bg_color': '#5eafd1','border':1, 'bold': True, 'font_size':12, 'align':'center'})
		number = workbook.add_format({'num_format':'#,##0.00'})
		border2 = workbook.add_format({'num_format':'#,##0.00','align':'center'})
		format1 = workbook.add_format({'font_size': 14, 'bold': True})
		format2 = workbook.add_format({'bg_color': '#5eafd1', 'bold': True,'border':1, 'num_format':'#,##0.00'})
		format3 = workbook.add_format({'bold': True, 'font_size': 18, 'align':'center'})
		format4 = workbook.add_format({'bold': True, 'align':'center','valign':'vcenter', 'border':1})
		sheet.write(0, 0, objects.company_id.name, format1)
		sheet.merge_range(2, 0, 2, 6, 'LAPORAN HARIAN PRODUKSI', format3)
		sheet.write(3, 0, 'Tanggal : '+datetime.strptime(objects.date,'%Y-%m-%d').strftime('%d/%m/%Y'), bold) 
		# sheet.merge_range(3,0,4,1, '', border)
		sheet.merge_range(4, 0, 4, 2, 'URAIAN', header)
		sheet.write(4, 3, 'SATUAN', header)
		sheet.write(4, 4, 'HARI INI', header)
		sheet.write(4, 5, 'SD HARI INI', header)
		sheet.write(4, 6, 'SD BULAN INI', header)
		# TBS
		buah_sisa_kemarin_hi = objects.saldo_awal_tbs_netto
		penerimaan_plasma_hi = objects.tbs_in_plasma
		penerimaan_ptpn_hi = objects.tbs_in_ptpn
		tbs_proses_hi = objects.tbs_proses_netto
		jam_olah_hi = objects.hm_ebc
		cpo_tangki_hi = objects.total_cpo_tangki
		pengiriman_cpo_hi = objects.total_pengiriman_cpo
		penjualan_cpo_hi = objects.total_penjualan_cpo + objects.total_penjualan_cpo_palopo
		produksi_cpo_hi = objects.total_produksi_cpo
		penjualan_cpo_hi_bms = objects.total_penjualan_cpo
		produksi_cpo_hi_ptpn = objects.total_produksi_cpo_ptpn
		produksi_cpo_hi_bms = produksi_cpo_hi - produksi_cpo_hi_ptpn
		cpo_tangki_hi_ptpn = objects.total_cpo_tangki_ptpn
		cpo_tangki_hi_bms = cpo_tangki_hi - cpo_tangki_hi_ptpn
		penyerahan_cpo_hi_ptpn = objects.total_penyerahan_cpo_ptpn
		saldo_awal_cpo_hi = objects.saldo_awal_cpo
		saldo_awal_cpo_hi_ptpn = objects.saldo_awal_cpo_ptpn
		saldo_awal_cpo_hi_palopo = objects.saldo_awal_cpo_palopo
		saldo_awal_cpo_hi_bms = saldo_awal_cpo_hi - saldo_awal_cpo_hi_ptpn
		penjualan_cpo_hi_palopo = objects.total_penjualan_cpo_palopo
		cpo_tangki_hi_palopo = objects.total_cpo_tangki_palopo
		total_stock_kernel_hi = objects.total_stock_kernel
		saldo_awal_kernel_hi = objects.saldo_awal_kernel
		saldo_awal_kernel_hi_ptpn = objects.saldo_awal_kernel_ptpn
		saldo_awal_kernel_hi_mpa = objects.saldo_awal_kernel_mpa
		saldo_awal_kernel_hi_bms = saldo_awal_kernel_hi - saldo_awal_kernel_hi_ptpn		
		pengiriman_kernel_hi = objects.total_pengiriman_kernel
		penjualan_kernel_hi = objects.total_penjualan_kernel + objects.total_penjualan_kernel_mpa
		produksi_kernel_hi = objects.total_produksi_kernel
		penjualan_kernel_hi_bms = objects.total_penjualan_kernel
		produksi_kernel_hi_ptpn = objects.total_produksi_kernel_ptpn
		produksi_kernel_hi_bms = produksi_kernel_hi - produksi_kernel_hi_ptpn
		total_kernel_hi_ptpn = objects.total_stock_kernel_ptpn
		total_kernel_hi_bms = total_stock_kernel_hi - total_kernel_hi_ptpn
		penyerahan_kernel_hi_ptpn = objects.total_penyerahan_kernel_ptpn
		total_kernel_hi_ptpn = objects.total_stock_kernel_ptpn
		penjualan_kernel_hi_mpa = objects.total_penjualan_kernel_mpa
		total_kernel_hi_mpa = objects.total_stock_kernel_mpa

		date_prev = datetime.strptime(objects.date, "%Y-%m-%d").date()-relativedelta(months=1)
		end_date = date_prev.replace(day=monthrange(date_prev.year,date_prev.month)[1])
		prev_month_lhp = self.env['mill.lhp'].search([('date', '=', end_date)])
		buah_sisa_kemarin_shi = prev_month_lhp[0].saldo_akhir_tbs_netto if prev_month_lhp else 0
		prev_month_lhp_shi = self.env['mill.lhp'].search([('date', '<=', objects.date),('date', '>=', datetime.strptime(objects.date, "%Y-%m-%d").date().replace(day=1))])
		penerimaan_plasma_shi = sum(prev_month_lhp_shi.mapped('tbs_in_plasma'))
		penerimaan_ptpn_shi = sum(prev_month_lhp_shi.mapped('tbs_in_ptpn'))
		tbs_proses_shi = sum(prev_month_lhp_shi.mapped('tbs_proses_netto'))
		jam_olah_shi = sum(prev_month_lhp_shi.mapped('hm_ebc'))
		pengiriman_cpo_shi = sum(prev_month_lhp_shi.mapped('total_pengiriman_cpo'))
		penjualan_cpo_shi = sum(prev_month_lhp_shi.mapped('total_penjualan_cpo'))+sum(prev_month_lhp_shi.mapped('total_penjualan_cpo_palopo'))
		produksi_cpo_shi = sum(prev_month_lhp_shi.mapped('total_produksi_cpo'))
		produksi_cpo_shi_ptpn = sum(prev_month_lhp_shi.mapped('total_produksi_cpo_ptpn'))
		penjualan_cpo_shi_bms = sum(prev_month_lhp_shi.mapped('total_penjualan_cpo'))
		penyerahan_cpo_shi_ptpn = sum(prev_month_lhp_shi.mapped('total_penyerahan_cpo_ptpn'))
		saldo_awal_cpo_shi = prev_month_lhp[0].total_cpo_tangki if prev_month_lhp else 0
		saldo_awal_cpo_shi_ptpn = prev_month_lhp[0].total_cpo_tangki_ptpn if prev_month_lhp else 0
		saldo_awal_cpo_shi_palopo = prev_month_lhp[0].total_cpo_tangki_palopo if prev_month_lhp else 0
		saldo_awal_cpo_shi_bms = saldo_awal_cpo_shi - saldo_awal_cpo_shi_ptpn
		penjualan_cpo_shi_palopo = sum(prev_month_lhp_shi.mapped('total_penjualan_cpo_palopo'))
		cpo_tangki_shi_palopo = sum(prev_month_lhp_shi.mapped('total_cpo_tangki_palopo'))
		saldo_awal_kernel_shi = prev_month_lhp[0].total_stock_kernel if prev_month_lhp else 0
		saldo_awal_kernel_shi_ptpn = prev_month_lhp[0].total_stock_kernel_ptpn if prev_month_lhp else 0
		saldo_awal_kernel_shi_mpa = prev_month_lhp[0].total_stock_kernel_mpa if prev_month_lhp else 0
		saldo_awal_kernel_shi_bms = saldo_awal_kernel_shi - saldo_awal_kernel_shi_ptpn
		pengiriman_kernel_shi = sum(prev_month_lhp_shi.mapped('total_pengiriman_kernel'))
		penjualan_kernel_shi = sum(prev_month_lhp_shi.mapped('total_penjualan_kernel'))+sum(prev_month_lhp_shi.mapped('total_penjualan_kernel_mpa'))
		produksi_kernel_shi = sum(prev_month_lhp_shi.mapped('total_produksi_kernel'))
		produksi_kernel_shi_ptpn = sum(prev_month_lhp_shi.mapped('total_produksi_kernel_ptpn'))
		penjualan_kernel_shi_bms = sum(prev_month_lhp_shi.mapped('total_penjualan_kernel'))
		penyerahan_kernel_shi_ptpn = sum(prev_month_lhp_shi.mapped('total_penyerahan_kernel_ptpn'))
		penjualan_kernel_shi_mpa = sum(prev_month_lhp_shi.mapped('total_penjualan_kernel_mpa'))

		year_prev = datetime.strptime(objects.date, "%Y-%m-%d").date()-relativedelta(year=1)
		end_year = year_prev.replace(month=12, day=31)
		prev_year_lhp = self.env['mill.lhp'].search([('date', '=', end_year)])
		januari = end_year.replace(month=1, day=31, year=datetime.strptime(objects.date, "%Y-%m-%d").date().year)
		if not prev_year_lhp:
			prev_year_lhp = self.env['mill.lhp'].search([('date', '>=', januari),('date', '<=', objects.date)], order="date asc", limit=1)
		buah_sisa_kemarin_sbi = prev_year_lhp[0].saldo_awal_tbs_netto if prev_year_lhp else 0
		year_lhp = self.env['mill.lhp'].search([('date', '>=', januari),('date', '<=', objects.date)])
		penerimaan_plasma_sbi = sum(year_lhp.mapped('tbs_in_plasma'))
		penerimaan_ptpn_sbi = sum(year_lhp.mapped('tbs_in_ptpn'))
		tbs_proses_sbi = sum(year_lhp.mapped('tbs_proses_netto'))
		jam_olah_sbi = sum(year_lhp.mapped('hm_ebc'))
		pengiriman_cpo_sbi = sum(year_lhp.mapped('total_pengiriman_cpo'))
		penjualan_cpo_sbi = sum(year_lhp.mapped('total_penjualan_cpo'))+sum(year_lhp.mapped('total_penjualan_cpo_palopo'))
		produksi_cpo_sbi = sum(year_lhp.mapped('total_produksi_cpo'))
		penjualan_cpo_sbi_bms = sum(year_lhp.mapped('total_penjualan_cpo'))
		produksi_cpo_sbi_ptpn = sum(year_lhp.mapped('total_produksi_cpo_ptpn'))
		penyerahan_cpo_sbi_ptpn = sum(year_lhp.mapped('total_penyerahan_cpo_ptpn'))
		saldo_awal_cpo_sbi = prev_year_lhp[0].total_cpo_tangki if prev_year_lhp else 0
		saldo_awal_cpo_sbi_ptpn = prev_year_lhp[0].total_cpo_tangki_ptpn if prev_year_lhp else 0
		saldo_awal_cpo_sbi_palopo = prev_year_lhp[0].total_cpo_tangki_palopo if prev_year_lhp else 0
		saldo_awal_cpo_sbi_bms = saldo_awal_cpo_sbi - saldo_awal_cpo_sbi_ptpn
		penjualan_cpo_sbi_palopo = sum(year_lhp.mapped('total_penjualan_cpo_palopo'))
		cpo_tangki_sbi_palopo = sum(year_lhp.mapped('total_cpo_tangki_palopo'))
		saldo_awal_kernel_sbi = prev_year_lhp[0].total_stock_kernel if prev_year_lhp else 0
		saldo_awal_kernel_sbi_ptpn = prev_year_lhp[0].total_stock_kernel_ptpn if prev_year_lhp else 0
		saldo_awal_kernel_sbi_mpa = prev_year_lhp[0].total_stock_kernel_mpa if prev_year_lhp else 0
		saldo_awal_kernel_sbi_bms = saldo_awal_cpo_sbi - saldo_awal_kernel_sbi_ptpn
		pengiriman_kernel_sbi = sum(year_lhp.mapped('total_pengiriman_kernel'))
		penjualan_kernel_sbi = sum(year_lhp.mapped('total_penjualan_kernel'))+sum(year_lhp.mapped('total_penjualan_kernel_mpa'))
		produksi_kernel_sbi = sum(year_lhp.mapped('total_produksi_kernel'))
		produksi_kernel_sbi_ptpn = sum(year_lhp.mapped('total_produksi_kernel_ptpn'))
		penjualan_kernel_sbi_bms = sum(year_lhp.mapped('total_penjualan_kernel'))
		penyerahan_kernel_sbi_ptpn = sum(year_lhp.mapped('total_penyerahan_kernel_ptpn'))
		penjualan_kernel_sbi_mpa = sum(year_lhp.mapped('total_penjualan_kernel_mpa'))

		sheet.write(5, 0, 'A. TBS', bold)
		sheet.write(6, 1, 'BUAH SISA KEMARIN')
		sheet.write(6, 3, 'Kilogram')
		sheet.write(6, 4, buah_sisa_kemarin_hi,number)
		sheet.write(6, 5, buah_sisa_kemarin_shi,number)
		sheet.write(6, 6, buah_sisa_kemarin_sbi,number)
		sheet.write(7, 1, 'PENERIMAAN TBS PLASMA')
		sheet.write(7, 3, 'Kilogram')
		sheet.write(7, 4, penerimaan_plasma_hi,number)
		sheet.write(7, 5, penerimaan_plasma_shi,number)
		sheet.write(7, 6, penerimaan_plasma_sbi,number)
		sheet.write(8, 1, 'PENERIMAAN TBS PTPN')
		sheet.write(8, 3, 'Kilogram')
		sheet.write(8, 4, penerimaan_ptpn_hi,number)
		sheet.write(8, 5, penerimaan_ptpn_shi,number)
		sheet.write(8, 6, penerimaan_ptpn_sbi,number)
		sheet.write(9, 1, 'TOTAL PENERIMAAN TBS')
		sheet.write(9, 3, 'Kilogram')
		sheet.write_formula(9, 4, '=E8+E9',number)
		sheet.write_formula(9, 5, '=F8+F9',number)
		sheet.write_formula(9, 6, '=G8+G9',number)
		sheet.write(10, 1, 'TBS PROSES')
		sheet.write(10, 3, 'Kilogram')
		sheet.write(10, 4, tbs_proses_hi,number)
		sheet.write(10, 5, tbs_proses_shi,number)
		sheet.write(10, 6, tbs_proses_sbi,number)
		sheet.write(11, 1, 'RESTAN')
		sheet.write(11, 3, 'Kilogram')
		sheet.write_formula(11, 4, '=E7+E10-E11',number)
		sheet.write_formula(11, 5, '=E7+E10-E11',number)
		sheet.write_formula(11, 6, '=E7+E10-E11',number)
		sheet.write(12, 1, 'JUMLAH JAM OLAH')
		sheet.write(12, 3, 'Jam')
		sheet.write(12, 4, jam_olah_hi,number)
		sheet.write(12, 5, jam_olah_shi,number)
		sheet.write(12, 6, jam_olah_sbi,number)
		sheet.write(13, 1, 'THROUGHPUT')
		sheet.write(13, 3, 'Ton/Jam')
		sheet.write_formula(13, 4, '=E11/1000/E13',number)
		sheet.write_formula(13, 5, '=F11/1000/F13',number)
		sheet.write_formula(13, 6, '=G11/1000/G13',number)

		sheet.write(15, 0, 'B. CPO', bold)
		sheet.write(16, 1, 'STOCK CPO DALAM TANGKI')
		sheet.write(16, 3, 'Kilogram')
		sheet.merge_range(16, 4, 16, 6, cpo_tangki_hi,border2)
		sheet.write(17, 1, 'STOCK KEMARIN')
		sheet.write(17, 3, 'Kilogram')
		sheet.write(17, 4, saldo_awal_cpo_hi,number)
		sheet.write(17, 5, saldo_awal_cpo_shi,number)
		sheet.write(17, 6, saldo_awal_cpo_sbi,number)
		sheet.write(18, 1, 'PENGIRIMAN CPO')
		sheet.write(18, 3, 'Kilogram')
		sheet.write(18, 4, pengiriman_cpo_hi,number)
		sheet.write(18, 5, pengiriman_cpo_shi,number)
		sheet.write(18, 6, pengiriman_cpo_sbi,number)
		sheet.write(19, 1, 'PENJUALAN CPO')
		sheet.write(19, 3, 'Kilogram')
		sheet.write(19, 4, penjualan_cpo_hi,number)
		sheet.write(19, 5, penjualan_cpo_shi,number)
		sheet.write(19, 6, penjualan_cpo_sbi,number)
		sheet.write(20, 1, 'PRODUKSI CPO')
		sheet.write(20, 3, 'Kilogram')
		sheet.write(20, 4, produksi_cpo_hi,number)
		sheet.write(20, 5, produksi_cpo_shi,number)
		sheet.write(20, 6, produksi_cpo_sbi,number)
		sheet.write(21, 1, 'RENDEMEN CPO')
		sheet.write(21, 3, 'Persen %')
		sheet.write_formula(21, 4, '=(E21/E11)*100',number)
		sheet.write_formula(21, 5, '=(F21/F11)*100',number)
		sheet.write_formula(21, 6, '=(G21/G11)*100',number)

		sheet.write(23, 1, 'CPO BMS')
		sheet.write(24, 2, 'STOCK KEMARIN')
		sheet.write(24, 3, 'Kilogram')
		sheet.write(24, 4, saldo_awal_cpo_hi_bms,number)
		sheet.write(24, 5, saldo_awal_cpo_shi_bms,number)
		sheet.write(24, 6, saldo_awal_cpo_sbi_bms,number)
		sheet.write(25, 2, 'PENJUALAN')
		sheet.write(25, 3, 'Kilogram')
		sheet.write(25, 4, penjualan_cpo_hi_bms,number)
		sheet.write(25, 5, penjualan_cpo_shi_bms,number)
		sheet.write(25, 6, penjualan_cpo_sbi_bms,number)
		sheet.write(26, 2, 'PRODUKSI')
		sheet.write(26, 3, 'Kilogram')
		sheet.write(26, 4, produksi_cpo_hi_bms,number)
		sheet.write_formula(26, 5, '=F21-F33',number)
		sheet.write_formula(26, 6, '=G21-G33',number)
		sheet.write(27, 2, 'STOCK DALAM TANGKI')
		sheet.write(27, 3, 'Kilogram')
		sheet.write(27, 4, cpo_tangki_hi_bms,number)
		sheet.write(27, 5, cpo_tangki_hi_bms,number)
		sheet.write(27, 6, cpo_tangki_hi_bms,number)

		sheet.write(29, 1, 'CPO PTPN')
		sheet.write(30, 2, 'STOCK KEMARIN')
		sheet.write(30, 3, 'Kilogram')
		sheet.write(30, 4, saldo_awal_cpo_hi_ptpn,number)
		sheet.write(30, 5, saldo_awal_cpo_shi_ptpn,number)
		sheet.write(30, 6, saldo_awal_cpo_sbi_ptpn,number)
		sheet.write(31, 2, 'PENYERAHAN')
		sheet.write(31, 3, 'Kilogram')
		sheet.write(31, 4, penyerahan_cpo_hi_ptpn,number)
		sheet.write(31, 5, penyerahan_cpo_shi_ptpn,number)
		sheet.write(31, 6, penyerahan_cpo_sbi_ptpn,number)
		sheet.write(32, 2, 'PRODUKSI')
		sheet.write(32, 3, 'Kilogram')
		sheet.write(32, 4, produksi_cpo_hi_ptpn,number)
		sheet.write(32, 5, produksi_cpo_shi_ptpn,number)
		sheet.write(32, 6, produksi_cpo_sbi_ptpn,number)
		sheet.write(33, 2, 'STOCK DALAM TANGKI')
		sheet.write(33, 3, 'Kilogram')
		sheet.write(33, 4, cpo_tangki_hi_ptpn,number)
		sheet.write(33, 5, cpo_tangki_hi_ptpn,number)
		sheet.write(33, 6, cpo_tangki_hi_ptpn,number)

		sheet.write(35, 1, 'CPO PALOPO')
		sheet.write(36, 2, 'STOCK KEMARIN')
		sheet.write(36, 3, 'Kilogram')
		sheet.write(36, 4, saldo_awal_cpo_hi_palopo,number)
		sheet.write(36, 5, saldo_awal_cpo_shi_palopo,number)
		sheet.write(36, 6, saldo_awal_cpo_sbi_palopo,number)
		sheet.write(37, 2, 'PENJUALAN')
		sheet.write(37, 3, 'Kilogram')
		sheet.write(37, 4, penjualan_cpo_hi_palopo,number)
		sheet.write(37, 5, penjualan_cpo_shi_palopo,number)
		sheet.write(37, 6, penjualan_cpo_sbi_palopo,number)
		sheet.write(38, 2, 'STOCK DALAM TANGKI')
		sheet.write(38, 3, 'Kilogram')
		sheet.write(38, 4, cpo_tangki_hi_palopo,number)
		sheet.write(38, 5, cpo_tangki_hi_palopo,number)
		sheet.write(38, 6, cpo_tangki_hi_palopo,number)

		sheet.write(40, 0, 'C. KERNEL', bold)
		sheet.write(41, 1, 'TOTAL STOCK KERNEL')
		sheet.write(41, 3, 'Kilogram')
		sheet.merge_range(41, 4, 41, 6, total_stock_kernel_hi,border2)
		sheet.write(42, 1, 'STOCK KEMARIN')
		sheet.write(42, 3, 'Kilogram')
		sheet.write(42, 4, saldo_awal_kernel_hi,number)
		sheet.write(42, 5, saldo_awal_kernel_shi,number)
		sheet.write(42, 6, saldo_awal_kernel_sbi,number)
		sheet.write(43, 1, 'PENGIRIMAN KERNEL')
		sheet.write(43, 3, 'Kilogram')
		sheet.write(43, 4, pengiriman_kernel_hi,number)
		sheet.write(43, 5, pengiriman_kernel_shi,number)
		sheet.write(43, 6, pengiriman_kernel_sbi,number)
		sheet.write(44, 1, 'PENJUALAN KERNEL')
		sheet.write(44, 3, 'Kilogram')
		sheet.write(44, 4, penjualan_kernel_hi,number)
		sheet.write(44, 5, penjualan_kernel_shi,number)
		sheet.write(44, 6, penjualan_kernel_sbi,number)
		sheet.write(45, 1, 'PRODUKSI KERNEL')
		sheet.write(45, 3, 'Kilogram')
		sheet.write(45, 4, produksi_kernel_hi,number)
		sheet.write(45, 5, produksi_kernel_shi,number)
		sheet.write(45, 6, produksi_kernel_sbi,number)
		sheet.write(46, 1, 'RENDEMEN KERNEL')
		sheet.write(46, 3, 'Persen %')
		sheet.write_formula(46, 4, '=(E46/E11)*100',number)
		sheet.write_formula(46, 5, '=(F46/F11)*100',number)
		sheet.write_formula(46, 6, '=(G46/G11)*100',number)

		sheet.write(48, 1, 'KERNEL BMS')
		sheet.write(49, 2, 'STOCK KEMARIN')
		sheet.write(49, 3, 'Kilogram')
		sheet.write(49, 4, saldo_awal_kernel_hi_bms,number)
		sheet.write(49, 5, saldo_awal_kernel_shi_bms,number)
		sheet.write(49, 6, saldo_awal_kernel_sbi_bms,number)
		sheet.write(50, 2, 'PENJUALAN')
		sheet.write(50, 3, 'Kilogram')
		sheet.write(50, 4, penjualan_kernel_hi_bms,number)
		sheet.write(50, 5, penjualan_kernel_shi_bms,number)
		sheet.write(50, 6, penjualan_kernel_sbi_bms,number)
		sheet.write(51, 2, 'PRODUKSI')
		sheet.write(51, 3, 'Kilogram')
		sheet.write(51, 4, produksi_kernel_hi_bms,number)
		sheet.write_formula(51, 5, '=F46-F58',number)
		sheet.write_formula(51, 6, '=G46-G58',number)
		sheet.write(52, 2, 'TOTAL STOCK')
		sheet.write(52, 3, 'Kilogram')
		sheet.write(52, 4, total_kernel_hi_bms,number)
		sheet.write(52, 5, total_kernel_hi_bms,number)
		sheet.write(52, 6, total_kernel_hi_bms,number)

		sheet.write(54, 1, 'KERNEL PTPN')
		sheet.write(55, 2, 'STOCK KEMARIN')
		sheet.write(55, 3, 'Kilogram')
		sheet.write(55, 4, saldo_awal_kernel_hi_ptpn,number)
		sheet.write(55, 5, saldo_awal_kernel_shi_ptpn,number)
		sheet.write(55, 6, saldo_awal_kernel_sbi_ptpn,number)
		sheet.write(56, 2, 'PENYERAHAN')
		sheet.write(56, 3, 'Kilogram')
		sheet.write(56, 4, penyerahan_kernel_hi_ptpn,number)
		sheet.write(56, 5, penyerahan_kernel_shi_ptpn,number)
		sheet.write(56, 6, penyerahan_kernel_sbi_ptpn,number)
		sheet.write(57, 2, 'PRODUKSI')
		sheet.write(57, 3, 'Kilogram')
		sheet.write(57, 4, produksi_kernel_hi_ptpn,number)
		sheet.write(57, 5, produksi_kernel_shi_ptpn,number)
		sheet.write(57, 6, produksi_kernel_sbi_ptpn,number)
		sheet.write(58, 2, 'TOTAL STOCK')
		sheet.write(58, 3, 'Kilogram')
		sheet.write(58, 4, total_kernel_hi_ptpn,number)
		sheet.write(58, 5, total_kernel_hi_ptpn,number)
		sheet.write(58, 6, total_kernel_hi_ptpn,number)

		sheet.write(60, 1, 'KERNEL MPA')
		sheet.write(61, 2, 'STOCK KEMARIN')
		sheet.write(61, 3, 'Kilogram')
		sheet.write(61, 4, saldo_awal_kernel_hi_mpa,number)
		sheet.write(61, 5, saldo_awal_kernel_shi_mpa,number)
		sheet.write(61, 6, saldo_awal_kernel_sbi_mpa,number)
		sheet.write(62, 2, 'PENJUALAN')
		sheet.write(62, 3, 'Kilogram')
		sheet.write(62, 4, penjualan_kernel_hi_mpa,number)
		sheet.write(62, 5, penjualan_kernel_shi_mpa,number)
		sheet.write(62, 6, penjualan_kernel_sbi_mpa,number)
		sheet.write(63, 2, 'TOTAL STOCK')
		sheet.write(63, 3, 'Kilogram')
		sheet.write(63, 4, total_kernel_hi_mpa,number)
		sheet.write(63, 5, total_kernel_hi_mpa,number)
		sheet.write(63, 6, total_kernel_hi_mpa,number)

LHPkumulatifXlsx('report.report_lhp_kumulatif_xlsx',
				 'mill.lhp')