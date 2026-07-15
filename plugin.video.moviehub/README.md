# MovieHub — Multi-Site Movie Kodi Addon

A personal Kodi video addon that scrapes four movie websites, extracts their
stream/download embeds, and resolves them to playable links. It is written in
pure Python 3 with **no third-party dependencies** (no BeautifulSoup, no
requests) so it runs on **any operating system where Kodi runs** — Windows,
Linux, macOS, Android, iOS, LibreELEC, and OSMC.

## Supported sites

| Site | Status | Notes |
|------|--------|-------|
| `moviesbazar.tv` | ✅ Fully working | Watch pages embed **direct `.m3u8` HLS** streams. Resolves and plays via `inputstream.adaptive`. |
| `watchindianmovie.com` | ✅ Working | Movie pages embed a player (`kayel…/play/tt…`) that resolves to a direct `.mp4`. YouTube trailers also resolve. |
| `hdmovie2a.top` | ⚠️ Partial | Embeds are extracted (`hdm2.ink/play?v=…` indistream player). The player is JavaScript-driven, so static resolution may fail; the addon reports it gracefully. |
| `moviehax.watch` | ⚠️ Partial | Embeds are extracted from the detail page. The `doo_player` AJAX endpoint is protected by Cloudflare, so some streams cannot be statically resolved. |

> **Honest note:** `moviesbazar` and `watchindianmovie` resolve end-to-end and
> play. `hdmovie2` and `moviehax` extract the embed URLs but their players are
> JS/Cloudflare protected; when a stream cannot be resolved the addon notifies
> you instead of failing silently. This is a hard limitation of scraping
> protected players, not a bug in the addon.

## Features

- **Automatic link & file detection** — every scraper scans the full HTML for
  movie links, thumbnails, and player embeds (`data-embed`, `data-link`,
  `player-option`, iframes, inline JS `file:` tokens).
- **Universal resolver** — detects and resolves:
  - Direct `.m3u8` (HLS) and `.mp4` links
  - YouTube (delegates to `plugin.video.youtube`)
  - Streamtape, Mixdrop, DoodStream, Filemoon, StreamWish/FileLions/VidHide
  - HDVB / playerjs style players (`slash423kix`, `kayel`, `gxplayer`, `1xcinema`)
  - `hdm2.ink` indistream player
  - A generic HTML/iframe scanner that catches anything else
- **Quality picker** — choose Auto / 1080p / 720p / 480p / 360p; the resolver
  sorts sources by detected quality.
- **Cross-platform** — pure stdlib (`urllib`, `re`, `gzip`, `json`), dual-mode
  code that also runs as plain Python for offline testing.

## Installation

### Option A — Copy the folder (simplest)

1. Locate Kodi's `addons` directory:
   - **Windows:** `%APPDATA%\Kodi\addons\`
   - **Linux:** `~/.kodi/addons/`
   - **macOS:** `~/Library/Application Support/Kodi/addons/`
   - **Android:** `/Android/data/org.xbmc.kodi/files/.kodi/addons/`
   - **LibreELEC/OSMC:** `/storage/.kodi/addons/` (or `/home/osmc/.kodi/addons/`)
2. Copy the entire `plugin.video.moviehub` folder into that `addons` directory.
3. Restart Kodi (or toggle the addon on in **Settings ▸ Add-ons ▸ My add-ons**).

### Option B — Install from a ZIP

1. Zip the `plugin.video.moviehub` folder (the folder name must stay exactly
   `plugin.video.moviehub`).
2. In Kodi: **Settings (gear) ▸ Add-ons ▸ Install from zip file** → select your
   zip.
3. The addon appears under **Video ▸ MovieHub**.

### Required dependency

The addon uses **`inputstream.adaptive`** for HLS (`.m3u8`) playback. It is
declared in `addon.xml`, so Kodi installs it automatically. If it is missing,
install it from the Kodi add-on repository (**VideoPlayer InputStream**).

> For YouTube links you also need the official **`plugin.video.youtube`** addon.

## First run / settings

Open **MovieHub ▸ (long-press / context menu) ▸ Settings** (or the in-addon
*Settings* entry). Available options:

| Setting | Default | Description |
|---------|---------|-------------|
| Enable hdmovie2a | on | Toggle the hdmovie2a.top source |
| Enable moviesbazar | on | Toggle the moviesbazar.tv source |
| Enable watchindianmovie | on | Toggle the watchindianmovie.com source |
| Enable moviehax | on | Toggle the moviehax.watch source |
| Prefer quality | Auto | Auto / 1080p / 720p / 480p / 360p |
| Max sources | 20 | Max stream sources listed per movie |
| Use InputStream Adaptive | on | Use `inputstream.adaptive` for HLS |
| Resolve timeout (s) | 25 | Per-host resolution timeout |
| Enable logging | on | Write debug logs |
| User-Agent | Chrome UA | Override the browser User-Agent |

## Usage

1. Open **MovieHub** from the video add-ons list.
2. Pick a site (or **Search All** to query every enabled site at once).
3. Browse **Latest**, **Genres**, or use **Search**.
4. Select a movie → the addon lists all detected stream sources.
5. Select a source → it is resolved and played. HLS sources use
   `inputstream.adaptive`; direct MP4s play natively; YouTube opens the YouTube
   addon.

## How it works (for tinkerers)

```
main.py                 Kodi router (menus, search, browse, resolve, play)
resources/lib/
  common.py             HTTP client (Net), parseDOM, Kodi/CLI helpers
  resolver.py           Universal stream resolver (host-specific + generic)
  scraper.py            SiteScraper base + auto-discovery registry
  sites/                One module per website
    watchindianmovie.py
    hdmovie2.py
    moviehax.py
    moviesbazar.py
tests/run_tests.py      Offline test harness (runs without Kodi)
```

- **Scrapers** subclass `SiteScraper` and implement `search`, `latest`,
  `genres`, `browse`, and `get_sources`. They are auto-discovered from the
  `sites/` package.
- **Resolver** (`resolve(url, preferred, referer)`) returns
  `{"url", "resolved", "kind", "referer"}`. It strips query/fragment before
  checking the extension, so `…/index.m3u8?skip=N` is correctly treated as HLS.
- **Search on JS-only sites** (`hdmovie2`, `moviehax`) falls back to the site
  sitemap XML because their search forms are JavaScript-driven.

## Offline testing

The code is dual-mode: it detects whether it runs inside Kodi and falls back to
a local settings store + `print` logging otherwise. To test the scraping and
resolution logic without Kodi:

```bash
cd plugin.video.moviehub
python tests/run_tests.py
```

This prints, per site, how many movies were found, how many embeds were
extracted, and whether each embed resolved.

## Troubleshooting

- **No sources / "unresolved" on hdmovie2 or moviehax** — expected for
  JS/Cloudflare-protected players. Use `moviesbazar` or `watchindianmovie` for
  guaranteed playback, or try again later (sites rotate players).
- **HLS won't play** — ensure `inputstream.adaptive` is installed and enabled,
  and *Use InputStream Adaptive* is on in settings.
- **Site unreachable / blocked** — some ISPs block these domains. The addon
  retries with backoff; a VPN may be required in your region.
- **Enable logging** in settings, then check Kodi's log
  (`%APPDATA%\Kodi\kodi.log` / `~/.kodi/temp/kodi.log`) for resolver details.

## Disclaimer

This addon is a personal scraping tool for the listed public websites. Stream
availability, quality, and legality depend on your jurisdiction and the source
sites, which change frequently. The author is not affiliated with any of the
listed sites. Use at your own risk and respect your local copyright laws.
