from odoo import models, fields, api
import time

class Partner(models.Model):
	_inherit = 'res.partner'

	sync_to_weighbridge_server = fields.Boolean('Sync to Weighbridge Server')
	synced_weighbridge_server_ids = fields.One2many('partner.weighbridge.server', 'partner_id', 'Synced Weighbridge Server')

	@api.model
	def get_partner_to_be_sync(self, server_key):
		if not server_key:
			return {}
		results = self.search([('sync_to_weighbridge_server','=',True)])
		res = {
			'sync_time': time.strftime('%Y-%m-%d %H:%M:%S'),
			'call_result': []
		}
		for partner in results:
			if not partner.synced_weighbridge_server_ids or \
					server_key not in partner.mapped('synced_weighbridge_server_ids.name'):
				res['call_result'].append({
						'odoo_partner_id': partner.id,
						'partner_name': partner.name,
						'partner_code': partner.ref,
					})
		return res

	@api.model
	def update_synced_partner(self, server_key, synced_partner_ids):
		for pid in synced_partner_ids:
			self.env['partner.weighbridge.server'].create({
					'partner_id': pid,
					'name': server_key,
					'synced': True,
				})
		return True


class PartnerWeighbridgeServer(models.Model):
	_name = 'partner.weighbridge.server'

	name = fields.Char('Server Key', required=True)
	partner_id = fields.Many2one('res.partner', 'Partner', required=True, ondelete='cascade')
	synced = fields.Boolean('Synced', default=False)