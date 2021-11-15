# -*- coding: utf-8 -*-
{
    'name': "Building Management Module of Consult10 Indonesia",

    'summary': """
        Building Management Module""",

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
    'depends': ['base', 'c10i_base','product','account'],

    # always loaded
    'data': [
        'security/bm_security.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_scsf_bill_views.xml',
        'wizard/wizard_utility_bill_views.xml',
        'views/bm_owner_views.xml',
        'views/bm_unit_views.xml',
        'views/bm_config_views.xml',
        'views/bm_unit_tenancy_views.xml',
        'views/bm_tower_views.xml',
        'views/bm_floor_views.xml',
        'views/bm_tuition_views.xml',
        'views/bm_electricity_usage_views.xml',
        'views/bm_water_usage_views.xml',
        'views/bm_utility_entry_views.xml',
        'views/menu_items.xml',
    ],
    'application': True,
}