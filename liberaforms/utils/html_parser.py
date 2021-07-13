"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

#import html
from bs4 import BeautifulSoup


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
