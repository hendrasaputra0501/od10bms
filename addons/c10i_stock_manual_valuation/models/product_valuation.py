# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
import time

class ProductValuation(models.Model):
    _name = 'product.valuation'
    _description = "Product Manual Periodic Valuation"
    _inherit = ['mail.thread']

    name = fields.Char('No', default='New Valuation', readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_stop = fields.Date('End Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Valuation Journal', domain="[('type','=','general')]", required=True, states={'draft': [('readonly', False)]})
    product_id = fields.Many2one('product.product', 'Product', domain="[('categ_id.property_valuation','=','manual_periodic')]", required=True, readonly=True, states={'draft': [('readonly', False)]})
    product_cost_account_ids = fields.Many2many('account.account', 'product_value_account_rel', 'product_valuation_id', 'account_id', string='Product Cost Account', readonly=False)
    move_ids = fields.Many2many('account.move', string='Journal Entries')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Posted')], string='Status', default='draft', index=True)

    opening_qty = fields.Float('Opening Qty', digits=dp.get_precision('Product Unit of Measure'))
    opening_value = fields.Float('Opening Value', digits=dp.get_precision('Account'))
    opening_account_move_ids = fields.Many2many('account.move.line', 'product_value_op_acc_move_line_rel',
                                    'product_valuation_id', 'move_line_id', string='Opening Journal Items')

    purchase_qty = fields.Float('Purchase Qty', digits=dp.get_precision('Product Unit of Measure'))
    purchase_value = fields.Float('Purchase Value', digits=dp.get_precision('Account'))
    purchase_account_move_ids = fields.Many2many('account.move.line', 'product_value_purch_acc_move_line_rel',
                                                 'product_valuation_id', 'move_line_id', string='Purchase Journal Items')

    cost_account_move_ids = fields.Many2many('account.move.line', 'product_value_cost_acc_move_line_rel',
                                             'product_valuation_id', 'move_line_id', string='Cost Journal Items')
    other_cost_value = fields.Float('Other Cost Value', digits=dp.get_precision('Account'))

    onhand_qty = fields.Float('Onhand Qty', digits=dp.get_precision('Product Unit of Measure'))
    onhand_value = fields.Float('Onhand Value', digits=dp.get_precision('Account'))
    average_cost_price = fields.Float('Avg. Cost Price', digits=(0, 0))

    sale_qty = fields.Float('Sale Qty (Invoiced)', digits=dp.get_precision('Product Unit of Measure'))
    sale_price = fields.Float('Avg. Sale Price', digits=(0, 0))
    sale_account_move_ids = fields.Many2many('account.move.line', 'product_value_sale_acc_move_line_rel',
                                             'product_valuation_id', 'move_line_id', string='Sales Journal Items')
    sale_value = fields.Float('Sale Value', digits=dp.get_precision('Account'))
    cogs_value = fields.Float('Cost of Goods Sales', digits=dp.get_precision('Account'))

    delivery_intransit_qty = fields.Float('Delivery Intransit (To be Invoice)',
                                          digits=dp.get_precision('Product Unit of Measure'))
    delivery_intransit_value = fields.Float('Delivery Intransit Value', digits=dp.get_precision('Account'))
    delivery_intransit_move_ids = fields.Many2many('stock.move', 'product_value_delivery_intransit',
                                                   'product_valuation', 'stock_move_id',
                                                   string='Delivery Intransit Moves')

    closing_qty = fields.Float('Closing Qty', digits=dp.get_precision('Product Unit of Measure'))
    closing_value = fields.Float('Closing Value', digits=dp.get_precision('Account'))

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.name = 'Valuation %s'%self.product_id.name
        else:
            self.name = 'New Valuation'

        if self.product_id and self.product_id.categ_id.property_stock_journal:
            self.journal_id = self.product_id.categ_id.property_stock_journal.id
        else:
            self.journal_id = False

        if self.product_id and self.product_id.cost_account_ids:
            self.product_cost_account_ids = [(6,0,self.product_id.cost_account_ids.ids)]
        elif self.product_id and self.product_id.categ_id.cost_account_categ_ids:
            self.product_cost_account_ids = [(6, 0, self.product_id.categ_id.cost_account_categ_ids.ids)]
        else:
            self.product_cost_account_ids = []

    @api.model
    def create(self, vals):
        if 'product_cost_account_ids' in vals.keys():
            to_be_added = []
            for item in vals['product_cost_account_ids']:
                if item[0] == 1:
                    to_be_added.append(item[1])
                elif item[0] == 6:
                    to_be_added.extend(item[2])
            if to_be_added:
                vals['product_cost_account_ids'] = [(6, 0, to_be_added)]
        return super(ProductValuation, self).create(vals)

    @api.multi
    def write(self, update_vals):
        for valuation in self:
            if 'product_cost_account_ids' in update_vals.keys():
                to_be_added = []
                for item in update_vals['product_cost_account_ids']:
                    if item[0] == 1:
                        to_be_added.append(item[1])
                    elif item[0] == 6:
                        to_be_added.extend(item[2])
                if to_be_added:
                    update_vals['product_cost_account_ids'] = [(6, 0, to_be_added)]
        return super(ProductValuation, self).write(update_vals)

    @api.multi
    def compute_product_value(self):
        self.ensure_one()
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
        MoveLine = self.env['stock.move']

        update_vals = {}
        date_start = datetime.strptime(self.date_start, DF).strftime('%Y-%m-%d 00:00:00')
        date_stop = datetime.strptime(self.date_stop, DF).strftime('%Y-%m-%d 23:59:59')
        default_domain = [('date','>=',self.date_start),('date','<=',self.date_stop)]
        product = self.product_id

        # 1. Select Opening Balance, both Qty and Value
        domain1 = default_domain[:]
        opening_account = product.property_stock_account_output or product.categ_id.property_stock_account_output_categ_id
        if not opening_account:
            raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product'))
        domain1.extend([('account_id','=',opening_account.id),
            ('product_id','=',product.id)])
        move_opening_bal = AccountMoveLine.search(domain1, limit=1)
        opening_qty = opening_value = 0.0
        if move_opening_bal:
            opening_qty = move_opening_bal.quantity
            opening_value = move_opening_bal.debit - move_opening_bal.credit
            if product.uom_id.id!=move_opening_bal.product_uom_id.id:
                opening_qty = move_opening_bal.product_uom_id._compute_quantity(opening_qty, product.uom_id)

        # 2. Select Purchase Movement, both Qty and Value
        purchase_qty = purchase_value = 0.0
        domain2 = default_domain[:]
        purchase_account = product.purchase_account_id or product.categ_id.purchase_account_categ_id
        if not purchase_account:
            raise ValidationError(_('Purchase Account not Found. Please define it in Product Category or Product'))
        domain2.extend([('account_id','=',purchase_account.id),
            ('product_id','=',product.id),('stock_move_id','!=',False)])
        move_purchase = AccountMoveLine.search(domain2)
        if move_purchase:
            for x in move_purchase:
                sign = -1 if (x.debit - x.credit)<0 else 1
                purchase_value += (x.debit - x.credit)
                if x.product_uom_id and product.uom_id.id!=x.product_uom_id.id:
                    purchase_qty += sign * x.product_uom_id._compute_quantity(x.quantity, product.uom_id)
                else:
                    purchase_qty += sign * x.quantity

        # 3. Select Other Cost
        domain3 = default_domain[:]
        cost_accounts = product.cost_account_ids or product.categ_id.cost_account_categ_ids
        cost_account_locations = product.cost_location_ids or product.categ_id.cost_location_categ_ids
        if cost_accounts and cost_account_locations:
            domain3.extend(['|',('account_id','in',cost_accounts.ids),
                ('account_location_id','in',cost_account_locations.ids)])
            move_other_cost = AccountMoveLine.search(domain3)
        elif cost_accounts:
            domain3.append(('account_id','in',cost_accounts.ids))
            move_other_cost = AccountMoveLine.search(domain3)
        elif cost_account_locations:
            domain3.append(('account_location_id','in',cost_account_locations.ids))
            move_other_cost = AccountMoveLine.search(domain3)
        else:
            move_other_cost = []
        other_cost_amount = move_other_cost and sum(move_other_cost.mapped('balance')) or 0.0

        # 4. Compute Average Price of all available product
        qty_available = opening_qty + purchase_qty
        value_available = opening_value + purchase_value + other_cost_amount
        avg_price = qty_available!=0.0 and value_available/qty_available or 0.0

        # 5. Select Sale Product
        avg_sale_price = qty_sale = value_sale = 0.0
        domain_sale = default_domain[:]
        sales_account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
        if not sales_account:
            raise ValidationError(_('Stock Income Account not Found. Please define it in Product Category or Product'))
        domain_sale.extend([('product_id','=',product.id),
            ('account_id','=',sales_account.id)])
        move_sales = AccountMoveLine.search(domain_sale)
        if move_sales:
            for x in move_sales:
                sign = -1 if (x.debit - x.credit) > 0 else 1
                value_sale += -1 * (x.debit - x.credit)
                if x.product_uom_id and product.uom_id.id != x.product_uom_id.id:
                    qty_sale += sign * x.product_uom_id._compute_quantity(x.quantity, product.uom_id)
                else:
                    qty_sale += sign * x.quantity
        avg_sale_price = abs(qty_sale and value_sale/qty_sale or 0.0)
        cogs_value = qty_sale * avg_price

        # 6. Compute Stock Intransit Qty
        stock_intransit_qty = 0.0
        intransit_moves = MoveLine.search([('product_id', '=', product.id), ('location_id.usage', '=', 'internal'),
                                           ('location_dest_id.usage', '=', 'customer'), ('state', '=', 'done'),
                                           '|', ('invoice_line_id', '=', False),
                                           ('invoice_line_id.invoice_id.date_invoice', '>', self.date_stop),
                                           ('date', '<=', date_stop)])
        if intransit_moves:
            for x in intransit_moves:
                if product.uom_id.id != x.product_uom.id:
                    stock_intransit_qty += x.product_uom._compute_quantity(x.product_uom_qty, product.uom_id)
                else:
                    stock_intransit_qty += x.product_uom_qty
        else:
            stock_intransit_qty = 0.0
        stock_intransit_value = stock_intransit_qty * avg_price

        # 7. Compute Closing Balance
        qty_closing = qty_available - qty_sale - stock_intransit_qty
        value_closing = qty_closing * avg_price

        self.write({
            'opening_qty': opening_qty,
            'opening_value': opening_value,
            'opening_account_move_ids': move_opening_bal and [(6,0,move_opening_bal.ids)] or [],
            'purchase_qty': purchase_qty,
            'purchase_account_move_ids': move_purchase and [(6,0,move_purchase.ids)] or [],
            'purchase_value': purchase_value,
            'cost_account_move_ids': move_other_cost and [(6,0,move_other_cost.ids)] or [],
            'other_cost_value': other_cost_amount,
            'sale_qty': qty_sale,
            'sale_value': value_sale,
            'sale_price': avg_sale_price,
            'cogs_value': cogs_value,
            'sale_account_move_ids': move_sales and [(6,0,move_sales.ids)] or [],
            'onhand_qty': qty_available,
            'onhand_value': value_available,
            'average_cost_price': avg_price,
            'delivery_intransit_qty': stock_intransit_qty,
            'delivery_intransit_value': stock_intransit_value,
            'delivery_intransit_move_ids': intransit_moves and [(6,0,intransit_moves.ids)] or [],
            'closing_qty': qty_closing,
            'closing_value': value_closing,
        })

        # 8. Create Closing Entry at the end of the date
        valuation_account = product.categ_id.property_stock_valuation_account_id
        if not valuation_account:
            raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category'))
        intransit_account = product.intransit_account_id or product.categ_id.intransit_account_categ_id
        if stock_intransit_qty and not intransit_account:
            raise ValidationError(
                _('Stock Intransit Account not Found. Please define it in Product Category or Product'))
        input_account = product.categ_id.stock_counterpart_valuation_account_categ_id
        if not input_account:
            raise ValidationError(_('Counterpart Valuation Account not Found. Please define it in Product Category or Product'))
        closing_move = AccountMove.create({
            'date': self.date_stop,
            'journal_id': self.journal_id.id,
            })
        move_line_dict = {
            'date': self.date_stop,
            'journal_id': self.journal_id.id,
            'name': 'Valuation %s'%product.name,
            'account_id': valuation_account.id,
            'product_id': product.id,
            'debit': value_closing, 
            'credit': 0.0,
            'price_unit': avg_price,
            'quantity': qty_closing,
            'move_id': closing_move.id
        }
        AccountMoveLine.create(move_line_dict)

        ct_move_line_dict = move_line_dict.copy()
        ct_move_line_dict['debit'] = 0.0
        ct_move_line_dict['credit'] = value_closing + stock_intransit_value
        ct_move_line_dict['quantity'] = qty_closing + stock_intransit_qty
        ct_move_line_dict['account_id'] = input_account.id
        AccountMoveLine.create(ct_move_line_dict)

        if stock_intransit_qty:
            int_move_line_dict = move_line_dict.copy()
            int_move_line_dict['debit'] = stock_intransit_value
            int_move_line_dict['quantity'] = stock_intransit_qty
            int_move_line_dict['account_id'] = intransit_account.id
            AccountMoveLine.create(int_move_line_dict)

        # 9. Create Reclass Closing Entry at the begining of the next period
        opening_move = AccountMove.create({
            'date': (datetime.strptime(self.date_stop, DF) + \
                    relativedelta(days=+1)).strftime(DF),
            'journal_id': self.journal_id.id,
            })
        move_line_dict = {
            'date': (datetime.strptime(self.date_stop, DF) + \
                    relativedelta(days=+1)).strftime(DF),
            'journal_id': self.journal_id.id,
            'name': 'Reclass Valua Closing as Opening',
            'account_id': opening_account.id,
            'product_id': product.id,
            'debit': value_closing + stock_intransit_value,
            'credit': 0.0,
            'price_unit': avg_price,
            'quantity': qty_closing + stock_intransit_qty,
            'move_id': opening_move.id
        }
        AccountMoveLine.create(move_line_dict)

        ct_move_line_dict = move_line_dict.copy()
        ct_move_line_dict['debit'] = 0.0
        ct_move_line_dict['credit'] = value_closing
        ct_move_line_dict['quantity'] = qty_closing
        ct_move_line_dict['account_id'] = valuation_account.id
        AccountMoveLine.create(ct_move_line_dict)

        if stock_intransit_qty:
            int_move_line_dict = move_line_dict.copy()
            int_move_line_dict['debit'] = 0.0
            int_move_line_dict['credit'] = stock_intransit_value
            int_move_line_dict['quantity'] = stock_intransit_qty
            int_move_line_dict['account_id'] = intransit_account.id
            AccountMoveLine.create(int_move_line_dict)

        self.move_ids = [(4,closing_move.id),(4,opening_move.id)]
        return (value_available - value_closing)

    @api.multi
    def post(self):
        for valuation in self:
            valuation.compute_product_value()
            valuation.state = 'done'
        return True

    @api.multi
    def cancel(self):
        for valuation in self:
            for move in valuation.move_ids:
                move.unlink()
            valuation.state = 'draft'