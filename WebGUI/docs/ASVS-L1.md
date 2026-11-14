# Security checklist: ASVS 5.0, level 1

The web tool gone through against the OWASP Application Security Verification Standard, version 5.0.0, level 1.
The chapter and requirement numbers are those of the standard. The requirement texts here are shortened: the
standard's own words decide.

## What is checked

The tool is a static site: HTML, CSS, JavaScript modules, the generators' Python files, fonts and a backup copy
of Pyodide, served by GitHub Pages. It has no server code of its own, no accounts, no cookies, no storage in
the browser, and it sends nothing anywhere. The Python generator runs in the visitor's browser, inside a Web
Worker. The one other host the page talks to is the CDN folder of the pinned Pyodide version
(`WebGUI/vendor.json`); when it does not answer, the page uses its own checked copy.

What comes in from outside, and is treated as not trusted:

| Input | Where it is read |
|---|---|
| The share link (`#single=`, `#dual=`, the older `#d=`) | `app/share.js` `readHash`, `applyDesign` |
| Imported files: `.txt`, `.py`, `.zip` | `app/share.js`, `WebGenerator.py` `read_import`, `_literals` |
| What is typed into a setting | `app/fields.js`, `app/core.js` `typedNumber`; the generator checks every value |
| A message from the page that frames the tool (the blog) | `app/main.js`, the `message` listener |
| The address of the page (`?…`) | `app/main.js` `pythonSources`: no parameter can name another source of code (`?pyodide=` is read only on `localhost`, for an address of that same computer) |

Each "Tested by" names a test in `WebGUI/tests/`. They run on Chromium, Firefox and WebKit on every pull
request into `WebUI`.

## V1 Encoding and sanitization

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 1.2.1 | Output is encoded for the place it is put (HTML, attribute, CSS) | Met | The page is built with DOM calls only (`el()`, `textContent`, `setAttribute`); there is no `innerHTML`, `outerHTML`, `insertAdjacentHTML` or `document.write` in the code. The generator's printed lines, file names, imported names and messages are text nodes. Tested by `security.spec.js` (a full visit breaks no policy) and `share.spec.js` (hostile names). |
| 1.2.2 | URLs built from untrusted data are encoded, and only safe schemes are used | Met | The page builds two kinds of address: the share link (base64url of the design, checked by `^#(single\|dual\|d)=[A-Za-z0-9_-]*$`) and `blob:` addresses of files it made itself. The address the blog passes for Share must start with `http://` or `https://` and is cut at 500 characters. |
| 1.2.3 | Output put into JavaScript or JSON is encoded | Met | Values cross to the worker as structured messages and as JSON made by `JSON.stringify` and `json.dumps`. No code is put together from text. |
| 1.2.4 | Database queries are parameterised | Not applicable | No database. |
| 1.2.5 | No operating system command injection | Not applicable | No operating system commands: Python runs in WebAssembly, in the browser's sandbox. |
| 1.3.1 | HTML from untrusted sources is sanitised | Not applicable | The page takes no HTML from anywhere. |
| 1.3.2 | No `eval()` or other run-time code from untrusted input | Met | The page has no `eval`, `new Function` or timer with a text. The security policy allows no inline script. In Python, imported files are read with `ast.literal_eval`, one assignment at a time, never run: tested by `test_bridge.py` `test_text_that_is_not_values_is_never_run`. The values a visitor sets are written into the parameter files as Python literals made by `_py_literal` (`test_text_values_are_written_safely`, `test_a_text_beyond_the_basic_plane_reaches_the_board_as_it_was_typed`). |
| 1.5.1 | XML parsers are set up safely | Not applicable | No XML is parsed. |

