# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
import time
import base64
import xlrd
import io
import itertools
import logging
import psycopg2
import operator
import os
import re
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from xlrd import open_workbook, XLRDError
from odoo import models, fields, tools, exceptions, api, _
from odoo.osv import expression
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.misc import ustr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
_logger = logging.getLogger(__name__)

def time_to_float(d, e):
    total_seconds   = (d - e).seconds
    return float((total_seconds) / 60.0 / 60.0)

def calculate_time_between_date(date_stop, date_start):
        if date_stop and date_start:
            return float((datetime.strptime(date_stop,DT) - datetime.strptime(date_start,DT)).seconds)/ 60 / 60

class hr_attendance_type(models.Model):
    _name = 'hr.attendance.type'

    name = fields.Char('Kode', required=True)
    description = fields.Char('Deskripsi', required=True)
    type = fields.Selection([('effective_work_day', 'Effective Work Day'), \
                             ('non_effective_work_day', 'Non-Effective Work Day'), \
                             ('overtime', 'Overtime (exclusive)'), \
                             ('not_available', 'Not Available'), \
                             ('not_working', 'Not Working')], string='Type', required=True)
    notes = fields.Text('Catatan')

class hr_attendance_check(models.Model):
    _name           = 'hr.attendance.check'
    _order          = "employee_id ASC"

    name            = fields.Char("Name", related="import_id.name")
    employee_id     = fields.Many2one(comodel_name ="hr.employee", string="Employee")
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department', store=True)
    attendance_type_id = fields.Many2one("hr.attendance.type", string="Attend")
    b_date_start    = fields.Date("Work Date Start")
    b_date_stop     = fields.Date("Work Date Stop")
    business_start  = fields.Float("Work Time Start")
    business_stop   = fields.Float("Work Time Stop")
    business_rest   = fields.Float("Work Time Rest")
    business_total  = fields.Float("Work Total(h)")
    o_date_start    = fields.Date("Overtime Start")
    o_date_stop     = fields.Date("Overtime Stop")
    overtime_start  = fields.Float("Overtime Time Start")
    overtime_stop   = fields.Float("Overtime Time Stop")
    overtime_rest   = fields.Float("Overtime Time Rest")
    overtime_total  = fields.Float("Overtime Total (h)")
    total           = fields.Float("Total (h)")
    import_id       = fields.Many2one(comodel_name="hr.attendance.import", string="Import", ondelete="cascade")

    @api.onchange('b_date_start', 'b_date_stop', 'business_start', 'business_stop', 'business_rest',\
                  'o_date_start', 'o_date_stop', 'overtime_start', 'overtime_stop', 'overtime_rest')
    def onchange_work_time(self):
        AttendanceType = self.env['hr.attendance.type']
        default_attendance_work = AttendanceType.search(['|',('name','=','KJ'),('type','=','effective_work_day')], limit=1)
        default_attendance_overtime = AttendanceType.search(['|',('name','=','L'),('type','=','overtime')], limit=1)
        if self.b_date_start and self.b_date_stop:
            date_work_start = self.b_date_start
            date_work_stop = self.b_date_stop
            date_b_start = date_work_start + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(self.business_start * 60, 60)))
            date_b_stop = date_work_stop + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(self.business_stop * 60, 60)))
            date_b_subtotal = calculate_time_between_date(date_b_stop, date_b_start)
            self.business_total = date_b_subtotal - self.business_rest

            date_overtime_start = self.o_date_start or date_work_start
            date_overtime_stop = self.o_date_stop or date_work_stop
            date_o_start = date_overtime_start + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(self.overtime_start * 60, 60)))
            date_o_stop = date_overtime_stop + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(self.overtime_stop * 60, 60)))
            date_o_subtotal = calculate_time_between_date(date_o_stop, date_o_start)
            self.overtime_total = date_o_subtotal - self.overtime_rest
            self.total = (date_b_subtotal - self.business_rest) + (date_o_subtotal - self.overtime_rest)

            if date_b_subtotal:
                self.attendance_type_id = default_attendance_work and default_attendance_work.id or False
            elif not date_b_subtotal and date_o_subtotal:
                self.attendance_type_id = default_attendance_overtime and default_attendance_overtime.id or False
            else:
                self.attendance_type_id = False

