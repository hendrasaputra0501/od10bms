# -*- coding: utf-8 -*-
{
    'name': "Weighbridge on Server",

    'summary': """
        This module was created to Synchronize Data on Weighbridge Device to Odoo Server""",

    'description': """
    """,

    'author': "Hendra Saputra <hendrasaputra0501@gmail.com>",
    'website': "http://www.konsaltenindonesia.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','sale','purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        
        'views/partner_views.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        
        'views/weighbridge_views.xml',
        'views/menuitems.xml',
    ],
}