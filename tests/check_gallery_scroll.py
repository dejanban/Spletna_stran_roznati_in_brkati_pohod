"""Keep gallery scroll position stable during slow image loads and failures."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic

from playwright.sync_api import sync_playwright, expect
from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'public')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = launch_browser(p)
            for width in (1280, 390):
                page = browser.new_page(viewport={'width': width, 'height': 850})
                errors, pending = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.route('https://tile.openstreetmap.org/**', lambda route: route.abort())
                page.route('**/__gallery-test__/*', lambda route: pending.append(route))
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.evaluate('''() => {
                    const event = window.EVENTS.find(e => e.id === 'roznati-2026');
                    event.photos = [
                        {url:'assets/novice/roznati-2026/001.jpg', caption:'Pohodniki na zbirnem mestu. '.repeat(12)},
                        {url:'__gallery-test__/second.jpg', caption:'Na poti.'}
                    ];
                }''')
                page.locator('[data-event="roznati-2026"]').first.click()
                expect(page.locator('.gallery-frame img')).to_be_visible()
                page.locator('[data-next]').focus()
                page.locator('#event-dialog').evaluate('e => e.scrollTop = e.scrollHeight')
                measure = '''() => {
                    const dialog = document.querySelector('#event-dialog');
                    const frame = document.querySelector('.gallery-frame').getBoundingClientRect();
                    return {scroll:dialog.scrollTop, top:frame.top, height:frame.height};
                }'''
                before = page.evaluate(measure)
                assert before['scroll'] > 0

                def stable():
                    after = page.evaluate(measure)
                    for key in before:
                        assert abs(after[key] - before[key]) <= 1, (width, key, before, after)

                def next_request():
                    deadline = monotonic() + 10
                    while not pending and monotonic() < deadline:
                        page.wait_for_timeout(20)
                    assert len(pending) == 1, 'Expected one pending image request'
                    return pending.pop()

                # The delayed response exposes a collapsed frame even on fast machines.
                page.locator('[data-next]').click()
                expect(page.locator('.gallery-loading')).to_contain_text('Nalagam fotografijo')
                stable()
                next_request().fulfill(content_type='image/jpeg', body=(ROOT / 'public/assets/novice/roznati-2026/002.jpg').read_bytes())
                expect(page.locator('.gallery-frame img')).to_be_visible()
                stable()
                page.locator('[data-prev]').click()
                expect(page.locator('.gallery-counter')).to_have_text('1 / 2')
                expect(page.locator('.gallery-frame img')).to_be_visible()
                stable()
                page.evaluate("window.EVENTS.find(e => e.id === 'roznati-2026').photos[1].url = '__gallery-test__/missing.jpg'")
                page.keyboard.press('ArrowRight')
                expect(page.locator('.gallery-loading')).to_contain_text('Nalagam fotografijo')
                stable()
                next_request().fulfill(status=404, body='Missing image')
                expect(page.locator('.gallery-loading')).to_contain_text('ni mogoče prikazati')
                stable()
                page.keyboard.press('ArrowLeft')
                expect(page.locator('.gallery-frame img')).to_be_visible()
                stable()
                assert not errors, errors
                page.close()
            browser.close()
        print('PASS: desktop/mobile scroll stays fixed for next/previous, keyboard, delayed loads, changing captions and image failures.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
