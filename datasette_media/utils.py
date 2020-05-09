import imghdr

heic_magics = {b"ftypheic", b"ftypheix", b"ftyphevc", b"ftyphevx"}


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
