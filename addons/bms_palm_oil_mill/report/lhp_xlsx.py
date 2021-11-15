from odoo import api, fields, models

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

class ReportLHPXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, objects):
        xlsx_style = {
            'arial': {'font_name': 'Arial', 'font_size': 10},
            'xlsx_title': {'bold': True, 'font_size':12, 'align': 'left'},
            'xlsx_cell': {'font_size':8},
            'borders_all': {'border':1},
            'border_top': {'top':1},
            'border_bottom': {'bottom':1},
            'bold': {'bold':True},
            'underline': {'underline': True},
            'italic': {'italic': True},

            'left': {'align': 'left'},
            'center': {'align': 'center'},
            'right': {'align': 'right'},
            'top': {'valign': 'top'},
            'vcenter': {'valign': 'vcenter'},
            'bottom': {'valign': 'bottom'},
            'wrap': {'text_wrap':True},
            
            'fill_blue': {'pattern':1, 'fg_color':'#99fff0'},
            'fill_grey': {'pattern':1, 'fg_color':'#e0e0e0'},
            'fill': {'pattern': 1, 'fg_color': '#ffff99'},

            'decimal': {'num_format':'#,##0.00;-#,##0.00;-'},
            'decimal4': {'num_format':'#,##0.0000;-#,##0.0000;-'},
            'percentage': {'num_format': '0%'},
            'percentage2': {'num_format': '0.00%'},
            'integer': {'num_format':'#,##0;-#,##0;-'},
            'date': {'num_format': 'dd-mmm-yy'},
            'date2': {'num_format': 'dd/mm/yy'},
        }

        def get_address(partner):
            address = ""
            if partner.street:
                address+= partner.street+". "
            if partner.street2:
                address+= partner.street2+". "
            if partner.city:
                if partner.state_id:
                    address+= partner.city + ", " + partner.state_id.name + ". "
                else:
                    address+= partner.city + ". "
            if partner.country_id:
                address+= partner.country_id.name + ". "
            return address

        hari_ind = {'Sunday': 'Minggu', 'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu'}
        for lhp in objects:
            lhp_date = datetime.strptime(lhp.date, DF)
            tanggal = lhp_date.day
            hari = hari_ind.get(lhp_date.strftime('%A'),'Not Found')
            bulan = lhp_date.strftime('%b %y')
            sheet_name = 'LHP CPO PK %s'%tanggal
            sheet = workbook.add_worksheet(sheet_name)
            sheet.set_portrait()
            sheet.set_footer('&R&6&"Courier New,Italic"Page &P of &N', {'margin': 0.25})
            row = 0

            column_width = [2, 7, 17, 10, 7, 10, 13, 13, 13, 13, 13, 13, 13, 13]
            for col_pos in range(0,14):
                sheet.set_column(col_pos, col_pos, column_width[col_pos])
            # KOP SUART

            # HEADER
            header1_cell_format = {'font_name': 'Arial', 'font_size': 11, 'valign': 'top', 'align': 'centre'}
            header1_style = workbook.add_format(header1_cell_format)
            sheet.merge_range(6, 1, 6, 13, "LAPORAN HARIAN PRODUKSI & PENGIRIMAN (CPO & KERNEL)", header1_style)
            
            header2_cell_format = {'font_name': 'Arial', 'font_size': 11, 'valign': 'top', 'align': 'left'}
            header2_style = workbook.add_format(header2_cell_format)
            # Header Kiri
            sheet.write_string(8, 1, "Bulan", header2_style)
            sheet.write_string(8, 2, bulan, header2_style)
            sheet.write_string(9, 1, "Tanggal", header2_style)
            sheet.write_number(9, 2, tanggal, header2_style)
            sheet.write_string(10, 1, "Hari", header2_style)
            sheet.write_string(10, 2, hari, header2_style)
            # Header Kanan
            sheet.write_string(8, 11, "Start Proses", header2_style)
            sheet.write_number(8, 12, lhp.sounding_id.start_olah_time, header2_style)
            sheet.write_string(8, 13, "WIB", header2_style)
            sheet.write_string(9, 11, "Stop Proses", header2_style)
            sheet.write_number(9, 12, lhp.sounding_id.stop_olah_time, header2_style)
            sheet.write_string(9, 13, "WIB", header2_style)

            # HEADER TABLE
            header_cell_format = {'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'border': 1}
            header_style = workbook.add_format(header_cell_format)

            sheet.merge_range(12, 1, 13, 1, 'NO.', header_style)
            sheet.merge_range(12, 2, 13, 4, 'URAIAN', header_style)
            sheet.merge_range(12, 5, 13, 5, 'SAT', header_style)
            sheet.merge_range(12, 6, 12, 9, 'HI', header_style)
            sheet.write_string(13, 6, 'CPO', header_style)
            sheet.write_string(13, 7, '%', header_style)
            sheet.write_string(13, 8, 'KERNEL', header_style)
            sheet.write_string(13, 9, '%', header_style)
            sheet.merge_range(12, 10, 12, 13, 'AKUMULASI S/D HI', header_style)
            sheet.write_string(13, 10, 'CPO', header_style)
            sheet.write_string(13, 11, '%', header_style)
            sheet.write_string(13, 12, 'KERNEL', header_style)
            sheet.write_string(13, 13, '%', header_style)

            # PART 1: DETAIL LAPORAN
            content_cell_format = {'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'center'}
            content_style = workbook.add_format(content_cell_format)
            content2_cell_format = content_cell_format.copy()
            content2_cell_format.update({'align': 'left'})
            content2_style = workbook.add_format(content2_cell_format)
            numeric_cell_format = content_cell_format.copy()
            numeric_cell_format.update({'align': 'right', 'num_format':'#,##0;-#,##0;-'})
            numeric_style = workbook.add_format(numeric_cell_format)

            sheet.write_number(14, 1, 1, content_style)
            # sheet.write_string(14, 2, "Saldo Awal ( CPO / PK )", content2_style)
            # sheet.write_string(14, 3, "", content_style)
            # sheet.write_string(14, 4, "", content_style)
            sheet.merge_range(14, 2, 14, 4, "Saldo Awal ( CPO / PK )", content2_style)
            sheet.write_string(14, 5, "kg", content_style)
            sheet.write_number(14, 6, lhp.saldo_awal_cpo, numeric_style)
            sheet.write_string(14, 7, "", content_style)
            sheet.write_number(14, 8, lhp.saldo_awal_kernel, numeric_style)
            sheet.write_string(14, 9, "", content_style)
            sheet.write_string(14, 10, "", numeric_style)
            sheet.write_string(14, 11, "", content_style)
            sheet.write_string(14, 12, "", numeric_style)
            sheet.write_string(14, 13, "", content_style)

            sheet.merge_range(15, 1, 16, 1, 2, content_style)
            sheet.merge_range(15, 2, 16, 3, "Saldo Awal TBS", content_style)
            sheet.write_string(15, 4, "Brutto", content2_style)
            sheet.write_string(15, 5, "kg", content_style)
            # sheet.write_number(15, 6, lhp.saldo_awal_tbs_bruto or 0.0, numeric_style)
            sheet.write_string(15, 7, "", content_style)
            sheet.write_string(15, 8, "", numeric_style)
            sheet.write_string(15, 9, "", content_style)
            sheet.write_string(15, 10, "", numeric_style)
            sheet.write_string(15, 11, "", content_style)
            sheet.write_string(15, 12, "", numeric_style)
            sheet.write_string(15, 13, "", content_style)
            sheet.write_string(16, 4, "Netto", content2_style)
            sheet.write_string(16, 5, "kg", content_style)
            # sheet.write_number(16, 6, lhp.saldo_awal_tbs_netto or 0.0, numeric_style)
            sheet.write_string(16, 7, "", content_style)
            sheet.write_string(16, 8, "", numeric_style)
            sheet.write_string(16, 9, "", content_style)
            sheet.write_string(16, 10, "", numeric_style)
            sheet.write_string(16, 11, "", content_style)
            sheet.write_string(16, 12, "", numeric_style)
            sheet.write_string(16, 13, "", content_style)

            current_period_start_date = lhp_date + relativedelta(day=1)
            lhp_current_period = self.env['mill.lhp'].search([('date','>=',current_period_start_date.strftime(DF)),('date','<',lhp.date)])
            cum_tbs_proses_bruto = lhp_current_period and sum(lhp_current_period.mapped('tbs_proses_brutto')) or 0.0
            cum_tbs_proses_netto = lhp_current_period and sum(lhp_current_period.mapped('tbs_proses_netto')) or 0.0
            trans_date = lhp_date + relativedelta(days=-1)
            current_period_tbs_in = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENERIMAAN TBS'), \
                    ('TIMBANG_RECSTS','=','F'),('TIMBANG_OUT_DATE','>=',current_period_start_date.strftime(DF)), \
                    ('TIMBANG_OUT_DATE','<',trans_date.strftime(DF))])
            cum_tbs_in_netto = current_period_tbs_in and sum(current_period_tbs_in.mapped('TIMBANG_TOTALBERAT')) or 0.0
            cum_tbs_in_bruto = current_period_tbs_in and sum(current_period_tbs_in.mapped('TIMBANG_NETTO')) or 0.0
            cum_tbs_in_sortasi = cum_tbs_in_bruto - cum_tbs_in_netto
            sheet.merge_range(17, 1, 19, 1, 3, content_style)
            sheet.merge_range(17, 2, 19, 3, "Penerimaan TBS", content_style)
            sheet.write_string(17, 4, "Brutto", content2_style)
            sheet.write_string(17, 5, "kg", content_style)
            sheet.write_number(17, 6, lhp.tbs_in_brutto or 0.0, numeric_style)
            sheet.write_string(17, 7, "", content_style)
            sheet.write_string(17, 8, "", numeric_style)
            sheet.write_string(17, 9, "", content_style)
            sheet.write_number(17, 10, (lhp.tbs_in_brutto or 0.0) + cum_tbs_in_bruto, numeric_style)
            sheet.write_string(17, 11, "", content_style)
            sheet.write_string(17, 12, "", numeric_style)
            sheet.write_string(17, 13, "", content_style)
            sheet.write_string(18, 4, "Sortasi", content2_style)
            sheet.write_string(18, 5, "kg", content_style)
            sheet.write_number(18, 6, (lhp.tbs_in_brutto or 0.0) - (lhp.tbs_in_netto or 0.0), numeric_style)
            sheet.write_string(18, 7, "", content_style)
            sheet.write_string(18, 8, "", numeric_style)
            sheet.write_string(18, 9, "", content_style)
            sheet.write_number(18, 10, ((lhp.tbs_in_brutto or 0.0) - (lhp.tbs_in_netto or 0.0)) + cum_tbs_in_sortasi, numeric_style)
            sheet.write_string(18, 11, "", content_style)
            sheet.write_string(18, 12, "", numeric_style)
            sheet.write_string(18, 13, "", content_style)
            sheet.write_string(19, 4, "Netto", content2_style)
            sheet.write_string(19, 5, "kg", content_style)
            sheet.write_number(19, 6, lhp.tbs_in_netto or 0.0, numeric_style)
            sheet.write_string(19, 7, "", content_style)
            sheet.write_string(19, 8, "", numeric_style)
            sheet.write_string(19, 9, "", content_style)
            sheet.write_number(19, 10, (lhp.tbs_in_netto or 0.0) + cum_tbs_in_netto, numeric_style)
            sheet.write_string(19, 11, "", content_style)
            sheet.write_string(19, 12, "", numeric_style)
            sheet.write_string(19, 13, "", content_style)

            sheet.merge_range(20, 1, 21, 1, 4, content_style)
            sheet.merge_range(20, 2, 21, 3, "Pengiriman TBS ke Pabrik Lain", content_style)
            sheet.write_string(20, 4, "Brutto", content2_style)
            sheet.write_string(20, 5, "kg", content_style)
            sheet.write_number(20, 6, 0, numeric_style)
            sheet.write_string(20, 7, "", content_style)
            sheet.write_number(20, 8, 0, numeric_style)
            sheet.write_string(20, 9, "", content_style)
            sheet.write_number(20, 10, 0, numeric_style)
            sheet.write_string(20, 11, "", content_style)
            sheet.write_number(20, 12, 0, numeric_style)
            sheet.write_string(20, 13, "", content_style)
            sheet.write_string(21, 4, "Netto", content2_style)
            sheet.write_string(21, 5, "kg", content_style)
            sheet.write_number(21, 6, 0, numeric_style)
            sheet.write_string(21, 7, "", content_style)
            sheet.write_number(21, 8, 0, numeric_style)
            sheet.write_string(21, 9, "", content_style)
            sheet.write_number(21, 10, 0, numeric_style)
            sheet.write_string(21, 11, "", content_style)
            sheet.write_number(21, 12, 0, numeric_style)
            sheet.write_string(21, 13, "", content_style)

            sheet.merge_range(22, 1, 23, 1, 5, content_style)
            sheet.merge_range(22, 2, 23, 3, "TBS Olah", content_style)
            sheet.write_string(22, 4, "Brutto", content2_style)
            sheet.write_string(22, 5, "kg", content_style)
            sheet.write_number(22, 6, lhp.tbs_proses_brutto or 0.0, numeric_style)
            sheet.write_number(22, 7, 0, numeric_style)
            sheet.write_number(22, 8, 0, numeric_style)
            sheet.write_number(22, 9, 0, numeric_style)
            sheet.write_number(22, 10, (lhp.tbs_proses_brutto or 0.0) + cum_tbs_proses_bruto, numeric_style)
            sheet.write_number(22, 11, 0, numeric_style)
            sheet.write_number(22, 12, 0, numeric_style)
            sheet.write_number(22, 13, 0, numeric_style)
            sheet.write_string(23, 4, "Netto", content2_style)
            sheet.write_string(23, 5, "kg", content_style)
            sheet.write_number(23, 6, lhp.tbs_proses_netto or 0.0, numeric_style)
            sheet.write_number(23, 7, 0, numeric_style)
            sheet.write_number(23, 8, 0, numeric_style)
            sheet.write_number(23, 9, 0, numeric_style)
            sheet.write_number(23, 10, (lhp.tbs_proses_netto or 0.0) + cum_tbs_proses_netto, numeric_style)
            sheet.write_number(23, 11, 0, numeric_style)
            sheet.write_number(23, 12, 0, numeric_style)
            sheet.write_number(23, 13, 0, numeric_style)

            cum_produksi_cpo = lhp_current_period and sum(lhp_current_period.mapped('total_produksi_cpo')) or 0.0
            cum_produksi_kernel = lhp_current_period and sum(lhp_current_period.mapped('total_produksi_kernel')) or 0.0
            sheet.write_number(24, 1, 6, content_style)
            # sheet.write_string(24, 2, "Hasil Produksi", content2_style)
            # sheet.write_string(24, 3, "", content_style)
            # sheet.write_string(24, 4, "", content_style)
            sheet.merge_range(24, 2, 24, 4, "Hasil Produksi", content2_style)
            sheet.write_string(24, 5, "kg", content_style)
            sheet.write_number(24, 6, lhp.total_produksi_cpo or 0.0, numeric_style)
            sheet.write_string(24, 7, "", content_style)
            sheet.write_number(24, 8, lhp.total_produksi_kernel or 0.0, numeric_style)
            sheet.write_string(24, 9, "", content_style)
            sheet.write_number(24, 10, (lhp.total_produksi_cpo or 0.0) + cum_produksi_cpo, numeric_style)
            sheet.write_string(24, 11, "", content_style)
            sheet.write_number(24, 12, (lhp.total_produksi_kernel or 0.0) + cum_produksi_kernel, numeric_style)
            sheet.write_string(24, 13, "", content_style)

            cum_durasi_olah = lhp_current_period and sum(lhp_current_period.mapped('sounding_id.durasi_olah')) or 0.0
            sheet.write_number(25, 1, 7, content_style)
            # sheet.write_string(25, 2, "Jumlah Jam Olah", content2_style)
            # sheet.write_string(25, 3, "", content_style)
            # sheet.write_string(25, 4, "", content_style)
            sheet.merge_range(25, 2, 25, 4, "Jumlah Jam Olah", content2_style)
            sheet.write_string(25, 5, "Jam", content_style)
            sheet.write_number(25, 6, lhp.sounding_id.durasi_olah or 0.0, numeric_style)
            sheet.write_string(25, 7, "", content_style)
            sheet.write_string(25, 8, "", numeric_style)
            sheet.write_string(25, 9, "", content_style)
            sheet.write_number(25, 10, (lhp.sounding_id.durasi_olah or 0.0) + cum_durasi_olah, numeric_style)
            sheet.write_string(25, 11, "", content_style)
            sheet.write_string(25, 12, "", numeric_style)
            sheet.write_string(25, 13, "", content_style)

            durasi_stagnan = 0.0
            cum_durasi_stagnan = 0.0
            sheet.write_number(26, 1, 8, content_style)
            # sheet.write_string(26, 2, "Jumlah Jam Stagnasi", content2_style)
            # sheet.write_string(26, 3, "", content_style)
            # sheet.write_string(26, 4, "", content_style)
            sheet.merge_range(26, 2, 26, 4, "Jumlah Jam Stagnasi", content2_style)
            sheet.write_string(26, 5, "Jam", content_style)
            sheet.write_number(26, 6, durasi_stagnan, numeric_style)
            sheet.write_string(26, 7, "", content_style)
            sheet.write_string(26, 8, "", numeric_style)
            sheet.write_string(26, 9, "", content_style)
            sheet.write_number(26, 10, durasi_stagnan + cum_durasi_stagnan, numeric_style)
            sheet.write_string(26, 11, "", content_style)
            sheet.write_string(26, 12, "", numeric_style)
            sheet.write_string(26, 13, "", content_style)

            durasi_olah_net = (lhp.sounding_id.durasi_olah or 0.0) - durasi_stagnan
            cum_durasi_olah_net = (lhp.sounding_id.durasi_olah or 0.0) - durasi_stagnan
            sheet.write_number(27, 1, 9, content_style)
            # sheet.write_string(27, 2, "Kapasitas Produksi", content2_style)
            # sheet.write_string(27, 3, "", content_style)
            # sheet.write_string(27, 4, "", content_style)
            sheet.merge_range(27, 2, 27, 4, "Kapasitas Produksi", content2_style)
            sheet.write_string(27, 5, "Ton/Jam", content_style)
            sheet.write_number(27, 6, durasi_olah_net and (lhp.tbs_proses_brutto or 0.0)/durasi_olah_net or 0.0, numeric_style)
            sheet.write_string(27, 7, "", content_style)
            sheet.write_string(27, 8, "", numeric_style)
            sheet.write_string(27, 9, "", content_style)
            sheet.write_number(27, 10, cum_durasi_olah_net and ((lhp.tbs_proses_brutto or 0.0) + cum_tbs_proses_bruto)/cum_durasi_olah_net or 0.0, numeric_style)
            sheet.write_string(27, 11, "", content_style)
            sheet.write_string(27, 12, "", numeric_style)
            sheet.write_string(27, 13, "", content_style)

            sheet.write_number(28, 1, 10, content_style)
            # sheet.write_string(28, 2, "Stock Dalam Proses (Sludge)", content2_style)
            # sheet.write_string(28, 3, "", content_style)
            # sheet.write_string(28, 4, "", content_style)
            sheet.merge_range(28, 2, 28, 4, "Stock Dalam Proses (Sludge)", content2_style)
            sheet.write_string(28, 5, "kg", content_style)
            sheet.write_number(28, 6, 0, numeric_style)
            sheet.write_string(28, 7, "", content_style)
            sheet.write_string(28, 8, "", numeric_style)
            sheet.write_string(28, 9, "", content_style)
            sheet.write_number(28, 10, 0, numeric_style)
            sheet.write_string(28, 11, "", content_style)
            sheet.write_string(28, 12, "", numeric_style)
            sheet.write_string(28, 13, "", content_style)

            sheet.write_number(29, 1, 11, content_style)
            # sheet.write_string(29, 2, "Sludge & Water terbuang cuci tangki", content2_style)
            # sheet.write_string(29, 3, "", content_style)
            # sheet.write_string(29, 4, "", content_style)
            sheet.merge_range(29, 2, 29, 4, "Sludge & Water terbuang cuci tangki", content2_style)
            sheet.write_string(29, 5, "kg", content_style)
            sheet.write_number(29, 6, 0, numeric_style)
            sheet.write_string(29, 7, "", content_style)
            sheet.write_string(29, 8, "", numeric_style)
            sheet.write_string(29, 9, "", content_style)
            sheet.write_number(29, 10, 0, numeric_style)
            sheet.write_string(29, 11, "", content_style)
            sheet.write_string(29, 12, "", numeric_style)
            sheet.write_string(29, 13, "", content_style)

            current_period_cpo_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENJUALAN CPO'), \
                    ('TIMBANG_RECSTS','=','F'),('TIMBANG_OUT_DATE','>=',current_period_start_date.strftime(DF)), \
                    ('TIMBANG_OUT_DATE','<',trans_date.strftime(DF))])
            current_period_pk_out = self.env['weighbridge.scale.metro'].search([('TIMBANG_TIPETRANS','=','PENJUALAN KERNEL'), \
                    ('TIMBANG_RECSTS','=','F'),('TIMBANG_OUT_DATE','>=',current_period_start_date.strftime(DF)), \
                    ('TIMBANG_OUT_DATE','<',trans_date.strftime(DF))])
            cum_cpo_out = current_period_cpo_out and current_period_cpo_out.mapped('TIMBANG_TOTALBERAT') or 0.0
            cum_pk_out = current_period_pk_out and current_period_pk_out.mapped('TIMBANG_TOTALBERAT') or 0.0
            sheet.write_number(30, 1, 12, content_style)
            # sheet.write_string(30, 2, "Pengiriman ( CPO / PK )", content2_style)
            # sheet.write_string(30, 3, "", content_style)
            # sheet.write_string(30, 4, "", content_style)
            sheet.merge_range(30, 2, 30, 4, "Pengiriman ( CPO / PK )", content2_style)
            sheet.write_string(30, 5, "kg", content_style)
            sheet.write_number(30, 6, lhp.total_pengiriman_cpo or 0.0, numeric_style)
            sheet.write_string(30, 7, "", content_style)
            sheet.write_number(30, 8, lhp.total_pengiriman_kernel or 0.0, numeric_style)
            sheet.write_string(30, 9, "", content_style)
            sheet.write_number(30, 10, (lhp.total_pengiriman_cpo or 0.0) + cum_cpo_out, numeric_style)
            sheet.write_string(30, 11, "", content_style)
            sheet.write_number(30, 12, (lhp.total_pengiriman_kernel or 0.0) + cum_pk_out, numeric_style)
            sheet.write_string(30, 13, "", content_style)


            onhand_cpo = lhp.saldo_awal_cpo + lhp.total_produksi_cpo - lhp.total_pengiriman_cpo
            onhand_kernel = lhp.saldo_awal_kernel + lhp.total_produksi_kernel - lhp.total_pengiriman_kernel
            sheet.write_number(31, 1, 13, content_style)
            # sheet.write_string(31, 2, "Stock Siap Kirim ( CPO / PK )", content2_style)
            # sheet.write_string(31, 3, "", content_style)
            # sheet.write_string(31, 4, "", content_style)
            sheet.merge_range(31, 2, 31, 4, "Stock Siap Kirim ( CPO / PK )", content2_style)
            sheet.write_string(31, 5, "kg", content_style)
            sheet.write_number(31, 6, onhand_cpo, numeric_style)
            sheet.write_string(31, 7, "", content_style)
            sheet.write_number(31, 8, onhand_kernel, numeric_style)
            sheet.write_string(31, 9, "", content_style)
            sheet.write_string(31, 10, "", numeric_style)
            sheet.write_string(31, 11, "", content_style)
            sheet.write_string(31, 12, "", numeric_style)
            sheet.write_string(31, 13, "", content_style)

            closing_cpo = onhand_cpo
            closing_kernel = onhand_kernel
            sheet.write_number(32, 1, 14, content_style)
            # sheet.write_string(32, 2, "Stock Akhir ( CPO / PK )", content2_style)
            # sheet.write_string(32, 3, "", content_style)
            # sheet.write_string(32, 4, "", content_style)
            sheet.merge_range(32, 2, 32, 4, "Stock Akhir ( CPO / PK )", content2_style)
            sheet.write_string(32, 5, "kg", content_style)
            sheet.write_number(32, 6, closing_cpo, numeric_style)
            sheet.write_string(32, 7, "", content_style)
            sheet.write_number(32, 8, closing_kernel , numeric_style)
            sheet.write_string(32, 9, "", content_style)
            sheet.write_string(32, 10, "", numeric_style)
            sheet.write_string(32, 11, "", content_style)
            sheet.write_string(32, 12, "", numeric_style)
            sheet.write_string(32, 13, "", content_style)

            closing_tbs_bruto = 0.0
            sheet.write_number(33, 1, 15, content_style)
            # sheet.write_string(33, 2, "Stock Akhir TBS ( Brutto )", content2_style)
            # sheet.write_string(33, 3, "", content_style)
            # sheet.write_string(33, 4, "", content_style)
            sheet.merge_range(33, 2, 33, 4, "Stock Akhir TBS ( Brutto )", content2_style)
            sheet.write_string(33, 5, "kg", content_style)
            sheet.write_number(33, 6, closing_tbs_bruto, numeric_style)
            sheet.write_string(33, 7, "", content_style)
            sheet.write_string(33, 8, "", numeric_style)
            sheet.write_string(33, 9, "", content_style)
            sheet.write_string(33, 10, "", numeric_style)
            sheet.write_string(33, 11, "", content_style)
            sheet.write_string(33, 12, "", numeric_style)
            sheet.write_string(33, 13, "", content_style)

            closing_tbs_netto = 0.0
            sheet.write_number(34, 1, 16, content_style)
            # sheet.write_string(34, 2, "Stock Akhir TBS ( Netto )", content2_style)
            # sheet.write_string(34, 3, "", content_style)
            # sheet.write_string(34, 4, "", content_style)
            sheet.merge_range(34, 2, 34, 4, "Stock Akhir TBS ( Netto )", content2_style)
            sheet.write_string(34, 5, "kg", content_style)
            sheet.write_number(34, 6, closing_tbs_netto, numeric_style)
            sheet.write_string(34, 7, "", content_style)
            sheet.write_string(34, 8, "", numeric_style)
            sheet.write_string(34, 9, "", content_style)
            sheet.write_string(34, 10, "", numeric_style)
            sheet.write_string(34, 11, "", content_style)
            sheet.write_string(34, 12, "", numeric_style)
            sheet.write_string(34, 13, "", content_style)

            # PART 2: PERINCIAN STOCK CPO DAN KERNEL
            c_cell_format = {'font_name': 'Arial', 'font_size': 11}
            c_style = workbook.add_format(c_cell_format)
            content_cell_format = {'font_name': 'Arial', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'border': 1}
            content_style = workbook.add_format(content_cell_format)
            content2_cell_format = content_cell_format.copy()
            content2_cell_format.update({'align': 'left'})
            content2_style = workbook.add_format(content2_cell_format)
            numeric_cell_format = content_cell_format.copy()
            numeric_cell_format.update({'align': 'right', 'num_format':'#,##0;-#,##0;-'})
            numeric_style = workbook.add_format(numeric_cell_format)
            numeric1_cell_format = content_cell_format.copy()
            numeric1_cell_format.update({'num_format':'#,##0.00;-#,##0.00;-'})
            numeric1_style = workbook.add_format(numeric1_cell_format)
            numeric2_cell_format = content_cell_format.copy()
            numeric2_cell_format.update({'align': 'right', 'num_format':'#.0%;-'})
            numeric2_style = workbook.add_format(numeric2_cell_format)

            sheet.write_string(36, 2, "Perincian Stock CPO", c_style)
            sheet.write_string(36, 7, "Perincian Stock Kernel", c_style)

            sheet.write_string(37, 2, "Storage Tank", content_style)
            sheet.write_string(38, 2, "No. 1", content_style)
            sheet.write_string(39, 2, "No. 2", content_style)
            sheet.write_string(40, 2, "No. 3", content_style)
            sheet.merge_range(41, 2, 41, 3, "Total Stock", content_style)
            sheet.merge_range(42, 2, 42, 3, "FFA Produksi CPO", content2_style)
            sheet.merge_range(43, 2, 43, 3, "FFA Pengiriman CPO", content2_style)
            sheet.merge_range(44, 2, 44, 3, "Dirth Produksi PK", content2_style)
            sheet.merge_range(45, 2, 45, 3, "Moisture Kernel", content2_style)

            sheet.write_string(37, 3, "FFA", content_style)
            sheet.write_number(38, 3, 1, numeric1_style)
            sheet.write_number(39, 3, 1, numeric1_style)
            sheet.write_number(40, 3, 1, numeric1_style)
            
            sheet.write_string(37, 4, "Sat", content_style)
            sheet.write_string(38, 4, "kg", content_style)
            sheet.write_string(39, 4, "kg", content_style)
            sheet.write_string(40, 4, "kg", content_style)
            sheet.write_string(41, 4, "kg", content_style)
            sheet.write_number(42, 4, 1, numeric1_style)
            sheet.write_number(43, 4, 1, numeric1_style)
            sheet.write_number(44, 4, 1, numeric2_style)
            sheet.write_number(45, 4, 1, numeric2_style)
            
            sheet.write_string(37, 5, "Qty", content_style)
            sheet.write_number(38, 5, 1, numeric_style)
            sheet.write_number(39, 5, 1, numeric_style)
            sheet.write_number(40, 5, 1, numeric_style)
            sheet.write_number(41, 5, 1, numeric_style)

            sheet.write_string(37, 6, "Kap. Tanki", content_style)
            sheet.write_number(38, 6, 1, numeric_style)
            sheet.write_number(39, 6, 1, numeric_style)
            sheet.write_number(40, 6, 1, numeric_style)
            sheet.write_number(41, 6, 1, numeric_style)

            sheet.write_string(37, 7, "Lokasi", content_style)
            sheet.write_string(38, 7, "Bunker 1", content2_style)
            sheet.write_string(39, 7, "Bunker 2", content2_style)
            sheet.write_string(40, 7, "Kernel Silo 1", content2_style)
            sheet.write_string(41, 7, "Kernel Silo 2", content2_style)
            sheet.write_string(42, 7, "Kernel Silo 3", content2_style)
            sheet.write_string(43, 7, "Nut Silo 1", content2_style)
            sheet.write_string(44, 7, "Nut Silo 2", content2_style)
            sheet.write_string(45, 7, "Nut Silo 3", content2_style)
            sheet.write_string(46, 7, "Kernel dilantai", content2_style)
            sheet.write_string(47, 7, "Nut dilantai", content2_style)
            sheet.write_string(48, 7, "Total Stock", content_style)

            sheet.write_string(37, 8, "DIRT", content_style)
            sheet.write_number(38, 8, 1, numeric2_style)
            sheet.write_number(39, 8, 1, numeric2_style)
            sheet.write_number(40, 8, 1, numeric2_style)
            sheet.write_number(41, 8, 1, numeric2_style)
            sheet.write_number(42, 8, 1, numeric2_style)
            sheet.write_number(43, 8, 1, numeric2_style)
            sheet.write_number(44, 8, 1, numeric2_style)
            sheet.write_number(45, 8, 1, numeric2_style)
            sheet.write_number(46, 8, 1, numeric2_style)
            sheet.write_number(47, 8, 1, numeric2_style)
            sheet.write_string(48, 8, "", content_style)

            sheet.write_string(37, 9, "Sat", content_style)
            sheet.write_string(38, 9, "kg", content_style)
            sheet.write_string(39, 9, "kg", content_style)
            sheet.write_string(40, 9, "kg", content_style)
            sheet.write_string(41, 9, "kg", content_style)
            sheet.write_string(42, 9, "kg", content_style)
            sheet.write_string(43, 9, "kg", content_style)
            sheet.write_string(44, 9, "kg", content_style)
            sheet.write_string(45, 9, "kg", content_style)
            sheet.write_string(46, 9, "kg", content_style)
            sheet.write_string(48, 9, "kg", content_style)

            sheet.write_string(37, 10, "Qty", content_style)
            sheet.write_number(38, 10, 1, numeric_style)
            sheet.write_number(39, 10, 1, numeric_style)
            sheet.write_number(40, 10, 1, numeric_style)
            sheet.write_number(41, 10, 1, numeric_style)
            sheet.write_number(42, 10, 1, numeric_style)
            sheet.write_number(43, 10, 1, numeric_style)
            sheet.write_number(44, 10, 1, numeric_style)
            sheet.write_number(45, 10, 1, numeric_style)
            sheet.write_number(46, 10, 1, numeric_style)
            sheet.write_number(47, 10, 1, numeric_style)
            sheet.write_number(48, 10, 1, numeric_style)
            
            sheet.merge_range(37, 12, 37, 13, "Losses %", content_style)
            sheet.write_string(38, 12, "CPO", content2_style)
            sheet.write_string(39, 12, "PK", content2_style)
            sheet.write_string(40, 12, "EB", content2_style)
            sheet.write_number(38, 13, 1, numeric1_style)
            sheet.write_number(39, 13, 1, numeric1_style)
            sheet.write_number(40, 13, 1, numeric1_style)

            # PART 3 : Pengiriman CPO
            # PART 4 : Pengiriman KERNEL

            sheet.set_margins(0.5, 0.5, 0.5, 0.5)
            sheet.print_area(0, 0, row, 6) #print area of selected cell
            sheet.set_paper(9)  # set A4 as page format
            sheet.center_horizontally()
            pages_horz = 1 # wide
            pages_vert = 0 # as long as necessary
            sheet.fit_to_pages(pages_horz, pages_vert)
        pass

ReportLHPXlsx('report.report_mill_lhp_xlsx', 'mill.lhp')