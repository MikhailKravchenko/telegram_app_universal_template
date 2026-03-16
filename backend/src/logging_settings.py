LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s %(pathname)s %(lineno)s %(funcName)s | %(message)s",
        },
        "system": {
            "format": "%(asctime)s %(levelname)s | %(message)s",
        },
        "security": {
            "format": "%(asctime)s %(levelname)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "system": {
            "class": "logging.StreamHandler",
            "formatter": "system",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "console",
            "filename": "logs/web.log",
            "maxBytes": 1024 * 1024 * 100,
            "backupCount": 10,
        },
        "system_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "system",
            "filename": "logs/web.log",
            "maxBytes": 1024 * 1024 * 100,
            "backupCount": 10,
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "security",
            "filename": "logs/security.log",
            "maxBytes": 1024 * 1024 * 50,
            "backupCount": 20,
        },
        "security_console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "security",
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["file", "console"],
        },
        "django.server": {
            "level": "WARNING",
            "handlers": ["system_file", "system"],
        },
        "security": {
            "level": "INFO",
            "handlers": ["security_file", "security_console"],
            "propagate": False,
        },
    },
}
