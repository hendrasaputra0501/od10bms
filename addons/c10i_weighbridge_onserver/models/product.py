from odoo import models, fields, api
import time

class Product(models.Model):
	_inherit = 'product.product'

	sync_to_weighbridge_server = fields.Boolean('Sync to Weighbridge Server')
	synced_weighbridge_server_ids = fields.One2many('product.weighbridge.server', 'product_id', 'Synced Weighbridge Server')

	@api.model
	def get_product_to_be_sync(self, server_key):
		if not server_key:
			return {}
		results = self.search([('sync_to_weighbridge_server','=',True)])
		res = {
			'sync_time': time.strftime('%Y-%m-%d %H:%M:%S'),
			'call_result': []
		}
		for product in results:
			if not product.synced_weighbridge_server_ids or \
					server_key not in product.mapped('synced_weighbridge_server_ids.name'):
				res['call_result'].append({
						'odoo_product_id': product.id,
						'product_name': product.name,
						'product_code': product.default_code,
					})
		return res

	@api.model
	def update_synced_product(self, server_key, synced_product_ids):
		for pid in synced_product_ids:
			self.env['product.weighbridge.server'].create({
					'product_id': pid,
					'name': server_key,
					'synced': True,
				})
		return True


class ProductWeighbridgeServer(models.Model):
	_name = 'product.weighbridge.server'

	name = fields.Char('Server Key', required=True)
	product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='cascade')
	synced = fields.Boolean('Synced', default=False)