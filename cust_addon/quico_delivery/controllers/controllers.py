# -*- coding: utf-8 -*-
# from odoo import http


# class QuicoDelivery(http.Controller):
#     @http.route('/quico_delivery/quico_delivery', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quico_delivery/quico_delivery/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('quico_delivery.listing', {
#             'root': '/quico_delivery/quico_delivery',
#             'objects': http.request.env['quico_delivery.quico_delivery'].search([]),
#         })

#     @http.route('/quico_delivery/quico_delivery/objects/<model("quico_delivery.quico_delivery"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quico_delivery.object', {
#             'object': obj
#         })
