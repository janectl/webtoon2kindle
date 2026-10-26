from io import BytesIO
from PIL import Image

def image_bytes(color="white", size=(240, 480)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()
