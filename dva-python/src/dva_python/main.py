from sys import stderr

import structlog
from structlog import make_filtering_bound_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import TimeStamper, StackInfoRenderer, JSONRenderer
from structlog.stdlib import add_log_level

import dva_python.msgconsumer
import dva_python.config


def main():
    setup_logging()
    dva_python.msgconsumer.run()


def setup_logging():
    shared_processors = [
        add_log_level,
        StackInfoRenderer(),
        TimeStamper(fmt='iso'),
    ]
    if stderr.isatty():
        processors = shared_processors + [ConsoleRenderer()]
    else:
        processors = shared_processors + [JSONRenderer()]

    logger = structlog.get_logger()
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(
            dva_python.config.LOG_LEVEL
        ),
    )


if __name__ == '__main__':
    main()
