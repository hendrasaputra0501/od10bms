# -*- coding: utf-8 -*-
from odoo import http

# class BmsAccount(http.Controller):
#     @http.route('/bms_account/bms_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_account/bms_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_account.listing', {
#             'root': '/bms_account/bms_account',
#             'objects': http.request.env['bms_account.bms_account'].search([]),
#         })

#     @http.route('/bms_account/bms_account/objects/<model("bms_account.bms_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_account.object', {
#             'object': obj
#         })