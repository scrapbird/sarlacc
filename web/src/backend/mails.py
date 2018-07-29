from quart import abort, Blueprint, current_app, jsonify, request
import logging


logger = logging.getLogger()

blueprint = Blueprint("mails", __name__)


@blueprint.route("/api/search")
async def search():
    query = request.args.get("q", "")
    logger.info("/api/search?q=" + query)
    results = await current_app.store.search_emails(query, attachment_content=False)
    logger.info("Results:")
    logger.info(results)
    return jsonify(results)

@blueprint.route("/")
async def index():
    logger.info("/")
    return await current_app.send_static_file("index.html")
