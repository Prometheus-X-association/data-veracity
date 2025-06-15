import plac
import uvicorn

import dva_python.config
import dva_python.log
import dva_python.msgconsumer
import dva_python.dryrun


@plac.flg(
    "dry_run",
    help="Dry run: works standalone and does not actually send any messages",
    abbrev="n",
)
def main(dry_run=False):
    dva_python.config.cfg.dry_run = dry_run
    dva_python.log.setup_logging()

    if dry_run:
        logger = dva_python.log.get_logger()
        logger.warning(
            "Dry run mode! Running uvicorn/FastAPI w/o actual processing effects"
        )

        uvicorn.run(
            dva_python.dryrun.app, host="127.0.0.1", port=5000, log_level="info"
        )
    else:
        dva_python.msgconsumer.run()


if __name__ == "__main__":
    plac.call(main)
