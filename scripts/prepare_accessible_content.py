"""Render the buildless text version of invitations and GPX essentials."""
from html import escape
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def meeting_html(meeting, finish=False):
    if not meeting:
        return ''
    lat, lon = meeting['coordinates']
    url = f'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}'
    label = 'Zaključek pohoda' if finish else 'Zbor in začetek pohoda'
    link_label = 'Poglej cilj na zemljevidu' if finish else 'Poglej zbirno mesto na zemljevidu'
    return f'<p><strong>{label}: {escape(meeting["address"])}</strong><br>GPS: {lat:.6f}, {lon:.6f}<br><a href="{escape(url)}">{link_label}</a></p>'


def paragraph_html(value):
    # Split before escaping so URLs and ordinary text remain safely encoded.
    return ''.join(f'<a href="{escape(part)}">{escape(part)}</a>' if part.startswith(('https://', 'http://')) else escape(part)
                   for part in re.split(r'(https?://[^\s]+)', value))


def render_vabila(events, routes):
    invitations = [event for event in events if event.get('posterText')]
    invitations.sort(key=lambda event: event['date'], reverse=True)
    links = ''.join(f'<li><a href="#{escape(e["id"])}">{escape(e["title"])}</a></li>' for e in invitations)
    sections = []
    for event in invitations:
        paragraphs = ''.join(f'<p>{paragraph_html(p)}</p>' for p in event['posterText'])
        poster = event.get('poster', '')
        original = f'<p><a href="{escape(poster)}">Ogled izvirnega slikovnega vabila: {escape(event["title"])}</a></p>' if poster else ''
        report = event.get('reportUrl', '')
        pdf = f'<p><a href="{escape(report)}">{escape(event["reportLabel"])}</a></p>' if report.endswith('.pdf') else ''
        sections.append(f'<section id="{escape(event["id"])}" class="poster-transcript"><h2>{escape(event["title"])}</h2>{meeting_html(event.get("meetingPoint"))}{meeting_html(event.get("finishPoint"), finish=True)}{paragraphs}{original}{pdf}</section>')
    route_sections = []
    for route in routes:
        if not route.get('segments'):
            route_sections.append(f'<section id="{escape(route["id"])}-pot"><h3>{escape(route["title"])}</h3>{meeting_html(route.get("meetingPoint"))}{meeting_html(route.get("finishPoint"), finish=True)}<p>Prikazani sta začetna točka in zaključek na smučišču Gače.</p></section>')
            continue
        points = [point for segment in route['segments'] for point in segment]
        coordinates = lambda p: f'{p[0]:.5f}, {p[1]:.5f}'
        distance = f'{route["distanceMeters"] / 1000:.1f}'.replace('.', ',')
        note = ('Krožna sled na območju Doblič in reke Dobličice. Sled se vrne do izhodišča.' if route['closed'] else
                'Sled Brkatega pohoda proti Mirni gori. Pot je enosmerna; povratek ni vključen v razdaljo.')
        route_sections.append(f'''<section id="{escape(route['id'])}-pot"><h3>{escape(route['title'])}</h3>
{meeting_html(route.get('meetingPoint'))}<p>{note}</p><dl><dt>Dolžina priložene sledi</dt><dd>{distance} km</dd>
<dt>Začetek sledi – zemljepisna širina in dolžina</dt><dd><code>{coordinates(points[0])}</code></dd>
<dt>Konec sledi – zemljepisna širina in dolžina</dt><dd><code>{coordinates(points[-1])}</code></dd></dl>
<p><a href="{escape(route['download'])}" download>Prenesi GPX: {escape(route['title'])}</a></p></section>''')
    return f'''<!doctype html>
<html lang="sl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vabila in poti v besedilu – Rožnati koraki &amp; Brkati pohod</title>
<link rel="stylesheet" href="css/styles.css?v=9"><link rel="stylesheet" href="css/accessibility.css?v=1"></head>
<body><a class="skip" href="#vsebina">Preskoči na vsebino</a>
<header class="content-header wrap"><a class="brand" href="index.html">Rožnati koraki &amp; Brkati pohod</a>
<nav aria-label="Glavna navigacija"><a href="index.html">Domov</a><a href="dostopnost.html">Izjava o dostopnosti</a></nav></header>
<main id="vsebina" tabindex="-1" class="content-page wrap"><h1>Vabila in poti v besedilu</h1>
<p>Informacije iz slikovnih vabil so na tej strani na voljo kot besedilo. Vabila preteklih pohodov so arhivska; za naslednji pohod preverite <a href="index.html#aktualno">aktualno napoved</a>.</p>
<nav aria-label="Kazalo vabil in poti"><ul>{links}<li><a href="#poti">Podatki poti in točk pohodov</a></li></ul></nav>
{''.join(sections)}<section id="poti"><h2>Podatki poti in točk pohodov</h2>
<p>Osnovni podatki zemljevida so dostopni tudi brez vizualnega prikaza. Za Rožnate korake so navedeni dolžina, potek in koordinate priložene sledi GPX, za Brkati pohod pa začetna in končna točka. Za zbirno mesto in program upoštevajte aktualno napoved.</p>
{''.join(route_sections)}</section>
<p><a href="mailto:ckz@zd-crnomelj.si">Dodatne informacije: ckz@zd-crnomelj.si</a> · <a href="tel:+38673061723">07 30 61 723</a></p></main>
<footer class="content-footer"><div class="wrap"><a href="index.html">Nazaj na spletno stran</a><a href="dostopnost.html#povratne-informacije">Prijavi težavo z dostopnostjo</a></div></footer></body></html>
'''


def main():
    public = ROOT / 'public'
    events = json.loads((public / 'data/events.json').read_text(encoding='utf-8'))['events']
    routes = json.loads((public / 'data/routes.json').read_text(encoding='utf-8'))['routes']
    (public / 'vabila.html').write_text(render_vabila(events, routes), encoding='utf-8')


if __name__ == '__main__':
    main()
