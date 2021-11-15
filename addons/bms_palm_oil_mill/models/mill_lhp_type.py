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

class MillLhpType(models.Model):
	_name = "mill.lhp.type"
	_description = "Laporan Harian Produksi Type"

	name = fields.Char(string="Name")
	location_id = fields.Many2one("stock.location", string="Source Location", domain=[('usage','=', 'internal')])
	location_dest_id = fields.Many2one("stock.location", string="Destination Location", domain=[('usage','=', 'internal')])
	product_tbs_id = fields.Many2one("product.product", string="Product TBS")
	product_cpo_id = fields.Many2one("product.product", string="Product CPO")
	product_kernel_id = fields.Many2one("product.product", string="Product Kernel")