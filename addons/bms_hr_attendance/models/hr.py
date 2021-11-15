import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class HrOperationType(models.Model):
	_name = 'hr.operation.type'

	name = fields.Char('Type Name')
	user_ids = fields.Many2many('res.users', 'hr_operation_type_user_allowed_rel', 'type_id', 'user_id', string='Allowed Users')

class Users(models.Model):
	_inherit = 'res.users'
	
	hr_type_ids = fields.Many2many('hr.operation.type', 'hr_operation_type_user_allowed_rel', 'user_id', 'type_id', string='HR Type')

class HrWage(models.Model):
	_inherit = 'hr.minimum.wage'

	operation_type_id = fields.Many2one('hr.operation.type', string='Hr Type')
	amount_natura = fields.Float('Natura')
	allowance_structural = fields.Float('Tunjangan Struktural')
	allowance_production = fields.Float('Tunjangan Produksi')
	no_induk = fields.Char("NIK")
	dasar_bpjs = fields.Float("Pendapatan Dasar BPJS")

class hr_employee(models.Model):
	_inherit        = 'hr.employee'
	_description    = 'Employee Management'

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			if record.no_induk:
				record_name = record.no_induk + ' - ' + record.name
				result.append((record.id, record_name))
		return result

	def get_insurance_values(self, min_wage):
		res = super(hr_employee, self).get_insurance_values(min_wage)
		date = self._context.get('date', time.strftime(DF))
		# bpjs kes
		if self.kesehatan and self.kesehatan_date_start<=date:
			bpjs_kes = self.env['hr.insurance'].search([('type','=','kesehatan'),('date_from','<=',date),('date_to','>=',date)])
			bpjs_kes_tunjangan = bpjs_kes_potongan = 0.0
			for x in bpjs_kes:
				bpjs_kes_tunjangan += min_wage.dasar_bpjs * x.tunjangan / 100
				bpjs_kes_potongan += min_wage.dasar_bpjs * x.potongan / 100
			res.update({
				'amount_bpjs_kes': bpjs_kes_potongan + bpjs_kes_tunjangan,
				'potongan_bpjs_kes': bpjs_kes_potongan,
				'tunjangan_bpjs_kes': bpjs_kes_tunjangan,
			})
		if self.ketenagakerjaan and self.ketenagakerjaan_date_start<=date:
			bpjs_tk = self.env['hr.insurance'].search([('type','=','ketenagakerjaan'),('date_from','<=',date),('date_to','>=',date)])
			bpjs_tk_tunjangan = bpjs_tk_potongan = 0.0
			for x in bpjs_tk:
				bpjs_tk_tunjangan += min_wage.dasar_bpjs * x.tunjangan / 100
				bpjs_tk_potongan += min_wage.dasar_bpjs * x.potongan / 100
			res.update({
				'amount_bpjs_tk': bpjs_tk_potongan + bpjs_tk_tunjangan,
				'potongan_bpjs_tk': bpjs_tk_potongan,
				'tunjangan_bpjs_tk': bpjs_tk_tunjangan,
			})
		if self.pensiun and self.pensiun_date_start <= date:
			bpjs_pensiun = self.env['hr.insurance'].search([('type','=','pensiun'),('date_from','<=',date),('date_to','>=',date)])
			bpjs_pen_tunjangan = bpjs_pen_potongan = 0.0
			for x in bpjs_pensiun:
				bpjs_pen_tunjangan += min_wage.dasar_bpjs * x.tunjangan / 100
				bpjs_pen_potongan += min_wage.dasar_bpjs * x.potongan / 100
			res.update({
				'amount_bpjs_pensiun': bpjs_pen_potongan + bpjs_pen_tunjangan,
				'potongan_bpjs_pensiun': bpjs_pen_potongan,
				'tunjangan_bpjs_pensiun': bpjs_pen_tunjangan,
			})
		return res