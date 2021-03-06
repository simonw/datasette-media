from datasette_media.utils import image_type_for_bytes
import pytest


GIF_1x1 = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;"
PNG_1x1 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\xfa\x0f\x00\x01\x05\x01\x02\xcf\xa0.\xcd\x00\x00\x00\x00IEND\xaeB`\x82"
JPEG = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xdb\x00C\x01\x03\x03\x03\x04\x03\x04\x08\x04\x04\x08\x10\x0b\t\x0b\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\xff\xc0\x00\x11\x08\x00\x10\x00\x10\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x16\x00\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x04\x05\xff\xc4\x00$\x10\x00\x01\x04\x01\x04\x02\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x06\x05\x07\x08\x12\x13\x11"\x00\x14\t12\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\xff\xc4\x00#\x11\x00\x01\x02\x05\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x11\x03\x04\x05\x06!\x00\x121\x15\x16a\x81\xe1\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\x14\xa6\xd2j\x1bs\xc1\xe6\x13\x12\xd4\x95\x1c\xf3\x11c\xe4%e\xbe\xbaZ\xeciE@\xb1\xe5 \xb2T\xa5\x1f\xd2\xca\xb8\xfa\xf2 \xab\x96=\x97l\x935\xe6\x9bw\xd7\xe6m\xa7\x17\x81\xa5W\x1c\x7f\x1c\xeaq\xe2K9\xd7\xe3"S\xf2\x1ai\xde\xd4qJ8\xb4\x82\xe8K\x89*qi\x1e\xcd-!;\xf1\xef\xb9\x1at\xac\xee\xa1Zu\x8e\xd5H\xace[\x85\x8b\x81\x85{!)\x98g\xa9k\x94\xb9IeO\xb9\xc8\x85)\x11K\x81*\xf0z\xd9\xf2<\x80~U\xbe\r\xf6b\xa1@\xcc\xe8\xe6\x9a=\\\xb7C\xb3\xd7zeX\xb1\xd9Q!\x88\xbfd\xb8\xd3\xf1\xc3h\x04)\xc0\xd0\xfe\xbb<\x02\xe0<T\x07\xb4\xbd\xd9{T\xe6\'\xfbn\xdf\x94`\x14\x82b\x13\x8d\xb8R\x98(7\x05\x89ry`\xe42\x89o\xc3\x82\x8e\xa7R\x8c\xea \x8d\xbex\x19\x1f\x07\xad\x7f\xff\xd9'
HEIC = b'\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic\x00\x00\x01*meta\x00\x00\x00\x00\x00\x00\x00!hdlr\x00\x00\x00\x00\x00\x00\x00\x00pict\x00\\\x00c\x001\x005\x00x\x002\x00\x00\x00\x00\x0epitm\x00\x00\x00\x00\x00\x01\x00\x00\x00"iloc\x00\x00\x00\x00D@\x00\x01\x00\x01\x00\x00\x00\x00\x01J\x00\x01\x00\x00\x00\x00\x00\x00\x008\x00\x00\x00#iinf\x00\x00\x00\x00\x00\x01\x00\x00\x00\x15infe\x02\x00\x00\x00\x00\x01\x00\x00hvc1\x00\x00\x00\x00\xaaiprp\x00\x00\x00\x8dipco\x00\x00\x00qhvcC\x01\x04\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xf0\x00\xfc\xfd\xf8\xf8\x00\x00\x0f\x03 \x00\x01\x00\x17@\x01\x0c\x01\xff\xff\x04\x08\x00\x00\x03\x00\x9f\xa8\x00\x00\x03\x00\x00\xff\xba\x02@!\x00\x01\x00&B\x01\x01\x04\x08\x00\x00\x03\x00\x9f\xa8\x00\x00\x03\x00\x00\xff\xa0 \x81\x05\x96\xeaI(\xae\x01\x00\x00\x03\x00\x01\x00\x00\x03\x00\x01\x08"\x00\x01\x00\x06D\x01\xc1q\x89\x12\x00\x00\x00\x14ispe\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00@\x00\x00\x00\x15ipma\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x02\x81\x02\x00\x00\x00@mdat\x00\x00\x004(\x01\xaf\x05\xb8\x14\x83\xea#@\x1f\xf7_\xee\x7f\xb5\xfdo\xce\xfc\xef\xce\xfc\xef\xcf|\xf7\xcf|\xf7\xcf|\xf7\xcf|\xf7\xfe\x14\x113\te\x03^\xdar\xb4\xe9\xc5 \xd6\xc0'


@pytest.mark.parametrize(
    "img_bytes,expected_type",
    [
        (GIF_1x1, "gif"),
        (PNG_1x1, "png"),
        (JPEG, "jpeg"),
        (HEIC, "heic"),
        (b"hello", None),
    ],
)
def test_image_type_for_bytes(img_bytes, expected_type):
    assert expected_type == image_type_for_bytes(img_bytes)
