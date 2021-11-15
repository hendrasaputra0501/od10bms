# -*- coding: utf-8 -*-

from odoo import models, fields, api
import time

class weighbridge_ticket(models.Model):
	_name = 'weighbridge.ticket'
	_description = 'Weighbridge Ticket'

	server_key = fields.Char('Source Server', required=True, readonly=True)
	name = fields.Char('Ticket No.', required=True, readonly=True)
	vehicle_number = fields.Char('Vehicle No.', readonly=True)
	driver_name = fields.Char('Driver', readonly=True)
	transporter_id = fields.Many2one('res.partner', 'Transportir')

	type = fields.Selection([('sale','Sale'),('purchase','Purchase'),('internal_in','Internal In'),('internal_out','Internal Out')], string='Type')
	sale_order_id = fields.Many2one('sale.order', 'Sale Order Ref', readonly=True)
	sale_line_id = fields.Many2one('sale.order.line', 'Sale Line Ref', readonly=True)
	purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order Ref', readonly=True)
	purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Line Ref', readonly=True)
	order_name = fields.Char(compute='_get_order_info', string='Order', store=True)
	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
	product_id = fields.Many2one('product.product', 'Product', readonly=True)

	weight_in = fields.Float('Weight In', readonly=True)
	date_in = fields.Datetime('Date in', readonly=True)
	weight_out = fields.Float('Weight Out', readonly=True)
	date_out = fields.Datetime('Date Out', readonly=True)

	weight_netto = fields.Float('Netto Weight', readonly=True)
	weight_sorted = fields.Float('Sorted Weight', readonly=True)
	weight_total = fields.Float('Total Weight', readonly=True)

	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, readonly=True)
	picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True)
	state = fields.Selection([('to_create','To be Created'),('to_update','To be Updated'),('to_delete', 'to be Deleted'),('done','Synced')], string='Status', default='to_create')

	_sql_constraints = [
        ('ticket_number', 'unique(name,server_key,company_id)', 'Tiket Timbang already Exist')
    ]

	@api.depends('type', 'sale_order_id', 'purchase_order_id')
	def _get_order_info(self):
		for ticket in self:
			if ticket.type=='sale' and ticket.sale_order_id:
				self.order_name = ticket.sale_order_id.name
			elif ticket.type=='purchase' and ticket.purchase_order_id:
				self.order_name = ticket.purchase_order_id.name

	@api.model
	def post_weighbridge_ticket(self, values):
		res = {'call_result': []}
		for ticket_values in values.get('data',[]):
			ticket = self.create(ticket_values)
			res['call_result'].append((ticket_values['data_id'], ticket.id))
		res.update({
			'result_time': time.strftime('%Y-%m-%d %H:%M:%S')
			})
		return res
	
	# @api.multi
	# def action_validate(self):
	#   for ticket in self: