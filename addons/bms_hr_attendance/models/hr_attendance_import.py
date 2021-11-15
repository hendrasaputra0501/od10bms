# -*- coding: utf-8 -*-

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

def calculate_time_between_date(date_stop, date_start):
		if date_stop and date_start:
			return float((datetime.strptime(date_stop,DT) - datetime.strptime(date_start,DT)).seconds)/ 60 / 60

class hr_attendance_import(models.Model):
	_inherit           = 'hr.attendance.import'

	@api.model
	def _get_default_tipe(self):
		user = self.env['res.users'].browse(self.env.uid).default_operating_unit_id.id
		return user

	operating_unit_id = fields.Many2one("operating.unit", string="Tipe", default=_get_default_tipe)
	search_ids = fields.Char(compute="_compute_search_ids", search='search_ids_search')
	# line_ids        = fields.One2many('hr.attendance', 'import_id', string="Attendances",compute='_compute_search_ids', readonly=True, states={'confirm': [('readonly',False)]})

	# @api.one
	# @api.depends('operating_unit_id')
	# def _compute_search_ids(self):
	# 	# if self.check_ids:
	# 	obj2 = self.line_ids.search([('import_id','=',self.id),('department_id.operating_unit_id','=',self.operating_unit_id.id)])
	# 	# print '==============================', obj
	# 	self.check_ids = obj
	# 	self.line_ids = obj2

	def search_ids_search(self,operator, operand):
		obj=self.env['hr.attendance.import'].search([('operating_unit_id','in',self.env.user.operating_unit_ids.ids)]).ids
		return [('id','in',obj)]

	def _prepare_check_value(self, employee):
		business_start = 0.0
		business_stop = 0.0
		b_date_start = self.date
		b_date_stop = self.date
		default_attendance_work = self.env['hr.attendance.type']
		for employ in sorted(self.biometric_ids.filtered(lambda x: x.bio_name_id.id==employee.id), key=lambda k: k.bio_date):	#filtered(lambda r: r.bio_name_id.id==employee.id):
			if employ.attn_state == 'check_in':
				date = datetime.strptime(employ.bio_date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)# convert into datetime fromat
				b_date_start = date.date()
				time = date.time()
				business_start = float(time.hour)+float(time.minute)/60
			elif employ.attn_state == 'check_out':
				date = datetime.strptime(employ.bio_date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)# convert into datetime fromat
				b_date_stop = date.date()
				time = date.time()
				business_stop = float(time.hour)+float(time.minute)/60
		if business_start and business_stop:
			AttendanceType = self.env['hr.attendance.type']
			default_attendance_work = AttendanceType.search(['|',('name','=','KJ'),('type','=','effective_work_day')], limit=1)
		return {
			'employee_id': employee.id,
			'import_id': self.id,
			'b_date_start': b_date_start,
			'b_date_stop': b_date_stop,
			'o_date_start': b_date_start,
			'o_date_stop': b_date_stop,
			'business_start': business_start,
			'business_stop': business_stop,
			'attendance_type_id': default_attendance_work.id,
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
		for employee in self.env['hr.employee'].search([('department_id.operating_unit_id','=',self.operating_unit_id.id)]):
			checkpoint_vals = self._prepare_check_value(employee)
			self.env['hr.attendance.check'].create(checkpoint_vals)

		self.state = 'manual_attendance'
		return True

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
							'bio_date'      : (date_bio - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
							'date'          : (date_bio - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
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

	def _prepare_attendance_value(self, checkpoint_line):
		min_wage = checkpoint_line.employee_id.get_salary(checkpoint_line.b_date_start)
		penalty_value = 0.0
		check_in = (datetime.strptime(
			checkpoint_line.b_date_start + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(checkpoint_line.business_start * 60, 60))),
			DT) + relativedelta(hours=-8)).strftime(DT)
		check_out = (datetime.strptime(
			checkpoint_line.b_date_stop + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(checkpoint_line.business_stop * 60, 60))),
			DT) + relativedelta(hours=-8)).strftime(DT)
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
					work_day = 1.0
					# work_day = working_time / work_day_std
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
			if checkpoint.overtime_total:
				if checkpoint.o_date_start<checkpoint.b_date_stop and checkpoint.overtime_total and checkpoint.business_total:
					raise exceptions.ValidationError(_(str(checkpoint.employee_id.name)+":Overtime start < Work Stop!"))
			att_line = self.env['hr.attendance'].create(self._prepare_attendance_value(checkpoint))
		self.state = 'confirm'
		return True

	@api.multi
	def action_reopen(self):
		self.ensure_one()
		for att in self.line_ids:
			if att.payroll_line_id:
				if att.payroll_line_id.payroll_id.state!='draft':
					raise exceptions.ValidationError(_("This attendance already used in Payroll.\n\
							Draft the payroll before editin this attendance"))
				else:
					att.sudo().payroll_line_id.unlink()
			att.valid = False
		self.state = 'confirm'
		return True


class hr_attendance_check(models.Model):
	_inherit           = 'hr.attendance.check'
	_order          = "employee_id ASC"

	@api.depends('business_start', 'business_stop', 'business_rest')
	def _get_business_total(self):
		for check in self:
			if check.business_stop or check.business_start:
				date_work_start = check.b_date_start
				date_work_stop = check.b_date_stop
				business_start = check.business_start if check.business_start else 00.00
				business_stop = check.business_stop if check.business_stop else 00.00
				date_b_start = date_work_start + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(business_start * 60, 60)))
				date_b_stop = date_work_stop + " %s:00" % ('{0:02.0f}:{1:02.0f}'.format(*divmod(business_stop * 60, 60)))
				date_b_subtotal = calculate_time_between_date(date_b_stop, date_b_start)
				check.business_total = date_b_subtotal - check.business_rest

	business_total  = fields.Float("Work Total(h)", compute=_get_business_total)
