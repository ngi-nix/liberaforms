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
import os
from logging.config import dictConfig

if not "LOG_TYPE" in os.environ:
    if  os.environ["FLASK_CONFIG"] == "development" or \
        os.environ["FLASK_ENV"] == "development":
        os.environ["LOG_TYPE"] = "stream"
        os.environ["LOG_LEVEL"] = "DEBUG"
    else:
        os.environ["LOG_TYPE"] = "watched"
if not "LOG_LEVEL" in os.environ:
    os.environ["LOG_LEVEL"] = "INFO"
log_type = os.environ["LOG_TYPE"]
logging_level = os.environ["LOG_LEVEL"]

if not "LOG_DIR" in os.environ:
    os.environ["LOG_DIR"] = "logs"
if "FQDN" in os.environ:
    os.environ["LOG_DIR"] = os.path.join(os.environ["LOG_DIR"], "hosts", os.environ["FQDN"])
log_directory = os.environ["LOG_DIR"]
if not os.path.isdir(log_directory):
    os.makedirs(log_directory)

if log_type != "stream":
    app_log_file_name = "app.log"
    www_log_file_name = "www.log"
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
