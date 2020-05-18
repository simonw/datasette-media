from starlette.responses import Response
import imghdr
import io
from PIL import Image, ExifTags

try:
    import pyheif
except ImportError:
    pyheif = None

heic_magics = {b"ftypheic", b"ftypheix", b"ftyphevc", b"ftyphevx"}
ORIENTATION_EXIF_TAG = dict((v, k) for k, v in ExifTags.TAGS.items())["Orientation"]


def image_type_for_bytes(b):
    image_type = imghdr.what(None, b)
    if image_type is not None:
        return image_type
    # Maybe it's an HEIC?
    if len(b) < 12:
        return None
    if b[4:12] in heic_magics:
        return "heic"
    return None


def should_reformat(row, plugin_config, request):
    # Decides if the provided row should be reformatted, based on request AND config
    # Returns None if it should not be, or a dict of resize/etc options if it should
    row_keys = row.keys()
    if any(
        key in row_keys for key in ("resize_width", "resize_height", "output_format")
    ):
        return dict(
            width=row["resize_width"] if "resize_width" in row_keys else None,
            height=row["resize_height"] if "resize_height" in row_keys else None,
            format=row["output_format"] if "output_format" in row_keys else None,
        )
    return None


def reformat_image(image_bytes, width=None, height=None, format=None):
    image_type = image_type_for_bytes(image_bytes)
    if image_type == "heic" and pyheif is not None:
        heic = pyheif.read_heif(image_bytes)
        image = Image.frombytes(mode=heic.mode, size=heic.size, data=heic.data)
    else:
        image = Image.open(io.BytesIO(image_bytes))
    # Does EXIF tell us to rotate it?
    try:
        exif = dict(image._getexif().items())
        if exif[ORIENTATION_EXIF_TAG] == 3:
            image = image.rotate(180, expand=True)
        elif exif[ORIENTATION_EXIF_TAG] == 6:
            image = image.rotate(270, expand=True)
        elif exif[ORIENTATION_EXIF_TAG] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass

    # Resize based on width and height, if set
    image_width, image_height = image.size
    if width is not None or height is not None:
        if height is None:
            # Set h based on w
            height = int((float(image_height) / image_width) * width)
        elif width is None:
            # Set w based on h
            width = int((float(image_width) / image_height) * height)
        image.thumbnail((width, height))

    return image


class ImageResponse(Response):
    def __init__(self, image, format=None):
        self.image = image
        output_image = io.BytesIO()
        if format is None:
            format = "PNG" if image.mode == "RGBA" else "JPEG"
        image.save(output_image, format)
        super().__init__(
            content=output_image.getvalue(),
            media_type="image/{}".format(format or "JPEG").lower(),
        )
