import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class HrAttendancePayroll(models.Model):
    _inherit = 'hr.attendance.payroll'

    operation_type_id = fields.Many2one('hr.operation.type', string='Hr Type')

    @api.multi
    def get_attendance_data(self):
        if self.line_ids:
            for unlink in self.line_ids:
                unlink.unlink()
        PayrollLine = self.env['hr.attendance.payroll.line']
        HrAttendance = self.env['hr.attendance']
        day_off = self.env['hr.holidays.public.line'].search([('date', '>=', self.date_start),('date', '<=', self.date_stop)])
        if day_off:
            day_off_dict = dict(map(lambda x: (x.date,'weekend' if x.is_weekend else 'national'), day_off))
        else:
            day_off_dict = {}

        overtime_datas = self.env['hr.overtime'].search([])
        if overtime_datas:
            overtime_dict = dict(map(lambda x: (x.hours, {'normal_day': x.normal_day,
                                'holiday': x.holiday, 'work_hours': x.work_hours}),overtime_datas))
        else:
            overtime_dict = {}

        list_employee = self.env['hr.minimum.wage'].search([('operation_type_id','=',self.operation_type_id.id)]).ids
        for employee in self.env['hr.employee'].search([('umr_ids.id','in',list_employee)]):
            min_wage = employee.get_salary(self.date_start)
            if min_wage:
                line_vals = {
                    'name'              : self.name,
                    'payroll_id'        : self.id,
                    'employee_id'       : employee.id,
                    'min_wage_id'       : min_wage.id,
                    'min_wage_month'    : min_wage.umr_month,
                    'operation_type_id'	: self.operation_type_id.id,
                }
            else:
                continue
            attendance_date_start = (datetime.strptime(self.date_start+' 00:00:00', "%Y-%m-%d %H:%M:%S") + timedelta(hours=-8)).strftime("%Y-%m-%d %H:%M:%S") if self.date_start else 0
            attendance_date_stop = (datetime.strptime(self.date_stop+' 23:59:59', "%Y-%m-%d %H:%M:%S") + timedelta(hours=-8)).strftime("%Y-%m-%d %H:%M:%S") if self.date_stop else 0
            attendances = self.env['hr.attendance'].search([('employee_id','=',employee.id),('valid','=',True), \
                    ('check_in','>=',attendance_date_start),('check_in','<=',attendance_date_stop)])
            att_to_update = self.env['hr.attendance']
            if attendances:
                effective_working_days = sum( \
                    attendances.filtered(lambda x: x.attendance_type_id.type=='effective_work_day').\
                        mapped('work_day'))
                non_effective_working_days = sum(\
                    attendances.filtered(lambda x: x.attendance_type_id.type == 'non_effective_work_day').\
                        mapped('work_day'))
                not_working = int(len(\
                    attendances.filtered(lambda x: x.attendance_type_id.type == 'not_working')))
                working_days_month = effective_working_days + non_effective_working_days + not_working
                working_days = effective_working_days + non_effective_working_days
                effective_working_salary_amt = 0.0
                non_effective_working_salary_amt = 0.0
                amount_natura = 0.0
                overtime_amt = 0.0
                penalty_amt = 0.0
                premi_amt = 0.0
                amount_pph21 = 0.0
                for att in attendances:
                    if not att.attendance_type_id:
                        continue
                    attendance_check_in = (datetime.strptime(att.check_in, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)) if att.check_in else 0
                    working_date = attendance_check_in.strftime(DF)
                    day_of_week = attendance_check_in.weekday()
                    if att.attendance_type_id.type=='effective_work_day':
                        # if working_date in day_off_dict.keys() or day_of_week==6:
                        #     effective_working_salary_amt += (att.work_day * (min_wage.umr_month/working_days_month))
                        #     overtime_t = float(att.working_time or 0.0) + float(att.overtime or 0.0)
                        #     base_overtime = float(int(overtime_t))
                        #     overtime_ratio = overtime_dict.get(base_overtime, {}).get('holiday', 0.0)
                        #     overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                        #     print '============================1',att.check_in,overtime_t, overtime_ratio, employee.name, overtime_amt
                        #     next_hour_overtime = overtime_t - base_overtime
                        #     if next_hour_overtime:
                        #         overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('holiday', 0.0)
                        #         overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2-overtime_ratio) * (min_wage.umr_month / 173)
                        # else:
                        effective_working_salary_amt += (att.work_day * (min_wage.umr_month/working_days_month))
                        overtime_t = float(att.overtime or 0.0)
                        base_overtime = float(int(overtime_t))
                        overtime_ratio = overtime_dict.get(base_overtime, {}).get('normal_day', 0.0)
                        overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                        next_hour_overtime = overtime_t - base_overtime
                        if next_hour_overtime:
                            overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('normal_day', 0.0)
                            overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2-overtime_ratio) * (min_wage.umr_month / 173)
                    elif att.attendance_type_id.type=='non_effective_work_day':
                            non_effective_working_salary_amt += (att.work_day * (min_wage.umr_month / working_days_month))
                    elif att.attendance_type_id.type=='overtime':
                        overtime_t = float(att.overtime or 0.0)
                        base_overtime = float(int(overtime_t))
                        overtime_ratio = overtime_dict.get(base_overtime, {}).get('holiday', 0.0)
                        overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                        next_hour_overtime = overtime_t - base_overtime
                        if next_hour_overtime:
                            overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('holiday', 0.0)
                            overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2 - overtime_ratio) * (min_wage.umr_month / 173)
                    elif att.attendance_type_id.type == 'not_available':
                        overtime_t = float(att.overtime or 0.0)
                        base_overtime = float(int(overtime_t))
                        overtime_ratio = overtime_dict.get(base_overtime, {}).get('normal_day', 0.0)
                        overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                        next_hour_overtime = overtime_t - base_overtime
                        if next_hour_overtime:
                            overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('holiday', 0.0)
                            overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2 - overtime_ratio) * (min_wage.umr_month / 173)
                    penalty_amt = 0 
                    premi_amt += att.premi_value
                    att_to_update |= att


                amount_natura = working_days < working_days_month and min_wage.amount_natura * (working_days/working_days_month) or min_wage.amount_natura or 0.0
                allowance_structural = min_wage.allowance_structural or 0.0
                allowance_production = working_days < working_days_month and min_wage.allowance_production * (working_days/working_days_month) or min_wage.allowance_production or 0.0

                if employee.type_id.monthly_employee:
                    effective_working_salary_amt = min_wage.umr_month
                    non_effective_working_salary_amt = 0
                    amount_natura = min_wage.amount_natura or 0.0
                    allowance_production = min_wage.allowance_production or 0.0

                # RAPEL
                rapel_ids = self.env['hr.attendance.rapel.line'].search([('employee_id', '=', employee.id), ('rapel_id.state', '=', 'confirm')]).filtered(lambda rekap: self.date_start <= rekap.rapel_id.date <= self.date_stop)
                rapel_value = sum(rapel_ids.mapped('total')) if rapel_ids else 0
                line_vals.update({
                    'effective_work_days': effective_working_days,
                    'effective_work_days_value': effective_working_salary_amt,
                    'non_effective_work_days': non_effective_working_days,
                    'non_effective_work_days_value': non_effective_working_salary_amt,
                    'overtime_value': overtime_amt,
                    'natura_value': amount_natura,
                    'penalty_value': penalty_amt,
                    'premi_value': premi_amt,
                    'allowance_production': allowance_production,
                    'allowance_structural': allowance_structural,
                    'amount_pph21': amount_pph21,
                    'rapel_value': rapel_value,
                })

            insurance_dict = employee.with_context(date=self.date_start).get_insurance_values(min_wage)
            line_vals.update(insurance_dict)
            payroll_line = PayrollLine.create(line_vals)

            if att_to_update:
                att_to_update.write({'payroll_line_id': payroll_line.id})

    @api.multi
    def action_create_bill(self):
        self.ensure_one()
        # 1. Grouping Salary Expenses
        grouped_hke = {}
        grouped_hkne = {}
        grouped_overtime = {}
        grouped_tunjangan = {}
        grouped_natura = {}
        grouped_bpjs_kes = {}
        grouped_bpjs_kes_pot = {}
        grouped_bpjs_tk = {}
        grouped_bpjs_tk_pot = {}
        grouped_bpjs_pen = {}
        grouped_bpjs_pen_pot = {}
        default_type_none = self.env['account.location.type'].search(['|', ('name', '=', '-'), ('code', '=', '-')],limit=1)
        for line in self.line_ids:
            employee = line.employee_id
            if not (line.effective_work_days_value or line.natura_value or line.overtime_value or line.non_effective_work_days_value):
                continue
            # 0.0 Validasi data
            salary_ok = bpjs_kes_ok = bpjs_tk_ok = bpjs_pen_ok = True
            if employee.default_account_salary_id:
                salary_ok = True
            else:
                raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Gaji.\n\
                        Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
            if line.potongan_bpjs_kes:
                if not employee.default_account_bpjs_allowance_id or not employee.inter_account_bpjs_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Kesehatan.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.") % employee.name)
                else:
                    bpjs_kes_ok = True

            if line.potongan_bpjs_tk:
                if not employee.default_account_ketenagakerjaan_allowance_id or not employee.inter_account_ketenagakerjaan_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Ketenagakerjaan.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
                else:
                    bpjs_tk_ok = True

            if line.potongan_bpjs_pensiun:
                if not employee.default_account_pensiun_allowance_id or not employee.inter_account_pensiun_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Pensiun.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
                else:
                    bpjs_pen_ok = True

            # 1.1 Grouped by Location are made for Basic Salary Expenses, Overtime Expenses, BPJS Kes and BPJS TK
            location_type = employee.default_location_type_id or (default_type_none or False)
            location = employee.default_location_id
            if location_type.id not in grouped_hke.keys() and salary_ok:
                grouped_hke.update({location_type.id: {}})
                grouped_hkne.update({location_type.id: {}})
                grouped_tunjangan.update({location_type.id: {}})
                grouped_natura.update({location_type.id: {}})
                grouped_overtime.update({location_type.id: {}})
                if bpjs_kes_ok:
                    grouped_bpjs_tk.update({location_type.id: {}})
                if bpjs_tk_ok:
                    grouped_bpjs_kes.update({location_type.id: {}})
                if bpjs_pen_ok:
                    grouped_bpjs_pen.update({location_type.id: {}})
            if location.id not in grouped_hke[location_type.id].keys() and salary_ok:
                grouped_hke[location_type.id].update({location.id:{}})
                grouped_hkne[location_type.id].update({location.id: {}})
                grouped_tunjangan[location_type.id].update({location.id: {}})
                grouped_natura[location_type.id].update({location.id: {}})
                grouped_overtime[location_type.id].update({location.id: {}})
                if bpjs_kes_ok:
                    grouped_bpjs_tk[location_type.id].update({location.id: {}})
                if bpjs_tk_ok:
                    grouped_bpjs_kes[location_type.id].update({location.id: {}})
                if bpjs_pen_ok:
                    grouped_bpjs_pen[location_type.id].update({location.id: {}})

            # 1.2 Grouped by Salary Account for Basic Salary Expenses
            salary_account = employee.default_account_salary_id
            if salary_account.id not in grouped_hke[location_type.id][location.id].keys() and salary_ok:
                grouped_hke[location_type.id][location.id].update({salary_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': salary_account.id,
                    'name': 'Beban Gaji Hari Kerja Efektif',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_hke[location_type.id][location.id][salary_account.id]['price_unit'] += (line.effective_work_days_value + line.premi_value - line.penalty_value)
            if salary_account.id not in grouped_hkne[location_type.id][location.id].keys() and salary_ok:
                grouped_hkne[location_type.id][location.id].update({salary_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': salary_account.id,
                    'name': 'Beban Gaji Hari Kerja Non-efektif',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_hkne[location_type.id][location.id][salary_account.id]['price_unit'] += line.non_effective_work_days_value

            allowance_account = employee.default_account_salary_id
            if allowance_account.id not in grouped_tunjangan[location_type.id][location.id].keys() and salary_ok:
                grouped_tunjangan[location_type.id][location.id].update({allowance_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': allowance_account.id,
                    'name': 'Beban Gaji Tunjangan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_tunjangan[location_type.id][location.id][allowance_account.id]['price_unit'] += line.allowance_structural + line.allowance_production

            # 1.3 Grouped by Overtime Account for Overtime Expenses
            overtime_account = employee.default_account_overtime_id or salary_account
            if overtime_account.id not in grouped_overtime[location_type.id][location.id].keys() and salary_ok:
                grouped_overtime[location_type.id][location.id].update({overtime_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': overtime_account.id,
                    'name': 'Beban Overtime',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_overtime[location_type.id][location.id][overtime_account.id]['price_unit'] += line.overtime_value

            # 1.4 Grouped by Natura Account for Overtime Expenses
            natura_account = employee.default_account_welfare_allowance_id or salary_account
            if natura_account.id not in grouped_natura[location_type.id][location.id].keys() and salary_ok:
                grouped_natura[location_type.id][location.id].update({natura_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': natura_account.id,
                    'name': 'Beban Natura',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_natura[location_type.id][location.id][natura_account.id]['price_unit'] += line.natura_value

            # BEBAN BPJS KES
            account_bpjs_kes = employee.default_account_bpjs_allowance_id
            if account_bpjs_kes.id not in grouped_bpjs_kes[location_type.id][location.id].keys() and bpjs_kes_ok:
                grouped_bpjs_kes[location_type.id][location.id].update({account_bpjs_kes.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_kes.id,
                    'name': 'Beban BPJS Kesehatan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_kes[location_type.id][location.id][account_bpjs_kes.id]['price_unit'] += line.tunjangan_bpjs_kes
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KESEHATAN
            account_bpjs_kes_pot = employee.inter_account_bpjs_allowance_id
            if account_bpjs_kes_pot.id not in grouped_bpjs_kes_pot.keys() and bpjs_kes_ok:
                grouped_bpjs_kes_pot.update({account_bpjs_kes_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_kes_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Kesehatan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_kes_pot[account_bpjs_kes_pot.id]['price_unit'] += line.potongan_bpjs_kes

            # BEBAN BPJS KETENAGAKERJAAN
            account_bpjs_tk = employee.default_account_ketenagakerjaan_allowance_id
            if account_bpjs_tk.id not in grouped_bpjs_tk[location_type.id][location.id].keys() and bpjs_tk_ok:
                grouped_bpjs_tk[location_type.id][location.id].update({account_bpjs_tk.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_tk.id,
                    'name': 'Beban BPJS Ketenagakerjaan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_tk[location_type.id][location.id][account_bpjs_tk.id]['price_unit'] += line.tunjangan_bpjs_tk
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KETENAGAKERJAAN
            account_bpjs_tk_pot = employee.inter_account_ketenagakerjaan_allowance_id
            if account_bpjs_tk_pot.id not in grouped_bpjs_tk_pot.keys() and bpjs_tk_ok:
                grouped_bpjs_tk_pot.update({account_bpjs_tk_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_tk_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Ketenagakerjaan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_tk_pot[account_bpjs_tk_pot.id]['price_unit'] += line.potongan_bpjs_tk

            # BEBAN BPJS PENSIUN
            account_bpjs_pen = employee.default_account_pensiun_allowance_id
            if account_bpjs_pen.id not in grouped_bpjs_pen[location_type.id][location.id].keys() and bpjs_pen_ok:
                grouped_bpjs_pen[location_type.id][location.id].update({account_bpjs_pen.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_pen.id,
                    'name': 'Beban BPJS Pensiun',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_pen[location_type.id][location.id][account_bpjs_pen.id]['price_unit'] += line.tunjangan_bpjs_pensiun
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KETENAGAKERJAAN
            account_bpjs_pen_pot = employee.inter_account_pensiun_allowance_id
            if account_bpjs_pen_pot.id not in grouped_bpjs_pen_pot.keys() and bpjs_pen_ok:
                grouped_bpjs_pen_pot.update({account_bpjs_pen_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_pen_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Pensiun',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_pen_pot[account_bpjs_pen_pot.id]['price_unit'] += line.potongan_bpjs_pensiun

        # Create Invoice AP
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        invoice_ids = []
        default_journal = self.env['account.journal'].search([('type','=','general')], limit=1)
        # 1. Create Invoice AP for Salary
        invoice1 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.payroll_partner_id.id,
            'account_id': self.payroll_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # Salary and Overtime Expenses
        salary_lines = []
        for loctype in grouped_hke.values() + grouped_hkne.values() + grouped_tunjangan.values() + grouped_natura.values():
            for loc in loctype.values():
                for x in loc.values():
                    salary_lines.append(x)
        for salary_expense in salary_lines:
            if not salary_expense['price_unit']:
                continue
            invoice_line_vals = salary_expense
            invoice_line_vals.update({'invoice_id': invoice1.id})
            AccountInvoiceLine.create(invoice_line_vals)
        overtime_lines = []
        for loctype in grouped_overtime.values():
            for loc in loctype.values():
                for x in loc.values():
                    overtime_lines.append(x)
        for overtime_expense in overtime_lines:
            if not overtime_expense['price_unit']:
                continue
            invoice_line_vals = overtime_expense
            invoice_line_vals.update({'invoice_id': invoice1.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_kes_pot in grouped_bpjs_kes_pot.values():
            if not bpjs_kes_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_pot
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_tk_pot in grouped_bpjs_tk_pot.values():
            if not bpjs_tk_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pot
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_tk_pen in grouped_bpjs_pen_pot.values():
            if not bpjs_tk_pen['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pen
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice1.compute_taxes()
        invoice_ids.append(invoice1.id)

        # 2. Create Invoice AP for BPJS Kesehatan
        invoice2 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.bpjs_kes_partner_id.id,
            'account_id': self.bpjs_kes_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # BPJS Expenses
        bpjs_lines = []
        for loctype in grouped_bpjs_kes.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines.append(x)
        for bpjs_kes_expenses in bpjs_lines:
            if not bpjs_kes_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_expenses
            invoice_line_vals.update({'invoice_id': invoice2.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_kes_pot in grouped_bpjs_kes_pot.values():
            if not bpjs_kes_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_pot
            invoice_line_vals.update({'invoice_id': invoice2.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice2.compute_taxes()
        invoice_ids.append(invoice2.id)

        # 3. Create Invoice AP for BPJS Ketenagakerjaan
        invoice3 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.bpjs_tk_partner_id.id,
            'account_id': self.bpjs_tk_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # BPJS Expenses
        bpjs_lines2 = []
        for loctype in grouped_bpjs_tk.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines2.append(x)
        for bpjs_tk_expenses in bpjs_lines2:
            if not bpjs_tk_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_expenses
            invoice_line_vals.update({'invoice_id': invoice3.id})
            AccountInvoiceLine.create(invoice_line_vals)
        bpjs_lines3 = []
        for loctype in grouped_bpjs_pen.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines3.append(x)
        for bpjs_pen_expenses in bpjs_lines3:
            if not bpjs_pen_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_pen_expenses
            invoice_line_vals.update({'invoice_id': invoice3.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_tk_pot in grouped_bpjs_tk_pot.values():
            if not bpjs_tk_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pot
            invoice_line_vals.update({'invoice_id': invoice3.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_pen_pot in grouped_bpjs_pen_pot.values():
            if not bpjs_pen_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_pen_pot
            invoice_line_vals.update({'invoice_id': invoice3.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice3.compute_taxes()
        invoice_ids.append(invoice3.id)

        self.invoice_ids = [(6,0,invoice_ids)]
        self.state='done'

        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice', 'default_journal_id': default_journal.id}
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        else:
            return False
        return result

class HrAttendancePayrollLine(models.Model):
    _inherit = 'hr.attendance.payroll.line'
    
    operation_type_id = fields.Many2one('hr.operation.type', related='payroll_id.operation_type_id', string='Hr Type')
    allowance_structural = fields.Float('Tunjangan Struktural')
    allowance_production = fields.Float('Tunjangan Produksi')
    amount_pph21 = fields.Float('PPH 21')
    premi_value = fields.Float('Nilai Premi')
    rapel_value = fields.Float("Rapel Value")