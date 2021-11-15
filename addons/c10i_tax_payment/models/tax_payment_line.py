from odoo import models, fields, api

class TaxPaymentLine(models.Model):
    _name = 'tax.payment.line'

    tax_payment_id = fields.Many2one('tax.payment', string='Tax Payment')
    name = fields.Char(string='Name')
    account_id = fields.Many2one('account.account', string='Account')
    amount = fields.Float(string='Amount')

    @api.multi
    def _prepare_voucher_line(self, voucher_id):
        self.ensure_one()
        default_type = self.env['account.location.type'].search(['|',('name','=','-'),('name','=','NA')])
        res = {
            'voucher_id': voucher_id,
            'name': self.name,
            'account_id': self.account_id.id,
            'price_unit': self.amount,
            'account_location_type_id': default_type and default_type.id or False,
        }
        return res