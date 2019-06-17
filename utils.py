from formbuilder import app
from unidecode import unidecode
import re, string, random


def sanitizeSlug(slug):
    if slug in app.config['RESERVED_SLUGS']:
        return None
    slug = unidecode(slug)
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return re.sub('[^A-Za-z0-9\-]', '', slug)
    
    p = re.compile(r"(\b[-']\b)|[\W_]")
    return p.sub(lambda m: (m.group(1) if m.group(1) else " "), slug)


def getRandomString(length=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def getFieldByNameInIndex(index, name):
    print(name)
    l = list(filter(lambda field: field['name'] == name, index))
    if l:
        return l[0]
    return None
