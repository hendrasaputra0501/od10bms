import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
import urllib3
from lxml import etree
import time

class CPOOngkir(models.Model):
    _name = 'cpo.ongkir'

    name = fields.Date('Date', required=True)
    partner_id = fields.Many2one('weighbridge.partner', 'Relasi', required=True)
    price_unit = fields.Float(string='Price Unit', store=True)
    tujuan = fields.Char(string="Tujuan")

class InvoiceAngkutCPO(models.Model):
    _name = 'invoice.angkut.cpo'

    def _get_default_journal(self):
        domain = [('type','=','purchase')]
        res = self.env['account.journal'].search(domain, limit=1)
        return res and res[-1].id or False

    name = fields.Char(string='Number', default='/')
    date_start = fields.Date('Date Start', required=True, readonly=True, states={'draft': [('readonly',False)]})
    date_stop = fields.Date('Date Stop', required=True, readonly=True, states={'draft': [('readonly',False)]})
    partner_id = fields.Many2one('res.partner', string='Vendor')
    # relasi_id = fields.Many2one('weighbridge.partner', 'Relasi')
    invoice_ongkir_cpo_ids = fields.One2many('invoice.ongkir.line', 'invoice_id', string='Price List', readonly=True, states={'draft': [('readonly',False)],'price_allocation': [('readonly',False)]})
    invoice_line_ids = fields.One2many('invoice.angkut.cpo.line', 'invoice_id', string='Detail Invoice', readonly=True, states={'price_allocation': [('readonly',False)]})
    weighbridge_ids = fields.Many2many('weighbridge.scale.metro', 'invoice_cpo_weighbridge_rel', 'invoice_id', 'weighbridge_id', string='Selected Timbangan')
    state = fields.Selection([('draft','Draft'),('price_allocation','Quantity & Price Allocation'),('confirmed','Confirm'),('invoiced','Invoiced')], string='Status', default='draft')

    date_invoice = fields.Date('Invoice Date', readonly=True, states={'confirmed': [('readonly',False)]})
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'confirmed': [('readonly',False)]}, compute='get_product')
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True, states={'confirmed': [('readonly', False)]}, default=_get_default_journal)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'confirmed': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.id)
    invoice_ids = fields.Many2many('account.invoice', 'invoice_angkut_cpo_account_invoice_rel', 'invoice_angkut_cpo_id', 'invoice_id', string='Vendor Bills')
    invoice_count = fields.Integer(compute="_compute_invoice", string='# of Bills', copy=False, default=0)
    advance_ids = fields.Many2many('account.invoice.advance', 'invoice_angkut_cpo_account_invoice_advance_rel', 'invoice_angkut_cpo_id', 'invoice_id', string='Advance Bills')
    advance_count = fields.Integer(compute="_compute_invoice", string='# of Bills', copy=False, default=0)

    @api.multi
    def unlink(self):
        for inv in self:
            if inv.state!='draft':
                raise ValidationError(_("You cannot delete invoice which is not in DRAFT state!"))
        return super(InvoiceAngkutCPO, self).unlink()

    @api.depends('weighbridge_ids')
    def get_product(self):
        if self.weighbridge_ids:
            product = self.weighbridge_ids.mapped('product_id')
            self.product_id = product.id

    @api.depends('invoice_ids', 'advance_ids.state')
    def _compute_invoice(self):
        for inv in self:
            inv.invoice_count = len(inv.invoice_ids)
            inv.advance_count= len(inv.advance_ids)

    @api.multi
    def button_generate_pricelist(self):
        self.ensure_one()
        if self.date_start and self.date_stop:
            if self.invoice_ongkir_cpo_ids:
                for x in self.invoice_ongkir_cpo_ids:
                    x.unlink()
            domain = [('TIMBANG_OUT_DATE', '>=', self.date_start),
                      ('TIMBANG_OUT_DATE', '<=', self.date_stop),
                      ('TIMBANG_TIPETRANS','ilike','CPO'),
                      ('wb_partner_id','!=',False), ('state','=','done'),
                      ('invoiced','=',False),
                      ('transporter_id','=',self.partner_id.id)]

            weighbridges = self.env['weighbridge.scale.metro'].search(domain)
            if not weighbridges:
                return False
            print '=========================================', weighbridges
            self.weighbridge_ids = [(6,0,weighbridges.ids)]
            # partners = weighbridges.mapped('wb_partner_id.related_partner_id')
            partners = weighbridges.mapped('wb_partner_id')
            # new_partner = self.env['res.partner']
            new_partner = self.env['weighbridge.partner']
            pricelists = self.env['cpo.ongkir']
            for partner in partners:
                pl1 = self.env['cpo.ongkir'].search([('partner_id','=',partner.id),('name','<=',self.date_start)], order='name desc', limit=1)
                for x in pl1:
                    pricelists |= x
                pl2= self.env['cpo.ongkir'].search([('partner_id', '=', partner.id), \
                                    ('name', '>', self.date_start),('name', '<=', self.date_stop)])
                for x in pl2:
                    pricelists |= x
                if not pl1 and not pl2:
                    new_partner |= partner

            for price in sorted(pricelists, key=lambda x: x.partner_id.id):
                if price.name < self.date_start:
                    price_date = self.date_start
                else:
                    price_date = price.name
                self.env['invoice.ongkir.line'].with_context(skip_new_pricelist=True).create({
                    'invoice_id': self.id,
                    'name': price_date,
                    'partner_id': price.partner_id.id,
                    'price_unit': price.price_unit,
                    'tujuan'    : price.tujuan,
                })

            for npartner in new_partner:
                self.env['invoice.ongkir.line'].with_context(skip_new_pricelist=True).create({
                    'invoice_id': self.id,
                    'name': self.date_start,
                    'partner_id': npartner.id,
                    'price_unit': 0.0,
                })
            self.state = 'price_allocation'
            return True
        return False

    @api.multi
    def button_generate_lines(self):
        self.ensure_one()
        partner_grouped = {}
        for x in self.invoice_line_ids:
            x.unlink()

        for price in self.invoice_ongkir_cpo_ids:
            if price.partner_id.id not in partner_grouped.keys():
                partner_grouped.update({
                    price.partner_id.id: {}
                })
            if price.name not in partner_grouped[price.partner_id.id].keys():
                partner_grouped[price.partner_id.id].update({
                    price.name: {
                        'invoice_id': self.id,
                        'partner_id': price.partner_id.id,
                        'name': '-',
                        'date_from': price.name,
                        'date_to': price.name,
                        'qty_bruto': 0.0,'qty_sortasi': 0.0,'qty_netto': 0.0, 'quantity': 0.0,
                        'default_sortasi': 0.0,
                        'price_unit': price.price_unit,
                    }
                })

        wb_to_remove_from_invoice = []
        for wb in self.weighbridge_ids:
            if wb.wb_partner_id.id not in partner_grouped.keys():
                wb_to_remove_from_invoice.append(wb.id)
                continue
            found = False
            for gdate in sorted(partner_grouped[wb.wb_partner_id.id].keys(), reverse=True):
                if wb.TIMBANG_OUT_DATE >= gdate and not found:
                    partner_grouped[wb.wb_partner_id.id][gdate]['qty_bruto'] += wb.TIMBANG_BERATNETTO
                    pct_sortasi = partner_grouped[wb.wb_partner_id.id][gdate]['default_sortasi'] or 0.0
                    qty_sortasi = round(wb.TIMBANG_BERATNETTO*(pct_sortasi/100.0) if pct_sortasi else wb.TIMBANG_POTONGAN)
                    partner_grouped[wb.wb_partner_id.id][gdate]['qty_sortasi'] += qty_sortasi
                    qty_netto = (wb.TIMBANG_BERATNETTO-qty_sortasi) if pct_sortasi else wb.TIMBANG_TOTALBERAT
                    partner_grouped[wb.wb_partner_id.id][gdate]['qty_netto'] += qty_netto
                    partner_grouped[wb.wb_partner_id.id][gdate]['quantity'] += qty_netto
                    partner_grouped[wb.wb_partner_id.id][gdate]['date_from'] = min(wb.TIMBANG_OUT_DATE,partner_grouped[wb.wb_partner_id.id][gdate]['date_from'])
                    partner_grouped[wb.wb_partner_id.id][gdate]['date_to'] = max(wb.TIMBANG_OUT_DATE,partner_grouped[wb.wb_partner_id.id][gdate]['date_to'])
                    found = True
                else:
                    continue

        for partner_id in partner_grouped.keys():
            for lvalue in sorted(partner_grouped[partner_id].values(), key=lambda x: x['date_from']):
                date_from = datetime.strptime(lvalue['date_from'], '%Y-%m-%d').strftime('%d %b %y')
                date_to = datetime.strptime(lvalue['date_to'], '%Y-%m-%d').strftime('%d %b %y')
                if date_from != date_to:
                    lvalue['name'] = 'Timbang dari Tgl. %s s/d %s'%(date_from,date_to)
                else:
                    lvalue['name'] = 'Timbang Tgl. %s'%date_from
                self.env['invoice.angkut.cpo.line'].create(lvalue)

        if wb_to_remove_from_invoice:
            self.weighbridge_ids = list(map(lambda x: (3,x), wb_to_remove_from_invoice))
        return True

    @api.multi
    def button_confirm(self):
        self.state = 'confirmed'

    @api.multi
    def set_draft(self):
        self.state = 'draft'

    @api.multi
    def button_cancel(self):
        self.ensure_one()
        for inv in self.invoice_ids:
            if inv.state!='draft':
                raise ValidationError(_("You cannot delete invoice which is not in DRAFT state!"))
            elif inv.move_name:
                raise ValidationError(_("You cannot delete invoice which is already have a number"))
            else:
                inv.sudo().unlink()
        self.state = 'price_allocation'
        self.weighbridge_ids.write({'invoiced': False})

    @api.multi
    def update_ongkir(self):
        self.ensure_one()
        ongkir_cpo = self.env['cpo.ongkir']
        for line in self.invoice_ongkir_cpo_ids:
            current_ongkir = ongkir_cpo.search([('name', '<=', line.name), ('price_unit', '=', line.price_unit), ('partner_id', '=',line.partner_id.id), \
                                    ('tujuan', '=', line.tujuan)])
            if not current_ongkir:
                ongkir_cpo.sudo().create({
                    'partner_id': line.partner_id.id, 'name': line.name,
                    'price_unit': line.price_unit,
                    'tujuan': line.tujuan,
                })

    @api.multi
    def action_create_bills(self):
        self.ensure_one()
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        invoice_ids = []
        invoice_vals = {
            'type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'date_invoice': self.date_invoice,
            'journal_id': self.journal_id.id,
            'account_id': self.partner_id.property_account_payable_id.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
        }
        invoice = AccountInvoice.create(invoice_vals)
        transport_account = self.env['weighbridge.product'].search([('related_product_id', '=', self.product_id.id)]).transport_account_id
        # cost_account = AccountInvoiceLine.get_invoice_line_account('in_invoice', self.product_id, False, self.company_id)
        for line in self.invoice_line_ids:
            invoice_line_vals = {
                'invoice_id': invoice.id,
                'product_id': self.product_id.id,
                'account_location_type_id': self.env['account.location.type'].search(['|',('code','=','-'),('name','=','-')]).id,
                'account_id': transport_account.id,
                'uom_id': self.product_id.uom_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'invoice_line_tax_ids': self.partner_id.default_taxes_ids and [(6,0,self.partner_id.default_taxes_ids.ids)] or [],
                'name': line.name,
            }
            AccountInvoiceLine.create(invoice_line_vals)
        invoice.compute_taxes()
        invoice_ids.append(invoice.id)
        self.invoice_ids = [(6, 0 , invoice_ids)]
        self.state = 'invoiced'
        self.weighbridge_ids.write({'invoiced': True})

        self.update_ongkir()

        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice', 'default_journal_id': self.journal_id.id}
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        else:
            return False
        return result

    @api.multi
    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_invoice', 'default_purchase_id': self.id}

        if not self.invoice_ids:
            # Choose a default account journal in the same currency in case a new invoice is created
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = self.invoice_ids[0].journal_id.id

        # choose the view_mode accordingly
        if len(self.invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        elif len(self.invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.invoice_ids.id
        return result

    @api.multi
    def action_view_advance(self):
        action = self.env.ref('c10i_account_invoice_advance.action_invoice_advance_tree2')
        result = action.read()[0]
        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_advance'}
        if not self.advance_ids:
            # Choose a default account journal in the same currency in case a new invoice is created
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = self.advance_ids[0].journal_id.id

        # choose the view_mode accordingly
        if len(self.advance_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.advance_ids.ids) + ")]"
        elif len(self.advance_ids) == 1:
            res = self.env.ref('c10i_account_invoice_advance.invoice_advance_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.advance_ids.id
        return result

class InvoiceOngkirLine(models.Model):
    _name = 'invoice.ongkir.line'

    invoice_id = fields.Many2one('invoice.angkut.cpo', string='Invoice')
    name = fields.Date('Date', required=True)
    partner_id = fields.Many2one('weighbridge.partner', 'Relasi', required=True)
    # partner_id = fields.Many2one('res.partner', 'Vendor', required=True)
    price_unit = fields.Float(string='Price Unit', store=True)
    tujuan = fields.Char(string="Tujuan")

    def create(self, vals):
        return super(InvoiceOngkirLine, self).create(vals)

    @api.multi
    def write(self, update_vals):
        return super(InvoiceOngkirLine, self).write(update_vals)

class InvoiceAngkutCPOLine(models.Model):
    _name = 'invoice.angkut.cpo.line'

    invoice_id = fields.Many2one('invoice.angkut.cpo', string='Invoice Ref')
    # partner_id = fields.Many2one('res.partner', 'Vendor')
    partner_id = fields.Many2one('weighbridge.partner', 'Relasi')
    name = fields.Text(string='Description')
    qty_bruto = fields.Float('Bruto')
    qty_sortasi = fields.Float('Sortasi')
    qty_netto = fields.Float('Netto')
    quantity = fields.Float('Invoice Qty')
    price_unit = fields.Float(string='Price Unit') 
    price_subtotal = fields.Float(string='Subtotal', compute='_amount_line', store=True)

    @api.depends('quantity', 'price_unit')
    def _amount_line(self):
        for line in self:
            line.price_subtotal = self.price_unit * self.quantity