# safetywork

A personal AI safety research workspace, from the first question to the final draft.

Live site: https://zsf-nju.github.io/safetywork/

## Beta 02 — languages and research overview

Use **EN / 简中** in the top bar to switch between English and Simplified Chinese. The selection persists in the current browser. Interface strings and dates are localized; project names, reading reflections, pseudocode, and experiment cells retain their original content. Existing workspace databases and backup formats remain compatible.

The Design studio now combines a deep-green research overview with split-number counters, a deadline queue, detailed project dossiers, segmented stage progress, a workflow index, and recent activity. The visual structure takes cues from the reference site's editorial panels and research indexes.

The monthly calendar uses only the required 4–6 week rows and a viewport-sized grid. Crowded days show a summary and a button opening all deadlines in a dialog, so additional events never stretch the month. Upcoming deadlines appear in a separately scrolling side panel on desktop. Six-row months are checked at 1440×900, 1366×768, 1280×720, and 390×844.

Run the additional language and layout acceptance suite with `python tests/test_locale_layout.py`. It verifies language persistence, Chinese forms and reading filters, canonical stored status values, unchanged user content, day-overflow dialogs, mobile layouts, and whole-month visibility.

## Research workflow

- **Home**: purpose, workflow overview, and entry into the design studio. No trending feed or animated research graph.
- **Design studio**: create projects with goals, direction, start date, expected deadline, and a customizable roadmap. The default six stages get an initial distribution of dates within the project period. Each milestone can be renamed, rescheduled, and given specific deliverables and time arrangements. Statuses: planned, in progress, blocked, done.
- **Literature review**: PDF upload (30 MB per file), title/authors/year, reading status, reflections, findings/questions. Preview, open, download, edit, or remove a paper.
- **Idea planning**: drag cards on a dotted board; edit the kind, title, details, or precise position; connect cards with directed edges. Remove cards/connections and export the board as SVG.
- **Algorithm design**: multiple notebook versions with pseudocode/code flow and reasoning. New versions copy the selected notebook; older versions remain independently editable. Drafts autosave. Explicit Save records an activity, and text download is available.
- **Benchmark testing**: reproducibility checklist plus a configurable evaluation-run table.
- **Experiment validation**: add/remove runs and columns, rename columns, edit results/config/metrics/findings, export CSV. Cells save when focus leaves them. Add multiple experiment milestones if you need separate tables.
- **Final writing**: a validated HTTPS Overleaf link opens the real writing project in a new tab. Writing checklist and revision notes are stored here. This is a link integration, not an embedded Overleaf editor.
- **Custom milestones**: flexible notebook and checklist for steps such as threat modeling, supervision meetings, or ethics/data review.
- **Update journal**: automatic activity history and editable, manually written updates for findings, blockers, and next steps.
- **Calendar**: monthly grid containing project and milestone deadlines, project filters, overdue/completed styling, upcoming agenda, .ics export.
- **Paper library**: all uploaded papers across projects, with project and reading-state filters plus full-text search over titles, authors, reflections, and findings.
- **Extras**: project search, progress indicators, archiving, explicit destructive-action confirmation, optional labelled example project, and complete backup/restore.

## Storage and privacy

This release is a **single-browser, local-first static app**. Records live in IndexedDB; PDFs are stored as Blobs, not in localStorage. Metadata and PDF changes are committed in the same database transaction. App source is public on GitHub; private research records and PDFs are never pushed there by the app.

No account service, automatic cloud synchronization, or shared multi-user workspace is configured. The website can be accessed from different devices, but records do not synchronize automatically. Use **Data & backup → Export full backup**, then **Restore backup** on the destination browser. Backups include the original PDF files and all project data. Restore validates the format, record identifiers, tool structures, and referenced PDFs before replacing the current workspace. Restoring replaces existing data; export first if needed.

Browser data can be cleared or evicted. The app provides a persistent-storage request, but browser permission is not guaranteed. Keep regular backups outside the browser. Private/incognito windows may discard data on exit. All pages on the same `github.io` origin share the browser's origin-level storage quota; this app uses its own named database.

Changing the website domain also changes the storage origin: export before moving. Backups over 300 MB are rejected by the current importer, so split large collections into separate browser workspaces or reduce PDF sizes before reaching that limit.

## Local development

No Node build or package installation is required:

```powershell
cd "G:\vibe coding\safetywork"
python -m http.server 5187 --bind 127.0.0.1
```

Open http://127.0.0.1:5187/. Use a local HTTP server rather than opening `index.html` as a file because the app loads ES modules.

Source layout:

- `index.html`: application shell and accessibility landmarks
- `styles.css`: responsive design
- `app.js`: routes, editors, project workflows, import/export
- `db.js`: IndexedDB transactions
- `schema.js`: backup validation
- `tests/test_workspace.py`: browser acceptance tests

Typography uses Google Fonts with local fallbacks. No external scripts, paid APIs, or credentials are required.

## Verification

Requires Python Playwright and a local Microsoft Edge installation:

```powershell
python tests/test_workspace.py
```

The test starts a temporary HTTP server in-process, uses an isolated browser context, exercises every research tool, checks reload persistence and full PDF backup restoration, and verifies mobile layout. Screenshots/downloads are generated under ignored `artifacts/` (test data is never published).

To exercise the deployed site in an isolated browser instead:

```powershell
$env:SAFETYWORK_TEST_URL = 'https://zsf-nju.github.io/safetywork/'
python tests/test_workspace.py
Remove-Item Env:SAFETYWORK_TEST_URL
```

## Deployment

GitHub Pages publishes the root of `main`. Push changes to `origin/main` and wait for `pages-build-deployment` to finish. Keep `.nojekyll`. No backend configuration or server secrets are needed.

Design reference: [AI Safety Index](https://gabrygao.github.io/ai-safety-index/) for its calm research-oriented structure and organization. This project has its own layout and code; its purpose is recording personal research progress.
