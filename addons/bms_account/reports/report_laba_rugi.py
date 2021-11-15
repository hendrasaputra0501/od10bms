from odoo import api, models, fields
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
# import datetime
import dateutil.rrule as rrule

# from datetime import date


class ReportLabaRugiXlsx(ReportXlsx):

    def _get_account_move_line(self, objects):
        acl = self.env['account.move.line'].sudo().search([('date','>=', objects.date_start),
                                                            ('date','<=', objects.date_end),
                                                            ('move_id.state','=', 'posted')
                                                            ])
        
        acl_4 = acl.filtered(lambda r: r.account_id.code[0] == '4')
        acl_5 = acl.filtered(lambda r: r.account_id.code[0] == '5')
        acl_6 = acl.filtered(lambda r: r.account_id.code[0] == '6')
        acl_46 = acl.filtered(lambda r: r.account_id.code[0] == '4' or r.account_id.code[0] == '6')

        # penjualan
        debit_penjualan = sum(acl_4.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_penjualan).mapped('debit'))
        credit_penjualan = sum(acl_4.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_penjualan).mapped('credit'))
        penjualan = debit_penjualan - credit_penjualan

        # beban pokok penjualan
        debit_beban_pokok_penjualan = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_pokok_penjualan).mapped('debit'))
        credit_beban_pokok_penjualan = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_pokok_penjualan).mapped('credit'))
        beban_pokok_penjualan = debit_beban_pokok_penjualan - credit_beban_pokok_penjualan

        # beban pemasaran
        debit_beban_pemasaran = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_pemasaran).mapped('debit'))
        credit_beban_pemasaran = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_pemasaran).mapped('credit'))
        beban_pemasaran = debit_beban_pemasaran - credit_beban_pemasaran
        
        # beban administrasi umum
        debit_beban_administrasi_umum = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_administrasi_umum).mapped('debit'))
        credit_beban_administrasi_umum = sum(acl_5.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_administrasi_umum).mapped('credit'))
        beban_administrasi_umum = debit_beban_administrasi_umum - credit_beban_administrasi_umum

        # pendapatan lain lain
        debit_pendapatan_lain_lain = sum(acl_46.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_pendapatan_lain_lain).mapped('debit'))
        credit_pendapatan_lain_lain = sum(acl_46.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_pendapatan_lain_lain).mapped('credit'))
        pendapatan_lain_lain = debit_pendapatan_lain_lain - credit_pendapatan_lain_lain

        # beban lain lain
        debit_beban_lain_lain = sum(acl_6.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_lain_lain).mapped('debit'))
        credit_beban_lain_lain = sum(acl_6.filtered(lambda r: r.account_id.parent_id.code in objects.account_id_beban_lain_lain).mapped('credit'))
        beban_lain_lain = debit_beban_lain_lain - credit_beban_lain_lain

        result = {
            'penjualan': penjualan,
            'beban_pokok_penjualan': beban_pokok_penjualan,
            'beban_pemasaran': beban_pemasaran,
            'beban_administrasi_umum': beban_administrasi_umum,
            'pendapatan_lain_lain': pendapatan_lain_lain,
            'beban_lain_lain': beban_lain_lain,
        }

        return result  

    def generate_xlsx_report(self, workbook, data, objects):
        sheet_name = 'LABA RUGI per '+ str(datetime.strptime(objects.date_end,"%Y-%m-%d").strftime("%d-%m-%Y"))
        sheet = workbook.add_worksheet(sheet_name)
        sheet.set_landscape()
        sheet.set_footer('&R&6&"Courier New,Italic"Page &P of &N', {'margin': 0.25})
        
        column_width = [4, 10, 30, 21]
        for col_pos in range(0,len(column_width)):
            sheet.set_column(col_pos, col_pos, column_width[col_pos])

        # TITLE
        t_cell_format = {'font_name': 'Arial', 'font_size': 14, 'bold': True, 'valign': 'vcenter', 'align': 'left'}
        t_style = workbook.add_format(t_cell_format)

        # 1
        t_cell_format1 = {'font_name': 'Arial', 'font_size': 14, 'bold': True, 'valign': 'vcenter', 'align': 'center', 'bg_color':'#6699ff'}
        t_style1 = workbook.add_format(t_cell_format1)
        # 2
        t_cell_format2 = {'font_name': 'Arial', 'font_size': 16, 'bold': True, 'valign': 'vcenter', 'align': 'left'}
        t_style2 = workbook.add_format(t_cell_format2)
        # 3
        t_cell_format3 = {'font_name': 'Arial', 'font_size': 12, 'bold': True, 'valign': 'vcenter', 'align': 'left'}
        t_style3 = workbook.add_format(t_cell_format3)
        # 4
        h_cell_format = {'font_name': 'Arial', 'font_size': 10, 'bold': False, 'valign': 'vcenter', 'align': 'left'}
        h_style = workbook.add_format(h_cell_format)
        # 
        h_cell_format_num = {'font_name': 'Arial', 'font_size': 10,'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.##;-#,##0.##;-'}
        h_style_num = workbook.add_format(h_cell_format_num)
        # 
        h_cell_format_num_tot = {'font_name': 'Arial', 'font_size': 10,'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.##;-#,##0.##;-', 'bg_color':'#ccccff'}
        h_style_num_tot = workbook.add_format(h_cell_format_num_tot)


        sheet.merge_range(0, 1, 0, 3, objects.company_id.name.upper(), t_style1)
        sheet.merge_range(1, 1, 1, 3, 'LABA RUGI', t_style1)
        sheet.merge_range(2, 1, 2, 3,'PER '+ str(datetime.strptime(objects.date_end,"%Y-%m-%d").strftime("%d-%m-%Y")), t_style1)
        sheet.merge_range(3, 1, 3, 3, "", t_style1)
        sheet.write(4, 3, "(Rp)", h_style)
        
        result = self._get_account_move_line(objects)
        row=6
        
        sheet.write(row, 1,"PENJUALAN", h_style)
        sheet.write(row, 3, result['penjualan'], h_style_num)
        row += 1
        sheet.write(row, 1,"BEBAN POKOK PENJUALAN", h_style)
        sheet.write(row, 3, result['beban_pokok_penjualan'], h_style_num)
        row += 1
        sheet.write(row, 1,"LABA KOTOR", h_style)
        sheet.write(row, 3, "=D7-D8", h_style_num)
        #
        row += 2
        sheet.write(row, 1,"BEBAN USAHA", h_style)
        row += 1
        sheet.write(row, 2,"Beban Pemasaran", h_style)
        sheet.write(row, 3, result['beban_pemasaran'], h_style_num)
        row += 1
        sheet.write(row, 2,"Beban Administrasi dan Umum", h_style)
        sheet.write(row, 3, result['beban_administrasi_umum'], h_style_num)
        row += 1
        sheet.write(row, 1,"Jumlah Beban Usaha", h_style)
        sheet.write(row, 3, "=D12-D13", h_style_num)
        #
        row += 2
        sheet.write(row, 1, 'LABA USAHA', h_style)
        sheet.write(row, 3, "=D9-D14", h_style_num)
        # 
        row += 2
        sheet.write(row, 1, 'PENDAPATAN/(BEBAN) LAIN LAIN', h_style)
        row += 1
        sheet.write(row, 2,"Pendapatan Lain Lain", h_style)
        sheet.write(row, 3, result['pendapatan_lain_lain'], h_style_num)
        row += 1
        sheet.write(row, 2,"Beban Lain Lain", h_style)
        sheet.write(row, 3, result['beban_lain_lain'], h_style_num)
        row += 1
        sheet.write(row, 1,"Jumlah Pendapatan/(beban) Lain Lain Bersih", h_style)
        sheet.write(row, 3, "=D19-D20", h_style_num)
        #
        row += 2
        sheet.write(row, 1,"LABA/(RUGI) SEBELUM PAJAK", h_style)
        sheet.write(row, 3, "=D21+D16", h_style_num)
        row += 1
        sheet.write(row, 1,"PAJAK PENGHASILAN (Estimasi)", h_style)
        sheet.write(row, 3, "=E23*22/100", h_style_num)
        #
        row +=2
        sheet.write(row, 1,"LABA BERSIH SETELAH PPH", h_style)
        sheet.write(row, 3, "=D23-D24", h_style_num)

ReportLabaRugiXlsx('report.report_laba_rugi_xlsx', 'wizard.laba.rugi.report')
