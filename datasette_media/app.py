from starlette.responses import HTMLResponse, FileResponse
from starlette.routing import Router, Route
from starlette.endpoints import HTTPEndpoint
from concurrent import futures
import asyncio
from . import utils


def serve_media_app(datasette):
    ServeMedia = get_class(datasette)
    return Router(
        routes=[Route("/-/media/{media_type}/{key:path}", endpoint=ServeMedia)]
    )


def get_class(datasette):
    plugin_config = datasette.plugin_config("datasette-media") or {}
    pool_size = plugin_config.get("num_threads") or 4
    resize_executor = futures.ThreadPoolExecutor(max_workers=pool_size)

    class ServeMedia(HTTPEndpoint):
        async def get(self, request):
            media_type = request.path_params["media_type"]
            key = request.path_params["key"]
            config = plugin_config.get(media_type)
            if config is None:
                return HTMLResponse("<h1>Invalid media type</h1>", status_code=404)
            sql = config.get("sql")
            if sql is None:
                return HTMLResponse(
                    "<h1>Missing SQL from configuration</h1>", status_code=404
                )
            database = config.get("database")
            if database is None:
                database = next(iter(datasette.databases.keys()))
            results = await datasette.execute(database, sql, {"key": key})
            row = results.first()
            if row is None:
                return HTMLResponse("<h1>404 - no results</h1>", status_code=404)
            row_keys = row.keys()
            if "filepath" not in row_keys:
                return HTMLResponse(
                    "<h1>404 - SQL must return 'filepath'</h1>", status_code=404
                )
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
                    image,
                    format=row["output_format"]
                    if "output_format" in row_keys
                    else None,
                )
            else:
                # Non-image files are returned directly
                return FileResponse(filepath)

    return ServeMedia
