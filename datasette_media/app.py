from starlette.responses import HTMLResponse
from starlette.routing import Router, Route
from starlette.endpoints import HTTPEndpoint


def serve_media_app(datasette):
    ServeMedia = get_class(datasette)
    return Router(
        routes=[Route("/-/media/{media_type}/{key:path}", endpoint=ServeMedia)]
    )


def get_class(datasette):
    class ServeMedia(HTTPEndpoint):
        async def get(self, request):
            media_type = request.path_params["media_type"]
            key = request.path_params["key"]

            return HTMLResponse("Type={}, Key={}".format(media_type, key))

    return ServeMedia
