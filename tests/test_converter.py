from web.services.converter import convert_stream, process_image
from tests.helpers import image_bytes
from zipfile import ZipFile

def test_uploaded_image_is_not_split_or_upscaled():
    raw = image_bytes(size=(1200, 2400))
    img = process_image(raw, grayscale=False, contrast=1.15, max_width=1072)
    try:
        assert img.size == (1072, 2144)
    finally:
        img.close()
    img = process_image(raw, grayscale=False, contrast=1.15, max_width=0)
    assert img.size == (1200, 2400)
    img.close()


def test_convert_stream_is_lazy(tmp_path):
    used = []
    def pages():
        for i in range(4):
            used.append(i)
            yield image_bytes(size=(100, 400))
    target = tmp_path / "comic.cbz"
    assert convert_stream(pages(), str(target), "cbz", grayscale=False) == 4
    assert used == list(range(4))
    with ZipFile(target) as z:
        assert len(z.namelist()) == 4