class hr_attendance_biometric(models.Model):
    _name           = 'hr.attendance.biometric'

    import_id       = fields.Many2one(comodel_name="hr.attendance.import", string="Import")
    bio_id          = fields.Integer("ID")
    bio_nik         = fields.Char("NIK")
    bio_name_real   = fields.Char("Real Name")
    bio_name_id     = fields.Many2one(comodel_name ="hr.employee", string="Name")
    bio_date        = fields.Datetime("Real Date")
    date            = fields.Datetime("Date")
    bio_status      = fields.Char("Status")
    bio_new_status  = fields.Char("Status Baru")
    bio_except      = fields.Char("Pengecualian")
    bio_note_check  = fields.Char("Attendance")
    bio_note_rest   = fields.Char("Rest")
    error_message   = fields.Char("Notification")
    state           = fields.Selection([('fail', 'Fail'), ('pass', 'Pass'), ('warning', 'warning')], string='Status', default='pass', index=True)
    attn_state      = fields.Selection([('none', 'None'), ('check_in', 'Check In'), ('check_out', 'Check Out'),
                                        ('rest_in', 'Rest In'), ('rest_out', 'Rest Out'), ('duplicate', 'Duplicate'),
                                        ('no_employee', 'No Employee'),
                                        ], string='Attendance Status', default='none', index=True)

class hr_attendance(models.Model):
    _inherit        = 'hr.attendance'
    _order          = 'employee_id ASC, check_in ASC'

    import_id = fields.Many2one(comodel_name="hr.attendance.import", string="Import", ondelete="cascade")
    attendance_type_id = fields.Many2one('hr.attendance.type', 'Attendance Type')
    total_time = fields.Float("Work Time")
    rest_in = fields.Datetime("Rest In")
    rest_out = fields.Datetime("Rest Out")
    total_rest = fields.Float("Rest Time")
    work_day_time = fields.Float("Basic Work Day")
    overtime = fields.Float("Overtime(h)")
    working_time = fields.Float("Total Time")
    work_day = fields.Float("Work Day")
    penalty_value = fields.Float('Penalty/Potongan')
    valid = fields.Boolean('Valid')
    note = fields.Text("Keterangan")
    employee_salary = fields.Float("Salary/Day")
    payroll_line_id = fields.Many2one('hr.attendance.payroll.line', string='Payroll')

    @api.onchange('check_in', 'check_out')
    def onchange_total_time(self):
        if self.check_in or self.check_out:
            if self.check_in and self.check_out:
                self.total_time     = calculate_time_between_date(self.check_out, self.check_in)
                self.working_time   = (calculate_time_between_date(self.check_out, self.check_in) or 0.0) - (calculate_time_between_date(self.rest_out, self.rest_in) or 0.0)
                self.hk             = self.working_time
                self.work_day_time  = self.working_day_time(self.check_in, self.env.user.company_id)

    @api.onchange('rest_in', 'rest_out')
    def onchange_rest_time(self):
        if self.rest_out or self.rest_in:
            if self.rest_in and self.rest_out:
                self.total_rest     = calculate_time_between_date(self.rest_out, self.rest_in)
                self.working_time   = (calculate_time_between_date(self.check_out, self.check_in) or 0.0) - (calculate_time_between_date(self.rest_out, self.rest_in) or 0.0)
                self.hk             = self.working_time
                self.work_day_time  = self.working_day_time(self.check_in, self.env.user.company_id)

    def working_day_time(self, date, company_id):
        if date and company_id:
            if fields.Date.from_string(date).weekday() == 0:
                return company_id.work_time_monday or 0.0
            elif fields.Date.from_string(date).weekday() == 1:
                return company_id.work_time_tuesday or 0.0
            elif fields.Date.from_string(date).weekday() == 2:
                return company_id.work_time_wednesday or 0.0
            elif fields.Date.from_string(date).weekday() == 3:
                return company_id.work_time_thursday or 0.0
            elif fields.Date.from_string(date).weekday() == 4:
                return company_id.work_time_friday or 0.0
            elif fields.Date.from_string(date).weekday() == 5:
                return company_id.work_time_saturday or 0.0
            elif fields.Date.from_string(date).weekday() == 6:
                return company_id.work_time_sunday or 0.0
            else:
                return 0.0
        else:
            return 0.0

