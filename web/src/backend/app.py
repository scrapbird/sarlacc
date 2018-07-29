import os
import asyncio
from quart import Quart
from configparser import ConfigParser
import logging

import storage
from mails import blueprint as mails_blueprint


logger = logging.getLogger()


def main():
    # Read config
    config = ConfigParser()
    config.readfp(open(os.path.dirname(os.path.abspath(__file__)) + "/web.cfg.default"))
    config.read(["web.cfg",])

    # Configure the logger
    logging.basicConfig(level=getattr(logging, config["logging"]["log_level"].upper()),
            format="%(levelname)s: %(asctime)s %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p")

    loop = asyncio.get_event_loop()

    app = Quart(__name__, static_url_path="")
    app.sarlacc_config = config


    @app.before_first_request
    async def init_store():
        # Init storage handlers
        app.store = await storage.create_storage(config, loop)


    app.register_blueprint(mails_blueprint)

    app.run(host=config["web"]["host"], port=config["web"]["port"], loop=loop, debug=True)


if __name__ == "__main__":
    main()
