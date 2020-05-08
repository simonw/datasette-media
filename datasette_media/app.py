from starlette.responses import HTMLResponse, FileResponse
from starlette.routing import Router, Route
from starlette.endpoints import HTTPEndpoint


def serve_media_app(datasette):
    ServeMedia = get_class(datasette)
    return Router(
        routes=[Route("/-/media/{media_type}/{key:path}", endpoint=ServeMedia)]
    )


def get_class(datasette):
    plugin_config = datasette.plugin_config("datasette-media") or {}

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
                return HTMLResponse("<h1>404</h1>", status_code=404)
            filepath = row["filepath"]
            return FileResponse(filepath)

    return ServeMedia
