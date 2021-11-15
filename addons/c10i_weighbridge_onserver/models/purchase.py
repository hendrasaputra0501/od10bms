from odoo import models, fields, api
import time

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	sync_to_weighbridge_server = fields.Boolean('Sync to Weighbridge Server')
	synced_weighbridge_server_ids = fields.One2many('purchase.order.weighbridge.server', 'order_id', 'Synced Weighbridge Server')

	@api.model
	def get_order_to_be_sync(self, server_key):
		if not server_key:
			return {}
		results = self.search([('sync_to_weighbridge_server','=',True)])
		res = {
			'sync_time': time.strftime('%Y-%m-%d %H:%M:%S'),
			'call_result': []
		}
		for order in results:
			if not order.synced_weighbridge_server_ids or \
					server_key not in order.mapped('synced_weighbridge_server_ids.name'):
				order_lines = []
				for line in order.order_line:
					if line.product_id.sync_to_weighbridge_server:
						order_lines.append({
								'odoo_product_id': line.product_id.id,
								'product_name': line.product_id.name,
								'product_code': line.product_id.default_code,
								'quantity': line.product_uom_qty,
							})
				if not order_lines:
					continue
				res['call_result'].append({
						'odoo_order_id': order.id,
						'order_number': order.name,
						'order_type': 'purchase',
						'order_line': order_lines,
					})
		return res

	@api.model
	def update_synced_order(self, server_key, synced_order_ids):
		for pid in synced_order_ids:
			self.env['purchase.order.weighbridge.server'].create({
					'order_id': pid,
					'name': server_key,
					'synced': True,
				})
		return True


class purchaseOrderWeighbridgeServer(models.Model):
	_name = 'purchase.order.weighbridge.server'

	name = fields.Char('Server Key', required=True)
	order_id = fields.Many2one('purchase.order', 'Order Ref', required=True, ondelete='cascade')
	synced = fields.Boolean('Synced', default=False)