from dateutil.parser import parse
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from datetime import datetime

class ReportHutangUsahaXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        date_from = parse(data['form']['date_from'])
        date_to = parse(data['form']['date_to'])

        account_ids = data['form']['account_ids']

        partner_ids = data['form']['partner_ids']
        if not partner_ids:
            partners = self.env['res.partner'].search([('supplier', '=', True)])
            for partner in partners:
                self.print_sheet(workbook, partner, account_ids, date_from, date_to)
        else:
            for partner_id in partner_ids:
                partner = self.env['res.partner'].search([('id', '=', partner_id)])
                self.print_sheet(workbook, partner, account_ids, date_from, date_to)

    def print_sheet(self, workbook, partner, account_ids, date_from, date_to):
        date_from_format = date_from.strftime('%d %B %Y')
        date_to_format = date_to.strftime('%d %B %Y')
        date_range_format = date_from_format + ' - ' + date_to_format

        sheet_name = str(partner.id) + ' ' + str(partner.name)
        sheet = workbook.add_worksheet(sheet_name)

        bold = workbook.add_format({'bold': True})
        bold_wrap = workbook.add_format({'bold': True})
        bold_wrap.set_text_wrap()
        h1_format = workbook.add_format({'font_size': 26, 'bold': True})
        h2_format = workbook.add_format({'font_size': 18})
        h3_format = workbook.add_format({'font_size': 12, 'bold': True})
        currency_format = workbook.add_format({'num_format': 'Rp#,##0.00'})
        currency_bold = workbook.add_format({'num_format': 'Rp#,##0.00', 'bold': True})

        sheet.set_column('A:A', 5)  # Kolom No
        sheet.set_column('B:B', 10) # Kolom Date
        sheet.set_column('C:C', 25) # Kolom Journal Entry
        sheet.set_column('D:D', 25) # Kolom Journal
        sheet.set_column('E:E', 25) # Kolom Account
        sheet.set_column('F:F', 60) # Kolom Label
        sheet.set_column('G:G', 15) # Kolom Reference
        sheet.set_column('H:H', 15) # Kolom Operating Unit
        sheet.set_column('I:I', 15) # Kolom Cost Center
        sheet.set_column('J:J', 9)  # Kolom Matching Number
        sheet.set_column('K:K', 15) # Kolom Debit
        sheet.set_column('L:L', 15) # Kolom Credit
        sheet.set_column('M:M', 15) # Kolom Balance

        column_no               = 0
        column_date             = 1
        column_journal_entry    = 2
        column_journal          = 3
        column_account          = 4
        column_label            = 5
        column_reference        = 6
        column_operating_unit   = 7
        column_cost_center      = 8
        column_matching_number  = 9
        column_debit            = 10
        column_credit           = 11
        column_balance          = 12
        
        sheet.write(0, 0, 'Laporan Hutang Usaha', h1_format)
        sheet.write(2, 0, partner.name, h2_format)
        sheet.write(3, 0, date_range_format, h3_format)
        sheet.write(4, 0, "Printed on: "+datetime.now().strftime('%d %B %Y'), h3_format)

        row_header = 6

        sheet.write(row_header, column_no, 'No', bold)
        sheet.write(row_header, column_date, 'Date', bold)
        sheet.write(row_header, column_journal_entry, 'Journal Entry', bold)
        sheet.write(row_header, column_journal, 'Journal', bold)
        sheet.write(row_header, column_account, 'Account', bold)
        sheet.write(row_header, column_label, 'Label', bold)
        sheet.write(row_header, column_reference, 'Reference', bold)
        sheet.write(row_header, column_operating_unit, 'Operating Unit', bold)
        sheet.write(row_header, column_cost_center, 'Cost Center', bold)
        sheet.write(row_header, column_matching_number, 'Matching Number', bold_wrap)
        sheet.write(row_header, column_debit, 'Debit', bold)
        sheet.write(row_header, column_credit, 'Credit', bold)
        sheet.write(row_header, column_balance, 'Balance', bold)

        row = 7
        for account_id in account_ids:
            account = self.env['account.account'].search([('id', '=', account_id)])

            saldo_awal = self.env['account.move.line'].read_group([
                ('partner_id', '=', partner.id),
                ('account_id', '=', account_id),
                ('date', '<', date_from)
            ], ['account_id', 'debit', 'credit'], ['account_id'])

            saldo_awal_row_formula = row + 1
            saldo_awal_formula = '=L%d-K%d' % (saldo_awal_row_formula, saldo_awal_row_formula)
            
            sheet.write(row, column_account, account.code + ' ' + account.name, bold)
            sheet.write(row, column_label, 'Saldo Awal', bold)
            sheet.write(row, column_debit, saldo_awal[0]['debit'] if saldo_awal else 0, currency_bold)
            sheet.write(row, column_credit, saldo_awal[0]['credit'] if saldo_awal else 0, currency_bold)
            sheet.write(row, column_balance, saldo_awal_formula, currency_bold)

            row += 1

            journals = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id', '=', account_id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ])

            number = 1
            first_row = row
            
            for journal in journals:
                sheet.write(row, column_no, number)
                sheet.write(row, column_date, journal.date)
                sheet.write(row, column_journal_entry, journal.move_id.name)
                sheet.write(row, column_journal, journal.journal_id.name)
                sheet.write(row, column_account, journal.account_id.code + ' ' + journal.account_id.name)
                sheet.write(row, column_label, journal.name)
                sheet.write(row, column_reference, journal.ref)
                sheet.write(row, column_operating_unit, journal.operating_unit_id.name if journal.operating_unit_id.name else '')
                sheet.write(row, column_cost_center, journal.cost_center_id.name if journal.cost_center_id.name else '')
                sheet.write(row, column_matching_number, journal.full_reconcile_id.name if journal.full_reconcile_id.name else '')
                sheet.write(row, column_debit, journal.debit, currency_format)
                sheet.write(row, column_credit, journal.credit, currency_format)
            
                number += 1
                row += 1

            last_row = row

            saldo_akhir_row = row
            saldo_akhir_row_formula = saldo_akhir_row + 1

            saldo_akhir_debit_formula = '=SUM(K%d:K%d)' % (first_row, last_row)
            saldo_akhir_kredit_formula = '=SUM(L%d:L%d)' % (first_row, last_row)
            saldo_akhir_balance_formula = '=L%d-K%d' % (saldo_akhir_row_formula, saldo_akhir_row_formula)

            sheet.write(saldo_akhir_row, column_label, 'Saldo Akhir YTD ' + date_to_format, bold)
            sheet.write(saldo_akhir_row, column_debit, saldo_akhir_debit_formula, currency_bold)
            sheet.write(saldo_akhir_row, column_credit, saldo_akhir_kredit_formula, currency_bold)
            sheet.write(saldo_akhir_row, column_balance, saldo_akhir_balance_formula, currency_bold)

            row += 2

ReportHutangUsahaXlsx('report.c10i_account.report_hutang_usaha_xlsx',
                 'account.invoice')
