"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

#import html
from bs4 import BeautifulSoup
from liberaforms.utils import sanitizers


def extract_text(html, with_links=False):
    soup = BeautifulSoup(html, features="lxml")
    if with_links:
        links = soup.findAll('a')
        for link in links:
            new_tag = soup.new_tag('span')
            new_tag.string = link.get('href')
            link.replace_with(new_tag)
    return soup.get_text()

def extract_images_src(html):
    soup = BeautifulSoup(html, features="lxml")
    images = soup.findAll('img')
    sources = []
    if images:
        for image in images:
            sources.append(image.get('src'))
    return sources

def get_short_text(html, truncate_at=155):
    text = extract_text(html, with_links=False).strip('\n')
    text = sanitizers.truncate_text(text, truncate_at=truncate_at)
    return text.strip('\n').strip(' ')

def get_opengraph_text(html):
    return get_short_text(html, truncate_at=155).replace('\n', ' ').replace('  ', ' ')
