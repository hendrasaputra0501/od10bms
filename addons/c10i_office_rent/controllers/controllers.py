# -*- coding: utf-8 -*-
from odoo import http

# class C10iBm(http.Controller):
#     @http.route('/c10i_bm/c10i_bm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/c10i_bm/c10i_bm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('c10i_bm.listing', {
#             'root': '/c10i_bm/c10i_bm',
#             'objects': http.request.env['c10i_bm.c10i_bm'].search([]),
#         })

#     @http.route('/c10i_bm/c10i_bm/objects/<model("c10i_bm.c10i_bm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('c10i_bm.object', {
#             'object': obj
#         })