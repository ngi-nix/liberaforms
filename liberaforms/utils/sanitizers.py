"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import re, markdown, html
from unidecode import unidecode
from bs4 import BeautifulSoup

def sanitize_string(string):
    string = unidecode(string)
    string = string.replace(" ", "")
    return re.sub('[^A-Za-z0-9\-\.]', '', string)

def sanitize_slug(slug):
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return sanitize_string(slug)

def sanitize_username(username):
    return sanitize_string(username)

def escape_markdown(MDtext):
    #removes html tags
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', MDtext)

def markdown2HTML(MDtext):
    MDtext=escape_markdown(MDtext)
    return markdown.markdown(MDtext, extensions=['markdown.extensions.nl2br'])

def strip_html_tags(text):
    # removes tags and tag content
    text=html.unescape(text)
    soup=BeautifulSoup(text, features="html.parser")
    return soup.get_text()

def clean_label(text):
    # We should change this to use a whitelist
    text=html.unescape(text)
    soup=BeautifulSoup(text, features="html.parser")
    for script in soup.find_all("script"):
        script.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    return html.escape(str(soup))

def remove_newlines(string):
    string = string.replace("\n", "")
    return string.replace("\r", "")

def remove_first_and_last_newlines(string):
    RE="^[\r\n]+|[\r\n]+$"
    return re.sub(RE, '', string)

def truncate_text(text, truncate_at=155): # 155 recommened opengraph length
    text = text.replace('\n', ' ').strip(' ').replace('  ', ' ')
    if len(text) > truncate_at:
        text = f"{text[0:truncate_at-3]}..."
    return text

"""
def isSaneUsername(username):
    if username and username == sanitize_username(username):
        return True
    return False
"""
"""
def isSaneSlug(slug):
    if slug and slug == sanitize_slug(slug):
        return True
    return False
"""
"""
def sanitizeHexidecimal(string):
    return re.sub('[^A-Fa-f0-9]', '', string)
"""
"""
def sanitizeTokenString(string):
    return re.sub('[^a-z0-9]', '', string)
"""
