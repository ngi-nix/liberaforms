"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask_babel import lazy_gettext as _

templates = [
    {
        'id': 1,
        'name': _('One day congress'),
        'description': "Let attendees choose one of two talks running in parallel. They will also select their lunch menu.",
        'introduction_md': _('# hello\none two three'),
        'structure': [
            {"name": "radio-group-1563733517177",
                "values": [
                    {"label": _("Room 1. Municipal Strategies"), "value": "strategies"},
                    {"label": _("Room 2. Decentralized tech. Freedom of speech"), "value": "feedom-speech"}
                ],
                "label": "10h - 12h", "type": "radio-group"},
            {"name": "radio-group-1563733735531",
                "values": [
                    {"label": "Room 1. AI descrimination", "value": "ai-descrimination"},
                    {"label": "Room 2. Build an anonymous web", "value": "anonymous-web"}
                ],
                "label": "12h - 14h", "type": "radio-group"},
            {"name": "radio-group-1563733855827",
                "values": [
                    {"label": _("Vegan"), "value": "vegan"},
                    {"label": _("Vegaterian"), "value": "vegaterian"},
                    {"label": _("I'm eating else where"), "value": "not-eating"}
                ],
                "label": "14h - 15h Lunch", "type": "radio-group"}
        ]
    },
    {
        'id': 2,
        'name': _("Summer courses"),
        'description': _("Students can enroll in a variety of activities spread out across three days."),
        'introduction_md': _('# hello'),
        'structure': [
            {"values":
                [
                    {"label": "10h - 13h. Neutral networks. A practical presentation of our WIFI installation", "value": "eXO-guifi-net"},
                    {"label": "18h - 20h. GIT for beginners Session 1", "value": "git-session-1"}
                ],
                "label": _("Tuesday 25th"), "type": "checkbox-group", "name": "checkbox-group-1563572627073"
            },
            {"values":
                [
                    {"label": "10h - 13h. Presentation/demo. TPV to manage the cafe", "value": "tpv-cafe"},
                    {"label": "16h - 19h. Social currencies. Local economy", "value": "local-economy"}
                ],
                "label": "Wednesday 26th", "type": "checkbox-group", "name": "checkbox-group-1563697624123"
            },
            {"values":
                [
                    {"label": "10h - 13h. Computer Lab management with Free software", "value": "fog-project"},
                    {"label": "18h - 20h. GIT for beginners Session 2", "value": "git-session-2"}
                ],
                "label": "Thursday 27th", "type": "checkbox-group", "name": "checkbox-group-1563698001314"
            },
            {"className": "form-control", "name": "text-1563692878245", "type": "text", "required": "true", "label": "Your name", "subtype": "text"},
            {"className": "form-control", "name": "text-1563692901766", "type": "text", "subtype": "email", "label": "Your email", "required": "true"}
        ]
    },
    {
        'id': 3,
        'name': _("Save our shelter"),
        'description': _("Petition citizen support for your local initiative."),
        'introduction_md': _('# hello'),
        'structure': [
            {"className": "form-control", "name": "text-1563737790717", "type": "text", "required": "true", "label": _("ID number"), "subtype": "text"},
            {"type": "text", "className": "form-control", "subtype": "email", "name": "text-1563737806028", "label": _("Email")},
            {"type": "textarea", "subtype": "textarea", "label": _("Comments"), "name": "textarea-1563737836394", "className": "form-control"}
        ]
    }
]