class hr_attendance_import(models.Model):
    _name           = 'hr.attendance.import'
    _description    = 'Attendance Import'
    _order          = 'name DESC, date DESC'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.attendance.import.sequence.number') or _('New')
        result = super(hr_attendance_import, self).create(vals)
        return result

    name            = fields.Char("Name", readonly=True, states={'draft': [('readonly',False)]})
    date            = fields.Date("Date", readonly=True, states={'draft': [('readonly',False)]})
    book            = fields.Binary(string='File Excel', readonly=True, states={'draft': [('readonly',False)]})
    book_filename   = fields.Char(string='File Name', readonly=True, states={'draft': [('readonly',False)]})
    line_ids        = fields.One2many('hr.attendance', 'import_id', string="Attendances", readonly=True, states={'confirm': [('readonly',False)]})
    biometric_ids   = fields.One2many('hr.attendance.biometric', 'import_id', string="Details", readonly=True, states={'draft': [('readonly',False)]})
    check_ids       = fields.One2many('hr.attendance.check', 'import_id', string="Check", readonly=True, states={'manual_attendance': [('readonly',False)]})
    company_id      = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get(), readonly=True, states={'draft': [('readonly',False)]})
    state           = fields.Selection([('draft', 'Draft'), ('imported', 'Imported'), ('manual_attendance','Manual Correction'), ('confirm', 'Confirmed'), ('validated', 'Validated')], string='Status', default='draft', index=True)

    def _prepare_check_value(self, employee):
        return {
            'employee_id': employee.id,
            'import_id': self.id,
            'b_date_start': self.date,
            'b_date_stop': self.date,
            'o_date_start': self.date,
            'o_date_stop': self.date,
            # 'business_start': self.date,
        }

    @api.multi
    def process_attendance_check(self):
        # This method is made to convert from raw data from fingerprint device
        # and then convert it into summary of start end end time of work for each employee
        self.ensure_one()
        for x in self.check_ids:
            x.unlink()

        # bikin defaulting Attendance Line
        # for employee in self.biometric_ids.mapped('bio_name_id'):
        for employee in self.env['hr.employee'].search([('department_id','!=',False)]):
            checkpoint_vals = self._prepare_check_value(employee)
            self.env['hr.attendance.check'].create(checkpoint_vals)

        self.state = 'manual_attendance'
        return True

    def _prepare_attendance_value(self, checkpoint_line):
        min_wage = checkpoint_line.employee_id.get_salary(checkpoint_line.b_date_start)
        penalty_value = 0.0
        check_in = (datetime.strptime(
            checkpoint_line.b_date_start + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(checkpoint_line.business_start * 60, 60))),
            DT) + relativedelta(hours=-7)).strftime(DT)
        check_out = (datetime.strptime(
            checkpoint_line.b_date_stop + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(checkpoint_line.business_stop * 60, 60))),
            DT) + relativedelta(hours=-7)).strftime(DT)
        work_day_std = self.env['hr.attendance'].working_day_time(check_in, self.env.user.company_id) or 7.0
        if not work_day_std:
            raise exceptions.ValidationError(_("Please input your Working Time Standard!"))
        office_time = checkpoint_line.business_total + checkpoint_line.business_rest
        total_time = checkpoint_line.business_total
        working_time = total_time + checkpoint_line.overtime_total
        if checkpoint_line.attendance_type_id.type == 'effective_work_day':
            if working_time: # Sesuaikan nilai HKE terhadap waktu kerja harian
                if working_time >= work_day_std:
                    work_day = 1.0
                else:
                    work_day = working_time / work_day_std
            else: # Jika tipe absensi adalah HKE, sedangkan employee tidak punya absensi, kemungkinan dia Dinas luar
                work_day = 1.0
        elif checkpoint_line.attendance_type_id.type == 'non_effective_work_day':
            work_day = 1.0
        elif checkpoint_line.attendance_type_id.type == 'not_working' and min_wage:
            penalty_value = min_wage.umr_day
            work_day = 0.0
        else:
            work_day  = 0.0
        return {
            'import_id' : self.id,
            'employee_id' : checkpoint_line.employee_id.id,
            'attendance_type_id': checkpoint_line.attendance_type_id.id,
            'check_in' : check_in,
            'check_out' : check_out,
            'total_time': total_time,
            'overtime' : checkpoint_line.overtime_total,
            'working_time': working_time,
            'work_day': work_day,
            'work_day_time': work_day_std,
            'penalty_value': penalty_value,
        }

    @api.multi
    def process_attendance(self):
        # This method is made to calculate hourly amount of salary based on attendance checkpoint
        self.ensure_one()
        for x in self.line_ids:
            x.unlink()

        for checkpoint in self.check_ids:
            att_line = self.env['hr.attendance'].create(self._prepare_attendance_value(checkpoint))
        self.state = 'confirm'
        return True

    @api.multi
    def action_validate(self):
        self.ensure_one()
        self.state='validated'
        for line in self.line_ids:
            line.valid = True
        return True

    @api.multi
    def check_attendance_biometric(self):
        self.ensure_one()
        ####Start Check Lines####
        for employee in self.biometric_ids.mapped('bio_name_id'):
            biometric_date      = False
            check_last_line     = 0
            check_in            = 0
            check_out           = 0
            rest_in             = 0
            rest_out            = 0
            duplicate           = False
            prev_biometric      = False
            biometric_data = sorted(self.biometric_ids.filtered(lambda x: x.bio_name_id.id==employee.id), key=lambda k: k.bio_date)
            for biometric in biometric_data:
                check_last_line += 1
                if biometric_date == biometric.bio_date:
                    biometric.attn_state = 'duplicate'
                    biometric.state = 'fail'
                    prev_biometric.attn_state ='duplicate'
                    prev_biometric.state = 'fail'
                    duplicate = True
                elif len(biometric_data) == check_last_line:
                    if check_in == 0:
                        biometric.attn_state = 'check_in'
                        biometric.state = 'pass'
                        biometric.error_message = 'Work'
                    else:
                        biometric.attn_state = 'check_out'
                        biometric.state = 'pass'
                        biometric.error_message = 'Work'
                        check_out += 1
                elif not biometric_date:
                    biometric.attn_state = 'check_in'
                    biometric.state = 'pass'
                    biometric.error_message = 'Work'
                    check_in += 1
                elif biometric_date and biometric.attn_state not in ['check_in', 'check_out', 'rest_out'] and rest_in == 0:
                    biometric.attn_state = 'rest_in'
                    rest_in += 1
                    biometric.state = 'pass'
                    biometric.error_message = 'Work'
                elif biometric_date and biometric.attn_state not in ['check_in', 'check_out', 'rest_in'] and rest_in <> 0:
                    biometric.attn_state = 'rest_out'
                    biometric.state = 'pass'
                    biometric.error_message = 'Work'
                    rest_out += 1
                biometric_date      = biometric.bio_date
                prev_biometric      = biometric

            for biometric in biometric_data:
                if duplicate == True:
                    biometric.state = 'fail'
                    biometric.error_message = 'Duplicate date'
        if 'fail' not in self.biometric_ids.mapped('state'):
            self.state = 'imported'
        return True #untuk keperluan debug

    @api.multi
    def import_attendance_biometric(self):
        """
        XL_CELL_EMPTY	0	empty string ‘’
        XL_CELL_TEXT	1	a Unicode string
        XL_CELL_NUMBER	2	float
        XL_CELL_DATE	3	float
        XL_CELL_BOOLEAN	4	int; 1 means True, 0 means False
        XL_CELL_ERROR	5	int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
        XL_CELL_BLANK	6	empty string ‘’. Note: this type will appear only when open_workbook(..., formatting_info= True) is used.
        """
        attendance_obj  = self.env['hr.attendance.biometric']
        if not self.book:
            raise exceptions.ValidationError(_("Upload your data first!"))
        ## Unlink First
        if self.line_ids:
            for lines in self.line_ids:
                lines.unlink()
        if self.biometric_ids:
            for unlink in self.biometric_ids:
                unlink.unlink()
        ######################################################################################################
        data        = base64.decodestring(self.book)
        try:
            xlrd.open_workbook(file_contents=data)
        except XLRDError:
            raise exceptions.ValidationError(_("Unsupported Format!"))
        wb          = xlrd.open_workbook(file_contents=data)
        total_sheet = len(wb.sheet_names())
        for i in range(total_sheet):
            sheet       = wb.sheet_by_index(i)
            for rows in range(sheet.nrows):
                #Rows 1 hanya untuk title
                if rows == 0:
                    for j in range(sheet.ncols):
                        if j == 0 and sheet.cell_value(rows, j) <> "ID":
                            raise exceptions.ValidationError(_("Column Title '1 A' must be 'ID'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 1 and sheet.cell_value(rows, j) <> "NIK":
                            raise exceptions.ValidationError(_("Column '1 B' must be 'ID'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 2 and sheet.cell_value(rows, j) <> "Nama":
                            raise exceptions.ValidationError(_("Column '1 C' must be 'Nama'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 3 and sheet.cell_value(rows, j) <> "Waktu":
                            raise exceptions.ValidationError(_("Column '1 D' must be 'Jam Masuk'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 4 and sheet.cell_value(rows, j) <> "Status":
                            raise exceptions.ValidationError(_("Column '1 E' must be 'Jam Istirahat'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 5 and sheet.cell_value(rows, j) <> "Status baru":
                            raise exceptions.ValidationError(_("Column '1 F' must be 'Jam Masuk Istirahat'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                        if j == 6 and sheet.cell_value(rows, j) <> "Pengecualian":
                            raise exceptions.ValidationError(_("Column '1 G' must be 'Jam Pulang'! \n Column Title Now : %s \n Error Sheet : %s")%(sheet.cell_value(rows, j), sheet.name))
                else:
                    employee_id     = False
                    date_bio        = False
                    state           = 'pass'
                    attn_state      = 'none'
                    error_message   = 'Work'
                    for k in range(sheet.ncols):
                        if k == 1:
                            nik = False
                            if sheet.cell(rows, k).ctype == 1:
                                nik = str(int(sheet.cell(rows, k).ctype))
                            elif sheet.cell(rows, k).ctype == 3:
                                nik = str(sheet.cell(rows, k).ctype)

                            if not nik:
                                state = 'fail'
                                attn_state = 'no_employee'
                                error_message = 'Please Input NIK for Employee %s' % (sheet.cell_value(rows, 2))
                                pass

                            employee_ids = self.env['hr.employee'].search([('no_induk', '=', sheet.cell_value(rows, k))])
                            if len(employee_ids) > 1:
                                employee_id = employee_ids[-1].id
                            elif len(employee_ids) == 0:
                                state = 'fail'
                                attn_state = 'no_employee'
                                error_message = 'Employee %s not found'%(sheet.cell_value(rows, k))
                                pass
                            else:
                                employee_id = employee_ids.id
                        else:
                            pass
                        if k == 3 and sheet.cell(rows, k).ctype == 3:
                            date_bio = datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rows, k), wb.datemode))
                        elif k == 3 and sheet.cell(rows, k).ctype == 1:
                            date_bio    = datetime.strptime(sheet.cell_value(rows, k), '%d/%m/%Y %H:%M')
                    # if date_bio.strftime('%Y-%m-%d') == self.date :
                    if True:
                        attendance_obj.create({
                            'import_id'     : self.id,
                            'bio_id'        : int(sheet.cell_value(rows, 0)),
                            'bio_nik'       : sheet.cell_value(rows, 1),
                            'bio_name_id'   : employee_id or False,
                            'bio_name_real' : sheet.cell_value(rows, 2),
                            'bio_date'      : (date_bio - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
                            'date'          : (date_bio - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
                            'bio_status'    : sheet.cell_value(rows, 4),
                            'bio_new_status': sheet.cell_value(rows, 5),
                            'bio_except'    : sheet.cell_value(rows, 6),
                            'bio_note_check': sheet.cell_value(rows, 7),
                            'bio_note_rest' : sheet.cell_value(rows, 8),
                            'state'         : state,
                            'attn_state'    : attn_state,
                            'error_message' : error_message,
                        })
        self.check_attendance_biometric()
        if self.biometric_ids:
            self.state='imported'
        return True

    @api.multi
    def back_to_manual_entry(self):
        self.ensure_one()
        for x in self.line_ids:
            x.sudo().unlink()
        self.state = 'manual_attendance'
        return True

    @api.multi
    def back_to_draft(self):
        self.ensure_one()
        self.state = 'draft'
        return True

    @api.multi
    def action_reopen(self):
        self.ensure_one()
        for att in self.line_ids:
            if att.payroll_line_id:
                if att.payroll_line_id.payroll_id.state!='cancel':
                    raise exceptions.ValidationError(_("This attendance already used in Payroll.\n\
                            Cancel the payroll before editin this attendance"))
                else:
                    att.sudo().payroll_line_id.unlink()
            att.valid = False
        self.state = 'confirm'
        return True