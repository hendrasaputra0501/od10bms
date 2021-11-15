# -*- coding: utf-8 -*-
from odoo import http

# class BmsApprovalNotification(http.Controller):
#     @http.route('/bms_approval_notification/bms_approval_notification/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_approval_notification/bms_approval_notification/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_approval_notification.listing', {
#             'root': '/bms_approval_notification/bms_approval_notification',
#             'objects': http.request.env['bms_approval_notification.bms_approval_notification'].search([]),
#         })

#     @http.route('/bms_approval_notification/bms_approval_notification/objects/<model("bms_approval_notification.bms_approval_notification"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_approval_notification.object', {
#             'object': obj
#         })