import threading

import plac
import uvicorn

import dva_processing.config
import dva_processing.http
import dva_processing.log


@plac.flg(
    "verbose",
    help="Be more verbose (INFO loglevel)",
    abbrev="v",
)
@plac.flg(
    "debug",
    help="Enable DEBUG log verbosity",
    abbrev="d",
)
@plac.flg(
    "no_http",
    help="Do not start the HTTP server",
    abbrev="H",
)
def main(verbose=False, debug=False, no_http=False):
    if debug:
        dva_processing.config.cfg.log_level = "debug"
    elif verbose:
        dva_processing.config.cfg.log_level = "info"
    dva_processing.log.setup_logging()
    logger = dva_processing.log.get_logger()

    threads = []

    if not no_http:
        http_thread = threading.Thread(
            target=uvicorn.run,
            args=(dva_processing.http.app,),
            kwargs=dict(host="0.0.0.0", port=5000, log_level="info"),
            daemon=True,
        )
        threads.append(http_thread)
    else:
        logger.info("HTTP server disabled in CLI options")

    for t in threads:
        t.start()
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Exiting due to keyboard interrupt")


def cli():
    plac.call(main)


if __name__ == "__main__":
    cli()
