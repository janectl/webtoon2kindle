"""Import publicly accessible episode images; no login or access-control bypass."""
from urllib.parse import urlparse, urljoin
import ipaddress
import socket
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image

MAX_BYTES = 15 * 1024 * 1024

def safe_url(url, allowed_hosts):
    p = urlparse(url)
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Only HTTPS URLs on approved hosts are supported.')
    host = (p.hostname or '').lower()
    if host not in allowed_hosts:
        raise ValueError('Unsupported image or episode host.')
    for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        addr = ipaddress.ip_address(item[4][0])
        if not addr.is_global:
            raise ValueError('Unsafe network destination.')
    return url

def get(url, hosts, session):
    safe_url(url, hosts)
    response = session.get(url, timeout=18, allow_redirects=False, stream=True, headers={'User-Agent':'Mozilla/5.0 Webtoon2Kindle/1.0'})
    if response.status_code != 200:
        raise ValueError(f'Remote server returned HTTP {response.status_code}.')
    size = 0
    data = BytesIO()
    for chunk in response.iter_content(65536):
        size += len(chunk)
        if size > MAX_BYTES:
            raise ValueError('Remote file is too large.')
        data.write(chunk)
    return data.getvalue()

def fetch_episode(url):
    hosts = {'www.webtoons.com', 'webtoons.com'}
    safe_url(url, hosts)
    if '/viewer' not in urlparse(url).path:
        raise ValueError('Paste a WEBTOON episode viewer link.')
    session = requests.Session()
    html = get(url, hosts, session)
    soup = BeautifulSoup(html, 'html.parser')
    viewer = soup.select_one('#_imageList')
    if viewer is None:
        raise ValueError('Episode images are not available in the public HTML.')
    image_urls = []
    for tag in viewer.select('img'):
        src = tag.get('data-url') or tag.get('data-src') or tag.get('src')
        if not src:
            continue
        src = urljoin(url, src)
        host = (urlparse(src).hostname or '').lower()
        if host not in {'webtoon-phinf.pstatic.net'} and not (host.endswith('.pstatic.net') and host.startswith('webtoon-')):
            raise ValueError('Unexpected episode image host.')
        image_urls.append(src)
    if not image_urls or len(image_urls) > 150:
        raise ValueError('No images found, or episode exceeds the 150-image limit.')
    images = []
    for src in image_urls:
        data = get(src, {urlparse(src).hostname.lower()}, session)
        try:
            img = Image.open(BytesIO(data))
            img.verify()
            img = Image.open(BytesIO(data))
            images.append(img.copy())
        except Exception as exc:
            raise ValueError('One episode image could not be decoded.') from exc
    return images
