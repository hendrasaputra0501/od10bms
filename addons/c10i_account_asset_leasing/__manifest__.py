# -*- coding: utf-8 -*-
{
	'name': 'Assets Management Leasing',
	'depends': ['base','account_asset', 'c10i_base', 'c10i_account_invoice_advance','account','stock','account_voucher'],
	'description': """
		Assets management Leasing
	""",
	'author'    : "Konsalten Indonesia (Consult10 Indonesia)",
	'website'   : "www.consult10indonesia.com",
	'category'  : 'Accounting Asset Leasing',
	'sequence'  : 101,
	'license'   : 'AGPL-3',
	'data': [
		'security/ir.model.access.csv',
		'data/account_asset_leasing_data.xml',
		'wizard/wizard_leasing_views.xml',
		'views/account_asset_leasing_views.xml',
	],
	'installable': True,
	'application': True,
}