## V2 Validation and business logic

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 2.1.1 | The rules for input are written down | Met | The rules are the generator's own table of settings (`ParameterRules.py`), which the page reads and shows: kind, range and choices of every setting. `test_bridge.py` holds the page's table against it. |
| 2.2.1 | Input is checked against what is allowed | Met | Every value is checked by the generator's own checker before a run and while typing; a value it refuses is named under its setting. A link or a file can only set names the generator has, to values a setting can hold (`_holdable`, `plain`). Tested by `settings.spec.js`, `share.spec.js`, `test_bridge.py`. |
| 2.2.2 | Checks are made where they cannot be skipped | Met, as far as it applies | There is no server to protect: the checks protect the visitor's own run, and they run in the same place as the generator. |
| 2.3.1 | Steps happen only in their order | Met | No run starts before Python has loaded, during another run, or while the other generator's settings are read; a download is offered only for the board on show. Tested by `states.spec.js`. |

## V3 Web frontend security

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 3.2.1 | Content is not rendered in a wrong context | Met | The site holds only its own files, served with their types; the page shows files of a run as text or as pictures it made itself. |
| 3.2.2 | Text is shown as text | Met | See 1.2.1. |
| 3.3.1 | Cookies have the Secure attribute | Not applicable | No cookies. |
| 3.4.1 | Strict-Transport-Security | Met by the host | GitHub Pages serves the site over HTTPS only and sends the header for `github.io`. |
| 3.4.2 | CORS allows only trusted origins | Not applicable | The site answers no cross-origin requests with data of a visitor: it has none. |
| 3.4.3 | A Content-Security-Policy is set | Met | Written into every page by `tools/build_site.py`: `default-src 'none'`, scripts from the site and the one CDN folder (plus WebAssembly), styles, fonts and pictures from the site, `base-uri 'none'`, `form-action 'none'`, `object-src 'none'`. No inline script or style anywhere. The policy is a `<meta>` tag because GitHub Pages sets no headers of ours. Tested by `security.spec.js` "the page carries the policy the build wrote, and a full visit breaks none of it"; every other test fails on any violation (`tests/frame.js`). |
| 3.4.4 | `X-Content-Type-Options: nosniff` | Left to the host | GitHub Pages decides the headers; a site on it cannot set its own. The page's scripts are modules and its worker a module worker, which a browser runs only when they are served as JavaScript, and the policy allows scripts from two places only. |
| 3.4.5 | A referrer policy | Met | `<meta name="referrer" content="strict-origin-when-cross-origin">`, and the share link keeps the design after the `#`, which no browser sends. |
| 3.4.6 | `frame-ancestors` limits who may frame the page | Not met, accepted | It cannot be set in a `<meta>` tag, and the tool is made to be framed by the blog. A page that frames the tool can show its own address in Share; it gets nothing from the tool, which holds no secrets. The listener for the frame's message takes only two texts, checked, from the parent window. |
| 3.5.1 to 3.5.3 | Protection against forged requests | Not applicable | Nothing on a server changes; there are no requests with a visitor's rights. |
| 3.6.1 | Outside code is loaded with an integrity check, or from the site | Met | All code is the site's own, except Pyodide from one pinned CDN folder. Pyodide checks the numpy wheel against the hash in its lock file; the site's backup copy is checked file by file against `vendor.json` at build time and again in the tests. Tested by `security.spec.js` "the CDN sends a numpy that is not the one Pyodide names: it is refused". No address parameter can name another source: "a link cannot point the page at another copy of Python". |
| 3.7.1 | Only technologies browsers still support | Met | No plug-ins, no Flash, no ActiveX. |
| 3.7.2 | Redirects go only to allowed places | Met | The page redirects nowhere. Its outside links are fixed in the code (the repository, the wiki, the blog) and open with `rel="noopener"`. |

## V4 API and web service

Not applicable: the site offers no API and calls none. The page fetches only its own files and Pyodide's.

