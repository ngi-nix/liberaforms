from formbuilder import app
from flask import flash, request
import string, random

import pprint


def smtpSendConfirmEmail(user):
    print(user.email)
    print("%suser/validate-email/%s" % (request.url_root, user.token['token']))
