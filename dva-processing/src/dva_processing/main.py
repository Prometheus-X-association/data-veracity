import plac
import uvicorn

import dva_processing.config
import dva_processing.log
import dva_processing.msgconsumer
import dva_processing.dryrun


@plac.flg(
    "dry_run",
    help="Dry run: works standalone and does not actually send any messages",
    abbrev="n",
)
def main(dry_run=False):
    dva_processing.config.cfg.dry_run = dry_run
    dva_processing.log.setup_logging()

    if dry_run:
        logger = dva_processing.log.get_logger()
        logger.warning(
            "Dry run mode! Running uvicorn/FastAPI w/o actual processing effects"
        )

        uvicorn.run(
            dva_processing.dryrun.app, host="127.0.0.1", port=5000, log_level="info"
        )
    else:
        dva_processing.msgconsumer.run()


if __name__ == "__main__":
    plac.call(main)
