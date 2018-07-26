from quart import Quart
from quart.static import send_from_directory

import storage

app = Quart(__name__)

@app.route("/api/hello")
async def hello():
    return "Testing. Hello World! I have been seen {} times.\n"

@app.route("/")
async def index():
    return await send_from_directory("./static/", "index.html")

@app.route("/<path:path>")
async def fallback(path):
    return await send_from_directory("./static/", path)

app.run(host="0.0.0.0", port=5000, debug=True)
