from dateutil.parser import parse
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

class ReportPPNXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        date_from = parse(data['form']['date_from'])
        date_to = parse(data['form']['date_to'])

        account_ids = data['form']['account_ids']

        partner_ids = data['form']['partner_ids']
        
        date_from_format = date_from.strftime('%d %B %Y')
        date_to_format = date_to.strftime('%d %B %Y')
        date_range_format = date_from_format + ' - ' + date_to_format

        sheet = workbook.add_worksheet('Laporan PPN Masukan-Keluaran')

        border = workbook.add_format({'border': 2})
        border_lr = workbook.add_format({'left': 2, 'right': 2})
        bold = workbook.add_format({'bold': True})
        bold_border = workbook.add_format({'bold': True, 'border': 2})
        h1_format = workbook.add_format({'font_size': 26, 'bold': True})
        h2_format = workbook.add_format({'font_size': 18})
        h3_format = workbook.add_format({'font_size': 12, 'bold': True})
        accounting_format = workbook.add_format({'num_format': 43, 'left': 2, 'right': 2})
        accounting_bold = workbook.add_format({'num_format': 43, 'bold': True})
        accounting_bold_border = workbook.add_format({'num_format': 43, 'bold': True, 'border': 2})

        sheet.set_column('A:A', 5)  # Kolom No
        sheet.set_column('B:B', 10) # Kolom Tgl.
        sheet.set_column('C:C', 21) # Kolom No. NPWP
        sheet.set_column('D:D', 31) # Kolom No. Inv / Faktur
        sheet.set_column('E:E', 21) # Kolom No. Faktur Pajak
        sheet.set_column('F:F', 39) # Kolom Partner
        sheet.set_column('G:G', 20) # Kolom Harga satuan
        sheet.set_column('H:H', 20) # Kolom Jumlah Excl PPN
        sheet.set_column('I:I', 20) # Kolom PPN

        column_no               = 0
        column_tgl              = 1
        column_no_npwp          = 2
        column_no_inv           = 3
        column_no_faktur        = 4
        column_partner          = 5
        column_harga_satuan     = 6
        column_jumlah_ex        = 7
        column_ppn              = 8
        
        sheet.write(0, 0, 'Laporan PPN Masukan-Keluaran', h1_format)
        sheet.write(2, 0, 'Pajak Keluaran ' + date_range_format, bold)

        row = 3

        sheet.write(row, column_no, 'No', bold_border)
        sheet.write(row, column_tgl, 'Tgl.', bold_border)
        sheet.write(row, column_no_npwp, 'No. NPWP', bold_border)
        sheet.write(row, column_no_inv, 'No. Inv / Faktur', bold_border)
        sheet.write(row, column_no_faktur, 'No. Faktur Pajak', bold_border)
        sheet.write(row, column_partner, 'Partner', bold_border)
        sheet.write(row, column_harga_satuan, 'Harga Satuan', bold_border)
        sheet.write(row, column_jumlah_ex, 'Jumlah Excl PPN', bold_border)
        sheet.write(row, column_ppn, 'PPN', bold_border)

        move_lines = []
        if not partner_ids:
            move_lines = self.env['account.move.line'].search([
                ('account_id', 'in', account_ids),
                ('journal_id','ilike','Customer Invoices'),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]) 
        else:    
            move_lines = self.env['account.move.line'].search([
                ('partner_id', 'in', partner_ids),
                ('journal_id','ilike','Customer Invoices'),
                ('account_id', 'in', account_ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]) 
        
        number = 1
        row += 1
        first_keluaran_row = row
        
        for move_line in move_lines:
            partner = move_line.partner_id
            invoice  = move_line.invoice_id

            sheet.write(row, column_no, number)
            sheet.write(row, column_tgl, move_line.date, border_lr)

            if partner:
                sheet.write(row, column_no_npwp, partner.npwp_number if partner.npwp_number else '', border_lr)
                sheet.write(row, column_partner, partner.name, border_lr)
            else:
                sheet.write(row, column_no_npwp, '', border_lr)
                sheet.write(row, column_partner, '', border_lr)

            if invoice:
                sheet.write(row, column_no_inv, invoice.number if invoice.number else '', border_lr)
                sheet.write(row, column_no_faktur, invoice.nomer_seri_faktur_pajak if invoice.nomer_seri_faktur_pajak else '', border_lr)
                sheet.write(row, column_jumlah_ex, invoice.amount_untaxed, accounting_format)
                sheet.write(row, column_ppn, sum(invoice.tax_line_ids.filtered(lambda x: "PPN" in x.name.split(' ')).mapped('amount')), accounting_format)

                invoice_lines = invoice.invoice_line_ids

                for invoice_line in invoice_lines:
                    if invoice_line:
                        tax = invoice_line.invoice_line_tax_ids
                        if tax:
                            sheet.write(row, column_harga_satuan, invoice_line.price_unit, accounting_format)
                            if len(invoice_line) > 1:
                                row += 1
                
            else:
                sheet.write(row, column_no_inv, '', border_lr)
                sheet.write(row, column_no_faktur, '', border_lr)
                sheet.write(row, column_harga_satuan, '', border_lr)
                sheet.write(row, column_jumlah_ex, '', border_lr)
                sheet.write(row, column_ppn, '', border_lr)

            number += 1
            row += 1
        
        last_keluaran_row = row

        total_keluaran_ex_formula = '=SUM(H%d:H%d)' % (first_keluaran_row, last_keluaran_row)
        total_keluaran_ppn_formula = '=SUM(I%d:I%d)' % (first_keluaran_row, last_keluaran_row)

        sheet.write(row, column_no, '', border)
        sheet.write(row, column_tgl, '', border)
        sheet.write(row, column_no_npwp, '', border)
        sheet.write(row, column_no_inv, '', border)
        sheet.write(row, column_no_faktur, '', border)
        sheet.write(row, column_partner, '', border)
        sheet.write(row, column_harga_satuan, '', border)
        sheet.write(row, column_jumlah_ex, total_keluaran_ex_formula, accounting_bold_border)
        sheet.write(row, column_ppn, total_keluaran_ppn_formula, accounting_bold_border)

        row += 2

        sheet.write(row, 0, 'Pajak Masukan ' + date_range_format, bold)

        row += 1

        sheet.write(row, column_no, 'No', bold_border)
        sheet.write(row, column_tgl, 'Tgl.', bold_border)
        sheet.write(row, column_no_npwp, 'No. NPWP', bold_border)
        sheet.write(row, column_no_inv, 'No. Inv / Faktur', bold_border)
        sheet.write(row, column_no_faktur, 'No. Faktur Pajak', bold_border)
        sheet.write(row, column_partner, 'Partner', bold_border)
        sheet.write(row, column_harga_satuan, 'Harga', bold_border)
        sheet.write(row, column_jumlah_ex, 'Jumlah Excl PPN', bold_border)
        sheet.write(row, column_ppn, 'PPN', bold_border)

        move_lines = []
        if not partner_ids:
            move_lines = self.env['account.move.line'].search([
                ('account_id', 'in', account_ids),
                ('journal_id','ilike','Vendor Bills'),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]) 
        else:    
            move_lines = self.env['account.move.line'].search([
                ('partner_id', 'in', partner_ids),
                ('journal_id','ilike','Vendor Bills'),
                ('account_id', 'in', account_ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ]) 

        row += 1
        number = 1
        first_masukan_row = row
        
        for move_line in move_lines:
            partner = move_line.partner_id
            bill  = move_line.invoice_id

            sheet.write(row, column_no, number, border_lr)
            sheet.write(row, column_tgl, move_line.date, border_lr)

            if partner:
                sheet.write(row, column_no_npwp, partner.npwp_number if partner.npwp_number else '', border_lr)
                sheet.write(row, column_partner, partner.name, border_lr)
            else:
                sheet.write(row, column_no_npwp, '', border_lr)
                sheet.write(row, column_partner, '', border_lr)

            if bill:
                sheet.write(row, column_no_inv, bill.reference if bill.reference else '', border_lr)
                sheet.write(row, column_no_faktur, bill.nomer_seri_faktur_pajak_bill if bill.nomer_seri_faktur_pajak_bill else '', border_lr)
                sheet.write(row, column_jumlah_ex, bill.amount_untaxed, accounting_format)
                sheet.write(row, column_ppn, sum(bill.tax_line_ids.filtered(lambda x: "PPN" in x.name.split(' ')).mapped('amount')), accounting_format)

                bill_lines = bill.invoice_line_ids

                for bill_line in bill_lines:
                    if bill_line:
                        tax = bill_line.invoice_line_tax_ids
                        if tax:
                            sheet.write(row, column_harga_satuan, bill_line.price_unit, accounting_format)
                            if len(bill_line) > 1:
                                row += 1
            else:
                sheet.write(row, column_no_inv, '', border_lr)
                sheet.write(row, column_no_faktur, '', border_lr)
                sheet.write(row, column_harga_satuan, '', border_lr)
                sheet.write(row, column_jumlah_ex, '', border_lr)
                sheet.write(row, column_ppn, '', border_lr)

            number += 1
            row += 1

        last_masukan_row = row

        total_masukan_ex_formula = '=SUM(H%d:H%d)' % (first_masukan_row, last_masukan_row)
        total_masukan_ppn_formula = '=SUM(I%d:I%d)' % (first_masukan_row, last_masukan_row)

        sheet.write(row, column_no, '', border)
        sheet.write(row, column_tgl, '', border)
        sheet.write(row, column_no_npwp, '', border)
        sheet.write(row, column_no_inv, '', border)
        sheet.write(row, column_no_faktur, '', border)
        sheet.write(row, column_partner, '', border)
        sheet.write(row, column_harga_satuan, '', border)
        sheet.write(row, column_jumlah_ex, total_masukan_ex_formula, accounting_bold_border)
        sheet.write(row, column_ppn, total_masukan_ppn_formula, accounting_bold_border)

        row += 2

        total_pk_pm_formula = '=I%d-I%d' % (last_masukan_row + 1, last_keluaran_row + 1)

        sheet.write(row, column_harga_satuan, 'Total PK-PM', bold)
        sheet.write(row, column_ppn, total_pk_pm_formula, accounting_bold)

        total_keluaran_masa = 0
        move_lines = []
        if not partner_ids:
            move_lines = self.env['account.move.line'].search([
                ('account_id', 'in', account_ids),
                ('journal_id','ilike','Customer Invoices'),
                ('date', '<', date_from)
            ]) 
        else:    
            move_lines = self.env['account.move.line'].search([
                ('partner_id', 'in', partner_ids),
                ('journal_id','ilike','Customer Invoices'),
                ('account_id', 'in', account_ids),
                ('date', '<', date_from)
            ])

        for move_line in move_lines:
            invoice  = move_line.invoice_id
            total_keluaran_masa += sum(invoice.tax_line_ids.filtered(lambda x: "PPN" in x.name.split(' ')).mapped('amount'))

        total_masukan_masa = 0
        move_lines = []
        if not partner_ids:
            move_lines = self.env['account.move.line'].search([
                ('account_id', 'in', account_ids),
                ('journal_id','ilike','Vendor Bills'),
                ('date', '<', date_from)
            ]) 
        else:    
            move_lines = self.env['account.move.line'].search([
                ('partner_id', 'in', partner_ids),
                ('journal_id','ilike','Vendor Bills'),
                ('account_id', 'in', account_ids),
                ('date', '<', date_from)
            ])

        for move_line in move_lines:
            bill  = move_line.invoice_id
            total_masukan_masa += sum(bill.tax_line_ids.filtered(lambda x: "PPN" in x.name.split(' ')).mapped('amount'))

        total_kompensasi_masa = total_masukan_masa - total_keluaran_masa
        
        row += 1
        total_pk_pm_row_formula = row


        sheet.write(row, column_harga_satuan, 'Kompensasi Masa Sebelumnya', bold)
        sheet.write(row, column_ppn, total_kompensasi_masa, accounting_bold)

        row += 1
        kompensasi_row_formula = row

        total_ppn_formula = '=I%d+I%d' % (total_pk_pm_row_formula, kompensasi_row_formula)

        sheet.write(row, column_harga_satuan, 'Total PK-PM', bold)
        sheet.write(row, column_ppn, total_ppn_formula, accounting_bold)


        
ReportPPNXlsx('report.c10i_tax_payment.report_ppn_xlsx',
                 'account.move.line')
