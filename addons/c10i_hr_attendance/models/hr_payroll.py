# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author1 Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   @author2 Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from datetime import datetime
from odoo import models, fields, tools, exceptions, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

class hr_attendance_payroll(models.Model):
    _name               = 'hr.attendance.payroll'
    _inherit            = ['mail.thread', 'ir.needaction_mixin']

    name                = fields.Char(readonly=True, compute='_compute_payroll_name', string='Name', store=True, track_visibility='onchange')
    date_start          = fields.Date("Date Start", track_visibility='onchange', readonly=True, states={'draft': [('readonly',False)]})
    date_stop           = fields.Date("Date Stop", track_visibility='onchange', readonly=True, states={'draft': [('readonly',False)]})
    account_period_id   = fields.Many2one("account.period", string="Accounting Periode", ondelete="restrict", track_visibility='onchange', readonly=True, states={'draft': [('readonly',False)]})
    company_id          = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get())
    line_ids            = fields.One2many("hr.attendance.payroll.line", inverse_name="payroll_id", string="Details", states={'done': [('readonly',True)]})
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Close')], string='Status', default='draft')

    @api.multi
    @api.depends('account_period_id')
    def _compute_payroll_name(self):
        for payroll in self:
            payroll.name = "Payroll " + str(payroll.account_period_id.name or "")

    @api.onchange('account_period_id')
    def onchange_account_period_id(self):
        if self.account_period_id:
            self.date_start = self.account_period_id.date_start
            self.date_stop = self.account_period_id.date_stop

    @api.multi
    def action_confirm(self):
        self.state = "confirmed"
        return True

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

        for employee in self.env['hr.employee'].search([]):
            min_wage = employee.get_salary(self.date_start)
            if min_wage:
                line_vals = {
                    'name'              : self.name,
                    'payroll_id'        : self.id,
                    'employee_id'       : employee.id,
                    'min_wage_id'       : min_wage.id,
                    'min_wage_month'    : min_wage.umr_month,
                }
            else:
                continue
            attendances = self.env['hr.attendance'].search([('employee_id','=',employee.id),('valid','=',True), \
                    ('check_in','>=',self.date_start+' 00:00:00'),('check_in','<=',self.date_stop+' 23:59:59')])
            att_to_update = self.env['hr.attendance']
            if attendances:
                effective_working_days = sum( \
                    attendances.filtered(lambda x: x.attendance_type_id.type=='effective_work_day').\
                        mapped('work_day'))
                non_effective_working_days = sum(\
                    attendances.filtered(lambda x: x.attendance_type_id.type == 'non_effective_work_day').\
                        mapped('work_day'))
                working_days = effective_working_days + non_effective_working_days
                effective_working_salary_amt = 0.0
                non_effective_working_salary_amt = 0.0
                overtime_amt = 0.0
                penalty_amt = 0.0
                for att in attendances:
                    if not att.attendance_type_id:
                        continue
                    working_date = datetime.strptime(att.check_in, DT).strftime(DF)
                    day_of_week = datetime.strptime(att.check_in, DT).weekday()
                    if att.attendance_type_id.type=='effective_work_day':
                        if working_date in day_off_dict.keys() or day_of_week==6:
                            overtime_t = float(att.working_time or 0.0) + float(att.overtime or 0.0)
                            base_overtime = float(int(overtime_t))
                            overtime_ratio = overtime_dict.get(base_overtime, {}).get('holiday', 0.0)
                            overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                            next_hour_overtime = overtime_t - base_overtime
                            if next_hour_overtime:
                                overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('holiday', 0.0)
                                overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2-overtime_ratio) * (min_wage.umr_month / 173)
                        else:
                            if employee.type_id.monthly_employee:
                                effective_working_salary_amt += (att.work_day * (min_wage.umr_month / working_days))
                            else:
                                effective_working_salary_amt += (att.work_day * min_wage.umr_day)
                            overtime_t = float(att.overtime or 0.0)
                            base_overtime = float(int(overtime_t))
                            overtime_ratio = overtime_dict.get(base_overtime, {}).get('normal_day', 0.0)
                            overtime_amt += overtime_ratio * (min_wage.umr_month / 173)
                            next_hour_overtime = overtime_t - base_overtime
                            if next_hour_overtime:
                                overtime_ratio2 = overtime_dict.get((base_overtime + 1), {}).get('normal_day', 0.0)
                                overtime_amt += ((next_hour_overtime * 60) / 60) * (overtime_ratio2-overtime_ratio) * (min_wage.umr_month / 173)
                    elif att.attendance_type_id.type=='non_effective_work_day':
                        if employee.type_id.monthly_employee:
                            non_effective_working_salary_amt += (att.work_day * (min_wage.umr_month / working_days))
                        else:
                            non_effective_working_salary_amt += (att.work_day * min_wage.umr_day)
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
                    penalty_amt += att.penalty_value
                    att_to_update |= att

                line_vals.update({
                    'effective_work_days': effective_working_days,
                    'effective_work_days_value': effective_working_salary_amt,
                    'non_effective_work_days': non_effective_working_days,
                    'non_effective_work_days_value': non_effective_working_salary_amt,
                    'overtime_value': overtime_amt,
                    'natura_value': employee.default_amount_natura,
                    'penalty_value': penalty_amt,
                })

            insurance_dict = employee.with_context(date=self.date_start).get_insurance_values(min_wage)
            line_vals.update(insurance_dict)
            payroll_line = PayrollLine.create(line_vals)

            if att_to_update:
                att_to_update.write({'payroll_line_id': payroll_line.id})

class hr_attendance_payroll_line(models.Model):
    _name = 'hr.attendance.payroll.line'

    name = fields.Char(string='Name')
    payroll_id = fields.Many2one('hr.attendance.payroll', string='Payroll')
    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete="restrict")
    min_wage_id = fields.Many2one('hr.minimum.wage', string='UMR ID', ondelete="restrict")
    effective_work_days = fields.Float('HKE')
    non_effective_work_days = fields.Float('HKNE')
    effective_work_days_value = fields.Float('HKE Value')
    non_effective_work_days_value = fields.Float('HKNE Value')
    overtime_value = fields.Float('Overtime Value')
    natura_value = fields.Float('Natura Value')
    penalty_value = fields.Float('Penalty Value')
    attendance_line_ids = fields.One2many('hr.attendance', 'payroll_line_id', string='Attendance Lines')