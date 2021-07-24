"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import current_app, Blueprint, request, Response, jsonify
from flask_babel import gettext as _
from feedgen.feed import FeedGenerator
from liberaforms.models.site import Site
from liberaforms.models.form import Form
from liberaforms.models.schemas.site import SiteSchema
from liberaforms.models.schemas.form import FormSchema
from liberaforms.utils import utils
from liberaforms.utils import html_parser
from liberaforms.utils.wraps import *

api_bp = Blueprint('api_bp', __name__)


""" Unsensitve site information only
"""
@api_bp.route('/api/site/info', methods=['GET'])
#@enabled_user_required__json
def site_info():
    site=SiteSchema(only=['created',
                          'hostname']).dump(Site.find())
    site['version'] = utils.get_app_version()
    site['timezone'] = current_app.config['DEFAULT_TIMEZONE']
    return jsonify(
        site=site
    ), 200


""" Public available form information only
"""
@api_bp.route('/api/form/<int:form_id>/info', methods=['GET'])
def form_info(form_id):
    form = Form.find(id=form_id)
    if not (form and form.is_public()):
        return jsonify("Denied"), 401
    return jsonify(
        form=FormSchema(only=['slug',
                              'created',
                              'introduction_md',
                              'structure']).dump(form)
    ), 200


""" RSS feed of latest 10 forms. Public information only
    TODO: Move this route somewhere else
"""
@api_bp.route('/feed', methods=['GET'])
@api_bp.route('/feed/<string:feed_type>', methods=['GET'])
def rss_feed(feed_type=None):
    feed_type = feed_type.lower() if feed_type else "rss"
    feed_type = feed_type if feed_type in ['rss', 'atom'] else "rss"
    fg = FeedGenerator()
    title = _("%s %s feed" % (g.site.siteName, feed_type))
    fg.id(f"{g.site.host_url}feed/{feed_type}")
    fg.title(title)
    fg.link(href=g.site.host_url)
    if feed_type == 'rss':
        fg.description(g.site.blurb['html'])
    if feed_type == 'atom':
        fg.description(html_parser.extract_text(g.site.blurb['html'],
                                                with_links=True))
    forms = Form.query.filter_by(enabled=True) \
                .order_by(Form.created.desc()) \
                .paginate(page=1, per_page=10) \
                .items
    for form in forms:
        if not form.is_enabled():
            # disabled by admin
            continue
        feed_entry = fg.add_entry()
        feed_entry.id(form.url)
        feed_entry.pubDate(form.created)
        feed_entry.title(form.slug)
        feed_entry.link(href=form.url)
        if feed_type == 'rss':
            feed_entry.description(form.introductionText['html'])
        if feed_type == 'atom':
            desc = html_parser.extract_text(form.introductionText['html'],
                                            with_links=True)
            feed_entry.description(desc)
    if feed_type == 'rss':
        return Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')
    else:
        return Response(fg.atom_str(pretty=True), mimetype='application/atom+xml')
