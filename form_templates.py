
formTemplates = [
    {
        'id': "tpl-1",
        'name': "One day congress",
        'description': "Let attendees choose one of two talks running in parallel. Lunch menu too.",
        'structure': [
            {"subtype": "h1", "label": "One day congress<br>", "type": "header"},
            {"subtype": "p", "label": "<div>12th July, all day event<br></div><div>Our meeting point.</div><div>46, Big Street.</div><div>Post code.</div>", "type": "paragraph"},
            {"subtype": "p", "label": "<div>We are holding talks all day on the 12th. We have two conference rooms, and are running the talks in parallel.</div><div><br></div><div>&lt;b&gt;09h - 10h Room 1. Presentation.&lt;/b&gt;<br></div>", "type": "paragraph"},
            {"name": "radio-group-1563733517177",
                "values": [
                    {"label": "Room 1. Municipal Strategies", "value": "strategies"},
                    {"label": "Room 2. Decentralized tech. Freedom of speech", "value": "feedom-speech"}
                ],
                "label": "10h - 12h<br>", "type": "radio-group"},
            {"name": "radio-group-1563733735531",
                "values": [
                    {"label": "Room 1. AI descrimination", "value": "ai-descrimination"},
                    {"label": "Room 2. Build an anonymous web", "value": "anonymous-web"}
                ],
                "label": "12h - 14h<br>", "type": "radio-group"},
            {"name": "radio-group-1563733855827",
                "values": [
                    {"label": "Vegan", "value": "vegan"},
                    {"label": "Vegaterian", "value": "vegaterian"},
                    {"label": "I'm eating else where", "value": "not-eating"}
                ],
                "label": "14h - 15h Lunch", "type": "radio-group"}
        ]
    },
    {
        'id': "tpl-2",
        'name': "Enroll in our Summer courses",
        'description': "Students can enroll in a variety of activities spread out across three days.",
        'structure': [
            {"label": "Summer courses", "subtype": "h1", "type": "header"},
            {"label": "<div><br></div><div>Please enroll here for this year's Summer courses</div><div><br></div>", "subtype": "p", "type": "paragraph"},
            {"values":
                [
                    {"label": "10h - 13h. Neutral networks. A practical presentation of our WIFI installation", "value": "eXO-guifi-net"},
                    {"label": "18h - 20h. GIT for beginners Session 1", "value": "git-session-1"}
                ],
                "label": "Tuesday 25th", "type": "checkbox-group", "name": "checkbox-group-1563572627073"
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
        'name': "Save our shelter",
        'description': "Petition citizen support for your local initiative.",
        'structure': [
            {"type": "header", "subtype": "h1", "label": "Save our shelter"},
            {"type": "paragraph", "subtype": "p", "label": "<div>During the civil war neighbors sought shelter from the aerial bombing. Last year the local Church bought the property and have started demolition to build a new parking lot.</div><div><br></div><div>If you want to save our local heritage, please give your support.</div><div><br> </div>"},
            {"className": "form-control", "name": "text-1563737790717", "type": "text", "required": "true", "label": "ID number", "subtype": "text"},
            {"type": "text", "className": "form-control", "subtype": "email", "name": "text-1563737806028", "label": "Email"},
            {"type": "textarea", "subtype": "textarea", "label": "Comments<br>", "name": "textarea-1563737836394", "className": "form-control"}
        ]
    }
]
