# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.konsaltenindonesia.com>
#   @author Chaidar Aji Nugroho <chaidaraji@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

{
    'name': 'Employee Advance & Settelement v2',
    'depends': ['c10i_base', 'c10i_hr', 'account', 'c10i_employee_advance','account_voucher'],
    'description': """
    Menu ini merupakan pengembangan dari c10i_employee_advance. menambahkan fungsi untuk menggabungkan beberapa employee
    advance menjadi satu settlement advance
    """,
    'author'    : "Konsaltén Indonesia (Consult10 Indonesia)",
    'website'   : "www.konsaltenindonesia.com",
    'category'  : 'Accounting',
    'sequence'  : 32,
    'license'   : 'AGPL-3',
    'data': [
            'views/settlement_advance_views.xml',
    ],
    'installable': True,
    'application': True,
}