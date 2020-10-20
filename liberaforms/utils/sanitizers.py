"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re, markdown, html
from unidecode import unidecode
from bs4 import BeautifulSoup

def sanitizeString(string):
    string = unidecode(string)
    string = string.replace(" ", "") 
    return re.sub('[^A-Za-z0-9\-]', '', string)

def sanitizeSlug(slug):
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return sanitizeString(slug)

def sanitizeUsername(username):
    return sanitizeString(username)
    
def escapeMarkdown(MDtext):
    #removed html tags
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', MDtext)

def markdown2HTML(MDtext):
    MDtext=escapeMarkdown(MDtext)
    return markdown.markdown(MDtext, extensions=['nl2br'])

def stripHTMLTags(text):
    # removes tags and tag content
    text=html.unescape(text) 
    soup=BeautifulSoup(text, features="html.parser")
    return soup.get_text()
    
def cleanLabel(text):
    # We should change this to use a whitelist
    text=html.unescape(text) 
    soup=BeautifulSoup(text, features="html.parser")
    for script in soup.find_all("script"):
        script.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    return html.escape(str(soup))

def removeNewLines(string):
    string = string.replace("\n", "")
    return string.replace("\r", "")
    
def removeFirstAndLastNewLines(string):
    RE="^[\r\n]+|[\r\n]+$"
    return re.sub(RE, '', string)


"""
def isSaneUsername(username):
    if username and username == sanitizeUsername(username):
        return True
    return False
"""
"""
def isSaneSlug(slug):
    if slug and slug == sanitizeSlug(slug):
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
