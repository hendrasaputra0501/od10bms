# -*- coding: utf-8 -*-
{
    'name': "Approval Notification for BMS",

    'summary': """
        BMS Approval Notification""",

    'description': """
        Document Approval Notification for BMS
    """,

    'author': "Konsaltén Indonesia",
    'website': "http://www.kosaltenindonesia.com",
    'license'   : 'AGPL-3',

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'bms_purchase', 'c10i_document_type'],

    'data': [
        'security/ir.model.access.csv',
        'data/po_approval_notification_scheduler_1.xml',
        'data/po_approval_notification_scheduler_2.xml',
        'data/po_approver_notification_email_template.xml',
        'data/po_user_notification_approved_direktur_email_template.xml',
        'data/po_user_notification_approved_manager_email_template.xml',
        'data/po_user_notification_rejected_email_template.xml',
        'views/approval_notification_views.xml',
    ],
    'installable': True,
    'application': True,
}