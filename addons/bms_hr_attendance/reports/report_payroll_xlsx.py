from odoo import api, models, fields

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class ReportSalaryXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        print("objects", objects)  # hr.attanceance.recap(id,id)
        report_name = objects.name
        # One sheet by partner
        sheet = workbook.add_worksheet(report_name[:31])
        bold = workbook.add_format({'bold': True})
        format1 = workbook.add_format({'font_size': 11, 'bold': True})
        sheet.write(0, 0, objects.company_id.name)
        sheet.write(1, 0, 'DAFTAR PEMBAYARAN GAJI')
        sheet.write(2, 0, objects.account_period_id.name)
        # departments = list(set([x.employee_id.department_id for x in objects.line_ids]))
        # temp = objects.line_ids.filtered(lambda x: x.employee_id.department_id == dept.id)
        # print "......................................", temp
        # departments = objects.line_ids.mapped('employee_id.department_id')

        sheet.merge_range(4, 0, 5, 0, "No")
        sheet.merge_range(4, 1, 5, 1, "NIK")
        sheet.merge_range(4, 2, 5, 2, "Nama")
        sheet.merge_range(4, 3, 5, 3, "Jabatan")
        sheet.merge_range(4, 4, 5, 4, "UMK 2019")
        sheet.merge_range(4, 5, 5, 5, "HKE")
        sheet.merge_range(4, 6, 5, 6, "HKE Value")
        sheet.merge_range(4, 7, 5, 7, "HKNE")
        sheet.merge_range(4, 8, 5, 8, "HKNE Value")
        sheet.merge_range(4, 9, 5, 9, "Overtime Value (Lembur)")
        sheet.merge_range(4, 10, 5, 10, "Premi Value")
        sheet.merge_range(4, 11, 5, 11, "Natura Value")
        sheet.merge_range(4, 12, 5, 12, "Tunjangan Struktural")
        sheet.merge_range(4, 13, 5, 13, "Tunjangan Produksi")
        sheet.merge_range(4, 14, 5, 14, "Rapel")
        sheet.merge_range(4, 15, 4, 17, "Tunjangan BPJS")
        sheet.write_string(5, 15, "BPJS Ketenagakerjaan")
        sheet.write_string(5, 16, "BPJS Kesehatan")
        sheet.write_string(5, 17, "BPJS Pensiunan")
        sheet.merge_range(4, 18, 5, 18, "Total Upah")
        sheet.merge_range(4, 19, 5, 19, "PTKP/bln")
        sheet.merge_range(4, 20, 5, 20, "Penghasilan Kena Pajak")
        sheet.merge_range(4, 21, 4, 21, "Potongan BPJS")
        sheet.write_string(5, 21, "BPJS Ketenagakerjaan")
        sheet.write_string(5, 22, "BPJS Kesehatan")
        sheet.write_string(5, 23, "BPJS Pensiunan")
        sheet.merge_range(4, 24, 5, 24, "Potongan Lain")
        sheet.merge_range(4, 25, 5, 25, "Penalty Value")
        sheet.merge_range(4, 26, 5, 26, "Penghasilan Yang Diterima")

        i = 1
        row = 6
        for data in objects.line_ids:
            total_upah = data.effective_work_days_value+data.non_effective_work_days_value+data.allowance_structural+data.allowance_production+data.premi_value+data.natura_value+data.overtime_value+data.rapel_value
            ptkp_month = data.employee_id.ptkp_history_ids[-1].ptkp_id.value/12
            pkp = 0#(total_upah - ptkp_month) if total_upah>ptkp_month else 0
            penghasilan_diterima = (total_upah)-pkp-data.penalty_value-data.potongan_bpjs_tk-data.potongan_bpjs_kes-data.potongan_bpjs_pensiun
            sheet.write(row, 0, i)
            sheet.write_string(row, 1, data.employee_id.no_induk)
            sheet.write_string(row, 2, data.employee_id.name)
            sheet.write_string(row, 3, data.employee_id.job_id.name)
            sheet.write(row, 4, data.employee_id.umr_ids[-1].dasar_bpjs)
            sheet.write(row, 5, data.effective_work_days)
            sheet.write(row, 6, data.effective_work_days_value)
            sheet.write(row, 7, data.non_effective_work_days)
            sheet.write(row, 8, data.non_effective_work_days_value)
            sheet.write(row, 9, data.overtime_value)
            sheet.write(row, 10, data.premi_value)
            sheet.write(row, 11, data.natura_value)
            sheet.write(row, 12, data.allowance_structural)
            sheet.write(row, 13, data.allowance_production)
            sheet.write(row, 14, data.rapel_value)
            sheet.write(row, 15, data.tunjangan_bpjs_tk)
            sheet.write(row, 16, data.tunjangan_bpjs_kes)
            sheet.write(row, 17, data.tunjangan_bpjs_pensiun)
            sheet.write(row, 18, total_upah)
            sheet.write(row, 19, ptkp_month)
            sheet.write(row, 20, pkp)
            sheet.write(row, 21, data.potongan_bpjs_tk)
            sheet.write(row, 22, data.potongan_bpjs_kes)
            sheet.write(row, 23, data.potongan_bpjs_pensiun)
            sheet.write(row, 24, 0)
            sheet.write(row, 25, data.penalty_value)
            sheet.write(row, 26, penghasilan_diterima)

            i += 1
            row += 1
                # sheet.write(4, 0, objects.name)
                # sheet.write(5, 0, 'cek')

                # sheet.write_string(row, 2, x.employee_id.id)

        # if line.employee_id.departmnet_id.id==dept.id:

        # for dept in objects_departments:


ReportSalaryXlsx('report.report_salary_xlsx_new',
                 'hr.attendance.payroll')