## V5 File handling

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 5.2.1 | Files are limited in size | Met | A file over 8 MB is not read (`app/share.js`); at most 64 files and 8 MB of text are read in one import, a line over 4000 characters is not a setting, a text over 1000 characters is no value (`WebGenerator.py`). Tested by `share.spec.js` "a file with no settings, and a file that is too large, are refused with a reason", `test_bridge.py` `test_a_file_saved_by_notepad_and_a_line_too_long_to_be_a_setting`. |
| 5.2.2 | A file is what its name says | Met | Only `.txt`, `.py` and `.zip` are taken, and their content decides: a file with no settings is refused with a reason. |
| 5.3.1 | Uploaded files are never run | Met | See 1.3.2. Files never leave the browser. |
| 5.3.2 | File names cannot reach other paths | Met | Of a name in a zip only the last part is used, and only as a label; an imported file is never written under its own name. |

## V6 to V10 Authentication, sessions, authorisation, tokens, OAuth

Not applicable: the tool has no accounts, no sign-in, no sessions, no rights and no tokens. Every visitor can do
the same thing: run the generator on their own computer.

## V11 Cryptography

Not applicable: the tool keeps no secrets and encrypts nothing. SHA-256 is used only to check the files of
Pyodide.

## V12 Secure communication

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 12.1.1 | Only current TLS versions | Met by the hosts | GitHub Pages and jsDelivr. |
| 12.2.1 | HTTPS for everything | Met | The site is HTTPS only; the policy allows connections to the site and the one CDN folder, both HTTPS. Tests fail on any request to another server. |
| 12.2.2 | Certificates everyone trusts | Met by the hosts | |

## V13 Configuration

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 13.4.1 | No source control folders, backups or test files on the site | Met | `tools/build_site.py` builds the site as a folder of its own: the page's files of the known types, the generators' Python files as one zip, the pictures of the help boxes and the checked copy of Pyodide. `tests/`, `tools/`, `docs/`, the package files and everything outside `WebGUI/` are left out. |
| 13.4.2 | No debug mode in production | Met | The page has none. |
| 13.4.5 | No needless information about the system | Met | The footer shows the build's commit, which is public. |

## V14 Data protection

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 14.2.1 | No sensitive data in addresses | Met | The share link holds the settings of a board, after the `#`. Nothing personal is asked for. |
| 14.3.1 | Client-side data is cleared when the session ends | Met | The page stores nothing: no cookies, no local storage, no IndexedDB of its own. A reload starts from the published values or the link. See `privacy.html`. |

## V15 Secure coding and architecture

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 15.1.1 | Outside components are listed, with a time to update them | Met | `vendor.json` (Pyodide and numpy, by version and hash), `package-lock.json` (the test tools: Playwright and axe, not part of the site), the fonts in `fonts/` with their licences. `licenses.html` lists them for the visitor. An update is a change of `vendor.json` with `tools/vendor_lock.py --update`; the build refuses a copy that does not match. |
| 15.2.1 | No component with a known weakness | Met at the time of writing | Pyodide 314.0.7; GitHub's Dependabot reads the default branch only, so the file for it is handed to the owner for `main`. |
| 15.3.1 | Only the needed data is returned | Not applicable | Nothing is returned to anyone. |

## V16 Logging and error handling

| # | Requirement, in short | Status | How |
|---|---|---|---|
| 16.5.1 | Errors show no sensitive detail | Met | An error of the generator is shown to the visitor on their own computer, with "Show the details" and "Report A Problem", which opens a new issue with nothing filled in but what the visitor sends. |
| 16.5.2 | The tool keeps working, safely, when something outside fails | Met | CDN refused, stalled or changed: Python comes from the site. No source answers: the page says so. A crash of the generator: the worker starts again. Tested by `security.spec.js`, `states.spec.js`. |

There is no logging: nothing is recorded about a visit.

## V17 WebRTC

Not applicable.

## How to check again

```
cd WebGUI
npx playwright test security share states      # the tests named above
python -m unittest tests/test_bridge.py        # from the repository folder: WebGUI/tests/test_bridge.py
grep -rn "innerHTML\|eval(\|new Function" app boot.js PyodideWorker.js   # must find nothing
```
