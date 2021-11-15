# -*- coding: utf-8 -*-
{
    'name'      : "Stock Module for Bumi Maju Sawit",
    'category'  : 'Palm Oil Mills',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.kosaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'stock', 'c10i_stock', 'c10i_stock_issue_product', 'report'],
    'summary'   : """
                        BMS Stock Module
                    """,
    'description'   : """
                        Customize Modul Stock BMS
                    """,

    'data': [
        'views/stock_picking.xml',
        # 'report/report_stockpicking_operations.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
