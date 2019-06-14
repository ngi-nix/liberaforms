from formbuilder import app
from unidecode import unidecode
import re


def sanitizeSlug(slug):
    if slug in app.config['RESERVED_SLUGS']:
        return None
    slug = unidecode(slug)
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return re.sub('[^A-Za-z0-9\-]', '', slug)
    
    p = re.compile(r"(\b[-']\b)|[\W_]")
    return p.sub(lambda m: (m.group(1) if m.group(1) else " "), slug)
