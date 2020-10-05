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

from flask_babel import lazy_gettext as _
 

formTemplates = [
    {
        'id': "tpl-1",
        'name': _('One day congress'),
        'description': "Let attendees choose one of two talks running in parallel. They will also select their lunch menu.",
        'structure': [
            {"subtype": "h1", "label": _('One day congress'), "type": "header"},
            {"subtype": "p", "label": "<div>12th July, all day event<br></div><div>Our meeting point.</div><div>46, Big Street.</div><div>Post code.</div>", "type": "paragraph"},
            {"subtype": "p", "label": "<div>We are holding talks all day on the 12th. We have two conference rooms, and are running the talks in parallel.</div><div><br></div><div>&lt;b&gt;09h - 10h Room 1. Presentation.&lt;/b&gt;<br></div>", "type": "paragraph"},
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
        'id': "tpl-2",
        'name': _("Summer courses"),
        'description': _("Students can enroll in a variety of activities spread out across three days."),
        'structure': [
            {"label": _("Summer courses"), "subtype": "h1", "type": "header"},
            {"label": "<div><br></div><div>Please enroll here for this year's Summer courses</div><div><br></div>", "subtype": "p", "type": "paragraph"},
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
        'id': "tpl-3",
        'name': _("Save our shelter"),
        'description': _("Petition citizen support for your local initiative."),
        'structure': [
            {"type": "header", "subtype": "h1", "label": _("Save our shelter")},
            {"type": "paragraph", "subtype": "p", "label": "<div>During the civil war neighbors sought shelter from the aerial bombing. Some time ago the local Church purchased the property and have recently started demolition to build a new parking lot.</div><div><br></div><div>If you want to save our local heritage, please give your support.</div><div><br> </div>"},
            {"className": "form-control", "name": "text-1563737790717", "type": "text", "required": "true", "label": _("ID number"), "subtype": "text"},
            {"type": "text", "className": "form-control", "subtype": "email", "name": "text-1563737806028", "label": _("Email")},
            {"type": "textarea", "subtype": "textarea", "label": _("Comments"), "name": "textarea-1563737836394", "className": "form-control"}
        ]
    }
]
