from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime

class KomparasiWizard(models.TransientModel):

	_name = 'komparasi.wizard'

	periode = fields.Selection([(num, str(num)) for num in range( ((datetime.datetime.now().year)-10), ((datetime.datetime.now().year)+1) )])

	@api.multi
	def komparasi_wizard_open_window(self):
		return self.env.ref('bms_account.action_komparasi_account_all').read()[0]
		