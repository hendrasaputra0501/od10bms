from odoo import api, models, fields
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
# import datetime
import dateutil.rrule as rrule

# from datetime import date


class ReportNeracaXlsx(ReportXlsx):

    def _get_account_move_line(self, objects):

        acl = self.env['account.move.line'].sudo().search([('date','>=', objects.date_start),
                                                            ('date','<=', objects.date_end),
                                                            ('move_id.state','=', 'posted')
                                                            ])

        
        acl_1 = acl.filtered(lambda r: r.account_id.code[0] == '1')
        # kas
        debit_kas = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_kas)).mapped('debit'))
        credit_kas = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_kas)).mapped('credit'))
        kas = debit_kas - credit_kas
        # bank
        debit_bank = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_bank)).mapped('debit'))
        credit_bank = sum(acl.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_bank)).mapped('credit'))
        bank = debit_bank - credit_bank
        # piutang usaha
        debit_piutang = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_piutang)).mapped('debit'))
        credit_piutang = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_piutang)).mapped('credit'))
        piutang = debit_piutang - credit_piutang
        # inventory
        debit_inventory = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_inventory)).mapped('debit'))
        credit_inventory = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_inventory)).mapped('credit'))
        inventory = debit_inventory - credit_inventory
        # persediaan barang dagang
        debit_pbd = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_pbd)).mapped('debit'))
        credit_pbd = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_pbd)).mapped('credit'))
        pbd = debit_pbd - credit_pbd
        # pajak dibayar dimuka
        debit_pdd = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_pdd)).mapped('debit'))
        credit_pdd = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_pdd)).mapped('credit'))
        pdd = debit_pdd - credit_pdd
        # uang muka
        debit_um = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_um)).mapped('debit'))
        credit_um = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_um)).mapped('credit'))
        um = debit_um - credit_um
        # total
        total_activa_lancar = sum([kas,bank,piutang,inventory,pbd,pdd,um]) 
        # aktiva lancar
        # aktiva tetap : 15000000
        # asset : 15110000
        debit_asset = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_asset)).mapped('debit'))
        credit_asset = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_asset)).mapped('credit'))
        asset = debit_asset - credit_asset
        # akumulasi penyusutan: 15599999
        debit_akp = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_akp)).mapped('debit'))
        credit_akp = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_akp)).mapped('credit'))
        akp = debit_akp - credit_akp
        # total aktiva tetap
        total_aktiva_tetap = sum([asset,akp])
        # Aktiva Tidak Lancar Lainnya
        debit_atll = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_atll)).mapped('debit'))
        credit_atll = sum(acl_1.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_atll)).mapped('credit'))
        atll = debit_atll - credit_atll

        acl_2 = acl.filtered(lambda r: r.account_id.code[0] == '2')
        # PASSIVA
        # hutang dagang
        debit_hd = sum(acl_2.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_hd)).mapped('debit'))
        credit_hd = sum(acl_2.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_hd)).mapped('credit'))
        hd = debit_hd - credit_hd
        # hutang pajak
        debit_hp = sum(acl_2.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_hp)).mapped('debit'))
        credit_hp = sum(acl_2.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_hp)).mapped('credit'))
        hp = debit_hp - credit_hp
        # total kewajiban jangka pendek
        total_kewajiban_jangka_pendek = sum([hd,hp])
        # HUTANG JANGKA PANJANG
        # Hutang Pemegang Saham
        debit_hps = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hps)).mapped('debit'))
        credit_hps = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hps)).mapped('credit'))
        hps = debit_hps - credit_hps
        # Sewa Guna Usaha Jangka Panjang
        debit_sgujp = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_sgujp)).mapped('debit'))
        credit_sgujp = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_sgujp)).mapped('credit'))
        sgujp = debit_sgujp - credit_sgujp
        # Hutang Kredit Investasi
        debit_hki = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hki)).mapped('debit'))
        credit_hki = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hki)).mapped('credit'))
        hki = debit_hki - credit_hki
        # Hutang Kredit Obligasi Jakarta
        debit_hkoj = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hkoj)).mapped('debit'))
        credit_hkoj = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hkoj)).mapped('credit'))
        hkoj = debit_hkoj - credit_hkoj
        # Hutang Bank Jakarta
        debit_hbj = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hbj)).mapped('debit'))
        credit_hbj = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hbj)).mapped('credit'))
        hbj = debit_hbj - credit_hbj
        # Hutang Kredit Obligasi
        debit_hko = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hko)).mapped('debit'))
        credit_hko = sum(acl_2.filtered(lambda r: r.account_id.code == str(objects.account_id_hko)).mapped('credit'))
        hko = debit_hko - credit_hko
        # Total Hutang Jangka Panjang
        total_hutang_jangka_panjang = sum([hps,sgujp,hki,hkoj,hbj,hko])
        # 
        acl_3 = acl.filtered(lambda r: r.account_id.code[0] == '3')
        # MODAL
        # Modal Yang Disetor
        debit_myd = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_myd)).mapped('debit'))
        credit_myd = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_myd)).mapped('credit'))
        myd = debit_myd - credit_myd
        # Saldo Laba di Tahan
        debit_sldt = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_sldt)).mapped('debit'))
        credit_sldt = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_sldt)).mapped('credit'))
        sldt = debit_sldt - credit_sldt
        # Penambahan Modal Disetor
        debit_pmd = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_pmd)).mapped('debit'))
        credit_pmd = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_pmd)).mapped('credit'))
        pmd = debit_pmd - credit_pmd
        # Saldo Laba s/d Bulan Lalu Jakarta
        debit_slblj = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_slblj)).mapped('debit'))
        credit_slblj = sum(acl_3.filtered(lambda r: r.account_id.code == str(objects.account_id_slblj)).mapped('credit'))
        slblj = debit_slblj - credit_slblj
        # Saldo Berjalan Bulan Ini
        debit_sbbi = sum(acl_3.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_sbbi)).mapped('debit'))
        credit_sbbi = sum(acl_3.filtered(lambda r: r.account_id.parent_id.code == str(objects.account_id_sbbi)).mapped('credit'))
        sbbi = debit_sbbi - credit_sbbi
        # TOTAL MODAL DAN EKUITAS
        total_modal_equitas = sum([myd,sldt,pmd,slblj,sbbi])
        result = {'kas':kas, 'bank':bank, 'piutang':piutang, 'inventory':inventory, 'pbd':pbd, 'pdd':pdd, 'um':um,'tal':total_activa_lancar,
                'asset':asset, 'akp':akp, 'tat': total_aktiva_tetap, 'atll': atll,
                'hutang_dagang': hd, 'hutang_pajak': hp, 'tkjp': total_kewajiban_jangka_pendek,
                'hutang_pemegang_saham': hps, 'sewa_guna_usaha_jangka_panjang': sgujp, 'hutang_kredit_investasi': hki, 'hutang_kredit_obligasi_jakarta': hkoj, 'hutang_bank_jakarta':hbj,
                'hutang_kredit_obligasi': hko, 'total_hutang_jangka_panjang':total_hutang_jangka_panjang,
                'modal_yang_disetor':myd, 'saldo_laba_ditahan': sldt, 'penambahan_modal_disetor': pmd, 'saldo_laba_bulan_lalu_jakarta':slblj,
                'saldo_berjalan_bulan_ini':sbbi, 'total_modal_equitas': total_modal_equitas
                }

        return result  


    def generate_xlsx_report(self, workbook, data, objects):
        sheet_name = 'NERACA per '+ str(datetime.strptime(objects.date_end,"%Y-%m-%d").strftime("%d-%m-%Y"))
        sheet = workbook.add_worksheet(sheet_name)
        sheet.set_landscape()
        sheet.set_footer('&R&6&"Courier New,Italic"Page &P of &N', {'margin': 0.25})
        
        column_width = [4, 50, 30]
        column_width = column_width
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
        h_cell_format = {'font_name': 'Arial', 'font_size': 10, 'bold': False, 'valign': 'vcenter', 'align': 'left', 'border': 1,}
        h_style = workbook.add_format(h_cell_format)
        # 
        h_cell_format_num = {'font_name': 'Arial', 'font_size': 10,'valign': 'vcenter', 'align': 'right', 'border': 1, 'num_format': '#,##0.##;-#,##0.##;-'}
        h_style_num = workbook.add_format(h_cell_format_num)
        # 
        h_cell_format_num_tot = {'font_name': 'Arial', 'font_size': 10,'valign': 'vcenter', 'align': 'right', 'border': 1, 'num_format': '#,##0.##;-#,##0.##;-', 'bg_color':'#ccccff'}
        h_style_num_tot = workbook.add_format(h_cell_format_num_tot)


        sheet.merge_range(1, 1, 1, 2, objects.company_id.name.upper(), t_style1)
        sheet.merge_range(2, 1, 2, 2, 'NERACA', t_style1)
        sheet.merge_range(3, 1, 3, 2,'PER '+ str(datetime.strptime(objects.date_end,"%Y-%m-%d").strftime("%d-%m-%Y")), t_style1)

        
        sheet.merge_range(6, 1, 6, 2, "AKTIVA", t_style2)
        sheet.write(6, 2, "(Rp)", t_style2)
        sheet.write(7, 1, "AKTIVA LANCAR", t_style3)
        sheet.write(7, 2, "", t_style3)

        result = self._get_account_move_line(objects)
        row=8
        sheet.write(row, 1,"Kas" , h_style)
        sheet.write(row, 2, result['kas'], h_style_num)
        row += 1
        sheet.write(row, 1,"Bank" , h_style)
        sheet.write(row, 2, result['bank'], h_style_num)
        row += 1
        sheet.write(row, 1,"Piutang Usaha" , h_style)
        sheet.write(row, 2, result['piutang'], h_style_num)
        row += 1
        sheet.write(row, 1,"Inventory" , h_style)
        sheet.write(row, 2, result['inventory'], h_style_num)
        row += 1
        sheet.write(row, 1,"Persediaan Barang Dagang" , h_style)
        sheet.write(row, 2, result['pbd'], h_style_num)
        row += 1
        sheet.write(row, 1,"Pajak Dibayar dimuka" , h_style)
        sheet.write(row, 2, result['pdd'], h_style_num)
        row += 1
        sheet.write(row, 1,"Uang Muka" , h_style)
        sheet.write(row, 2, result['um'], h_style_num)
        row += 1
        sheet.write(row, 1, 'TOTAL AKTIVA LANCAR', h_style)
        sheet.write(row, 2, result['tal'], h_style_num)
        # 
        row += 3
        sheet.merge_range(row,1, row, 2,"AKTIVA TETAP", t_style3)
        row += 1
        sheet.write(row,1,"Aktiva Tetap", h_style)
        sheet.write(row,2, result['asset'], h_style_num)
        row += 1
        sheet.write(row,1,"Akumulasi Penyusutan",h_style)
        sheet.write(row,2, result['akp'], h_style_num)
        row += 1
        sheet.write(row,1,"Total Aktiva Tetap",h_style)
        sheet.write(row,2, result['tat'],h_style_num)
        # 
        row += 1
        sheet.write(row,1,"Aktiva Tidak Lancar Lainnya", h_style)
        sheet.write(row,2, result['atll'], h_style_num)
        # 
        row += 2
        sheet.write(row,1,"Total Aktiva", h_style_num_tot)
        sheet.write(row,2, result['tal']+result['tat']+result['atll'], h_style_num_tot)
        # 
        row += 2
        sheet.merge_range(row,1, row, 2,"PASIVA", t_style2)
        row += 1
        sheet.merge_range(row,1,row,2,"KEWAJIBAN JANGKA PENDEK", t_style3)
        row += 1
        sheet.write(row,1,"Hutang Dagang",h_style)
        sheet.write(row,2, result['hutang_dagang'], h_style_num)
        row += 1
        sheet.write(row,1,"Hutang Pajak", h_style)
        sheet.write(row,2, result['hutang_pajak'], h_style_num)
        row += 1
        sheet.write(row,1,"Total Kewajiban Jangka Pendek", h_style)
        sheet.write(row,2, result['tkjp'], h_style_num)
        # 
        row += 3
        sheet.merge_range(row,1,row,2,"HUTANG JANGKA PANJANG", t_style3)
        row += 1
        sheet.write(row,1,"Hutang Pemegang Saham",h_style)
        sheet.write(row,2,result['hutang_pemegang_saham'], h_style_num)
        row += 1
        sheet.write(row,1,"Sewa Guna Usaha Jangka Panjang",h_style)
        sheet.write(row,2,result['sewa_guna_usaha_jangka_panjang'],h_style_num)
        row += 1
        sheet.write(row,1,"Hutang Kredit Investasi",h_style)
        sheet.write(row,2,result['hutang_kredit_investasi'],h_style_num)
        row += 1
        sheet.write(row,1,"Hutang Kredit Obligasi Jakarta",h_style)
        sheet.write(row,2,result['hutang_kredit_obligasi_jakarta'],h_style_num)
        row += 1
        sheet.write(row,1,"Hutang Bank Jakarta",h_style)
        sheet.write(row,2,result['hutang_bank_jakarta'],h_style_num)
        row += 1
        sheet.write(row,1,"Hutang Kredit Obligasi",h_style)
        sheet.write(row,2,result['hutang_kredit_obligasi'],h_style_num)
        row += 1
        sheet.write(row,1,"TOTAL HUTANG JANGKA PANJANG",h_style)
        sheet.write(row,2,result['total_hutang_jangka_panjang'],h_style_num)
        # 
        
        row += 3
        sheet.merge_range(row,1,row,2,"MODAL", t_style3)
        row += 1
        sheet.write(row,1,"Modal Yang Disetor",h_style)
        sheet.write(row,2,result['modal_yang_disetor'], h_style_num)
        row += 1
        sheet.write(row,1,"Saldo Laba di Tahan",h_style)
        sheet.write(row,2,result['saldo_laba_ditahan'],h_style_num)
        row += 1
        sheet.write(row,1,"Penambahan Modal Disetor",h_style)
        sheet.write(row,2,result['penambahan_modal_disetor'],h_style_num)
        row += 1
        sheet.write(row,1,"Saldo Laba s/d Bulan Lalu Jakarta",h_style)
        sheet.write(row,2,result['saldo_laba_bulan_lalu_jakarta'],h_style_num)
        row += 1
        sheet.write(row,1,"Saldo Berjalan Bulan Ini",h_style)
        sheet.write(row,2,result['saldo_berjalan_bulan_ini'],h_style_num)
        row += 1
        sheet.write(row,1,"TOTAL MODAL DAN EKUITAS",h_style)
        sheet.write(row,2,result['total_modal_equitas'],h_style_num)
        # 
        row += 2
        sheet.write(row,1,"Total PASSIVA", h_style_num_tot)
        sheet.write(row,2, result['tkjp']+result['total_hutang_jangka_panjang']+result['total_modal_equitas'], h_style_num_tot)



ReportNeracaXlsx('report.report_neraca_xlsx', 'wizard.neraca.report')