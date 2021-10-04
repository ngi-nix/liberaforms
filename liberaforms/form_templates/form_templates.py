"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask_babel import lazy_gettext as _

templates = [
    {
        'id': 1,
        'name': _('One day congress'),
        'description': _("Let attendees choose one of two talks running in parallel and their lunch menu."),
        'introduction_md': _("# Congress II\r\nLast year's congress was such a success we doing it again.\r\n\r\nRegister now for this year's sessions!"),
        'structure': [
            {
                "label": _("10h - 12h"),
                "type": "radio-group", "name": "radio-group-1563733517177",
                "values": [
                    {
                        "label": _("Room 1. Municipal Strategies"),
                        "value": ""
                    },
                    {
                        "label": _("Room 2. Decentralized tech. Freedom of speech"),
                        "value": ""
                    }
                ],
            },
            {
                "label":_("12h - 14h"),
                "type": "radio-group", "name": "radio-group-1563733735531",
                "values": [
                    {
                        "label":_("Room 1. AI descrimination"),
                        "value": ""
                    },
                    {
                        "label":_("Room 2. Build an anonymous website"),
                        "value": ""
                    }
                ],

            },
            {
                "label":_("14h - 15h Lunch"),
                "type": "radio-group", "name": "radio-group-1563733855827",
                "values": [
                    {
                        "label": _("Vegan"),
                        "value": ""
                    },
                    {
                        "label": _("Vegaterian"),
                        "value": ""
                    },
                    {
                        "label": _("I'm eating else where"),
                        "value": ""
                    }
                ],
            }
        ]
    },
    {
        'id': 2,
        'name': _("Summer courses"),
        'description': _("Students can enroll in a variety of activities spread out across three days."),
        'introduction_md': _("# Summer courses\r\n\r\nWe've prepared three days of courses and workshops.\r\n\r\nPlease reserve your place now. First in, first served."),
        'structure': [
            {
                "label": _("Tuesday 25th"),
                "type": "checkbox-group", "name": "checkbox-group-1563572627073",
                "values":[
                    {
                    "label": _("10h - 13h. Neutral networks. A practical presentation of our WIFI installation"),
                    "value": ""
                    },
                    {
                    "label": _("18h - 20h. GIT for beginners Session 1"),
                    "value": ""
                    }
                ]
            },
            {
                "label": "Wednesday 26th",
                "type": "checkbox-group", "name": "checkbox-group-1563697624123",
                "values": [
                    {
                    "label": _("10h - 13h. Presentation/demo. TPV to manage the cafe"),
                    "value": ""
                    },
                    {
                    "label": _("16h - 19h. Social currencies. Local economy"),
                    "value": ""
                    }
                ]
            },
            {
                "label": _("Thursday 27th"),
                "type": "checkbox-group", "name": "checkbox-group-1563698001314",
                "values": [
                    {
                    "label": _("10h - 13h. Computer Lab management with Free software"),
                    "value": ""
                    },
                    {
                    "label": _("18h - 20h. GIT for beginners Session 2"),
                    "value": ""
                    }
                ],

            },
            {
                "label": _("Your name"),
                "className": "form-control", "name": "text-1563692878245",
                "type": "text", "required": True, "subtype": "text"
            },
            {
                "label": _("Your email"),
                "className": "form-control", "name": "text-1563692901766", "type": "text",
                "subtype": "email", "required": True
            }
        ]
    },
    {
        'id': 3,
        'name': _("Save our shelter"),
        'description': _("Petition citizens support for your local initiative."),
        'introduction_md': _('# hello'),
        'structure': [
            {
                "label": _("ID number"),
                "className": "form-control", "name": "text-1563737790717",
                "type": "text", "required": True, "subtype": "text"},
            {
                "label": _("Email"),
                "type": "text", "className": "form-control",
                "subtype": "email", "name": "text-1563737806028"
                },
            {
                "label": _("Comments"),
                "type": "textarea", "subtype": "textarea",
                "name": "textarea-1563737836394", "className": "form-control"
            }
        ]
    },
    {
        'id': 4,
        'name': _("Hotel booking"),
        'description': _("Book a room and come stay with us!"),
        'introduction_md': _("# Hotel booking\r\nCome stay with us! Fill out this form to book a room at our hotel.\r\n\r\nEl Riuet Hotel\r\nCarrer d'Orient, 33\r\nVidreres, 17411, Girona.\r\nCatalunya, Espanya\r\n\r\nPhone number: (+34) 93 553 43 25 \r\n[Website](https://elriuethotel.com)\r\n[Map](https://www.openstreetmap.org/way/218557184)\r\n"),
        'structure': [
            {
                "label": _("Contact information"),
                "subtype":"h2", "type":"header"
            },
            {
                "label":_("Name"),
                "placeholder":_("e.g. Mary"),
                "className":"form-control", "name":"text-1630654621925",
                "required":True, "subtype":"text", "type":"text"
            },
            {
                "label":_("Surname"),
                "placeholder":_("e.g. Poppins"),
                "className":"form-control", "name":"text-1630943188770",
                "required":True, "subtype":"text", "type":"text"
            },
            {
                "label":_("Email"),
                "placeholder":_("e.g. mary@example.com"),
                "className":"form-control", "name":"text-1630655000269",
                "required":True, "subtype":"email", "type":"text"
            },
            {
                "label":_("Telephone number"),
                "placeholder":_("e.g. +34 678 655 333"),
                "className":"form-control", "name":"text-1630937342029",
                "required":False, "subtype":"tel", "type":"text"
            },
            {
                "label":_("Booking information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Type of room"),
                "inline":False, "name":"radio-group-1630943305453", "other":False,
                "required":True, "type":"radio-group",
                "values":[
                    {
                        "label":_("Single bed"),
                        "value":""
                    },
                    {
                        "label":_("Double bed"),
                        "value":""
                    },
                    {
                        "label":_("Double bed + single bed"),
                        "value":""
                    },
                    {
                        "label":_("Shared room (bunk beds with 3 other people)"),
                        "value":""
                    }
                ]},
            {
                "label":_("Date of arrival"),
                "description": _("(check in from 12pm)"),
                "className":"form-control", "name":"date-1630937446951",
                "required":True,"type":"date"
            },
            {
                "label":_("Date for departure"),
                "description":_("(check out 12pm maximum)"),
                "className":"form-control", "name":"date-1630943461719",
                "required":True,"type":"date"
            },
            {
                "label":_("Will you eat at the hotel?"),
                "inline":False,"name":"radio-group-1630943800634",
                "other":False, "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("Full board (breakfast, lunch and dinner)"),
                        "value":""
                    },
                    {
                        "label":_("Just breakfast"),
                        "value":""
                    },
                    {
                        "label":_("Just lunch"),
                        "value":""
                    },
                    {
                        "label":_("Just dinner"),
                        "value":""
                    },
                    {
                        "label":_("Breakfast and lunch"),
                        "value":""
                    },
                    {
                        "label":_("Breakfast and dinner"),
                        "value":""
                    },
                    {
                        "label":_("Lunch and dinner"),
                        "value":""
                    },
                    {
                        "label":_("I'm eating out, thanks for asking"),
                        "value":""
                    }
                ]},
            {
                "label":_("Other information"),
                "subtype":"h2", "type":"header"
            },
            {
                "label":_("Do you want us to send you a reminder?"),
                "inline":False, "name":"radio-group-1630938215269",
                "other":False,"required":False,"type":"radio-group",
                "values":[
                    {
                        "label":_("Yes, by email 5 days before"),
                        "value":""
                    },
                    {
                        "label":_("Yes, by phone 5 days before"),
                        "value":""
                    },
                    {
                        "label":_("No thanks. I will remember."),
                        "value":""
                    }
                 ]
            },
            {
                "label":_("Have a comment?"),
                "placeholder":_("e.g. I've already stayed at your hotel and it's very nice!"),
                "className":"form-control", "name":"textarea-1631016372067",
                "required":False,"subtype":"textarea","type":"textarea"
            }
        ]
    },
    {
        'id': 5,
        'name': _("Activity feedback"),
        'description': _("Ask participants for their feedback about your activity."),
        'introduction_md': _("# Activity Feedback \r\nThank you for participating in this activity. Please share with us your impression so we can improve future activities."),
        'structure': [
            {
                "label":_("Content"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Rate the quality of content"),
                "description":_("Poor to excellent"),
                "inline":True, "name":"radio-group-1631271361249","other":False,
                "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("1"),
                        "value":""
                    },
                    {
                        "label":_("2"),
                        "value":""
                    },
                    {
                        "label":_("3"),
                        "value":""
                    },
                    {
                        "label":_("4"),
                        "value":""
                    },
                    {
                        "label":_("5"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("Comment about the content"),
                "description":_("What did you like? What can we improve?"),
                "placeholder":_("e.g. First session was very interesting although I did expect more information about it."),
                "className":"form-control","name":"textarea-1631271439802",
                "required":False,"rows":5,"subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Tempos"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("You felt that first session was..."),
                "inline":False, "name":"radio-group-1631271743849","other":False,
                "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("Too short"),
                        "value":""
                    },
                    {
                        "label":_("About right"),
                        "value":""
                    },
                    {
                        "label":_("Too long"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("You felt that second session was..."),
                "inline":False,"name":"radio-group-1631272427480","other":False,
                "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("Too short"),
                        "value":""
                    },
                    {
                        "label":_("About right"),
                        "value":""
                    },
                    {
                        "label":_("Too long"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("You felt breaks were..."),
                "inline":False,"name":"radio-group-1631272372930","other":False,
                "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("Too short"),
                        "value":""
                    },
                    {
                        "label":_("About right"),
                        "value":""
                    },
                    {
                        "label":_("Too long"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("Comment about tempos"),
                "description":_("What did you like? What can we improve?"),
                "placeholder":_("e.g. There was no green tea in the coffeebreak."),
                "className":"form-control","name":"textarea-1631273416226","required":False,
                "rows":5,"subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Instructor"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Rate the explainations of the instructor"),
                "inline":True,"name":"radio-group1631273164109","other":False,
                "required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("1"),
                        "value":""
                    },
                    {
                        "label":_("2"),
                        "value":""
                    },
                    {
                        "label":_("3"),
                        "value":""
                    },
                    {
                        "label":_("4"),
                        "value":""
                    },
                    {
                        "label":_("5"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("Comment about instructor"),
                "description":_("What did you like? What can we improve?"),
                "placeholder":_("e.g. I did enjoy both sessions. The instructor was very passionate about the subject."),
                "className":"form-control","name":"textarea-1631273298161","required":False,
                "rows":5,"subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Future activities"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Subjects"),
                "description":_("Tell us if you are interested in a particular subject."),
                "placeholder":_("e.g. GDPR compliance and linguistic justice."),
                "className":"form-control","name":"textarea-1631273992020",
                "required":False,"rows":5,"subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Comments"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Other things you want to express."),
                "placeholder":_("e.g. It was nice in general. Thanks."),
                "className":"form-control","name":"textarea-1631274361198",
                "required":False,"rows":5,"subtype":"textarea","type":"textarea"
            }
        ]
    },
    {
        'id': 6,
        'name': _("Restaurant booking"),
        'description': _("Do you want to taste our delicious food? Save a date in your agenda!"),
        'introduction_md': _("# Restaurant booking\r\nDo you want to taste our delicious food? Fill out this form and save the date in your agenda!  \r\n\r\n[Delicious Restaurant Map](https://www.openstreetmap.org/way/314016327)\r\nCarrer de les Avellanes, 15\r\nEl Sec\u00e0 de Sant Pere, 25005, Lleida.\r\nCatalunya, Espanya\r\n\r\nPhone number: (+34) 93 423 44 44"),
        'structure': [
            {
                "label":_("Contact information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Name or nick"),
                "placeholder":_("e.g. Mary"),
                "className":"form-control", "name":"text-1630654621925","required":True,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Email"),
                "placeholder":_("e.g. mary@exemple.com"),
                "className":"form-control","name":"text-1630655000269","required":True,
                "subtype":"email","type":"text"
            },
            {
                "label":_("Telephone number"),
                "placeholder":_("e.g. +34 678 655 333"),
                "className":"form-control","name":"text-1630937342029","required":False,
                "subtype":"tel","type":"text"
            },
            {
                "label":_("Booking information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("How many people are you?"),
                "description":_("Maximum 10 people per reservation."),
                "className":"form-control", "max":10, "min":1, "name":"number-1630938282328",
                "required":True, "type":"number"
            },
            {
                "label":_("Choose the day you want to come"),
                "description":_("(from Tuesday to Sunday)"),
                "className":"form-control", "name":"date-1630937446951", "required":True, "type":"date"
            },
            {
                "label":_("When do you want to eat"),
                "description":_("remember we only open from 20h30 to 23h30)"),
                "inline":False,"name":"radio-group-1630937627244",
                "other":False,"required":True,"type":"radio-group",
                "values":[
                    {
                        "label":_("20h30"),
                        "value":""
                    },
                    {
                        "label":_("21h"),
                        "value":""
                    },
                    {
                        "label":_("21h30"),
                        "value":""
                    },
                    {
                        "label":_("22h"),
                        "value":""
                    }
                ]
            },
            {
                "label":_("Do you want us to send you a reminder?"),
                "inline":False,"name":"radio-group-1630938215269","other":False,
                "required":False, "type":"radio-group",
                "values":[
                    {
                        "label":_("Yes, by email 3 days before"),
                        "value":""
                    },
                    {
                        "label":_("Yes, by phone 3 days before"),
                        "value":""
                    },
                    {
                        "label":_("No, thanks. I will remember."),
                        "value":""
                    }
                ]
            },
            {
                "label":_("Other information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Have a comment?"),
                "placeholder":_("e.g. I've already been in your restaurant and it's very nice!"),
                "className":"form-control","name":"textarea-1632655788357",
                "required":False,"subtype":"textarea","type":"textarea"
            }
        ]
    },
    {
        'id': 7,
        'name': _("Project Application"),
        'description': _("Apply for a grant. Tell us about your proposal."),
        'introduction_md': _("# Project Application Form\r\nHave a project? Fill out this form to tell us about your proposal. \r\n\r\nThis form is for project applications only. If you have any other question, please use our [contact form](https://example.com/contact-form)."),
        'structure': [
            {
                "label":_("Contact information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Name or nick"),
                "placeholder":_("e.g. Mary"),
                "className":"form-control","name":"text-1630654621925","required":True,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Email"),
                "placeholder":_("e.g. mary@exemple.com"),
                "className":"form-control","name":"text-1630655000269","required":True,
                "subtype":"email","type":"text"
            },
            {
                "label":_("Organization"),
                "description":_("(if any)"),
                "placeholder":_("e.g. Association, cooperative, collective"),
                "className":"form-control","name":"text-1630657091678","required":False,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Country"),
                "placeholder":_("e.g. Spain"),
                "className":"form-control","name":"text-1630767249034","required":False,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Project information"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Project name"),
                "placeholder":_("e.g. FediBook"),
                "className":"form-control","name":"text-1630767175601","required":True,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Website"),
                "placeholder":_("e.g. https://fedi.cat"),
                "className":"form-control","name":"text-1630767003399","required":False,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Project description"),
                "description":_("Explain here your project. Focus on what and how."),
                "placeholder":_("e.g. We want to write a book about the Fediverse."),
                "className":"form-control","name":"textarea-1630767057130","required":True,
                "rows":5,"subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Requested amount"),
                "description":_("up to €5,000"),
                "className":"form-control","max":5000,"name":"number-1630767226789",
                "required":True,"type":"number"
            },
            {
                "label":_("Cost justification"),
                "description":_("Explain what the requested budget will be used for."),
                "placeholder":_("e.g. Buy hardware, hire someone, etc."),
                "className":"form-control","name":"textarea-1630767513362","required":True,
                "subtype":"textarea","type":"textarea"
            },
            {
                "label":_("Attachments"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Add additional information about the project."),
                "className":"form-control","name":"file-1630768136100","required":False,
                "subtype":"file","type":"file"
            },
            {
                "label":_("Add a second file if you wish."),
                "className":"form-control","name":"file-1630769011444","required":False,
                "subtype":"file","type":"file"
            },
            {
                "label":_("Privacy"),
                "subtype":"h2","type":"header"
            },
            {
                "label":_("Your data."),
                "description":_("What should we do if your project is not immediately selected?"),
                "inline":False,"name":"radio-group-1630768294860","other":False,"required":True,
                "type":"radio-group",
                "values":[
                    {
                        "label":_("I allow you to keep the information I submit for future funding opportunities"),
                        "value":""
                    },
                    {
                        "label":_("I want you to erase all information if the project is not selected"),
                        "value":""
                    }
                ]
            }
        ]
    },
    {
        'id': 8,
        'name': _("Contact Form"),
        'description': _("Apply for a grant. Tell us about your proposal."),
        'introduction_md': _("# Contact Form\r\nHave a question? Fill out this contact form and we'll get in touch as soon as possible."),
        'structure': [
            {
                "label":_("Name or nick"),
                "placeholder":_("e.g. Mary"),
                "className":"form-control","name":"text-1630654621925","required":True,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Email"),
                "placeholder":_("e.g. mary@exemple.com"),
                "className":"form-control","name":"text-1630655000269","required":True,
                "subtype":"email","type":"text"
            },
            {
                "label":_("Message"),
                "placeholder":_("e.g. Just to say hello!"),
                "className":"form-control","name":"textarea-1632851405391","required":True,
                "subtype":"textarea","type":"textarea"
            }
        ]
    },
    {
        'id': 9,
        'name': _("Lottery"),
        'description': _("Put your name down to win a prize"),
        'introduction_md': _("# Lottery\r\nWin 5 tickets to the cinema! Answer this form before September 20th."),
        'structure': [
            {
                "label":_("Name or nick"),
                "description":_("How should we call you?"),
                "placeholder":_("e.g. Mary"),
                "className":"form-control","name":"text-1630654621925","required":True,
                "subtype":"text","type":"text"
            },
            {
                "label":_("Email"),
                "description":_("If you win, we'll send you an email!"),
                "placeholder":_("e.g. mary@exemple.com"),
                "className":"form-control","name":"text-1630655000269","required":True,
                "subtype":"email","type":"text"
            },
            {
                "label":_("How did you find out about this lottery?"),
                "inline":False,"name":"radio-group-1630658345634","other":False,"required":False,
                "type":"radio-group",
                "values":[
                    {
                        "label":_("A friend told me"),
                        "value":""
                    },
                    {
                        "label":_("Browsing the Internets"),
                        "value":""
                    },
                    {
                        "label":_("I receive your newletters"),
                        "value":""
                    }
                ]
            }
        ]
    },
]
