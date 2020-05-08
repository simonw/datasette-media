from datasette import hookimpl
from .app import serve_media_app


@hookimpl
def asgi_wrapper(datasette):
    def wrap_with_serve_media_app(app):
        async def wrapped_app(scope, receive, send):
            path = scope["path"]
            if path.startswith("/-/media/"):
                await (serve_media_app(datasette))(scope, receive, send)
            else:
                await app(scope, receive, send)

        return wrapped_app

    return wrap_with_serve_media_app
