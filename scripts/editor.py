"""Local editing API used by serve.py; no external dependencies."""
import base64
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import secrets
from threading import Lock
from urllib.parse import urlparse
import uuid

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
TOKEN = secrets.token_urlsafe(32)
LOCK = Lock()


def read_state():
    events = json.loads((PUBLIC / 'data/events.json').read_text())
    news = json.loads((PUBLIC / 'data/news.json').read_text())
    version = hashlib.sha256(json.dumps([events, news], sort_keys=True).encode()).hexdigest()
    return events, news, version


def text(value, required=False):
    if not isinstance(value, str) or len(value) > 30000 or (required and not value.strip()):
        raise ValueError('Izpolnite obvezna polja; besedilo je lahko dolgo največ 30.000 znakov.')
    return value.strip()


def paragraphs(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 100:
        raise ValueError('Vnesite besedilo dogodka oziroma novice.')
    return [text(p, True) for p in value]


def asset(value):
    value = text(value)
    if not value:
        return value
    path = (PUBLIC / value).resolve()
    if not value.startswith('assets/') or not path.is_relative_to(PUBLIC / 'assets') or not path.is_file():
        raise ValueError('Slika mora biti shranjena v mapi assets.')
    return value


def upload(value, pending):
    if not isinstance(value, dict):
        raise ValueError('Neveljavna slika.')
    data = base64.b64decode(value.get('data', ''), validate=True)
    if not 0 < len(data) <= 15 * 1024 * 1024:
        raise ValueError('Posamezna slika je lahko velika največ 15 MB.')
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        ext = '.png'
    elif data.startswith(b'\xff\xd8\xff'):
        ext = '.jpg'
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        ext = '.webp'
    else:
        raise ValueError('Uporabite slike JPG, PNG ali WebP.')
    relative = 'assets/urednik/' + uuid.uuid4().hex + ext
    pending.append((PUBLIC / relative, data))
    return relative, data


def save(payload):
    events, news, version = read_state()
    if payload.get('version') != version:
        raise ValueError('Vsebina se je medtem spremenila. Osvežite urejevalnik in poskusite znova.')
    supplied = payload.get('event', {})
    event_id = text(supplied.get('id'), True)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', event_id):
        raise ValueError('Oznaka dogodka naj vsebuje male črke, številke in vezaje.')
    existing = next((e for e in events['events'] if e['id'] == event_id), None)
    if payload.get('isNew') and existing:
        raise ValueError('Dogodek s to oznako že obstaja.')
    if not payload.get('isNew') and not existing:
        raise ValueError('Dogodek ne obstaja več. Osvežite urejevalnik.')
    event = dict(existing or {})
    event['id'] = event_id
    event['type'] = supplied.get('type')
    if event['type'] not in ('brkati', 'roznati'):
        raise ValueError('Izberite vrsto pohoda.')
    event['date'] = text(supplied.get('date'), True)
    date.fromisoformat(event['date'])
    for key in ('title', 'location', 'summary'):
        event[key] = text(supplied.get(key), True)
    for key in ('time', 'endTime', 'route'):
        event[key] = text(supplied.get(key, ''))
    for key in ('time', 'endTime'):
        if event[key] and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', event[key]):
            raise ValueError('Uro vnesite v obliki HH:MM.')
    event['paragraphs'] = paragraphs(supplied.get('paragraphs'))
    event.setdefault('photos', [])
    event.setdefault('driveFolderId', '')
    event.setdefault('reportUrl', '')
    event.setdefault('reportLabel', '')
    pending = []
    event['poster'] = asset(supplied.get('poster', ''))
    if payload.get('posterUpload'):
        event['poster'], _ = upload(payload['posterUpload'], pending)
    article = payload.get('article')
    copy = json.loads((ROOT / 'content/news-copy.json').read_text())
    if article is not None:
        prior = next((a for a in news['articles'] if a['eventId'] == event_id), {})
        result = dict(prior)
        result.update(eventId=event_id, editorManaged=True)
        for key in ('title', 'summary', 'photoCredit'):
            result[key] = text(article.get(key), True)
        result['paragraphs'] = paragraphs(article.get('paragraphs'))
        result['publishedAt'] = text(article.get('publishedAt'), True)
        date.fromisoformat(result['publishedAt'][:10])
        result['sourceName'] = text(article.get('sourceName', 'Organizator'))
        result['sourceUrl'] = text(article.get('sourceUrl', ''))
        if result['sourceUrl'] and urlparse(result['sourceUrl']).scheme not in ('http', 'https'):
            raise ValueError('Povezava do članka mora uporabljati http ali https.')
        result['sourceTitle'] = text(article.get('sourceTitle', ''))
        result['sourceCredit'] = text(article.get('sourceCredit', ''))
        result['photos'] = []
        for photo in article.get('photos', []):
            if 'upload' in photo:
                url, data = upload(photo['upload'], pending)
                saved = {'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            else:
                url = asset(photo.get('url', ''))
                saved = next((dict(p) for p in prior.get('photos', []) if p['url'] == url), {'url': url})
            saved['caption'] = text(photo.get('caption', '')) or result['photoCredit']
            result['photos'].append(saved)
        if not result['photos']:
            raise ValueError('Novici dodajte vsaj eno fotografijo.')
        cover_index = article.get('coverIndex', 0)
        if not isinstance(cover_index, int) or not 0 <= cover_index < len(result['photos']):
            raise ValueError('Izberite naslovno fotografijo.')
        result['cover'] = result['photos'][cover_index]['url']
        news['articles'] = [a for a in news['articles'] if a['eventId'] != event_id] + [result]
        news['articles'].sort(key=lambda a: a['publishedAt'], reverse=True)
        copy[event_id] = {key: result[key] for key in ('title', 'summary', 'paragraphs', 'photoCredit')}
    events['events'] = [event if e['id'] == event_id else e for e in events['events']]
    if not existing:
        events['events'].append(event)
    encode = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
    files = {
        PUBLIC / 'data/events.json': encode(events) + '\n',
        PUBLIC / 'data/events.js': '/* Generated by the local editor; edit events.json or use /urejevalnik/. */\nwindow.SITE_CONFIG = ' + encode(events['config']) + ';\nwindow.EVENTS = ' + encode(events['events']) + ';\n',
        PUBLIC / 'data/news.json': encode(news) + '\n',
        PUBLIC / 'data/news.js': '/* Generated catalog. */\nwindow.NEWS_DATABASE = ' + encode(news) + ';\n',
        ROOT / 'content/news-copy.json': encode(copy) + '\n',
    }
    backup = ROOT / 'artifacts/editor-backups' / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    for path in files:
        target = backup / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    for path, data in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for path, value in files.items():
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(value, encoding='utf-8')
        temporary.replace(path)
    return {'message': 'Shranjeno. Spremembe so vidne na spletni strani.', 'version': read_state()[2]}


def handle_get(handler):
    if handler.path != '/api/editor':
        return False
    with LOCK:
        events, news, version = read_state()
    handler.send_json(200, {'events': events['events'], 'articles': news['articles'], 'version': version, 'token': TOKEN})
    return True


def handle_post(handler):
    host = handler.headers.get('Host', '')
    origin = handler.headers.get('Origin', '')
    if handler.path != '/api/editor/save':
        handler.send_json(404, {'error': 'Neznana povezava.'})
        return
    if handler.headers.get('X-Editor-Token') != TOKEN or origin != 'http://' + host or host.split(':')[0] not in ('localhost', '127.0.0.1'):
        handler.send_json(403, {'error': 'Urejevalnik uporabljajte na lokalnem naslovu.'})
        return
    try:
        length = int(handler.headers.get('Content-Length', 0))
        if not 0 < length <= 80 * 1024 * 1024:
            raise ValueError('Naenkrat naložite največ 80 MB podatkov.')
        payload = json.loads(handler.rfile.read(length))
        with LOCK:
            result = save(payload)
        handler.send_json(200, result)
    except (ValueError, TypeError, KeyError) as error:
        handler.send_json(400, {'error': str(error)})
    except OSError:
        handler.send_json(500, {'error': 'Shranjevanje ni uspelo. Preverite dostop do projektne mape.'})
