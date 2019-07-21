
formTemplates = [
    {
        'id': "form-one",
        'structure': [
            {"type": "header", "label": "T\u00edtulo", "subtype": "h1"},
            {"type": "paragraph", "label": "P\u00e1rrafo", "subtype": "p"},
            {"type": "radio-group", "label": "Grupo de Selecci\u00f3n", "name": "radio-group-1562689002158",
                            "values": [
                                    {"value": "option-1", "label": "Option 1"},
                                    {"value": "option-2", "label": "Option 2"},
                                    {"value": "option-3", "label": "Option 3"}]},
            {"className": "form-control", "type": "date", "label": "Campo de Fecha", "name": "date-1562689003596"}]
    },
    {
        'id': "form-two",
        'name': "2. this is the name",
        'description': "This is the description",
        'structure': [
            {"type": "header", "label": "T\u00edtulo", "subtype": "h1"},
            {"type": "paragraph", "label": "P\u00e1rrafo", "subtype": "p"},
            {"type": "radio-group", "label": "Grupo de Selecci\u00f3n", "values": [{"value": "option-1", "label": "Option 1"}, {"value": "option-2", "label": "Option 2"}, {"value": "option-3", "label": "Option 3"}], "name": "radio-group-1562689002158"},
            {"className": "form-control", "type": "date", "label": "Campo de Fecha", "name": "date-1562689003596"}]
    } ,
    {
        'id': "form-three",
        'name': "Enroll summer courses",
        'description': "Enroll summer courses",
        'structure': [
            {"label": "Summer courses<br>", "subtype": "h1", "type": "header"},
            {"label": "<div><br></div><div>Please enroll here for this year's Summer courses</div><div><br></div>", "subtype": "p", "type": "paragraph"},
            {"values":
                [
                    {"label": "10h - 13h. Neutral networks. Presentation of the WIFI installation at the Lleialtat", "value": "eXO-guifi"},
                    {"label": "18h - 20h. GIT for beginners Session 1", "value": "git-session-1"}
                ],
                "label": "<div>Tuesday 25th</div>", "type": "checkbox-group", "name": "checkbox-group-1563572627073"
            },
            {"values":
                [
                    {"label": "10h - 13h. Presentation/demo. TPV to manage the caf\u00e9", "value": "tpv-cafe"},
                    {"label": "16h - 19h. Social currencies. Local economy", "value": "local-economy"}
                ],
                "label": "<div>Wednesday 26th</div>", "type": "checkbox-group", "name": "checkbox-group-1563697624123"
            },
            {"values":
                [
                    {"label": "10h - 13h. Computer Lab management with Free software", "value": "fog-project"},
                    {"label": "18h - 20h. GIT for beginners Session 2", "value": "git-session-2"}
                ],
                "label": "<div>Thursday 27th</div>", "type": "checkbox-group", "name": "checkbox-group-1563698001314"
            },
            {"className": "form-control", "name": "text-1563692878245", "type": "text", "required": "true", "label": "Your name<br>", "subtype": "text"},
            {"className": "form-control", "name": "text-1563692901766", "type": "text", "subtype": "email", "label": "Your email<br>", "required": "true"}
        ]
    }
]
