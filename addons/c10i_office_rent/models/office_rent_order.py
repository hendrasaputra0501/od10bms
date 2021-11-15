from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class OfficeRentOrder(models.Model):
	_name = 'office.rent.order'
	_inherit = 'sale.order'
	_description = 'Office rent order'

	rent_order = fields.Boolean(string='Rent Order', default=True)
	start_date = fields.Date(string='Start Date', required=True,)
	end_date = fields.Date(string='End Date', required=True, )
	duration = fields.Integer(string='Duration', required=True, default=0)
	next_payment = fields.Date(string='Last Payment',)
	order_line_ids = fields.One2many('office.rent.order.line', 'order_id', string='Order Lines')
	tenancy_ids = fields.Many2many('office.rent.unit.tenancy', 'relasi_tenancy_order', 'order_id', 'tenancy_id')
	payment_method_period = fields.Selection([(1,"1 Month"),
			(3,"3 months"),
			(6,"6 months"),
			(12,"1 year")], string="Period of Rent Payment", default=1, required=True,)
	tuition_schedule_date = fields.Integer(string="Schedule Date of Tuition Payment", 
        default=lambda self: self.env.user.company_id.tuition_schedule_date, required=True,
        help="Please put Schedule Date for this Units Bills to be generated")

	@api.multi	
	def action_confirm(self, vals):
		# print "========================", self
		unit = self.env['office.rent.unit'].search([('name','=',self.order_line_ids['product_id'].name)])
		tenant = self.env["office.rent.unit.tenancy"]
		tenant.create({
			'partner_id':self.partner_id.id,
			'unit_id':unit.id,
			'tenant_code':self.partner_id.name, 
			'start_date':self.start_date, 
			'end_date':self.end_date,
			'invoice_service_charge_partner_id':self.partner_id.id,
			'invoice_sinking_fund_partner_id':self.partner_id.id, 
			'invoice_utility_partner_id':self.partner_id.id,
			'rent_order_ids':[(6,0,[self.id])],
			'tuition_schedule_date':self.tuition_schedule_date})
		print '--------------------', tenant['rent_order_ids']
		self.state = 'sale'
		print "===============================", unit.id, unit.name, 

	@api.onchange('start_date')
	@api.multi
	def compute_end_date(self):
		if self.start_date:
			self.end_date = (datetime.strptime(self.start_date,'%Y-%m-%d') + relativedelta(months=self.duration)).strftime('%Y-%m-%d')
			self.next_payment = datetime.strptime(self.start_date,'%Y-%m-%d').replace(day=self.tuition_schedule_date)

	@api.depends('order_line_ids.price_total')
	def _amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.order_line_ids:
				amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if order.company_id.tax_calculation_rounding_method == 'round_globally':
					price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
					taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			amount_untaxed*=self.duration
			amount_tax*=self.duration
			order.update({
				'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
				'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
				'amount_total': (amount_untaxed) + (amount_tax),
			})


class OfficeRentOrderLine(models.Model):
	_name = 'office.rent.order.line'
	_inherit = 'sale.order.line'
	_description = 'Office rent order line'

	order_id = fields.Many2one('office.rent.order', string='Order Reference')
	unit_id = fields.Many2one('office.rent.unit', string='Unit')

	@api.depends('price_unit', 'tax_id')
	def _compute_amount(self):
		"""
		Compute the amounts of the SO line.
		"""
		for line in self:
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})