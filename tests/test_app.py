from io import BytesIO
from PIL import Image
from app import app, convert_images, export_pdf, export_cbz
from zipfile import ZipFile


def test_exports():
    im = Image.new('RGB', (600, 1700), 'white')
    b = BytesIO(); im.save(b, 'PNG'); b.seek(0)
    class Uploaded:
        filename = 'sample.png'
        stream = b
    pages = convert_images([Uploaded()])
    assert len(pages) == 3
    assert pages[0].size == (1236, 1648)
    assert export_pdf(pages).read(4) == b'%PDF'
    with ZipFile(export_cbz(pages)) as z:
        assert len(z.namelist()) == 3


def test_route():
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert client.post('/convert').status_code == 400
