# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    tax_payment_id = fields.Many2one('tax.payment', 'Tax Payment Reference')

    @api.multi
    def action_move_line_create(self):
    	res = super(AccountVoucher, self).action_move_line_create()
        for voucher in self:
        	if voucher.move_id and voucher.tax_payment_id:
        		for line in voucher.move_id.line_ids:
        			line.tax_payment_id = voucher.tax_payment_id.id
        			line.tax_payment = True
        return res
