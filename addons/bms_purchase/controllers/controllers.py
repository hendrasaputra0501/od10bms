# -*- coding: utf-8 -*-
from odoo import http

# class BmsPurchase(http.Controller):
#     @http.route('/bms_purchase/bms_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_purchase/bms_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_purchase.listing', {
#             'root': '/bms_purchase/bms_purchase',
#             'objects': http.request.env['bms_purchase.bms_purchase'].search([]),
#         })

#     @http.route('/bms_purchase/bms_purchase/objects/<model("bms_purchase.bms_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_purchase.object', {
#             'object': obj
#         })