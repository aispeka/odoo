# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import werkzeug

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)

MAPPED_RATES = {
    1: 1,
    5: 3,
    10: 5,
}

class Rating(http.Controller):

    @http.route('/rate/<string:token>/<int:rate>', type='http', auth="public", website=True)
    def action_open_rating(self, token, rate, **kwargs):
        if rate not in (1, 3, 5):
            raise ValueError(_("Incorrect rating: should be 1, 3 or 5 (received %d)"), rate)

        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return werkzeug.exceptions.Forbidden()

        record_sudo = request.env[rating.res_model].sudo().browse(rating.res_id)
        if not record_sudo.exists():
            return werkzeug.exceptions.Forbidden()

        rating.write({'rating': rate, 'consumed': True})

        lang = rating.partner_id.lang or get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('rating.rating_external_page_submit', {
            'rating': rating,
            'token': token,
            'rate_names': {
                5: _("Satisfied"),
                3: _("Okay"),
                1: _("Dissatisfied"),
            },
            'rate': rate,
        })

    @http.route(['/rate/<string:token>/submit_feedback'], type="http", auth="public", methods=['post', 'get'], website=True)
    def action_submit_rating(self, token, rate=0, **kwargs):

        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return werkzeug.exceptions.Forbidden()

        record_sudo = request.env[rating.res_model].sudo().browse(rating.res_id)
        if not record_sudo.exists():
            return werkzeug.exceptions.Forbidden()

        if request.httprequest.method == "POST":
            rate = int(rate)
            if rate not in (1, 3, 5):
                raise ValueError(_("Incorrect rating: should be 1, 3 or 5 (received %d)"), rate)
            record_sudo.rating_apply(rate,
                                     rating=rating,
                                     feedback=kwargs.get('feedback'),
                                     subtype_xmlid=None,  # force default subtype choice
                                     )

        lang = rating.partner_id.lang or get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('rating.rating_external_page_view', {
            'web_base_url': rating.get_base_url(),
            'rating': rating,
        })
