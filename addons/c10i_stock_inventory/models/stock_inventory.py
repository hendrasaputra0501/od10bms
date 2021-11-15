# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class AdjustmentsInventory(models.Model):
    _inherit = "stock.inventory"
    _description = "Inventory"


    default_account_id = fields.Many2one('account.account', string='Adjustments Account', ondelete='restrict')
    adjustment_date = fields.Datetime(
        'Inventory Adjustments Date',
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")
    use_adjustment_date = fields.Boolean(string='Use Adjustment Date', default=False)

    @api.multi
    def action_start(self):
        for inventory in self:
            vals = {'state': 'confirm', 'date': fields.Datetime.now() if not self.use_adjustment_date else self.adjustment_date}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                if not inventory.use_adjustment_date:
                    vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
                else:
                    vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
                    
            inventory.write(vals)
        # Attention: this is not default odoo , modify for dynamic inventory adjustments by adjustment_date
        # do repetitions to fill theoretical_qty field in model :  stock.inventory.line
        # this looping is force to do because inventory.write(vals) function result still: theoretical_qty = 0. maybe _compute_theoretical_qty define its.
        if self.use_adjustment_date:
            temp = inventory._get_inventory_lines_values()
            self._compute_qty_forced(temp)
        
        return True
    prepare_inventory = action_start


    @api.multi
    def _compute_qty_forced(self, temp):
        for rec in self:
            if rec.line_ids:
                for lines in rec.line_ids:
                    for line in temp:
                        if lines.product_id.id == line["product_id"] and lines.location_id.id == line["location_id"] and lines.product_uom_id.id == line["product_uom_id"]:
                             lines["theoretical_qty"] = line["theoretical_qty"]

        return True

    def get_price_per_product(self, lines):
        for line_vals in lines:
            product = self.env['product.product'].browse(line_vals['product_id'])
            line_vals.update({
                'current_price_unit': product.standard_price,
                'new_price_unit': product.standard_price,
                })
        return lines

    @api.multi
    def _get_inventory_lines_values(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        
        domain_adjustments = ' location_dest_id in %s'
        args = (tuple(locations.ids),)

        # add filter by adjustment date
        date = str(self.adjustment_date)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)

            domain_adjustments += ' AND company_id = %s'
        
        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)

            domain_adjustments += ' AND owner_id = %s'
        #case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)

            domain_adjustments += ' AND lot_id = %s'
        #case 3: Filter on One product
        if self.product_id:
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
            domain_adjustments += ' AND product_id = %s'
        #case 4: Filter on A Pack
        if self.package_id:
            args += (self.package_id.id,)
            domain_adjustments += ' AND package_id = %s'
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

            domain_adjustments += ' AND product_id = ANY (%s)'
        # filter by adjustment_date
        if self.use_adjustment_date:
            domain += " AND date < %s AND state='done'"
            args += (str(self.adjustment_date),)
            domain_adjustments += " AND date < %s AND state='done'"

        
        if not self.use_adjustment_date: 
            self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                FROM stock_quant
                WHERE %s
                GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)
        else:
            temp_args = args+args
            self.env.cr.execute("""SELECT product_id, sum(product_qty) as product_qty, location_id, company_id, lot_id as prod_lot_id, product_packaging as package_id, partner_id from 
                    (
                    SELECT product_id, sum(product_uom_qty) as product_qty, location_dest_id as location_id, company_id, restrict_lot_id as lot_id, product_packaging, partner_id 
                    FROM stock_move
                    WHERE %s
                    GROUP BY product_id, location_dest_id, company_id, restrict_lot_id, product_packaging, partner_id
                    UNION ALL
                    SELECT product_id, sum(-product_uom_qty) as product_qty, location_id as location_id, company_id,  restrict_lot_id as lot_id, product_packaging, partner_id
                    FROM stock_move
                    WHERE %s
                    GROUP BY product_id, location_id, company_id, restrict_lot_id, product_packaging, partner_id
                    ) 
                    as stock_move
                    GROUP BY product_id, location_id, company_id, lot_id, product_packaging, partner_id"""% (domain_adjustments, domain), temp_args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            # add account number
            product_data['account_id'] = self.default_account_id.id or False
            # 
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
    
        res = self.get_price_per_product(vals)
        return res


class InventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    account_id = fields.Many2one('account.account', string='Inventory Details Account', ondelete='restrict')
    theoretical_qty = fields.Float(
        'Theoretical Quantity', compute='_compute_theoretical_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=False, store=True)
    current_price_unit = fields.Float("Price Unit")
    new_price_unit = fields.Float("Price Unit")

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        if self.inventory_id.use_adjustment_date:
            locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id]),('usage','=','internal')])
            domain_source = ' location_id in %s'
            domain_dest = ' location_dest_id in %s'
            args = (tuple(locations.ids),)
            # case 0: Filter on company
            if self.company_id:
                domain_source += ' AND company_id = %s'
                domain_dest += ' AND company_id = %s'
                args += (self.company_id.id,)
            #case 1: Filter on One owner only or One product for a specific owner
            # if self.partner_id:
            #     domain_source += ' AND owner_id = %s'
            #     domain_dest += ' AND owner_id = %s'
            #     args += (self.partner_id.id,)
            #case 2: Filter on One Lot/Serial Number
            if self.prod_lot_id:
                domain_source += ' AND lot_id = %s'
                domain_dest += ' AND lot_id = %s'
                args += (self.prod_lot_id.id,)
            #case 3: Filter product
            if self.product_id:
                domain_source += ' AND product_id = %s'
                domain_dest += ' AND product_id = %s'
                args += (self.product_id.id,)
            #case 4: Filter on A Pack
            if self.package_id:
                domain_source += ' AND package_id = %s'
                domain_dest += ' AND package_id = %s'
                args += (self.package_id.id,)
            # filter by adjustment_date
            if self.inventory_id.use_adjustment_date:
                domain_source += " AND date < %s AND state='done'"
                domain_dest += " AND date < %s AND state='done'"
                args += (str(self.inventory_id.adjustment_date),)
            
            self.env.cr.execute("""SELECT product_id, sum(product_qty) as product_qty, location_id, company_id, lot_id as prod_lot_id, product_packaging as package_id, partner_id from 
                    (
                    SELECT product_id, sum(product_uom_qty) as product_qty, location_dest_id as location_id, company_id, restrict_lot_id as lot_id, product_packaging, partner_id 
                    FROM stock_move
                    WHERE %s
                    GROUP BY product_id, location_dest_id, company_id, restrict_lot_id, product_packaging, partner_id
                    UNION ALL
                    SELECT product_id, sum(-product_uom_qty) as product_qty, location_id as location_id, company_id,  restrict_lot_id as lot_id, product_packaging, partner_id
                    FROM stock_move
                    WHERE %s
                    GROUP BY product_id, location_id, company_id, restrict_lot_id, product_packaging, partner_id
                    ) 
                    as stock_move
                    GROUP BY product_id, location_id, company_id, lot_id, product_packaging, partner_id"""%(domain_dest, domain_source), args+args)
            product_data = self.env.cr.dictfetchone()
            self.theoretical_qty = product_data and product_data['product_qty'] or 0.0
        else:
            if not self.product_id:
                self.theoretical_qty = 0
                return
            theoretical_qty = sum([x.qty for x in self._get_quants()])
            if theoretical_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
                theoretical_qty = self.product_id.uom_id._compute_quantity(theoretical_qty, self.product_uom_id)
            self.theoretical_qty = theoretical_qty


    def _get_move_values(self, qty, location_id, location_dest_id):
        self.ensure_one()
        res = super(InventoryLine, self)._get_move_values(qty, location_id, location_dest_id)
        res.update({
            'account_id': self.account_id.id,
            'price_unit': self.new_price_unit,
            })
        return res

    # def _fixup_negative_quants(self):
    #     """ This will handle the irreconciable quants created by a force availability followed by a
    #     return. When generating the moves of an inventory line, we look for quants of this line's
    #     product created to compensate a force availability. If there are some and if the quant
    #     which it is propagated from is still in the same location, we move it to the inventory
    #     adjustment location before getting it back. Getting the quantity from the inventory
    #     location will allow the negative quant to be compensated.
    #     """
    #     self.ensure_one()
    #     for quant in self._get_quants().filtered(lambda q: q.propagated_from_id.location_id.id == self.location_id.id):
    #         # send the quantity to the inventory adjustment location
    #         move_out_vals = self._get_move_values(quant.qty, self.location_id.id, self.product_id.property_stock_inventory.id)
    #         move_out = self.env['stock.move'].create(move_out_vals)
    #         self.env['stock.quant'].quants_reserve([(quant, quant.qty)], move_out)
    #         move_out.action_done()

    #         # get back the quantity from the inventory adjustment location
    #         move_in_vals = self._get_move_values(quant.qty, self.product_id.property_stock_inventory.id, self.location_id.id)
    #         move_in = self.env['stock.move'].create(move_in_vals)
    #         move_in.action_done()
    
    def _generate_moves(self):
        moves = self.env['stock.move']
        Quant = self.env['stock.quant']
        for line in self:
            if line.current_price_unit!=line.new_price_unit:
                cost_method = line.product_id.cost_method or line.product_id.categ_id.cost_method
                average_cost_type = line.product_id.average_cost_type or line.product_id.categ_id.average_cost_type
                if cost_method=='average' and average_cost_type=='by_location':
                    line.product_id.with_context(location_id=line.location_id.id).do_change_standard_price(line.new_price_unit, line.account_id.id)
                else:
                    line.product_id.do_change_standard_price(line.new_price_unit, line.account_id.id)

            line._fixup_negative_quants()

            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id)
            move = moves.create(vals)

            if diff > 0:
                domain = [('qty', '>', 0.0), ('package_id', '=', line.package_id.id), ('lot_id', '=', line.prod_lot_id.id), ('location_id', '=', line.location_id.id)]
                preferred_domain_list = [[('reservation_id', '=', False)], [('reservation_id.inventory_id', '!=', line.inventory_id.id)]]
                quants = Quant.quants_get_preferred_domain(move.product_qty, move, domain=domain, preferred_domain_list=preferred_domain_list)
                Quant.quants_reserve(quants, move)
            elif line.package_id:
                move.action_done()
                move.quant_ids.write({'package_id': line.package_id.id})
                quants = Quant.search([('qty', '<', 0.0), ('product_id', '=', move.product_id.id),
                                       ('location_id', '=', move.location_dest_id.id), ('package_id', '!=', False)], limit=1)
                if quants:
                    for quant in move.quant_ids:
                        if quant.location_id.id == move.location_dest_id.id:  #To avoid we take a quant that was reconcile already
                            quant._quant_reconcile_negative(move)
        return moves