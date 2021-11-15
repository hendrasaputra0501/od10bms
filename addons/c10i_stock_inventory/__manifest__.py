# -*- coding: utf-8 -*-
{
	'name': 'Inventory Management - Inventory Adjustments By Date',
	'depends': ['base','c10i_base','stock','c10i_stock','account','stock_account','c10i_stock_account'],
	'description': """
		Inventory Adjustment By Date
	""",
	'author'    : "Konsalten Indonesia (Consult10 Indonesia)",
	'website'   : "www.consult10indonesia.com",
	'category'  : 'Warehouse',
	'license'   : 'AGPL-3',
	'data': [
		'views/adjustments_advance_views.xml',
	],
	'installable': True,
	'application': False,
}
