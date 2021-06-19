"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
# https://docs.python.org/3/howto/logging.html
# https://medium.com/tenable-techblog/the-boring-stuff-flask-logging-21c3a5dd0392
# https://github.com/tenable/flask-logging-demo/tree/master/app_factory_pattern

# CRITICAL:50 <- ERROR:40 <- WARNING:30 <- INFO:20 <- DEBUG:10

#from flask.logging import default_handler
from logging.config import dictConfig


class LogSetup(object):
    def __init__(self, app=None, **kwargs):
        if app is not None:
            #app.logger.removeHandler(default_handler)
            self.init_app(app, **kwargs)

    def init_app(self, app):
        log_type = app.config["LOG_TYPE"]
        logging_level = app.config["LOG_LEVEL"]
        if log_type != "stream":
            try:
                log_directory = app.config["LOG_DIR"]
                app_log_file_name = "app.log"
                www_log_file_name = "www.log"
            except KeyError as e:
                print(f"{e} is a required parameter for log_type '{log_type}'")
                exit(code=f"{e} is a required parameter for log_type '{log_type}'")
            app_log = "/".join([log_directory, app_log_file_name])
            www_log = "/".join([log_directory, www_log_file_name])

        if log_type == "stream":
            logging_policy = "logging.StreamHandler"
        elif log_type == "watched":
            logging_policy = "logging.handlers.WatchedFileHandler"
        else:
            print(f"'{log_type}' is not a supported LOG_TYPE, check your .env")
            exit(code="Not a supported log_type")
        std_format = {
            "formatters": {
                "default": {
                    "format": "[%(asctime)s.%(msecs)03d] %(levelname)s %(module)s:%(funcName)s: %(message)s",
                    "datefmt": "%d/%b/%Y:%H:%M:%S",
                },
                "access": {"format": "%(message)s"},
            }
        }
        std_logger = {
            "loggers": {
                "": {"level": logging_level, "handlers": ["default"], "propagate": True},
                "app.access": {
                    "level": logging_level,
                    "handlers": ["access_logs"],
                    "propagate": False,
                },
                "gunicorn": {"level": logging_level, "handlers": ["default"]},
                "root": {"level": logging_level, "handlers": ["default"]},
            }
        }
        if log_type == "stream":
            logging_handler = {
                "handlers": {
                    "default": {
                        "level": logging_level,
                        "formatter": "default",
                        "class": logging_policy,
                    },
                    "access_logs": {
                        "level": logging_level,
                        "class": logging_policy,
                        "formatter": "access",
                    },
                }
            }
        elif log_type == "watched":
            logging_handler = {
                "handlers": {
                    "default": {
                        "level": logging_level,
                        "class": logging_policy,
                        "filename": app_log,
                        "formatter": "default",
                        "delay": True,
                    },
                    "access_logs": {
                        "level": logging_level,
                        "class": logging_policy,
                        "filename": www_log,
                        "formatter": "access",
                        "delay": True,
                    },
                }
            }
        log_config = {
            "version": 1,
            "formatters": std_format["formatters"],
            "loggers": std_logger["loggers"],
            "handlers": logging_handler["handlers"],
        }
        dictConfig(log_config)
