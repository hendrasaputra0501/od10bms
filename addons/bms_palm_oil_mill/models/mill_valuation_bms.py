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


class MillValuationBMS(models.Model):
    _name = 'mill.valuation.bms'

    @api.model
    def _get_last_valuation(self):
        last_valuation = self.search([('id','>',0),('state','=','posted')], order="date_stop desc", limit=1)
        if last_valuation:
            date_start = datetime.strptime(last_valuation.date_stop, DF) + relativedelta(days=+1)
            return date_start.strftime(DF)
        else:
            return (datetime.now() + relativedelta(month=1, day=1)).strftime(DF)

    name = fields.Char('No', default='New Valuation', readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_get_last_valuation)
    date_stop = fields.Date('As of Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: datetime.now().strftime(DF))
    total_production_hours = fields.Float('Total Production Hours', readonly=True, states={'draft': [('readonly', False)]})
    valuation_categ_id = fields.Many2one('mill.valuation.category', 'Category', required=True, readonly=True, states={'draft': [('readonly', False)]})
    bom_id = fields.Many2one('mrp.bom', related='valuation_categ_id.bom_id', string='Bill of Material', required=True, readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Journal', domain="[('type','=','general')]", required=True, readonly=True, states={'draft': [('readonly', False)]})
    production_cost_account_ids = fields.Many2many('account.account', string='Production Cost Account', readonly=False, states={'draft': [('readonly', False)]})
    # production_cost_location_ids = fields.Many2many('account.location', string='Production Cost Account Location', readonly=False, states={'draft': [('readonly', False)]})
    @api.onchange('valuation_categ_id')
    def onchange_product(self):
        if self.valuation_categ_id:
            self.name = 'Valuation %s'%self.valuation_categ_id.name
        else:
            self.name = 'New Valuation'

        if self.valuation_categ_id and self.valuation_categ_id.journal_id:
            self.journal_id = self.valuation_categ_id.journal_id.id
        else:
            self.journal_id = False

        if self.valuation_categ_id.production_cost_account_ids:
            # self.production_cost_account_ids = map(lambda x: (4, x.id), self.valuation_categ_id.production_cost_account_ids)
            self.production_cost_account_ids = [(6,0,self.valuation_categ_id.production_cost_account_ids.ids)]
        else:
            self.production_cost_account_ids = []

    initial_value = fields.Boolean('Initial Value', states={'draft': [('readonly',False)]}, readonly=True)
    move_ids = fields.Many2many('account.move', string='Valuation Journal Entries')
    state = fields.Selection([('draft', 'Draft'),
        ('compute1', 'TBS - CPO - Kernel'),
        ('compute2', 'Manufacturing Cost'),
        ('compute3', 'Finish Goods'),
        ('posted', 'Posted')], string='Status', default='draft', index=True)
    # TBS
    tbs_initial_qty = fields.Float('TBS Initial Qty', digits=dp.get_precision('Product Unit of Measure'), states={'draft': [('readonly',False)]}, readonly=True)
    tbs_initial_value = fields.Float('TBS Initial Value', digits=dp.get_precision('Account'), states={'draft': [('readonly',False)]}, readonly=True)
    tbs_opening_qty = fields.Float('TBS Opening Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_opening_value = fields.Float('TBS Opening Value', digits=dp.get_precision('Account'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_purchase_qty = fields.Float('TBS Purchase Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_purchase_value = fields.Float('TBS Purchase Value', digits=dp.get_precision('Account'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_ptpn_purchase_qty = fields.Float('TBS PTPN Incoming Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_onhand_qty = fields.Float('TBS Onhand Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_closing', store=True)
    tbs_onhand_value = fields.Float('TBS Onhand Value', digits=dp.get_precision('Account'), compute='compute_closing', store=True)
    tbs_average_cost_price = fields.Float('TBS Avg. Cost Price', digits=(0,0), compute='compute_closing', store=True)
    tbs_consume_qty = fields.Float('Consume Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_consume_value = fields.Float('Consume Value', digits=dp.get_precision('Account'), compute='compute_closing', store=True)
    tbs_consume_hour_proportion = fields.Float('Consume Proportion', digits=dp.get_precision('Account'), compute='compute_closing', store=True)
    tbs_ptpn_consume_qty = fields.Float('Consume Qty (PTPN)', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_ptpn_consume_hour_proportion = fields.Float('Consume Proportion (PTPN)', digits=dp.get_precision('Account'), compute='compute_closing', store=True)
    tbs_closing_qty = fields.Float('Closing Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_closing', store=True)
    tbs_closing_value = fields.Float('Closing Value', digits=dp.get_precision('Account'), compute='compute_closing', store=True)
    tbs_opname_qty = fields.Float('Consume Qty (PTPN)', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    
    @api.depends('total_production_hours', 'tbs_opening_qty', 'tbs_opening_value', 'tbs_purchase_qty', \
        'tbs_purchase_value', 'tbs_consume_qty', 'tbs_ptpn_consume_qty',
        'tbs_initial_qty', 'tbs_initial_value', 'initial_value')
    def compute_closing(self):
        for hpp in self:
            onhand_qty = (hpp.tbs_initial_qty if hpp.initial_value else hpp.tbs_opening_qty) + hpp.tbs_purchase_qty
            onhand_value = (hpp.tbs_initial_value if hpp.initial_value else hpp.tbs_opening_value) + hpp.tbs_purchase_value
            hpp.tbs_onhand_qty = onhand_qty
            hpp.tbs_onhand_value = onhand_value
            average_cost_price = onhand_value/onhand_qty if onhand_qty else 0.0
            hpp.tbs_average_cost_price = average_cost_price

            consume_value = hpp.tbs_consume_qty * average_cost_price
            hpp.tbs_consume_value = consume_value
            total_consume = hpp.tbs_consume_qty + hpp.tbs_ptpn_consume_qty
            hpp.tbs_consume_hour_proportion = (hpp.tbs_consume_qty/total_consume)*hpp.total_production_hours if total_consume else 0.0
            hpp.tbs_ptpn_consume_hour_proportion = (hpp.tbs_ptpn_consume_qty/total_consume)*hpp.total_production_hours if total_consume else 0.0

            closing_qty = onhand_qty - hpp.tbs_consume_qty
            closing_value = onhand_value - consume_value
            hpp.tbs_closing_qty = closing_qty
            hpp.tbs_closing_value = closing_value

    tbs_total_cpo_produce_qty = fields.Float('TBS - CPO Total Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_total_cpo_tbs_pct = fields.Float('% CPO Produce', digits=dp.get_precision('Account'), compute='compute_tbs_pct_produce', store=True)
    tbs_total_kernel_produce_qty = fields.Float('TBS - Kernel Total Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_total_kernel_tbs_pct = fields.Float('% Kernel Produce', digits=dp.get_precision('Account'), compute='compute_tbs_pct_produce', store=True)
    tbs_total_shell_produce_qty = fields.Float('TBS - Cangkang Total Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_total_shell_tbs_pct = fields.Float('% Cangkang Produce', digits=dp.get_precision('Account'), compute='compute_tbs_pct_produce', store=True)
    tbs_total_prod_tbs_pct = fields.Float('Direct Material Used', digits=dp.get_precision('Account'), compute='compute_tbs_pct_produce', store=True)

    tbs_ptpn_pct_cpo_produce_qty = fields.Float('TBS PTPN - CPO Produce Qty from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_ptpn_pct_kernel_produce_qty = fields.Float('TBS PTPN - Kernel Produce Qty from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_ptpn_pct_shell_produce_qty = fields.Float('TBS PTPN - Cangkang Produce Qty from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)

    tbs_ptpn_actual_cpo_produce_qty = fields.Float('TBS PTPN - Actual CPO Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_ptpn_actual_kernel_produce_qty = fields.Float('TBS PTPN - Actual Kernel Produce', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)
    tbs_ptpn_actual_shell_produce_qty = fields.Float('TBS PTPN - Actual Cangkang Produce', digits=dp.get_precision('Product Unit of Measure'), states={'compute1': [('readonly',False)]}, readonly=True)

    tbs_ptpn_cpo_produce_qty_bonus = fields.Float('TBS PTPN - Bonus CPO Produce Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_ptpn_kernel_produce_qty_bonus = fields.Float('TBS PTPN - Bonus Kernel Produce Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_ptpn_shell_produce_qty_bonus = fields.Float('TBS PTPN - Bonus Cangkang Produce Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    
    tbs_pct_cpo_produce_qty = fields.Float('TBS - CPO Produce Qty from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_pct_kernel_produce_qty = fields.Float('TBS - Kernel Produce from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)
    tbs_pct_shell_produce_qty = fields.Float('TBS - Cangkang Produce from %', digits=dp.get_precision('Product Unit of Measure'), compute='compute_tbs_pct_produce', store=True)

    @api.depends('tbs_consume_qty', 'tbs_ptpn_consume_qty', 'tbs_total_cpo_produce_qty', \
        'tbs_total_kernel_produce_qty', 'tbs_total_shell_produce_qty', \
        'tbs_ptpn_consume_qty', 'tbs_ptpn_actual_kernel_produce_qty', \
        'tbs_ptpn_actual_cpo_produce_qty', 'tbs_ptpn_actual_shell_produce_qty')
    def compute_tbs_pct_produce(self):
        for hpp in self:
            total_olah = hpp.tbs_consume_qty + hpp.tbs_ptpn_consume_qty
            cpo_pct = hpp.tbs_total_cpo_produce_qty/total_olah if total_olah else 0.0
            hpp.tbs_total_cpo_tbs_pct = cpo_pct*100.0
            kernel_pct = hpp.tbs_total_kernel_produce_qty/total_olah if total_olah else 0.0
            hpp.tbs_total_kernel_tbs_pct = kernel_pct*100.0
            shell_pct = hpp.tbs_total_shell_produce_qty/total_olah if total_olah else 0.0
            hpp.tbs_total_shell_tbs_pct = shell_pct*100.0
            hpp.tbs_total_prod_tbs_pct = (cpo_pct + kernel_pct + shell_pct) * 100.0

            tbs_ptpn_cpo_qty = hpp.tbs_ptpn_consume_qty * cpo_pct
            hpp.tbs_ptpn_pct_cpo_produce_qty = tbs_ptpn_cpo_qty
            tbs_ptpn_kernel_qty = hpp.tbs_ptpn_consume_qty * kernel_pct
            hpp.tbs_ptpn_pct_kernel_produce_qty = tbs_ptpn_kernel_qty
            tbs_ptpn_shell_qty = hpp.tbs_ptpn_consume_qty * shell_pct
            hpp.tbs_ptpn_pct_shell_produce_qty = tbs_ptpn_shell_qty

            hpp.tbs_ptpn_cpo_produce_qty_bonus = tbs_ptpn_cpo_qty - hpp.tbs_ptpn_actual_cpo_produce_qty
            hpp.tbs_ptpn_kernel_produce_qty_bonus = tbs_ptpn_kernel_qty - hpp.tbs_ptpn_actual_kernel_produce_qty
            hpp.tbs_pct_shell_produce_qty = tbs_ptpn_shell_qty - hpp.tbs_ptpn_actual_shell_produce_qty

            hpp.tbs_pct_cpo_produce_qty = hpp.tbs_consume_qty * cpo_pct
            hpp.tbs_pct_kernel_produce_qty = hpp.tbs_consume_qty * kernel_pct
            hpp.tbs_pct_shell_produce_qty = hpp.tbs_consume_qty * shell_pct

            hpp.tbs_pct_cpo_produce_qty_and_bonus = (hpp.tbs_consume_qty * cpo_pct) + (tbs_ptpn_cpo_qty - hpp.tbs_ptpn_actual_cpo_produce_qty)
            hpp.tbs_pct_kernel_produce_qty_and_bonus = (hpp.tbs_consume_qty * kernel_pct) + (tbs_ptpn_kernel_qty - hpp.tbs_ptpn_actual_kernel_produce_qty)
            hpp.tbs_pct_shell_produce_qty_and_bonus = (hpp.tbs_consume_qty * shell_pct) + (tbs_ptpn_shell_qty - hpp.tbs_ptpn_actual_shell_produce_qty)
    
    # Manufacturing Cost
    cogm_tbs_consume_value = fields.Float('COGM - TBS Consume Value', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_production_cost_ids = fields.One2many('mill.valuation.bms.production.cost', 'valuation_id','COGM - Production Cost')
    cogm_value = fields.Float('Manufacturing Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_value = fields.Float('PTPN Manufacturing Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_cpo_bonus_value = fields.Float('COGM - CPO Bonus Price', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_cpo_bonus_price = fields.Float('COGM - CPO Bonus Value', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_kernel_bonus_value = fields.Float('COGM - Kernal Bonus Value', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_kernel_bonus_price = fields.Float('COGM - Kernel Bonus Price', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_value2 = fields.Float('Manufacturing Cost 2', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_value2 = fields.Float('PTPN Manufacturing Cost 2', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    production_cost_ptpn_account = fields.Many2one('account.account', string='COGM Account PTPN', states={'compute2': [('readonly',False)]}, readonly=True)

    cogm_cpo_sale_price = fields.Float('COGM - Harga Jual CPO BMS', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_kernel_sale_price = fields.Float('COGM - Harga Jual Kernel BMS', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_cpo_sale_price = fields.Float('COGM - Harga Jasa Olah CPO PTPN', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_kernel_sale_price = fields.Float('COGM - Harga Jasa Olah Kernel PTPN', digits=dp.get_precision('Account'), states={'compute2': [('readonly',False)]}, readonly=True)

    cogm_cpo_produce_qty = fields.Float('COGM - CPO Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_kernel_produce_qty = fields.Float('COGM - Kernel Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_total_produce_qty = fields.Float('COGM - Total Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_cpo_produce_qty = fields.Float('COGM - PTPN CPO Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_kernel_produce_qty = fields.Float('COGM - PTPN Kernel Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_ptpn_total_produce_qty = fields.Float('COGM - PTPN Total Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute2': [('readonly',False)]}, readonly=True)
    
    cogm_cpo_production_cost = fields.Float('COGM - CPO Production Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_cpo_consume_tbs_rate = fields.Float('COGM - CPO Consumed TBS Rate', digits=dp.get_precision('Account'), default=0.95, states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_cpo_consume_tbs_cost = fields.Float('COGM - CPO Consumed TBS Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_cpo_total_cogm = fields.Float('COGM - CPO Total Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_kernel_production_cost = fields.Float('COGM - Kernel Production Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_kernel_consume_tbs_rate = fields.Float('COGM - Kernel Consumed TBS Rate', digits=dp.get_precision('Account'), default=0.05, states={'compute2': [('readonly',False)]}, readonly=True)
    cogm_kernel_consume_tbs_cost = fields.Float('COGM - Kernel Consumed TBS Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_kernel_total_cogm = fields.Float('COGM - Kernel Total Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_cpo_total_cogm = fields.Float('COGM - CPO PTPN Total Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)
    cogm_ptpn_kernel_total_cogm = fields.Float('COGM - Kernel PTPN Total Cost', digits=dp.get_precision('Account'), compute='compute_cogm', store=True)

    @api.depends('cogm_tbs_consume_value', 'cogm_production_cost_ids.amount', 'cogm_production_cost_ids.amount_ptpn', \
        'cogm_ptpn_cpo_bonus_price', 'cogm_ptpn_kernel_bonus_price', \
        'cogm_cpo_produce_qty', 'cogm_kernel_produce_qty', 'cogm_total_produce_qty', \
        'cogm_ptpn_cpo_produce_qty', 'cogm_ptpn_kernel_produce_qty', 'cogm_ptpn_total_produce_qty', \
        'cogm_cpo_sale_price', 'cogm_kernel_sale_price', 'cogm_ptpn_cpo_sale_price', 'cogm_ptpn_kernel_sale_price')
    def compute_cogm(self):
        for hpp in self:
            production_cost = sum(hpp.cogm_production_cost_ids.mapped('amount'))
            ptpn_production_cost = sum(hpp.cogm_production_cost_ids.mapped('amount_ptpn'))

            hpp.cogm_value = hpp.cogm_tbs_consume_value + production_cost
            hpp.cogm_ptpn_value = ptpn_production_cost

            cpo_bonus_production_cost = hpp.tbs_ptpn_cpo_produce_qty_bonus * hpp.cogm_ptpn_cpo_bonus_price
            kernel_bonus_production_cost = hpp.tbs_ptpn_kernel_produce_qty_bonus * hpp.cogm_ptpn_kernel_bonus_price
            hpp.cogm_ptpn_cpo_bonus_value = -cpo_bonus_production_cost
            hpp.cogm_ptpn_kernel_bonus_value = -kernel_bonus_production_cost

            hpp.cogm_value2 = hpp.cogm_tbs_consume_value + production_cost + cpo_bonus_production_cost + kernel_bonus_production_cost
            hpp.cogm_ptpn_value2 = ptpn_production_cost - cpo_bonus_production_cost - kernel_bonus_production_cost

            # CARA HITUNG BMS
            cpo_production_cost_total = production_cost + cpo_bonus_production_cost + kernel_bonus_production_cost
            cogm_cpo_production_cost = (hpp.cogm_cpo_produce_qty/hpp.cogm_total_produce_qty)*cpo_production_cost_total if hpp.cogm_total_produce_qty else 0.0
            # hpp.cogm_cpo_production_cost = cogm_cpo_production_cost
            cogm_cpo_consume_tbs_cost = hpp.cogm_tbs_consume_value*hpp.cogm_cpo_consume_tbs_rate
            # hpp.cogm_cpo_consume_tbs_cost = cogm_cpo_consume_tbs_cost
            # hpp.cogm_cpo_total_cogm = cogm_cpo_production_cost + cogm_cpo_consume_tbs_cost

            kernel_production_cost_total = production_cost + cpo_bonus_production_cost + kernel_bonus_production_cost
            cogm_kernel_production_cost = (hpp.cogm_kernel_produce_qty/hpp.cogm_total_produce_qty)*kernel_production_cost_total if hpp.cogm_total_produce_qty else 0.0
            # hpp.cogm_kernel_production_cost = cogm_kernel_production_cost
            cogm_kernel_consume_tbs_cost = hpp.cogm_tbs_consume_value*hpp.cogm_kernel_consume_tbs_rate
            # hpp.cogm_kernel_consume_tbs_cost = cogm_kernel_consume_tbs_cost
            # hpp.cogm_kernel_total_cogm = cogm_kernel_production_cost + cogm_kernel_consume_tbs_cost
            
            # CARA HITUNG ODOO
            x_sale_price = hpp.cogm_cpo_sale_price if hpp.cogm_cpo_sale_price>hpp.cogm_kernel_sale_price else hpp.cogm_kernel_sale_price
            cpo_populated_produce_qty = (hpp.cogm_cpo_sale_price/x_sale_price if x_sale_price else 0.0) * hpp.cogm_cpo_produce_qty
            kernel_populated_produce_qty = (hpp.cogm_kernel_sale_price/x_sale_price if x_sale_price else 0.0) * hpp.cogm_kernel_produce_qty
            total_populated_produce_qty = cpo_populated_produce_qty + kernel_populated_produce_qty

            production_cost_total = hpp.cogm_tbs_consume_value + production_cost + cpo_bonus_production_cost + kernel_bonus_production_cost
            hpp.cogm_cpo_total_cogm = (cpo_populated_produce_qty/total_populated_produce_qty if total_populated_produce_qty else 0.0) * production_cost_total
            hpp.cogm_kernel_total_cogm = (kernel_populated_produce_qty/total_populated_produce_qty if total_populated_produce_qty else 0.0) * production_cost_total

            x_sale_price_ptpn = hpp.cogm_ptpn_cpo_sale_price if hpp.cogm_ptpn_cpo_sale_price>hpp.cogm_ptpn_kernel_sale_price else hpp.cogm_ptpn_kernel_sale_price
            cpo_ptpn_populated_produce_qty = (hpp.cogm_ptpn_cpo_sale_price/x_sale_price_ptpn if x_sale_price_ptpn else 0.0) * hpp.cogm_ptpn_cpo_produce_qty
            kernel_ptpn_populated_produce_qty = (hpp.cogm_ptpn_kernel_sale_price/x_sale_price_ptpn if x_sale_price_ptpn else 0.0) * hpp.cogm_ptpn_kernel_produce_qty
            total_populated_ptpn_produce_qty = cpo_ptpn_populated_produce_qty + kernel_ptpn_populated_produce_qty

            production_cost_total_ptpn = ptpn_production_cost - cpo_bonus_production_cost - kernel_bonus_production_cost
            hpp.cogm_ptpn_cpo_total_cogm = (cpo_ptpn_populated_produce_qty/total_populated_ptpn_produce_qty if total_populated_ptpn_produce_qty else 0.0) * production_cost_total_ptpn
            hpp.cogm_ptpn_kernel_total_cogm = (kernel_ptpn_populated_produce_qty/total_populated_ptpn_produce_qty if total_populated_ptpn_produce_qty else 0.0) * production_cost_total_ptpn

    # CPO
    cpo_initial_qty = fields.Float('CPO Initial Qty', digits=dp.get_precision('Product Unit of Measure'), states={'draft': [('readonly',False)]}, readonly=True)
    cpo_initial_value = fields.Float('CPO Initial Value', digits=dp.get_precision('Account'), states={'draft': [('readonly',False)]}, readonly=True)
    cpo_opening_qty = fields.Float('CPO - Opening Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_opening_value = fields.Float('CPO - Opening Value', digits=dp.get_precision('Account'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_produce_qty = fields.Float('CPO - Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_produce_value = fields.Float('CPO - Produce Value', digits=dp.get_precision('Account'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_produce_qty_ptpn = fields.Float('CPO - PTPN Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_onhand_qty = fields.Float('CPO - Onhand Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_value_cpo', store=True)
    cpo_onhand_value = fields.Float('CPO - Onhand Value', digits=dp.get_precision('Account'), compute='compute_value_cpo', store=True)
    cpo_average_price_cost = fields.Float('CPO - Average Cost Price', digits=dp.get_precision('Account'), compute='compute_value_cpo', store=True)
    cpo_sale_qty = fields.Float('CPO - Sale Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_sale_value = fields.Float('CPO - Sale Value', digits=dp.get_precision('Account'), compute='compute_value_cpo', store=True)
    cpo_sale_diff_qty = fields.Float('CPO - Difference Sale Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    cpo_sale_diff_value = fields.Float('CPO - Difference Sale Value', digits=dp.get_precision('Account'), compute='compute_value_cpo', store=True)
    cpo_closing_qty = fields.Float('CPO - Closing Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_value_cpo', store=True)
    cpo_closing_value = fields.Float('CPO - Closing Qty', digits=dp.get_precision('Account'), compute='compute_value_cpo', store=True)
    cpo_opname_qty = fields.Float('CPO - Opname Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    
    @api.depends('cpo_opening_qty', 'cpo_opening_value', 'cpo_produce_qty', \
        'cpo_produce_value', 'cpo_produce_qty_ptpn', 'cpo_sale_qty', \
        'cpo_initial_qty', 'cpo_initial_value', 'initial_value')
    def compute_value_cpo(self):
        for hpp in self:
            # onhand_qty = (hpp.cpo_initial_qty if hpp.initial_value else hpp.cpo_opening_qty) + hpp.cpo_produce_qty + hpp.cpo_produce_qty_ptpn
            onhand_qty = (hpp.cpo_initial_qty if hpp.initial_value else hpp.cpo_opening_qty) + hpp.cpo_produce_qty + hpp.cpo_produce_qty_ptpn
            # onhand_value = (hpp.cpo_initial_value if hpp.initial_value else hpp.cpo_opening_value) + hpp.cpo_produce_value
            onhand_value = (hpp.cpo_initial_value if hpp.initial_value else hpp.cpo_opening_value) + hpp.cpo_produce_value
            cost_price = onhand_value/onhand_qty if onhand_qty else 0.0

            hpp.cpo_onhand_qty = onhand_qty
            hpp.cpo_onhand_value = onhand_value
            hpp.cpo_average_price_cost = cost_price

            hpp.cpo_sale_value = hpp.cpo_sale_qty * cost_price
            hpp.cpo_sale_diff_value = hpp.cpo_sale_diff_qty * cost_price
            # hpp.cpo_closing_qty = onhand_qty - hpp.cpo_sale_qty - hpp.cpo_sale_diff_qty
            # hpp.cpo_closing_qty = onhand_qty - hpp.cpo_sale_qty
            hpp.cpo_closing_qty = onhand_qty - hpp.cpo_sale_qty + hpp.cpo_opname_qty
            # hpp.cpo_closing_value = (onhand_qty - hpp.cpo_sale_qty - hpp.cpo_sale_diff_qty) * cost_price
            # hpp.cpo_closing_value = (onhand_qty - hpp.cpo_sale_qty) * cost_price
            hpp.cpo_closing_value = (onhand_qty - hpp.cpo_sale_qty + hpp.cpo_opname_qty) * cost_price

    # KERNEL
    kernel_initial_qty = fields.Float('Kernel Initial Qty', digits=dp.get_precision('Product Unit of Measure'), states={'draft': [('readonly',False)]}, readonly=True)
    kernel_initial_value = fields.Float('Kernel Initial Value', digits=dp.get_precision('Account'), states={'draft': [('readonly',False)]}, readonly=True)
    kernel_opening_qty = fields.Float('Kernel - Opening Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_opening_value = fields.Float('Kernel - Opening Value', digits=dp.get_precision('Account'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_produce_qty = fields.Float('Kernel - Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_produce_value = fields.Float('Kernel - Produce Value', digits=dp.get_precision('Account'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_produce_qty_ptpn = fields.Float('Kernel - PTPN Produce Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_onhand_qty = fields.Float('Kernel - Onhand Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_value_kernel', store=True)
    kernel_onhand_value = fields.Float('Kernel - Onhand Value', digits=dp.get_precision('Account'), compute='compute_value_kernel', store=True)
    kernel_average_price_cost = fields.Float('Kernel - Average Cost Price', digits=dp.get_precision('Account'), compute='compute_value_kernel', store=True)
    kernel_sale_qty = fields.Float('Kernel - Sale Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_sale_value = fields.Float('Kernel - Sale Value', digits=dp.get_precision('Account'), compute='compute_value_kernel', store=True)
    kernel_sale_diff_qty = fields.Float('Kernel - Difference Sale Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)
    kernel_sale_diff_value = fields.Float('Kernel - Difference Sale Value', digits=dp.get_precision('Account'), compute='compute_value_kernel', store=True)
    kernel_closing_qty = fields.Float('Kernel - Closing Qty', digits=dp.get_precision('Product Unit of Measure'), compute='compute_value_kernel', store=True)
    kernel_closing_value = fields.Float('Kernel - Closing Value', digits=dp.get_precision('Account'), compute='compute_value_kernel', store=True)
    kernel_opname_qty = fields.Float('Kernel - Opname Qty', digits=dp.get_precision('Product Unit of Measure'), states={'compute3': [('readonly',False)]}, readonly=True)

    @api.depends('kernel_opening_qty', 'kernel_opening_value', 'kernel_produce_qty', 'kernel_produce_value', 'kernel_produce_qty_ptpn', 'kernel_sale_qty')
    def compute_value_kernel(self):
        for hpp in self:
            onhand_qty = (hpp.kernel_initial_qty if hpp.initial_value else hpp.kernel_opening_qty) + hpp.kernel_produce_qty + hpp.kernel_produce_qty_ptpn
            onhand_value = (hpp.kernel_initial_value if hpp.initial_value else hpp.kernel_opening_value) + hpp.kernel_produce_value
            cost_price = onhand_value/onhand_qty if onhand_qty else 0.0

            hpp.kernel_onhand_qty = onhand_qty
            hpp.kernel_onhand_value = onhand_value
            hpp.kernel_average_price_cost = cost_price

            hpp.kernel_sale_value = hpp.kernel_sale_qty * cost_price
            hpp.kernel_sale_diff_value = hpp.kernel_sale_diff_qty * cost_price
            # hpp.kernel_closing_qty = onhand_qty - hpp.kernel_sale_qty - hpp.kernel_sale_diff_qty
            # hpp.kernel_closing_qty = onhand_qty - hpp.kernel_sale_qty
            hpp.kernel_closing_qty = onhand_qty - hpp.kernel_sale_qty + hpp.kernel_opname_qty
            # hpp.kernel_closing_value = (onhand_qty - hpp.kernel_sale_qty - hpp.kernel_sale_diff_qty) * cost_price
            # hpp.kernel_closing_value = (onhand_qty - hpp.kernel_sale_qty) * cost_price
            hpp.kernel_closing_value = (onhand_qty - hpp.kernel_sale_qty + hpp.kernel_opname_qty) * cost_price

    @api.multi
    def compute_tbs_consumption(self):
        self.ensure_one()
        prev_hpp = self.env['mill.valuation.bms'].search([('date_stop','<',self.date_start), ('state','=','posted')], limit=1)
        tbs_opening_qty = self.tbs_initial_qty if self.initial_value else (prev_hpp.tbs_closing_qty if prev_hpp else 0.0)
        tbs_opening_value = self.tbs_initial_value if self.initial_value else (prev_hpp.tbs_closing_value if prev_hpp else 0.0)

        total_production_hours = self.total_production_hours or 0.0
        tbs_purchase_qty = tbs_purchase_value = tbs_ptpn_purchase_qty = tbs_consume_qty = tbs_ptpn_consume_qty = 0.0
        tbs_total_cpo_produce_qty = tbs_total_kernel_produce_qty = tbs_total_shell_produce_qty = 0.0
        tbs_ptpn_actual_cpo_produce_qty = tbs_ptpn_actual_kernel_produce_qty = tbs_ptpn_actual_shell_produce_qty = 0.0
        current_period_lhp = self.env['mill.lhp'].search([('date','>=',self.date_start),('date','<=',self.date_stop),('state','=','approved')])
        if current_period_lhp:
            total_production_hours = sum(current_period_lhp.mapped('hm_ebc'))
            tbs_purchase_qty = sum(current_period_lhp.mapped('tbs_in_plasma'))
            tbs_ptpn_purchase_qty = sum(current_period_lhp.mapped('tbs_in_ptpn'))
            tbs_consume_qty = sum(current_period_lhp.mapped('tbs_proses_netto')) - tbs_ptpn_purchase_qty
            tbs_ptpn_consume_qty = tbs_ptpn_purchase_qty
            tbs_ptpn_actual_cpo_produce_qty = sum(current_period_lhp.mapped('total_produksi_cpo_ptpn'))
            tbs_ptpn_actual_kernel_produce_qty = sum(current_period_lhp.mapped('total_produksi_kernel_ptpn'))
            tbs_total_cpo_produce_qty = sum(current_period_lhp.mapped('total_produksi_cpo'))
            tbs_total_kernel_produce_qty = sum(current_period_lhp.mapped('total_produksi_kernel'))

        product = self.valuation_categ_id.bom_id.product_id
        purchase_account = product.purchase_account_id or product.categ_id.purchase_account_categ_id
        if not purchase_account:
            raise ValidationError(_('Purchase Account not Found. Please define it in Product Category or Product%s')%product.name)
        move_purchase = self.env['account.move.line'].search([('date','>=',self.date_start),('date','<=',self.date_stop),('account_id','=',purchase_account.id),('product_id','=',product.id)])
        if move_purchase:
            tbs_purchase_qty = 0.0
            for x in move_purchase:
                sign = -1 if (x.debit - x.credit)<0 else 1
                tbs_purchase_value += (x.debit - x.credit)
                if x.product_uom_id and product.uom_id.id!=x.product_uom_id.id:
                    tbs_purchase_qty += sign * x.product_uom_id._compute_quantity(x.quantity, product.uom_id)
                else:
                    tbs_purchase_qty += sign * x.quantity

        update_vals = {
            'total_production_hours': total_production_hours,
            'tbs_opening_qty': tbs_opening_qty,
            'tbs_opening_value': tbs_opening_value,
            'tbs_purchase_qty': tbs_purchase_qty,
            'tbs_purchase_value': tbs_purchase_value,
            'tbs_ptpn_purchase_qty': tbs_ptpn_purchase_qty,
            'tbs_consume_qty': tbs_consume_qty,
            'tbs_ptpn_consume_qty': tbs_ptpn_consume_qty,
            'tbs_total_cpo_produce_qty': tbs_total_cpo_produce_qty,
            'tbs_total_kernel_produce_qty': tbs_total_kernel_produce_qty,
            'tbs_total_shell_produce_qty': tbs_total_shell_produce_qty,
            'tbs_ptpn_actual_cpo_produce_qty': tbs_ptpn_actual_cpo_produce_qty,
            'tbs_ptpn_actual_kernel_produce_qty': tbs_ptpn_actual_kernel_produce_qty,
            'tbs_ptpn_actual_shell_produce_qty': tbs_ptpn_actual_shell_produce_qty,
            'state': 'compute1',
        }
        self.write(update_vals)
        return True

    @api.multi
    def compute1_to_draft(self):
        for hpp in self:
            hpp.state='draft'

    @api.multi
    def compute_tbs_cogm(self):
        self.ensure_one()
        AccountMoveLine = self.env['account.move.line']
        prev_hpp = self.search([('date_stop','=',self.date_start),('state','=','posted')], limit=1)
        production_cost_lines = []
        move_lines = AccountMoveLine.search([('account_id','in',self.production_cost_account_ids.ids),('date','>=',self.date_start),('date','<=',self.date_stop)])
        for account in move_lines.mapped('account_id').sorted(lambda x: x.code):
            aml = move_lines.filtered(lambda x: x.account_id.id==account.id)
            amount = sum(aml.mapped('debit')) - sum(aml.mapped('credit'))
            if not amount:
                continue
            production_cost_lines.append({
                'account_id': account.id,
                'amount': self.tbs_consume_hour_proportion/self.total_production_hours * amount if self.total_production_hours else 0.0,
                'amount_ptpn': self.tbs_ptpn_consume_hour_proportion/self.total_production_hours * amount if self.total_production_hours else 0.0,
                })

        update_vals = {
            'production_cost_ptpn_account': prev_hpp.production_cost_ptpn_account.id if prev_hpp and prev_hpp.production_cost_ptpn_account else False,
            'cogm_ptpn_cpo_bonus_price': prev_hpp.cogm_ptpn_cpo_bonus_price if prev_hpp else 0.0,
            'cogm_ptpn_kernel_bonus_price': prev_hpp.cogm_ptpn_kernel_bonus_price if prev_hpp else 0.0,
            'cogm_cpo_consume_tbs_rate': prev_hpp.cogm_cpo_consume_tbs_rate if prev_hpp else 0.95,
            'cogm_kernel_consume_tbs_rate': prev_hpp.cogm_kernel_consume_tbs_rate if prev_hpp else 0.05,
            'cogm_cpo_sale_price': prev_hpp.cogm_cpo_sale_price if prev_hpp else 0.0,
            'cogm_kernel_sale_price': prev_hpp.cogm_kernel_sale_price if prev_hpp else 0.0,
            'cogm_ptpn_cpo_sale_price': prev_hpp.cogm_ptpn_cpo_sale_price if prev_hpp else 0.0,
            'cogm_ptpn_kernel_sale_price': prev_hpp.cogm_ptpn_kernel_sale_price if prev_hpp else 0.0,
            
            'cogm_tbs_consume_value': self.tbs_consume_value,
            'cogm_production_cost_ids': list(map(lambda x: (0,0,x), production_cost_lines)) if production_cost_lines else [],
            'cogm_cpo_produce_qty': self.tbs_pct_cpo_produce_qty,
            'cogm_kernel_produce_qty': self.tbs_pct_kernel_produce_qty,
            'cogm_total_produce_qty': self.tbs_pct_cpo_produce_qty + self.tbs_pct_kernel_produce_qty,
            'cogm_ptpn_cpo_produce_qty': self.tbs_ptpn_actual_cpo_produce_qty,
            'cogm_ptpn_kernel_produce_qty': self.tbs_ptpn_actual_kernel_produce_qty,
            'cogm_ptpn_total_produce_qty': self.tbs_ptpn_actual_cpo_produce_qty + self.tbs_ptpn_actual_kernel_produce_qty,
            'state': 'compute2',
        }
        self.write(update_vals)
        return True

    @api.multi
    def compute2_to_draft(self):
        for hpp in self:
            hpp.state='compute1'
            for x in hpp.cogm_production_cost_ids:
                x.unlink()

    @api.multi
    def compute_finish_goods(self):
        self.ensure_one()
        prev_hpp = self.env['mill.valuation.bms'].search([('date_stop','<',self.date_start), ('state','=','posted')], limit=1)
        cpo_opening_qty = self.cpo_initial_qty if self.initial_value else (prev_hpp.cpo_closing_qty if prev_hpp else 0.0)
        cpo_opening_value = self.cpo_initial_value if self.initial_value else (prev_hpp.cpo_closing_value if prev_hpp else 0.0)
        kernel_opening_qty = self.kernel_initial_qty if self.initial_value else (prev_hpp.kernel_closing_qty if prev_hpp else 0.0)
        kernel_opening_value = self.kernel_initial_value if self.initial_value else (prev_hpp.kernel_closing_value if prev_hpp else 0.0)

        cpo_produce_qty = cpo_sale_qty = cpo_sale_diff_qty = cpo_opname_qty = 0.0
        kernel_produce_qty = kernel_sale_qty = kernel_sale_diff_qty = kernel_opname_qty = 0.0
        current_period_lhp = self.env['mill.lhp'].search([('date','>=',self.date_start),('date','<=',self.date_stop),('state','=','approved')])
        if current_period_lhp:
            # cpo_produce_qty = sum(current_period_lhp.mapped('total_produksi_cpo')) - sum(current_period_lhp.mapped('total_produksi_cpo_ptpn'))
            cpo_produce_qty = self.tbs_pct_cpo_produce_qty
            cpo_sale_qty = sum(current_period_lhp.mapped('total_penjualan_cpo')) + sum(current_period_lhp.mapped('total_penjualan_cpo_palopo'))
            cpo_sale_diff_qty = sum(current_period_lhp.mapped('selisih_timbang_penjualan_cpo'))
            cpo_opname_qty = sum(current_period_lhp.mapped('total_penyesuaian_cpo')) + sum(current_period_lhp.mapped('total_penyesuaian_cpo_palopo'))
            
            # kernel_produce_qty = sum(current_period_lhp.mapped('total_produksi_kernel')) - sum(current_period_lhp.mapped('total_produksi_kernel_ptpn'))
            kernel_produce_qty = self.tbs_pct_kernel_produce_qty
            kernel_sale_qty = sum(current_period_lhp.mapped('total_penjualan_kernel')) + sum(current_period_lhp.mapped('total_penjualan_kernel_mpa'))
            kernel_sale_diff_qty = sum(current_period_lhp.mapped('selisih_timbang_penjualan_kernel'))
            kernel_opname_qty = sum(current_period_lhp.mapped('total_penyesuaian_kernel')) + sum(current_period_lhp.mapped('total_penyesuaian_kernel_mpa'))

        produce_products = self.valuation_categ_id.bom_id.mapped('bom_line_ids.product_id')
        product_cpo = produce_products.filtered(lambda x: x.default_code=='CPO')
        # cpo_sale_account = product_cpo.property_account_income_id or product_cpo.categ_id.property_account_income_categ_id
        # if not cpo_sale_account:
        #     raise ValidationError(_('Income Account not Found. Please define it in Product Category %s')%product_cpo.name)
        # cpo_current_period_sales_move = self.env['account.move.line'].search([('date','>=',self.date_start),('date','<=',self.date_stop),('account_id','=',cpo_sale_account.id), ('product_id','=',product_cpo.id)])
        # if cpo_current_period_sales_move:
        #     for x in cpo_current_period_sales_move:
        #         sign = -1 if (x.debit - x.credit)>0 else 1
        #         if x.product_uom_id and product_cpo.uom_id.id!=x.product_uom_id.id:
        #             cpo_sale_qty += sign * x.product_uom_id._compute_quantity(x.quantity, product_cpo.uom_id)
        #         else:
        #             cpo_sale_qty += sign * x.quantity

        product_kernel = produce_products.filtered(lambda x: x.default_code=='PK')
        # kernel_sale_account = product_kernel.property_account_income_id or product_kernel.categ_id.property_account_income_categ_id
        # if not kernel_sale_account:
        #     raise ValidationError(_('Income Account not Found. Please define it in Product Category %s')%product_kernel.name)
        # kernel_current_period_sales_move = self.env['account.move.line'].search([('date','>=',self.date_start),('date','<=',self.date_stop),('account_id','=',kernel_sale_account.id), ('product_id','=',product_kernel.id)])
        # if kernel_current_period_sales_move:
        #     for x in kernel_current_period_sales_move:
        #         sign = -1 if (x.debit - x.credit)>0 else 1
        #         if x.product_uom_id and product_kernel.uom_id.id!=x.product_uom_id.id:
        #             kernel_sale_qty += sign * x.product_uom_id._compute_quantity(x.quantity, product_kernel.uom_id)
        #         else:
        #             kernel_sale_qty += sign * x.quantity

        update_vals = {
            'cpo_opening_qty': cpo_opening_qty,
            'cpo_opening_value': cpo_opening_value,
            'cpo_produce_qty': cpo_produce_qty,
            'cpo_produce_value': self.cogm_cpo_total_cogm,
            'cpo_produce_qty_ptpn': self.tbs_ptpn_cpo_produce_qty_bonus,
            'cpo_sale_qty': cpo_sale_qty,
            'cpo_sale_diff_qty': cpo_sale_diff_qty,
            'kernel_opening_qty': kernel_opening_qty,
            'kernel_opening_value': kernel_opening_value,
            'kernel_produce_qty': kernel_produce_qty,
            'kernel_produce_value': self.cogm_kernel_total_cogm,
            'kernel_produce_qty_ptpn': self.tbs_ptpn_kernel_produce_qty_bonus,
            'kernel_sale_qty': kernel_sale_qty,
            'kernel_sale_diff_qty': kernel_sale_diff_qty,
            'state': 'compute3',
        }
        self.write(update_vals)
        return True

    @api.multi
    def compute3_to_draft(self):
        for hpp in self:
            hpp.state='compute2'

    # @api.multi
    # def action_validate(self):
    #     AccountMove = self.env['account.move']
    #     AccountMoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
    #     for hpp in self:
    #         created_move_ids = []
    #         product_tbs = self.valuation_categ_id.bom_id.product_id
    #         tbs_valuation_account = product_tbs.categ_id.property_stock_valuation_account_id
    #         if not tbs_valuation_account:
    #             raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_tbs.name)
    #         produce_products = self.valuation_categ_id.bom_id.mapped('bom_line_ids.product_id')
    #         product_cpo = produce_products.filtered(lambda x: x.default_code=='CPO')
    #         cpo_valuation_account = product_cpo.categ_id.property_stock_valuation_account_id
    #         if not cpo_valuation_account:
    #             raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_cpo.name)
    #         product_kernel = produce_products.filtered(lambda x: x.default_code=='PK')
    #         kernel_valuation_account = product_kernel.categ_id.property_stock_valuation_account_id
    #         if not kernel_valuation_account:
    #             raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_kernel.name)
    #         # Jurnal TBS
    #         if hpp.tbs_purchase_value:
    #             tbs_move = AccountMove.create({
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 })
    #             # Jurnal Stock, dari Qty Purchase dan Value Purchase
    #             if hpp.tbs_purchase_value:
    #                 tbs_purchase_account = product_tbs.purchase_account_id or product_tbs.categ_id.purchase_account_categ_id
    #                 if not tbs_purchase_account:
    #                     raise ValidationError(_('Purchase Account not Found. Please define it in Product Category or Product %s')%product_tbs.name)
    #                 move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': 'Pembelian %s'%product_tbs.name,
    #                     'account_id': tbs_valuation_account.id,
    #                     'product_id': product_tbs.id,
    #                     'product_uom_id': product_tbs.uom_id.id,
    #                     'debit': hpp.tbs_purchase_value > 0.0 and hpp.tbs_purchase_value or 0.0,
    #                     'credit': hpp.tbs_purchase_value < 0.0 and -hpp.tbs_purchase_value or 0.0,
    #                     'price_unit': 0.0,
    #                     'quantity': hpp.tbs_purchase_qty,
    #                     'move_id': tbs_move.id
    #                 }
    #                 AccountMoveLine.create(move_line_dict)
    #                 ct_move_line_dict = move_line_dict.copy()
    #                 ct_move_line_dict['debit'] = hpp.tbs_purchase_value < 0.0 and -hpp.tbs_purchase_value or 0.0
    #                 ct_move_line_dict['credit'] = hpp.tbs_purchase_value > 0.0 and hpp.tbs_purchase_value or 0.0
    #                 ct_move_line_dict['account_id'] = tbs_purchase_account.id
    #                 AccountMoveLine.create(ct_move_line_dict)
    #             created_move_ids.append(tbs_move.id)

    #         # Jurnal Produksi CPO dan Kernel
    #         if hpp.cpo_produce_value and hpp.kernel_produce_value and hpp.tbs_consume_value:
    #             production_move = AccountMove.create({
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 })
    #             # Jurnal Produksi CPO
    #             if hpp.cpo_produce_value:
    #                 cpo_cogm_move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': 'Produksi %s'%product_cpo.name,
    #                     'account_id': cpo_valuation_account.id,
    #                     'product_id': product_cpo.id,
    #                     'product_uom_id': product_cpo.uom_id.id,
    #                     'debit': hpp.cpo_produce_value > 0.0 and hpp.cpo_produce_value or 0.0,
    #                     'credit': hpp.cpo_produce_value < 0.0 and -hpp.cpo_produce_value or 0.0,
    #                     'price_unit': 0.0,
    #                     'quantity': hpp.cpo_produce_qty,
    #                     'move_id': production_move.id
    #                 }
    #                 AccountMoveLine.create(cpo_cogm_move_line_dict)

    #             # Jurnal Produksi KERNEL
    #             if hpp.kernel_produce_value:
    #                 kernel_cogm_move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': 'Produksi %s'%product_kernel.name,
    #                     'account_id': kernel_valuation_account.id,
    #                     'product_id': product_kernel.id,
    #                     'product_uom_id': product_kernel.uom_id.id,
    #                     'debit': hpp.kernel_produce_value > 0.0 and hpp.kernel_produce_value or 0.0,
    #                     'credit': hpp.kernel_produce_value < 0.0 and -hpp.kernel_produce_value or 0.0,
    #                     'price_unit': 0.0,
    #                     'quantity': hpp.kernel_produce_qty,
    #                     'move_id': production_move.id
    #                 }
    #                 AccountMoveLine.create(kernel_cogm_move_line_dict)

    #             # Jurnal Produksi Pabrikasi PTPN
    #             if hpp.cogm_ptpn_value2:
    #                 production_cost_ptpn_account = hpp.production_cost_ptpn_account
    #                 ptpn_cogm_move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': 'Produksi PTPN',
    #                     'account_id': production_cost_ptpn_account.id,
    #                     'product_id': False,
    #                     'product_uom_id': False,
    #                     'debit': hpp.cogm_ptpn_value2 > 0.0 and hpp.cogm_ptpn_value2 or 0.0,
    #                     'credit': hpp.cogm_ptpn_value2 < 0.0 and -hpp.cogm_ptpn_value2 or 0.0,
    #                     'price_unit': 0.0,
    #                     'quantity': hpp.cogm_ptpn_total_produce_qty,
    #                     'move_id': production_move.id
    #                 }
    #                 AccountMoveLine.create(ptpn_cogm_move_line_dict)
                
    #             # Jurnal Konsumsi TBS
    #             if hpp.tbs_consume_value:
    #                 tbs_cogm_move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': 'Pengolahan %s'%product_tbs.name,
    #                     'account_id': tbs_valuation_account.id,
    #                     'product_id': product_tbs.id,
    #                     'product_uom_id': product_tbs.uom_id.id,
    #                     'debit': hpp.tbs_consume_value < 0.0 and -hpp.tbs_consume_value or 0.0,
    #                     'credit': hpp.tbs_consume_value > 0.0 and hpp.tbs_consume_value or 0.0,
    #                     'price_unit': hpp.tbs_average_cost_price,
    #                     'quantity': hpp.tbs_consume_qty,
    #                     'move_id': production_move.id
    #                 }
    #                 AccountMoveLine.create(tbs_cogm_move_line_dict)
    #             # Jurnal Konsumsi Biaya Produksi Lainnya
    #             for othcost in hpp.cogm_production_cost_ids:
    #                 oth_cogm_move_line_dict = {
    #                     'date': self.date_stop,
    #                     'journal_id': self.journal_id.id,
    #                     'name': othcost.account_id.name,
    #                     'account_id': othcost.account_id.id,
    #                     'product_id': False,
    #                     'product_uom_id': False,
    #                     'debit': othcost.subtotal < 0.0 and -othcost.subtotal or 0.0,
    #                     'credit': othcost.subtotal > 0.0 and othcost.subtotal or 0.0,
    #                     'price_unit': 0.0,
    #                     'quantity': 0.0,
    #                     'move_id': production_move.id
    #                 }
    #                 AccountMoveLine.create(oth_cogm_move_line_dict)
    #             created_move_ids.append(production_move.id)

    #         # Jurnal Penjualan CPO
    #         if hpp.cpo_sale_value:
    #             cpo_sale_move = AccountMove.create({
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 })
    #             # Jurnal Harga Pokok Penjualan
    #             output_account = product_cpo.property_stock_account_output or product_cpo.categ_id.property_stock_account_output_categ_id
    #             if not output_account:
    #                 raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product %s')%product_cpo.name)
    #             cpo_sale_move_line_dict = {
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 'name': 'Harga Pokok Penjualan %s'%product_cpo.name,
    #                 'account_id': output_account.id,
    #                 'product_id': product_cpo.id,
    #                 'product_uom_id': product_cpo.uom_id.id,
    #                 'debit': hpp.cpo_sale_value > 0.0 and hpp.cpo_sale_value or 0.0,
    #                 'credit': hpp.cpo_sale_value < 0.0 and -hpp.cpo_sale_value or 0.0,
    #                 'price_unit': hpp.cpo_average_price_cost,
    #                 'quantity': hpp.cpo_sale_qty,
    #                 'move_id': cpo_sale_move.id
    #             }
    #             AccountMoveLine.create(cpo_sale_move_line_dict)
    #             ct_cpo_sale_move_line_dict = cpo_sale_move_line_dict.copy()
    #             ct_cpo_sale_move_line_dict['debit'] = hpp.cpo_sale_value < 0.0 and -hpp.cpo_sale_value or 0.0
    #             ct_cpo_sale_move_line_dict['credit'] = hpp.cpo_sale_value > 0.0 and hpp.cpo_sale_value or 0.0
    #             ct_cpo_sale_move_line_dict['account_id'] = cpo_valuation_account.id
    #             AccountMoveLine.create(ct_cpo_sale_move_line_dict)

    #             created_move_ids.append(cpo_sale_move.id)
            
    #         # Jurnal KERNEL
    #         if hpp.kernel_sale_value:
    #             kernel_sale_move = AccountMove.create({
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 })
    #             # Jurnal Harga Pokok Penjualan
    #             kernel_output_account = product_kernel.property_stock_account_output or product_kernel.categ_id.property_stock_account_output_categ_id
    #             if not output_account:
    #                 raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product %s')%product_kernel.name)
    #             kernel_sale_move_line_dict = {
    #                 'date': self.date_stop,
    #                 'journal_id': self.journal_id.id,
    #                 'name': 'Harga Pokok Penjualan %s'%product_kernel.name,
    #                 'account_id': kernel_output_account.id,
    #                 'product_id': product_kernel.id,
    #                 'product_uom_id': product_kernel.uom_id.id,
    #                 'debit': hpp.kernel_sale_value > 0.0 and hpp.kernel_sale_value or 0.0,
    #                 'credit': hpp.kernel_sale_value < 0.0 and -hpp.kernel_sale_value or 0.0,
    #                 'price_unit': hpp.kernel_average_price_cost,
    #                 'quantity': hpp.kernel_sale_qty,
    #                 'move_id': kernel_sale_move.id
    #             }
    #             AccountMoveLine.create(kernel_sale_move_line_dict)
    #             ct_kernel_sale_move_line_dict = kernel_sale_move_line_dict.copy()
    #             ct_kernel_sale_move_line_dict['debit'] = hpp.kernel_sale_value < 0.0 and -hpp.kernel_sale_value or 0.0
    #             ct_kernel_sale_move_line_dict['credit'] = hpp.kernel_sale_value > 0.0 and hpp.kernel_sale_value or 0.0
    #             ct_kernel_sale_move_line_dict['account_id'] = kernel_valuation_account.id
    #             AccountMoveLine.create(ct_kernel_sale_move_line_dict)

    #             created_move_ids.append(kernel_sale_move.id)

    #         if created_move_ids:
    #             hpp.move_ids = list(map(lambda x: (4,x), created_move_ids))
    #         hpp.state='posted'
    #     return True

    @api.multi
    def action_validate(self):
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
        for hpp in self:
            closing_date = hpp.date_stop
            opening_date = (datetime.strptime(hpp.date_stop, DF) + relativedelta(days=+1)).strftime(DF)
            created_move_ids = []
            product_tbs = self.valuation_categ_id.bom_id.product_id
            tbs_valuation_account = product_tbs.categ_id.property_stock_valuation_account_id
            if not tbs_valuation_account:
                raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_tbs.name)
            produce_products = self.valuation_categ_id.bom_id.mapped('bom_line_ids.product_id')
            product_cpo = produce_products.filtered(lambda x: x.default_code=='CPO')
            cpo_valuation_account = product_cpo.categ_id.property_stock_valuation_account_id
            if not cpo_valuation_account:
                raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_cpo.name)
            product_kernel = produce_products.filtered(lambda x: x.default_code=='PK')
            kernel_valuation_account = product_kernel.categ_id.property_stock_valuation_account_id
            if not kernel_valuation_account:
                raise ValidationError(_('Stock Valuation Account not Found. Please define it in Product Category %s')%product_kernel.name)
            # Jurnal TBS
            if hpp.tbs_closing_value:
                tbs_closing_move = AccountMove.create({
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    })
                tbs_opening_move = AccountMove.create({
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    })
                tbs_input_account = product_tbs.categ_id.stock_counterpart_valuation_account_categ_id
                if not tbs_input_account:
                    raise ValidationError(_('Stock Counterpart Valuation Account not Found. Please define it in Product Category or Product %s')%product_tbs.name)
                tbs_output_account = product_tbs.property_stock_account_output or product_tbs.categ_id.property_stock_account_output_categ_id
                if not tbs_output_account:
                    raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product %s')%product_tbs.name)
                move_line_dict1 = {
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Akhir %s'%product_tbs.name,
                    'account_id': tbs_valuation_account.id,
                    'product_id': product_tbs.id,
                    'product_uom_id': product_tbs.uom_id.id,
                    'debit': hpp.tbs_closing_value > 0.0 and hpp.tbs_closing_value or 0.0,
                    'credit': hpp.tbs_closing_value < 0.0 and -hpp.tbs_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.tbs_closing_qty,
                    'move_id': tbs_closing_move.id
                }
                AccountMoveLine.create(move_line_dict1)
                ct_move_line_dict1 = move_line_dict1.copy()
                ct_move_line_dict1['debit'] = hpp.tbs_closing_value < 0.0 and -hpp.tbs_closing_value or 0.0
                ct_move_line_dict1['credit'] = hpp.tbs_closing_value > 0.0 and hpp.tbs_closing_value or 0.0
                ct_move_line_dict1['account_id'] = tbs_input_account.id
                AccountMoveLine.create(ct_move_line_dict1)
                created_move_ids.append(tbs_closing_move.id)

                move_line_dict2 = {
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Awal %s'%product_tbs.name,
                    'account_id': tbs_output_account.id,
                    'product_id': product_tbs.id,
                    'product_uom_id': product_tbs.uom_id.id,
                    'debit': hpp.tbs_closing_value > 0.0 and hpp.tbs_closing_value or 0.0,
                    'credit': hpp.tbs_closing_value < 0.0 and -hpp.tbs_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.tbs_opening_qty,
                    'move_id': tbs_opening_move.id
                }
                AccountMoveLine.create(move_line_dict2)
                ct_move_line_dict2 = move_line_dict2.copy()
                ct_move_line_dict2['debit'] = hpp.tbs_closing_value < 0.0 and -hpp.tbs_closing_value or 0.0
                ct_move_line_dict2['credit'] = hpp.tbs_closing_value > 0.0 and hpp.tbs_closing_value or 0.0
                ct_move_line_dict2['account_id'] = tbs_valuation_account.id
                AccountMoveLine.create(ct_move_line_dict2)
                created_move_ids.append(tbs_opening_move.id)

            # Jurnal CPO
            if hpp.cpo_closing_value:
                cpo_closing_move = AccountMove.create({
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    })
                cpo_opening_move = AccountMove.create({
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    })
                cpo_input_account = product_cpo.categ_id.stock_counterpart_valuation_account_categ_id
                if not cpo_input_account:
                    raise ValidationError(_('Stock Counterpart Valuation Account not Found. Please define it in Product Category or Product %s')%product_cpo.name)
                cpo_output_account = product_cpo.property_stock_account_output or product_cpo.categ_id.property_stock_account_output_categ_id
                if not cpo_output_account:
                    raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product %s')%product_cpo.name)
                move_line_dict3 = {
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Akhir %s'%product_cpo.name,
                    'account_id': cpo_valuation_account.id,
                    'product_id': product_cpo.id,
                    'product_uom_id': product_cpo.uom_id.id,
                    'debit': hpp.cpo_closing_value > 0.0 and hpp.cpo_closing_value or 0.0,
                    'credit': hpp.cpo_closing_value < 0.0 and -hpp.cpo_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.cpo_closing_qty,
                    'move_id': cpo_closing_move.id
                }
                AccountMoveLine.create(move_line_dict3)
                ct_move_line_dict3 = move_line_dict3.copy()
                ct_move_line_dict3['debit'] = hpp.cpo_closing_value < 0.0 and -hpp.cpo_closing_value or 0.0
                ct_move_line_dict3['credit'] = hpp.cpo_closing_value > 0.0 and hpp.cpo_closing_value or 0.0
                ct_move_line_dict3['account_id'] = cpo_input_account.id
                AccountMoveLine.create(ct_move_line_dict3)
                created_move_ids.append(cpo_closing_move.id)

                move_line_dict4 = {
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Awal %s'%product_cpo.name,
                    'account_id': cpo_output_account.id,
                    'product_id': product_cpo.id,
                    'product_uom_id': product_cpo.uom_id.id,
                    'debit': hpp.cpo_closing_value > 0.0 and hpp.cpo_closing_value or 0.0,
                    'credit': hpp.cpo_closing_value < 0.0 and -hpp.cpo_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.cpo_closing_qty,
                    'move_id': cpo_opening_move.id
                }
                AccountMoveLine.create(move_line_dict4)
                ct_move_line_dict4 = move_line_dict4.copy()
                ct_move_line_dict4['debit'] = hpp.cpo_closing_value < 0.0 and -hpp.cpo_closing_value or 0.0
                ct_move_line_dict4['credit'] = hpp.cpo_closing_value > 0.0 and hpp.cpo_closing_value or 0.0
                ct_move_line_dict4['account_id'] = cpo_valuation_account.id
                AccountMoveLine.create(ct_move_line_dict4)
                created_move_ids.append(cpo_opening_move.id)
            
            # Jurnal KERNEL
            if hpp.kernel_closing_value:
                kernel_closing_move = AccountMove.create({
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    })
                kernel_opening_move = AccountMove.create({
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    })
                kernel_input_account = product_kernel.categ_id.stock_counterpart_valuation_account_categ_id
                if not kernel_input_account:
                    raise ValidationError(_('Stock Counterpart Valuation Account not Found. Please define it in Product Category or Product %s')%product_kernel.name)
                kernel_output_account = product_kernel.property_stock_account_output or product_kernel.categ_id.property_stock_account_output_categ_id
                if not kernel_output_account:
                    raise ValidationError(_('Stock Output Account not Found. Please define it in Product Category or Product %s')%product_kernel.name)
                move_line_dict5 = {
                    'date': closing_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Akhir %s'%product_kernel.name,
                    'account_id': kernel_valuation_account.id,
                    'product_id': product_kernel.id,
                    'product_uom_id': product_kernel.uom_id.id,
                    'debit': hpp.kernel_closing_value > 0.0 and hpp.kernel_closing_value or 0.0,
                    'credit': hpp.kernel_closing_value < 0.0 and -hpp.kernel_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.kernel_closing_qty,
                    'move_id': kernel_closing_move.id
                }
                AccountMoveLine.create(move_line_dict5)
                ct_move_line_dict5 = move_line_dict5.copy()
                ct_move_line_dict5['debit'] = hpp.kernel_closing_value < 0.0 and -hpp.kernel_closing_value or 0.0
                ct_move_line_dict5['credit'] = hpp.kernel_closing_value > 0.0 and hpp.kernel_closing_value or 0.0
                ct_move_line_dict5['account_id'] = kernel_input_account.id
                AccountMoveLine.create(ct_move_line_dict5)
                created_move_ids.append(kernel_closing_move.id)

                move_line_dict6 = {
                    'date': opening_date,
                    'journal_id': hpp.journal_id.id,
                    'name': 'Saldo Awal %s'%product_kernel.name,
                    'account_id': kernel_output_account.id,
                    'product_id': product_kernel.id,
                    'product_uom_id': product_kernel.uom_id.id,
                    'debit': hpp.kernel_closing_value > 0.0 and hpp.kernel_closing_value or 0.0,
                    'credit': hpp.kernel_closing_value < 0.0 and -hpp.kernel_closing_value or 0.0,
                    'price_unit': 0.0,
                    'quantity': hpp.kernel_closing_qty,
                    'move_id': kernel_opening_move.id
                }
                AccountMoveLine.create(move_line_dict6)
                ct_move_line_dict6 = move_line_dict6.copy()
                ct_move_line_dict6['debit'] = hpp.kernel_closing_value < 0.0 and -hpp.kernel_closing_value or 0.0
                ct_move_line_dict6['credit'] = hpp.kernel_closing_value > 0.0 and hpp.kernel_closing_value or 0.0
                ct_move_line_dict6['account_id'] = kernel_valuation_account.id
                AccountMoveLine.create(ct_move_line_dict6)
                created_move_ids.append(kernel_opening_move.id)

            if created_move_ids:
                hpp.move_ids = list(map(lambda x: (4,x), created_move_ids))
            hpp.state='posted'
        return True

    @api.multi
    def button_cancel(self):
        for hpp in self:
            for move in hpp.move_ids:
                move.unlink()
            for x in hpp.cogm_production_cost_ids:
                x.unlink()
            hpp.state='draft'

    @api.model
    def create(self, vals):
        if 'production_cost_account_ids' in vals.keys():
            to_be_added = []
            for item in vals['production_cost_account_ids']:
                if item[0]==1:
                    to_be_added.append(item[1])
                elif item[0]==6:
                    to_be_added.extend(item[2])
            if to_be_added:
                vals['production_cost_account_ids'] = [(6,0, to_be_added)]
        return super(MillValuationBMS, self).create(vals)

    def unlink(self):
        if self.state!='draft':
            raise ValidationError(_('Mill Valuation cannot be deleted due to the state which is not in draft state'))
        return super(MillValuationBMS, self).unlink()

    @api.multi
    def write(self, update_vals):
        for valuation in self:
            if 'production_cost_account_ids' in update_vals.keys():
                to_be_added = []
                for item in update_vals['production_cost_account_ids']:
                    if item[0] == 1:
                        to_be_added.append(item[1])
                    elif item[0] == 6:
                        to_be_added.extend(item[2])
                if to_be_added:
                    update_vals['production_cost_account_ids'] = [(6, 0, to_be_added)]
        return super(MillValuationBMS, self).write(update_vals)

class MillValuationBMSProductionCost(models.Model):
    _name = 'mill.valuation.bms.production.cost'

    valuation_id = fields.Many2one('mill.valuation.bms', 'Valuation ID', requried=True)
    account_id = fields.Many2one('account.account', 'Account', requried=True)
    amount = fields.Float('Cost', digits=dp.get_precision('Account'))
    amount_ptpn = fields.Float('Cost (PTPN)', digits=dp.get_precision('Account'))
    subtotal = fields.Float('Subtotal', compute='compute_amount_line')

    @api.depends('amount','amount_ptpn')
    def compute_amount_line(self):
        for line in self:
            line.subtotal = line.amount + line.amount_ptpn