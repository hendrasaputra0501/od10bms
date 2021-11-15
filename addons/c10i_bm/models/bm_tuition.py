from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class TuitionRate(models.Model):
    _name = 'bm.tuition.rate'
    _description = 'BM Tuition Rate'

    date = fields.Date(string='Date')
    product_id = fields.Many2one('product.product', string='Product')
    rate = fields.Float(string='Rate')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    _rec_name = 'date'

    # ----------------------------------------
    # Function
    # ----------------------------------------
    @api.model
    def get_rate(self):
        ctx = self._context
        domain = [('product_id','=',ctx.get('product_id',False))]
        if ctx.get('date'):
            domain.append(('date','<=', ctx['date']))
        rates = self.search(domain, order='date desc', limit=1)
        if not rates:
            raise ValidationError(_("Please input your Service Charge Rate."))
        return rates

class Tuition(models.Model):
    _name = 'bm.tuition'
    _description = 'BM Tuition'

    unit_id = fields.Many2one('bm.unit', string="Unit", required=True,)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    date = fields.Date(sting="Date Start", required=True)
    amount = fields.Float(string="Amount")
    invoice_id = fields.Many2one('account.invoice', 'Vendor Bill')
    invoice_state = fields.Selection([('draft','Nothing to Bill'),('open', 'Open'),('invoiced', 'Invoiced'),('paid', 'Paid')], compute="_invoice_state", string="Billing Status", default="draft", store=True)

    # ----------------------------------------
    # Helpers
    # ----------------------------------------
    @api.depends('invoice_id', 'invoice_id.state')
    def _invoice_state(self):
        for tuition in self:
            if tuition.amount>0.0:
                if tuition.invoice_id:
                    if tuition.invoice_id.state=='open':
                        tuition.invoice_state='invoiced'
                    elif tuition.invoice_id.state=='paid':
                        tuition.invoice_state='paid'
                    else:
                        tuition.invoice_state='open'
                else:
                    tuition.invoice_state='open'
            else:
                tuition.invoice_state = 'draft'

    # ----------------------------------------
    # Actions
    # ----------------------------------------
    @api.multi
    def unlink(self):
        valid = self.filtered(lambda x: x.invoice_id)
        if valid:
            raise ValidationError(_("Some of these data already Invoiced.\n \
                Please delete its Invoice before deleting this data"))
        return super(ServiceChargeTuition, self).unlink()