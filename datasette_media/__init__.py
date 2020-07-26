import asyncio
from datasette import hookimpl
from datasette.utils.asgi import Response, AsgiFileDownload
from concurrent import futures
from mimetypes import guess_type
from PIL import Image
import io
from . import utils

resize_executor = None


@hookimpl
def register_routes():
    return [
        (r"/-/media/(?P<media_type>[^/]+)/(?P<key>.+)", serve_media),
    ]


async def serve_media(datasette, request):
    global resize_executor
    plugin_config = datasette.plugin_config("datasette-media") or {}
    pool_size = plugin_config.get("num_threads") or 4
    if resize_executor is None:
        resize_executor = futures.ThreadPoolExecutor(max_workers=pool_size)

    media_type = request.url_vars["media_type"]
    key = request.url_vars["key"]
    config = plugin_config.get(media_type)
    if config is None:
        return Response.html("<h1>Invalid media type</h1>", status=404)
    sql = config.get("sql")
    if sql is None:
        return Response.html("<h1>Missing SQL from configuration</h1>", status=404)
    database = config.get("database")
    if database is None:
        database = next(iter(datasette.databases.keys()))
    results = await datasette.execute(database, sql, {"key": key})
    row = results.first()
    if row is None:
        return Response.html("<h1>404 - no results</h1>", status=404)
    row_keys = row.keys()
    if "filepath" not in row_keys and "binary_content" not in row_keys:
        return Response.html(
            "<h1>404 - SQL must return 'filepath' or 'binary_content'</h1>", status=404
        )
    if "binary_content" in row_keys:
        binary_content = row["binary_content"]
        image = Image.open(io.BytesIO(binary_content))
        return utils.ImageResponse(image)
    else:
        filepath = row["filepath"]

    # Images are special cases, triggered by a few different conditions
    should_reformat = utils.should_reformat(row, plugin_config, request)
    if should_reformat:
        image_bytes = open(filepath, "rb").read()
        image = await asyncio.get_event_loop().run_in_executor(
            resize_executor,
            lambda: utils.reformat_image(image_bytes, **should_reformat),
        )
        return utils.ImageResponse(
            image, format=row["output_format"] if "output_format" in row_keys else None,
        )
    else:
        # Non-image files are returned directly
        return AsgiFileDownload(filepath, content_type=guess_type(filepath)[0])
