# -*- coding: utf-8 -*-
{
    'name': "Office Rental Management Module",

    'summary': """
        Office Rental Management Module""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Konsaltén Indonesia (Consult10 Indonesia)",
    'website': "www.consult10indonesia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['c10i_base', 'c10i_bm','sale','product'],

    # always loaded
    'data': [
        'security/rent_security.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_orent_tuition_bill_views.xml',
        'wizard/wizard_orent_rental_bill_views.xml',
        # 'views/bm_owner_views.xml',
        'views/office_rent_order_views.xml',
        'views/office_rent_unit_tenancy_views.xml',
        'views/office_rent_unit_views.xml',
        'views/menu_items.xml',
    ],
    'application': True,
}