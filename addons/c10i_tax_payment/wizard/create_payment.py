import time
import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import odoo.addons.decimal_precision as dp

class CreatePayment(models.Model):
    _name = 'create.payment'
    _description = "Create Payment"

    journal_id = fields.Many2one('account.journal', 'Payment Journal', domain="[('type','in',['cash','bank'])]", required=True)
    payment_date = fields.Date('Payment Date', required=True)
    tax_amount_total = fields.Float('Return Amount', digits=dp.get_precision('Account'))

    @api.model
    def default_get(self, fields):
        tax_datas = self.env['tax.payment'].browse(self._context.get('active_id'))
        result = super(CreatePayment, self).default_get(fields)
        if tax_datas:
            if 'tax_amount_total' in fields:
                result['tax_amount_total'] = tax_datas[-1].amount_to_pay
        return result

    @api.multi
    def create_payment(self):
        self.ensure_one()
        payment_datas = self.env['tax.payment'].browse(self._context.get('active_id'))
        voucher_id = payment_datas.action_create_payment(self.payment_date, self.journal_id.id)