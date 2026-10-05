"""Exercise editor persistence and uploads in an isolated project copy."""
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import editor
from serve import Handler


def main():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        shutil.copytree(ROOT / 'public', root / 'public')
        shutil.copytree(ROOT / 'content', root / 'content')
        editor.ROOT = root
        editor.PUBLIC = root / 'public'
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(editor.PUBLIC)))
        Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.route('https://tile.openstreetmap.org/**', lambda r: r.abort())
                page.goto(base + '/urejevalnik/')
                page.locator('#new').click()
                values = {'id':'roznati-test','date':'2027-10-02','title':'Testni pohod','location':'Dobliče','summary':'Napoved novega pohoda.','paragraphs':'Prvi odstavek.\n\nDrugi odstavek.'}
                for name, value in values.items():
                    page.locator(f'[name="{name}"]').fill(value)
                image = next((root / 'public/assets/novice').rglob('*.jpg'))
                page.locator('#poster-file').set_input_files(image)
                page.locator('#save').click()
                expect(page.locator('#save-status')).to_contain_text('Shranjeno')
                expect(page.locator('[name="id"]')).to_have_attribute('readonly', '')
                events, news, version = editor.read_state()
                event = next(e for e in events['events'] if e['id'] == 'roznati-test')
                assert (root / 'public' / event['poster']).read_bytes() == image.read_bytes()
                site = browser.new_page()
                site.route('https://tile.openstreetmap.org/**', lambda r: r.abort())
                site.goto(base)
                expect(site.locator('#upcoming-content')).to_contain_text('Testni pohod')
                page.locator('[name="date"]').fill('2025-10-02')
                page.locator('#publish-news').check()
                for name,value in {'newsTitle':'Zgodba testnega pohoda','newsSummary':'Lep dan na poti.','newsParagraphs':'Poročilo o pohodu.','photoCredit':'PGD Dobliče'}.items():
                    page.locator(f'[name="{name}"]').fill(value)
                page.locator('#photos-file').set_input_files([image,image])
                page.locator('.photo input[type="radio"]').nth(1).check()
                page.locator('#save').click()
                expect(page.locator('#save-status')).to_contain_text('Shranjeno')
                expect(page.locator('#publish-news')).to_be_disabled()
                events, news, version = editor.read_state()
                article = next(a for a in news['articles'] if a['eventId'] == 'roznati-test')
                assert len(article['photos']) == 2 and article['cover'] == article['photos'][1]['url']
                assert article['editorManaged'] and article['sourceUrl'] == ''
                assert json.loads((root / 'content/news-copy.json').read_text())['roznati-test']['photoCredit'] == 'PGD Dobliče'
                site.reload()
                expect(site.locator('#news-grid')).to_contain_text('Zgodba testnega pohoda')
                site.locator('#news-grid [data-news="roznati-test"]').first.click()
                expect(site.locator('.photo-credit')).to_have_text('PGD Dobliče')
                expect(site.locator('.news-source')).to_have_count(0)
                expect(site.locator('.gallery-frame img')).to_be_visible()
                page.locator('.photo button').first.click()
                page.locator('#save').click()
                expect(page.locator('#save-status')).to_contain_text('Shranjeno')
                _, news, _ = editor.read_state()
                assert len(next(a for a in news['articles'] if a['eventId'] == 'roznati-test')['photos']) == 1
                for width in [360,768,1440]:
                    page.set_viewport_size({'width':width,'height':900})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                # Saving without the session token is forbidden.
                response = page.request.post(base + '/api/editor/save', data={})
                assert response.status == 403
                # Stale versions and path traversal cannot modify the catalog.
                before = editor.read_state()[2]
                for payload in [
                    {'version':'stale','event':event,'isNew':False},
                    {'version':before,'event':{**event,'poster':'assets/../../scripts/serve.py'},'isNew':False},
                    {'version':before,'event':event,'isNew':True},
                ]:
                    try:
                        editor.save(payload)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError('Invalid save accepted')
                    assert editor.read_state()[2] == before
                assert list((root / 'artifacts/editor-backups').iterdir())
                assert not errors, errors
                browser.close()
            print('PASS: event creation, poster upload, news publication, gallery upload/removal/cover, persisted files, public rendering, backups, mobile layout, token, stale writes and path validation.')
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
