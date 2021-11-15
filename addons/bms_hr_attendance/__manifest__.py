# -*- coding: utf-8 -*-
{
    'name'      : "HR Attendance Module for Bumi Maju Sawit",
    'category'  : 'Palm Oil Mills',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.kosaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'c10i_base', 'c10i_hr_attendance', 'c10i_hr_attendance_palm_oil','report_xlsx'],
    'summary'   : """
                        BMS HR Attendance Module
                    """,
    'description'   : """
                        Customize Modul hr attendance BMS
                    """,
    'data': [
        'views/hr_attendance_import_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_views.xml',
        'views/hr_payroll_views.xml',
        'views/hr_rapel_views.xml',
        'security/hr_operation_type_rule.xml',
        'security/ir.model.access.csv',
    ],

    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
