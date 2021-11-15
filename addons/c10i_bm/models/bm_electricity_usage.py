from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ElectricityRate(models.Model):
    _name = 'bm.electricity.usage.rate'
    _description = 'BM Electricity Usage Rate'

    date = fields.Date(string='Date')
    product_id = fields.Many2one('product.product', string='Product')
    rate = fields.Float(string='Unsubsidized Rate')
    subsidized_rate = fields.Float('Subsidized Rate')
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
            raise ValidationError(_("Please input your Electricity Usage Rate."))
        return rates

class ElectricityUsage(models.Model):
    _name = 'bm.electricity.usage'
    _description = 'BM Electricity Usage'

    entry_id = fields.Many2one('bm.utility.entry', string="Entry Ref", ondelete='cascade')
    unit_id = fields.Many2one('bm.unit', string="Unit", required=True,)
    date_start = fields.Date(sting="Date Start", required=True)
    date_stop = fields.Date(string="Date Stop", required=True)
    meter_start = fields.Float(string="Prev. Reading", required=True)
    meter_stop = fields.Float(string="Current Reading", required=True)
    meter_factor = fields.Float(string="Meter Factor")
    load_voltage = fields.Float(string="Load Voltage (kVA)")
    saving_limit = fields.Float(string="Saving Limit")
    usage_meter = fields.Float(string="Usage", compute='_compute_usage', store=True)
    consumption_meter = fields.Float(string="Consumption (kWh)", compute='_compute_usage', store=True)
    subsidized_rate = fields.Float(string="Subsidized Rate")
    unsubsidized_rate = fields.Float(string="Unubsidized Rate")
    subsidized_meter = fields.Float(string="Subsidized (kWh)", compute='_compute_cost_amount', store=True)
    unsubsidized_meter = fields.Float(string="Unsubsidized (kWh)", compute='_compute_cost_amount', store=True)
    subsidized_cost = fields.Float(string="Subsidized Cost", compute='_compute_cost_amount', store=True)
    unsubsidized_cost = fields.Float(string="Unsubsidized Cost", compute='_compute_cost_amount', store=True)
    cost_amount = fields.Float(string="Cost Amount", compute='_compute_cost_amount', store=True)
    tax_amount = fields.Float(string="Tax Amount", compute='_compute_cost_amount', store=True)
    total_amount = fields.Float(string="Total Amount", compute='_compute_cost_amount', store=True)
    state = fields.Selection([('draft', 'Draft'),('computed', 'Computed'),('confirmed', 'Confirmed')], string="Status", default="draft")
    invoice_id = fields.Many2one('account.invoice', 'Vendor Bill')
    invoice_state = fields.Selection([('draft','Nothing to Bill'),('open', 'Open'),('invoiced', 'Invoiced'),('paid', 'Paid')], compute="_invoice_state", string="Billing Status", default="draft", store=True)
    initial_value = fields.Boolean('Initial Value')

    # ----------------------------------------
    # Helpers
    # ----------------------------------------
    @api.onchange('unit_id', 'initial_value', 'date_stop', 'meter_stop')
    def _onchange_unit(self):
        if self.unit_id:
            self.meter_factor = self.unit_id.electricity_factor
            self.load_voltage = self.unit_id.electricity_load_voltage
            self.saving_limit = self.unit_id.electricity_saving_limit
            last_usage = self.env['bm.electricity.usage'].search([('unit_id','=',self.unit_id.id)], order='date_stop desc', limit=1)
            if last_usage:
                self.date_start = (datetime.strptime(last_usage.date_stop, DF) + relativedelta(days=1)).strftime(DF)
                self.meter_start = last_usage.meter_stop
            elif self.initial_value:
                self.date_start = self.date_stop
                self.meter_start = self.meter_stop
            else:
                raise ValidationError(_("Please input your Electricity Initial Value before inputing current Usage."))
        else:
            self.date_start = False
            self.meter_start = 0.0

    @api.depends('unit_id', 'date_stop', 'meter_start', 'meter_factor')
    def _compute_usage(self):
        for usage in self:
            if usage.unit_id and usage.date_start and usage.meter_start and usage.meter_stop:
                if usage.meter_start > usage.meter_stop:
                    raise ValidationError(_("Meter Stop should always be greater than or equal to Meter Start"))
                usage_meter = usage.meter_stop - usage.meter_start
                usage.usage_meter = usage_meter
                usage.consumption_meter = usage_meter * usage.meter_factor
            else:
                usage.usage_meter = 0.0
                usage.consumption_meter = 0.0

    @api.depends('unit_id', 'subsidized_rate', 'unsubsidized_rate')
    def _compute_cost_amount(self):
        for usage in self:

            subsidized_meter = (usage.saving_limit * usage.load_voltage) / 1000.0
            unsubsidized_meter = (usage.consumption_meter - subsidized_meter) if (usage.consumption_meter > subsidized_meter) else 0.0
            subsidized_cost = (subsidized_meter * usage.subsidized_rate) if (unsubsidized_meter > subsidized_meter) else (usage.consumption_meter * usage.subsidized_rate)
            unsubsidized_cost = unsubsidized_meter * usage.unsubsidized_rate
            cost_amount = subsidized_cost + unsubsidized_cost
            tax_amount = cost_amount * 0.05
            
            usage.subsidized_meter = subsidized_meter
            usage.unsubsidized_meter = unsubsidized_meter
            usage.subsidized_cost = subsidized_cost
            usage.unsubsidized_cost = unsubsidized_cost
            usage.cost_amount = cost_amount
            usage.tax_amount = tax_amount
            usage.total_amount = cost_amount + tax_amount

    @api.depends('state', 'invoice_id', 'invoice_id.state')
    def _invoice_state(self):
        for usage in self:
            if usage.state=='confirmed':
                if usage.total_amount >0.0:
                    if usage.invoice_id:
                        if usage.invoice_id.state=='open':
                            usage.invoice_state='invoiced'
                        elif usage.invoice_id.state=='paid':
                            usage.invoice_state='paid'
                        else:
                            usage.invoice_state='open'
                    else:
                        usage.invoice_state='open'
                else:
                    usage.invoice_state='paid'

            else:
                usage.invoice_state = 'draft'

    # ----------------------------------------
    # Actions
    # ----------------------------------------
    @api.multi
    def allocate_price(self):
        for usage in self:
            rate = self.env['bm.electricity.usage.rate'].with_context(date=usage.date_start, product_id=usage.unit_id.electricity_cost_product_id.id).get_rate()
            if not rate:
                raise ValidationError(_("Please input your Electricity Usage Rate."))

            if not usage.meter_factor:
                usage.meter_factor = usage.unit_id.electricity_factor
                usage.load_voltage = usage.unit_id.electricity_load_voltage
                usage.saving_limit = usage.unit_id.electricity_saving_limit

            usage.subsidized_rate = rate.subsidized_rate
            usage.unsubsidized_rate = rate.rate
            usage.state = 'computed'
        return True

    @api.multi
    def confirm(self):
        invoiced = self.filtered(lambda x: x.invoice_state in ('invoiced','paid'))
        if invoiced:
            raise ValidationError(_("Some of these data already Invoiced"))
        drafts = self.filtered(lambda x: x.state=='draft').allocate_price()
        return self.write({'state': 'confirmed'})

    @api.multi
    def set_draft(self):
        invoiced = self.filtered(lambda x: x.invoice_state in ('invoiced','paid'))
        if invoiced:
            raise ValidationError(_("Some of these data already Invoiced"))
        return self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        valid = self.filtered(lambda x: x.state!='draft')
        if valid:
            raise ValidationError(_("Some of these data already Valid.\n \
                You can not delete data other than Draft State"))
        return super(ElectricityUsage, self).unlink()