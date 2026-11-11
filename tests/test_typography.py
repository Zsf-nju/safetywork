"""Readable sidebar text, actual font loading and populated six-week calendars."""
from test_workspace import BASE, OUT
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE+'/#studio')
    page.locator('[data-action="demo"]').click()
    page.locator('.bar nav [href="#studio"]').click()
    for lang in ['en','zh-CN']:
        page.locator('[data-lang="'+lang+'"]').click()
        page.evaluate('document.fonts.ready')
        for family, weight, sample in [('Fraunces',500,'Research'),('DM Sans',400,'Research'),('DM Sans',500,'Research'),('DM Sans',600,'Research'),('DM Sans',700,'Research'),('Safetywork Serif SC',600,'研究')]:
            loaded=page.evaluate('async ([family,weight,sample]) => (await document.fonts.load(`${weight} 20px "${family}"`,sample)).length', [family,weight,sample])
            assert loaded, (family, weight)
        for selector, minimum in [('.panel-title h2',20),('.workflow-row strong',15),('.deadline-row strong',15),('.record-preview strong',15),('.record-preview time',12),('.deadline-row small',12),('.deadline-row time',12),('.workflow-count',12)]:
            sizes=page.locator(selector).evaluate_all('(els)=>els.map(e=>parseFloat(getComputedStyle(e).fontSize))')
            assert sizes and min(sizes)>=minimum,(selector,sizes)
        expect(page.locator('.archive-heading h2')).to_have_text('Project archive' if lang=='en' else '项目档案')
        expect(page.locator('.studio-index .panel-title h2').first).to_have_text('Stage progress' if lang=='en' else '阶段进度')
        # A smaller desktop and a phone must not overflow after text enlargement.
        for width in [1024,768,390]:
            page.set_viewport_size({'width':width,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(lang,width)
        page.set_viewport_size({'width':1440,'height':900})
        page.locator('#toast').evaluate('(e)=>e.classList.remove("visible")')
        page.screenshot(path=str(OUT/f'typography-studio-{lang}.png'),full_page=True)
    page.locator('[data-lang="en"]').click()
    page.locator('[data-action="new-project"]').first.click()
    form=page.locator('#dialog-form')
    form.locator('[name=title]').fill('Six-week month / full deadline')
    form.locator('[name=goal]').fill('Check a populated final week at laptop and phone sizes.')
    form.locator('[name=start]').fill('2026-03-01')
    form.locator('[name=due]').fill('2026-03-31')
    form.locator('[type=submit]').click()
    expect(page.locator('#modal')).not_to_be_visible()
    page.locator('.bar nav [href="#calendar"]').click()
    # Navigate to a known six-week month regardless of the test runner's date.
    while page.locator('.month-panel .toolbar h2').inner_text()!='March 2026':
        page.locator('[data-action="month-prev"]').click()
    for lang in ['en','zh-CN']:
        page.locator('[data-lang="'+lang+'"]').click()
        for size in [{'width':1280,'height':720},{'width':1366,'height':768},{'width':390,'height':844}]:
            page.set_viewport_size(size)
            expect(page.locator('.day')).to_have_count(42)
            grid=page.locator('.calendar-grid').bounding_box()
            assert grid['y']+grid['height']<=size['height'],(lang,size,grid)
            more=page.locator('.more-events[data-id="2026-03-31"]')
            b=more.bounding_box()
            cell=more.locator('..').bounding_box()
            assert b['y']+b['height']<=cell['y']+cell['height'],(lang,size,b,cell)
            more.click()
            expect(page.locator('#modal .agenda-item')).to_have_count(2)
            page.locator('[data-action="close-modal"]').click()
            page.screenshot(path=str(OUT/f'typography-calendar-{lang}-{size["width"]}.png'))
    assert not errors, errors
    browser.close()
    print('PASS: fonts load locally, sidebar reading sizes, concise bilingual headings, tablet/mobile width, populated final-week overflow and full month visibility.')
