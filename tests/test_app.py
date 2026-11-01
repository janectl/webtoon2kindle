"""Self-contained tests; no live website requests required."""
from io import BytesIO
from zipfile import ZipFile

import pytest
from PIL import Image
from tests.helpers import image_bytes

from web.app import create_app


def sample_cbz():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("0002.png", image_bytes("black"))
        archive.writestr("0001.png", image_bytes("white"))
    buffer.seek(0)
    return buffer


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    assert b"Comix chapter URL" in client.get("/").data
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/healthz").json == {"status": "ok"}


def test_conversion_requires_exactly_one_input(client):
    assert client.post("/convert").status_code == 400
    response = client.post("/convert", data={"url": "https://example.org/"})
    assert response.status_code == 400
    assert b"Unsupported source" in response.data


def test_convert_uploaded_images_to_cbz(client):
    result = client.post("/convert", data={
        "images": [(BytesIO(image_bytes("red")), "2.png"),
                   (BytesIO(image_bytes("blue")), "10.png"),
                   (BytesIO(image_bytes("white")), "1.png")],
        "format": "cbz", "name": "Test: Volume", "max_width": "1072",
        "grayscale": "on", "contrast": "1.15"
    }, content_type="multipart/form-data")
    assert result.status_code == 200
    assert "Test Volume.cbz" in result.headers["Content-Disposition"]
    with ZipFile(BytesIO(result.data)) as z:
        assert z.namelist() == ["00001.jpg", "00002.jpg", "00003.jpg"]
        with Image.open(z.open("00001.jpg")) as img:
            assert img.size == (240, 480)
            assert img.getpixel((10, 10))[0] > 230


def test_convert_uploaded_cbz_to_pdf(client):
    result = client.post("/convert", data={"cbz": (sample_cbz(), "chapter-1.cbz"),
                                          "format": "pdf", "max_width": "0"},
                         content_type="multipart/form-data")
    assert result.status_code == 200
    assert result.data[:4] == b"%PDF"


def test_merge_two_cbz(client):
    cbz2 = sample_cbz()
    cbz1 = sample_cbz()
    result = client.post("/merge-cbz", data={
        "cbz_files": [(cbz2, "Episode 2.cbz"), (cbz1, "Episode 1.cbz")],
        "volume_name": "My Volume", "order_mode": "auto",
    }, content_type="multipart/form-data")
    assert result.status_code == 200
    assert "Episodes 1-2" in result.headers["Content-Disposition"]
    with ZipFile(BytesIO(result.data)) as z:
        assert z.namelist() == [f"{i:06d}.png" for i in range(1, 5)]


def test_bad_archive_handled(client):
    result = client.post("/convert", data={"cbz": (BytesIO(b"not a zip"), "invalid.cbz")},
                         content_type="multipart/form-data")
    assert result.status_code == 400


def test_inspect_requires_url(client):
    response = client.post("/inspect", data={})
    assert response.status_code == 400
    assert "Paste a chapter URL" in response.json["error"]


def test_inspect_unsupported_source(client):
    response = client.post("/inspect", data={"url": "https://example.org/title/test"})
    assert response.status_code == 400
    assert "Unsupported source" in response.json["error"]