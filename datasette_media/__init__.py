import asyncio
from datasette import hookimpl
from datasette.utils.asgi import Response, AsgiFileDownload
from concurrent import futures
from mimetypes import guess_type
from PIL import Image
import io
from . import utils

transform_executor = None
RESERVED_MEDIA_TYPES = ("transform_threads", "enable_transform")

@hookimpl
def register_routes():
    return [
        (r"/-/media/(?P<media_type>[^/]+)/(?P<key>.+)", serve_media),
    ]


async def serve_media(datasette, request):
    global transform_executor
    plugin_config = datasette.plugin_config("datasette-media") or {}
    pool_size = plugin_config.get("transform_threads") or 4
    if transform_executor is None:
        transform_executor = futures.ThreadPoolExecutor(max_workers=pool_size)

    media_type = request.url_vars["media_type"]
    key = request.url_vars["key"]

    config = plugin_config.get(media_type)
    if media_type in RESERVED_MEDIA_TYPES or config is None:
        return Response.html("<h1>Invalid media type</h1>", status=404)
    sql = config.get("sql")
    if sql is None:
        return Response.html("<h1>Missing SQL from configuration</h1>", status=404)
    database = datasette.get_database(config.get("database"))
    results = await database.execute(sql, {"key": key})
    row = results.first()
    if row is None:
        return Response.html("<h1>404 - no results</h1>", status=404)
    row_keys = row.keys()
    if "filepath" not in row_keys and "content" not in row_keys:
        return Response.html(
            "<h1>404 - SQL must return 'filepath' or 'content'</h1>", status=404
        )
    if "content" in row_keys:
        image = Image.open(io.BytesIO(row["content"]))
        return utils.ImageResponse(image)
    else:
        filepath = row["filepath"]

    # Images are special cases, triggered by a few different conditions
    should_transform = utils.should_transform(row, plugin_config, request)
    if should_transform:
        image_bytes = open(filepath, "rb").read()
        image = await asyncio.get_event_loop().run_in_executor(
            transform_executor,
            lambda: utils.transform_image(image_bytes, **should_transform),
        )
        return utils.ImageResponse(
            image, format=row["output_format"] if "output_format" in row_keys else None,
        )
    else:
        # Non-image files are returned directly
        return AsgiFileDownload(filepath, content_type=guess_type(filepath)[0])
