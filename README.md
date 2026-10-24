# Dr. Mohamed Elgindi — Law Firm Website

Bilingual (Arabic / English) Django website for **د. محمد الجندي — Dr. Mohamed Elgindi**, a law firm handling criminal cases, felony cases and cassation appeals.

**Status:** the home page, the Videos page and the About Us page are built. The About page has a cinematic hero and a gold centre line, from the logo's rule, that grows as the visitor scrolls, with sections alternating on either side (firm, practice areas, team, principles, consultation). Its text is in `core/content.py` under `about_page`; its photos go in `static/images/about/` (see the README there). The Contact Us page is built on light grounds: a hero composed like the logo (text | gold rule | the firm's business card), three routes by situation (urgent, case in court, enquiry/appointment), the consultation form (shared with the home page) and the office visit details. Only Articles is still routed to an "in preparation" page (marked *Soon* / *قريبًا* in the navigation and excluded from search engines with `noindex`).

## Requirements

- Python 3.12+ (developed on 3.13)
- No paid services. Fonts load from Google Fonts.

## Run locally (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then fill in what the firm has supplied
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open <http://127.0.0.1:8000/>. It redirects to `/ar/` or `/en/` based on the browser language. Arabic is the default.

macOS / Linux: use `source .venv/bin/activate`, then `python ...` with the same commands.

### Viewing consultation requests

Form submissions are saved to the database (SQLite in development). To read them:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Then open <http://127.0.0.1:8000/admin/> → *Consultation requests*. Nobody is notified automatically yet; see "Not done yet".

### Site photos

Admin → *Site photos* → *Add*: choose a slot (home portrait, home office, About hero and sections 01–05), upload a JPG/PNG/WebP up to 5 MB, and add an Arabic description (English optional). The recommended size is shown for each slot. Replacing the image deletes the old file. Without an upload, the slot falls back to the static file in `static/images/…`, then to the marked placeholder.

Uploads are stored in `media/` (not in Git). **On the live site, `media/` must be persistent storage**: either a persistent disk on the host, or object storage such as Cloudflare R2 / Amazon S3 (adds `django-storages`). Files on a host's own app disk are usually lost on redeploy.

### Adding videos

Videos are hosted on YouTube; the site stores only the link.

1. Upload the video to the firm's YouTube channel (public or unlisted).
2. Open <http://127.0.0.1:8000/admin/> → *Videos* → *Add video*.
3. Paste the YouTube link (watch, youtu.be, Shorts and live links all work), add the Arabic title, and optionally the English title and the descriptions.
4. Optionally choose a *topic* and enter the *duration* as shown on YouTube (e.g. `7:05`).
5. Save. All published videos appear on `/ar/videos/` and `/en/videos/` (12 per page, filterable by topic).

**Home page and spotlight:** tick *featured* and set *featured order* (1, 2, 3). The home page shows the featured videos in that order, topped up with the newest ones if fewer than three are featured. Featured video no. 1 is also the large spotlight at the top of the Videos page. Both can be edited straight from the video list in the admin.

The firm's first 12 videos are loaded by migration `core/migrations/0004_load_firm_videos.py`: YouTube titles with hashtags removed and spelling tidied, YouTube dates and durations, and no English titles yet.

- Untick *Show on website* to hide a video without deleting it.
- Without an English title, the English site shows the Arabic title (correctly right-to-left). Without an English description, none is shown.
- Only the YouTube thumbnail loads with the page. The player (`youtube-nocookie.com`, privacy-enhanced) loads when a visitor presses play. Without JavaScript, the thumbnail opens the video on YouTube.
- Videos set to *Private* or with embedding disabled on YouTube will not play on the site.

### Tests

```powershell
.\.venv\Scripts\python.exe manage.py test core
```

## Project layout

```text
config/                 settings (reads .env), root URLs (/admin/ + /ar/ /en/)
core/
  content.py            ALL interface text, Arabic and English: edit copy here
  context_processors.py language, direction, nav, firm details for every template
  forms.py              consultation form: server validation, honeypot
  models.py             ConsultationRequest
  views.py              home page; "in preparation" view for the other pages
  tests.py              routing, RTL/LTR, placeholders, form validation, CSRF
templates/
  base.html             <html lang dir>, meta/SEO, fonts, header/footer
  partials/logo.html    Concept 05 logo lockup (live text)
  core/home.html        home page sections
  core/pending.html     "in preparation" page
static/
  css/style.css         design tokens (:root) + all styles, RTL-aware
  js/main.js            menu, header state, reveal-on-scroll, form shortcuts
  images/favicon.svg    E | ج mark from Concept 05
  images/photos/        drop lawyer.jpg / office.jpg here (see README inside)
```

## Brand

The site follows the approved **Concept 05, "Bilingual balance"**, in the version with the enlarged *DR. MOHAMED / د. محمد*:

| Token | Value | Use |
|---|---|---|
| `--ink` | `#171717` | main dark ground, text on light |
| `--gold` | `#B89A5E` | accents on dark grounds |
| `--gold-deep` | `#7D6436` | accents and small text on light grounds (gold on ivory is too faint) |
| `--ivory` | `#F5F1E8` | light ground, text on dark |

Fonts: **Jost** + **Reem Kufi** (from the logo), **IBM Plex Sans Arabic** for Arabic body text.

The logo is rebuilt as live HTML text in `templates/partials/logo.html`, with the same fonts and proportions as the approved board. No vector logo file existed in the workspace. Before launch, a final outlined SVG/PNG logo should be exported from the approved design and can replace the partial.

## Adding the firm's details

Fill these in `.env` (see `.env.example`). Empty values show a marked *To be added / يُضاف قريبًا* placeholder instead of invented information:

`FIRM_WHATSAPP_NUMBER` (digits with country code, e.g. `20XXXXXXXXXX`), `FIRM_PHONE`, `FIRM_EMAIL`, `FIRM_ADDRESS_AR`, `FIRM_ADDRESS_EN`, `FIRM_MAPS_URL`, `FIRM_HOURS_AR`, `FIRM_HOURS_EN`, `SITE_URL`.

Restart the server after editing `.env`.

### Social accounts

The firm's Facebook, TikTok and YouTube profiles are set in `FIRM_SOCIAL` in `config/settings.py`, with tracking parameters removed. They appear in the footer, in the contact section ("Follow us"), and as "Watch on YouTube" in the videos section. Override any of them with `FIRM_FACEBOOK_URL`, `FIRM_TIKTOK_URL` or `FIRM_YOUTUBE_URL` in `.env`. An empty value hides that account.

## Not done yet (needs the firm or a later phase)

- Professional photos: `static/images/photos/lawyer.jpg` and `office.jpg`.
- Approved biography, qualifications, years of experience: placeholders in `core/content.py` (`about`).
- Contact details, WhatsApp number, address, map link, working hours: `.env`.
- Notification when a consultation request arrives (email or similar). Submissions are stored and visible in admin only.
- Articles page.
- Approved English titles for the videos (the English site shows the Arabic titles until then).
- Production setup: `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, a production database, `collectstatic`, HTTPS.
- All Arabic and English copy (practice-area descriptions, approach section) is a draft for the firm to approve.
