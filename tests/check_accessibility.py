"""Keyboard, responsive layout, content and optional axe-core accessibility audit.

Set AXE_CORE_PATH to a local axe.min.js to include automated WCAG 2.1 AA checks.
Set BROWSER_EXECUTABLE for an installed Chromium when Microsoft Edge is absent.
The checks cannot replace testing with real screen readers or user evaluation.
"""
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from threading import Thread
from playwright.sync_api import sync_playwright, expect
from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from serve import Handler


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'public')))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    axe_path = os.environ.get('AXE_CORE_PATH')
    report = []
    def audit(page, name):
        if not axe_path:
            return
        page.add_script_tag(path=axe_path)
        result = page.evaluate("""async () => {
          const result = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}});
          return {violations:result.violations, incomplete:result.incomplete};
        }""")
        report.append({'page': name, **result})
        Path(os.environ.get('ACCESSIBILITY_REPORT', '/tmp/pohodi-accessibility-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            page = browser.new_page(viewport={'width':1280, 'height':960}, reduced_motion='reduce')
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.route('https://tile.openstreetmap.org/**', lambda r: r.abort())
            assert page.goto(base).status == 200
            page.keyboard.press('Tab')
            expect(page.locator('.skip')).to_be_focused()
            page.keyboard.press('Enter')
            expect(page.locator('#vsebina')).to_be_focused()
            audit(page, 'Domov – namizni prikaz')
            # Actual keyboard use of modal, controls and native focus containment.
            trigger = page.locator('[data-news]').first
            trigger.focus(); page.keyboard.press('Enter')
            expect(page.locator('.dialog-close')).to_be_focused()
            expect(page.locator('.gallery-frame img')).to_be_visible()
            expect(page.locator('[data-pause]')).to_have_text('Predvajaj')
            first = page.locator('.gallery-counter').inner_text()
            page.wait_for_timeout(5700)
            expect(page.locator('.gallery-counter')).to_have_text(first)
            page.locator('[data-next]').focus(); page.keyboard.press('Enter')
            expect(page.locator('.gallery-counter')).to_have_text('2 / 27')
            page.keyboard.press('Tab')
            expect(page.locator('.gallery')).to_be_visible()
            assert page.evaluate('document.activeElement.closest("dialog") !== null')
            page.keyboard.press('Escape')
            expect(trigger).to_be_focused()
            catalog = json.loads((ROOT / 'public/data/news.json').read_text())
            for article in catalog['articles']:
                page.locator(f'[data-news="{article["eventId"]}"]').first.click()
                expect(page.locator('.gallery-frame img')).to_be_visible()
                audit(page, 'Novica ' + article['eventId'])
                page.keyboard.press('Escape')
                assert all(p['caption'].strip() and ' · Fotografija ' not in p['caption'] for p in article['photos'])
            for event in json.loads((ROOT / 'public/data/events.json').read_text())['events']:
                if not event.get('poster'):
                    continue
                page.locator(f'[data-event="{event["id"]}"]').first.click()
                expect(page.locator('.poster-transcript')).to_be_visible()
                audit(page, 'Vabilo v pojavnem oknu ' + event['id'])
                page.keyboard.press('Escape')
            for filename in ['index.html', 'dostopnost.html', 'vabila.html']:
                assert page.goto(base + '/' + filename).status == 200
                for width in [320,360,768,1280]:
                    page.set_viewport_size({'width':width,'height':900})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (filename,width)
                    audit(page, filename + ' – ' + str(width) + ' px')
                # WCAG text spacing: content must remain usable without clipping.
                style = page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}')
                for width in [320,640,1280]:
                    page.set_viewport_size({'width':width,'height':900})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('text spacing',filename,width)
                style.evaluate('e => e.remove()')
            page.goto(base);page.set_viewport_size({'width':320,'height':900})
            page.locator('.menu-toggle').focus();page.keyboard.press('Enter')
            audit(page, 'Odprt mobilni meni')
            page.keyboard.press('Escape');expect(page.locator('.menu-toggle')).to_be_focused()
            expect(page.locator('#navigation')).not_to_be_visible()
            page.locator('.menu-toggle').click()
            page.locator('#navigation a[href="#arhiv"]').focus();page.keyboard.press('Enter')
            expect(page.locator('#arhiv')).to_be_focused()
            page.goto(base + '/urejevalnik/')
            page.locator('#new').click()
            audit(page, 'Urejevalnik – nov dogodek')
            page.locator('#events button').filter(has_text='Brkati pohod 2026').click()
            audit(page, 'Urejevalnik – obstoječi dogodek')
            assert not errors, errors
            browser.close()
            no_js = playwright.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE'), headless=True) if os.environ.get('BROWSER_EXECUTABLE') else launch_browser(playwright)
            plain = no_js.new_page(java_script_enabled=False)
            for filename in ['dostopnost.html','vabila.html']:
                plain.goto(base+'/'+filename)
                expect(plain.locator('h1')).to_be_visible()
                expect(plain.locator('a[href="mailto:ckz@zd-crnomelj.si"]')).to_be_visible()
            no_js.close()
        if axe_path:
            output = Path(os.environ.get('ACCESSIBILITY_REPORT', '/tmp/pohodi-accessibility-report.json'))
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            failures = [(r['page'], v['id'], [n['target'] for n in v['nodes']]) for r in report for v in r['violations']]
            assert not failures, json.dumps(failures, ensure_ascii=False, indent=2)
            print(f'PASS: {len(report)} axe-core audits without violations; report: {output}')
        else:
            print('SKIP: axe-core audit (set AXE_CORE_PATH).')
        print('PASS: keyboard, focus, static invitations, 227 photo descriptions, mobile layout and text spacing.')
    finally:
        server.shutdown();server.server_close()


if __name__ == '__main__':
    main()
