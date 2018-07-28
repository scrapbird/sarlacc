import os
from quart import Quart
from configparser import ConfigParser
import storage
import logging


logger = logging.getLogger()
app = Quart(__name__, static_url_path="")


# @app.route("/api/hello")
# async def hello():
#     return "Testing. Hello World! I have been seen {} times.\n"


@app.route("/")
async def index():
    return await app.send_static_file("index.html")


def main():
    # Read config
    config = ConfigParser()
    config.readfp(open(os.path.dirname(os.path.abspath(__file__)) + "/web.cfg.default"))
    config.read(["web.cfg",])

    # Configure the logger
    logging.basicConfig(level=getattr(logging, config["logging"]["log_level"].upper()),
            format="%(levelname)s: %(asctime)s %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p")

    app.run(host=config["web"]["host"], port=config["web"]["port"], debug=True)


if __name__ == "__main__":
    main()
