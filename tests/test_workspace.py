"""End-to-end acceptance tests. Run under with_server.py (see README)."""
from pathlib import Path
from datetime import date, timedelta
import json
import os
import http.server
import threading
from functools import partial
from playwright.sync_api import sync_playwright, expect

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass

SERVER = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(Path(__file__).resolve().parent.parent)))
threading.Thread(target=SERVER.serve_forever, daemon=True).start()
BASE = os.environ.get('SAFETYWORK_TEST_URL', f'http://127.0.0.1:{SERVER.server_port}').rstrip('/')
OUT = Path(__file__).resolve().parent.parent / 'artifacts'
OUT.mkdir(exist_ok=True)

def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        expect(page.get_by_role('heading', name='Safety research.')).to_be_visible()
        page.screenshot(path=str(OUT/'home-desktop.png'), full_page=True)

        def click(action, root=None):
            (root or page).locator(f'[data-action="{action}"]').first.click()

        def modal(): return page.locator('#modal')

        def submit():
            modal().locator('button[type="submit"]').click()
            expect(modal()).not_to_be_visible()

        def goto_stage(name):
            page.locator('.stage-nav').get_by_role('link', name=name).click()
            expect(page.locator('.tool-header h2')).to_contain_text(name)

        def capture(name):
            page.screenshot(path=str(OUT/name), full_page=True)

        # Project creation, date constraints, default stages, roadmap & persistence.
        click('new-project')
        modal().locator('[name=title]').fill('Agent reliability study')
        modal().locator('[name=direction]').fill('Agent safety')
        start = date.today()
        due = start + timedelta(days=30)
        modal().locator('[name=start]').fill(start.isoformat())
        modal().locator('[name=due]').fill((start-timedelta(days=1)).isoformat())
        modal().locator('[name=goal]').fill('Record reproducible safety evaluations and decisions.')
        modal().locator('button[type=submit]').click()
        expect(modal().locator('.form-error')).to_contain_text('Deadline must')
        modal().locator('[name=due]').fill(due.isoformat())
        submit()
        expect(page.locator('.stage-nav .stage-link')).to_have_count(7)
        project_url = page.url
        page.reload()
        expect(page.locator('.project-summary h1')).to_have_text('Agent reliability study')

        # Uploaded PDF, reading card, reflection, global collection, preview, original download.
        click('new-paper')
        modal().locator('[name=title]').fill('A paper to question <not HTML>')
        modal().locator('[name=authors]').fill('A. Researcher')
        modal().locator('[name=year]').fill('2026')
        modal().locator('[name=status]').select_option('Read')
        pdf_bytes = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'
        modal().locator('[name=pdf]').set_input_files({'name':'test-paper.pdf','mimeType':'application/pdf','buffer':pdf_bytes})
        modal().locator('[name=feelings]').fill('Clear framing; the scope needs more care.')
        modal().locator('[name=findings]').fill('Compare context shifts with a fixed seed.\nQuestion the baseline.')
        submit()
        expect(page.locator('.paper-card h3')).to_have_text('A paper to question <not HTML>')
        click('open-pdf')
        expect(modal().locator('iframe')).to_be_visible()
        with page.expect_download() as dl:
            modal().get_by_role('link',name='Download PDF').click()
        original = OUT/'downloaded-paper.pdf'
        dl.value.save_as(str(original))
        assert original.read_bytes() == pdf_bytes
        click('close-modal',modal())
        page.get_by_role('link',name='Paper library',exact=True).click()
        expect(page.locator('.paper-card')).to_have_count(1)
        page.locator('#paper-search').fill('nonexistent')
        expect(page.locator('.paper-card')).to_have_count(0)
        page.locator('#paper-search').fill('baseline')
        expect(page.locator('.paper-card')).to_have_count(1)
        page.locator('#reading-filter').select_option('To read')
        expect(page.locator('.paper-card')).to_have_count(0)
        page.locator('#reading-filter').select_option('Read')
        capture('paper-library.png')
        page.goto(project_url)

        # Milestone dates, custom stage, notes, checklist.
        click('new-stage')
        modal().locator('[name=title]').fill('Threat model review')
        modal().locator('[name=type]').select_option('custom')
        modal().locator('[name=goal]').fill('Review assumptions on Friday at 15:00.')
        modal().locator('[name=due]').fill((due+timedelta(days=1)).isoformat())
        modal().locator('button[type=submit]').click()
        expect(modal().locator('.form-error')).to_contain_text('within the project')
        modal().locator('[name=due]').fill(due.isoformat())
        submit()
        expect(page.locator('.tool-header h2')).to_have_text('Threat model review')
        page.locator('#notes-form textarea').fill('Assumptions: model access, task distribution, and evaluation scope.')
        expect(page.locator('#storage-status')).to_contain_text('Saved on this browser')
        # Draft must survive navigation without pressing Save.
        goto_stage('Idea planning')
        goto_stage('Threat model review')
        expect(page.locator('#notes-form textarea')).to_have_value('Assumptions: model access, task distribution, and evaluation scope.')
        page.locator('#notes-form button').click()
        click('add-check')
        modal().locator('[name=text]').fill('Validate assumptions with supervisor')
        submit()
        page.locator('[data-check]').check()
        expect(page.locator('.check-row.done')).to_have_count(1)
        page.reload()
        expect(page.locator('[data-check]')).to_be_checked()
        expect(page.locator('#notes-form textarea')).to_have_value('Assumptions: model access, task distribution, and evaluation scope.')

        # Idea board creation, editing, connector, drag persistence and SVG download.
        goto_stage('Idea planning')
        for title in ['Question', 'Method']:
            click('new-node')
            modal().locator('[name=title]').fill(title)
            modal().locator('[name=detail]').fill('A carefully stated '+title.lower())
            if title=='Method': modal().locator('[name=x]').fill('430')
            submit()
        page.locator('[data-node]').first.click()
        click('edit-node')
        modal().locator('[name=title]').fill('Research question')
        submit()
        click('connect')
        submit()
        expect(page.locator('.connection')).to_have_count(1)
        node = page.locator('[data-node]').first
        box=node.bounding_box()
        page.mouse.move(box['x']+45,box['y']+12)
        page.mouse.down()
        page.mouse.move(box['x']+100,box['y']+70,steps=8)
        page.mouse.up()
        moved=node.evaluate('(el)=>[el.style.left,el.style.top]')
        expect(page.locator('#storage-status')).to_contain_text('Saved on this browser')
        page.reload()
        assert page.locator('[data-node]').first.evaluate('(el)=>[el.style.left,el.style.top]') == moved
        expect(page.locator('.connection')).to_have_count(1)
        with page.expect_download() as dl: click('export-board')
        dl.value.save_as(str(OUT/'board.svg'))
        assert 'Research question' in (OUT/'board.svg').read_text('utf-8')
        capture('idea-board.png')

        # Algorithms: versions have independent contents and retain prior work.
        goto_stage('Algorithm design')
        click('new-version')
        page.locator('#version-form [name=code]').fill('for task in tasks:\n    record(task, seed=42)')
        page.locator('#version-form [name=notes]').fill('Baseline procedure.')
        page.locator('#version-form [type=submit]').click()
        click('new-version')
        expect(page.locator('#version-form [name=code]')).to_contain_text('seed=42')
        page.locator('#version-form [name=code]').fill('for task in tasks:\n    compare(task, seeds=[42,43])')
        page.locator('#version-form [type=submit]').click()
        page.locator('[data-action=select-version]').first.click()
        expect(page.locator('#version-form [name=code]')).to_have_value('for task in tasks:\n    record(task, seed=42)')
        with page.expect_download() as dl: click('download-code')
        dl.value.save_as(str(OUT/'algorithm.txt'))
        capture('algorithm-notebook.png')

        # Experiment table: new columns, cells, reload, CSV.
        goto_stage('Experiment validation')
        click('add-column')
        modal().locator('[name=name]').fill('GPU hours')
        submit()
        click('add-row')
        cells=page.locator('td input')
        for i,value in enumerate(['baseline','seed=42','ASR','0.12','Check confidence interval','2.5']):
            cells.nth(i).fill(value)
            cells.nth(i).press('Tab')
        expect(page.locator('#storage-status')).to_contain_text('Saved on this browser')
        page.reload()
        expect(page.locator('td input').nth(3)).to_have_value('0.12')
        expect(page.locator('td input').nth(5)).to_have_value('2.5')
        with page.expect_download() as dl: click('export-csv')
        dl.value.save_as(str(OUT/'experiments.csv'))
        assert 'GPU hours' in (OUT/'experiments.csv').read_text('utf-8-sig')
        capture('experiments.png')

        goto_stage('Benchmark testing')
        click('add-check')
        modal().locator('[name=text]').fill('Record dataset release version')
        submit()
        page.locator('[data-check]').check()
        click('add-row')
        expect(page.locator('tbody tr')).to_have_count(1)

        # Writing URL validation, saved link, notes.
        goto_stage('Final writing')
        click('set-overleaf')
        modal().locator('[name=url]').fill('https://example.com/test')
        modal().locator('[type=submit]').click()
        expect(modal().locator('.form-error')).to_contain_text('overleaf.com')
        modal().locator('[name=url]').fill('https://www.overleaf.com/project/example-project')
        submit()
        expect(page.get_by_role('link',name='Open in Overleaf')).to_have_attribute('href','https://www.overleaf.com/project/example-project')
        page.locator('#notes-form textarea').fill('Updated the evaluation paragraph. Next: figures.')
        page.locator('#notes-form button').click()
        page.locator('#stage-status').select_option('done')
        expect(page.locator('.project-dates')).to_contain_text('1 of 7')

        # Manual update and auto activities.
        page.locator('.stage-nav').get_by_role('link',name='Update journal').click()
        click('new-update')
        modal().locator('[name=title]').fill('Weekly research reflection')
        modal().locator('[name=body]').fill('Changed the seed protocol. Found a confound. Next: rerun controls.')
        submit()
        expect(page.locator('.journal')).to_contain_text('Weekly research reflection')
        expect(page.locator('.journal')).to_contain_text('Experiment result updated')
        capture('update-journal.png')

        # Calendar includes all project and sub-deadlines, exports ICS, filter persists.
        page.get_by_role('link',name='Calendar',exact=True).click()
        expect(page.locator('.calendar-grid')).to_be_visible()
        expect(page.locator('.event').filter(has_text='Literature review')).to_be_visible()
        with page.expect_download() as dl: click('export-ics')
        dl.value.save_as(str(OUT/'deadlines.ics'))
        ics=(OUT/'deadlines.ics').read_text()
        assert ics.count('BEGIN:VEVENT') == 8
        assert 'Threat model review' in ics
        capture('calendar.png')

        # Full backup, rejected malformed import, replacement restore with original PDF.
        click('settings')
        # A malformed backup must not replace a healthy workspace.
        click('import-backup',modal())
        submit()
        page.locator('#backup-input').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'{"format":"safetywork-backup","version":1,"state":{}}'})
        expect(page.locator('#toast')).to_contain_text('Restore failed')
        click('settings')
        with page.expect_download() as dl: click('export-backup',modal())
        backup_path = OUT/'workspace-backup.json'
        dl.value.save_as(str(backup_path))
        backup = json.loads(backup_path.read_text('utf-8'))
        assert len(backup['state']['projects']) == 1
        assert len(backup['pdfs']) == 1
        assert backup['state']['projects'][0]['stages'][4]['table']['rows'][0]['cells'][3]=='0.12'
        click('close-modal',modal())

        page.locator('.bar nav').get_by_role('link',name='Design studio',exact=True).click()
        capture('studio.png')
        page.locator('.project-card a').first.click()
        click('delete-project')
        submit()
        expect(page.locator('.project-card')).to_have_count(0)
        click('settings')
        click('import-backup',modal())
        submit()
        page.locator('#backup-input').set_input_files(str(backup_path))
        expect(page.locator('.project-card')).to_have_count(1)
        page.locator('.project-card a').first.click()
        expect(page.locator('.paper-card')).to_have_count(1)
        click('open-pdf')
        with page.expect_download() as dl: modal().get_by_role('link',name='Download PDF').click()
        restored = OUT/'restored.pdf'
        dl.value.save_as(str(restored))
        assert restored.read_bytes() == pdf_bytes
        click('close-modal',modal())

        # Archiving changes the project index; unarchive returns it to active work.
        click('archive')
        expect(page.locator('.project-summary')).to_contain_text('ARCHIVED')
        page.locator('.bar nav').get_by_role('link',name='Design studio',exact=True).click()
        expect(page.locator('.project-card')).to_have_count(0)
        page.locator('#project-filter').select_option('archived')
        expect(page.locator('.project-card')).to_have_count(1)
        page.locator('.project-card a').first.click()
        click('archive')

        # Default workflow example is optional, explicitly labelled, and editable.
        page.locator('.bar nav').get_by_role('link',name='Design studio',exact=True).click()
        click('demo')
        expect(page.locator('.project-summary')).to_contain_text('EXAMPLE')
        goto_stage('Idea planning')
        expect(page.locator('[data-node]')).to_have_count(3)
        expect(page.locator('.connection')).to_have_count(2)

        # Desktop and narrow-screen layout has no unintended horizontal overflow.
        for hash_route in ['#home','#studio','#calendar','#library',project_url.split('#')[1]]:
            page.set_viewport_size({'width':390,'height':844})
            page.goto(BASE+'/#'+hash_route.lstrip('#'))
            page.wait_for_load_state('networkidle')
            overflow=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,els:[...document.querySelectorAll("body *")].filter(e=>e.getBoundingClientRect().right>innerWidth).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right]).slice(0,10)})')
            assert overflow['scroll'] <= overflow['width'], (hash_route,overflow)
        page.goto(BASE+'/#home')
        capture('home-mobile.png')
        assert not errors, errors
        browser.close()
        print('PASS: all requested tools, persistence, PDFs, backup round trip, date constraints, calendar, exports, and mobile layouts.')

if __name__=='__main__': run()
