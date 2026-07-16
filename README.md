# MovieHub — Free Movies on Kodi

MovieHub is a Kodi video addon that lets you browse and stream a curated
catalogue of movies and web series. Access is protected by a **4-digit
subscription passcode** that is **locked to a single device** — one code works
on only one Kodi installation.

---

## 1. Get your access code

You need a **4-digit code** from the person who gave you this addon (your
provider/admin). Each code can be used on **one device only**. If you try to use
the same code on a second device, it will be rejected.

---

## 2. Install on Kodi (recommended — via repository, auto-updates)

Kodi's **Add source** needs a **browsable web address** (a page it can read
links from), not a direct file link. The standard way to host a Kodi repo on
GitHub is **GitHub Pages**: you enable it, then point Kodi at the Pages address,
which lists the install files.

### One-time: enable GitHub Pages
1. On GitHub, open the `teenpatti007/1` repo → **Settings → Pages**.
2. **Source:** Deploy from a branch → **Branch: main** → **Folder: /docs** → Save.
3. Wait about a minute. Your site address becomes `https://teenpatti007.github.io/1/`
   and the install files (index.html, zips) are served from that address.

### In Kodi
1. **Settings (gear) → File manager → Add source → `<None>`**.
2. Enter exactly:
   ```
   https://teenpatti007.github.io/1/
   ```
3. Name it `MovieHub Repo`, **OK**.
4. **Settings → Add-ons → Install from zip file → MovieHub Repo** →
   choose **`repository.moviehub.zip`** and install it.
5. **Settings → Add-ons → Install from repository → MovieHub Repository →
   Video add-ons → MovieHub → Install**.

> The `MovieHub/docs/` folder must be pushed to the `main` branch **and** GitHub
> Pages must be enabled, or Kodi shows "Could not connect". The repository then
> updates itself automatically (it fetches `addons.xml` from the raw GitHub URL).

---

## 3. Install via ZIP (alternative, no auto-update)

If you prefer not to use GitHub Pages, download the zip on any device and
sideload it:

1. Download `plugin.video.moviehub.zip` (from the GitHub repo's
   `MovieHub/docs/` folder, or the website).
2. Get the file onto the Kodi device (USB, network share, or download on the
   device itself).
3. In Kodi: **Settings → Add-ons → Install from zip file** → navigate to the
   downloaded zip.
4. MovieHub appears under **Video → MovieHub**.

---

## 4. First launch — enter your code

1. Open **MovieHub** from the video add-ons list.
2. When prompted, enter your **4-digit access code**.
3. The code is now linked to this device. On every launch the addon re-checks
   the code, so you normally won't be asked again.

If you see **"Invalid or expired code"**, contact your provider for a new code.
If you see **"This code is already used on another device"**, the code was used
elsewhere and cannot be reused — ask your provider for a fresh one.

---

## 5. Using MovieHub

- **Latest** — newest added movies. At the bottom there is a
  **`>> Next Page`** item to load more.
- **Genres / Categories** — browse by category; these also support
  **Next Page**.
- **Search** — type a movie name to find it.
- **Play a movie** — pick a title, then choose one of the listed stream
  sources. MovieHub resolves the link and plays it. HLS (`.m3u8`) streams use
  `inputstream.adaptive`; direct MP4s play natively.

---

## 6. Settings

Open **MovieHub → (long-press / context menu) → Settings**, or the in-addon
*Settings* entry.

| Setting | Default | What it does |
|---------|---------|--------------|
| Preferred quality | Auto | Auto / 1080p / 720p / 480p / 360p for source picking |
| Maximum sources | 20 | How many stream sources to list per movie |
| Use inputstream.adaptive | On | Use `inputstream.adaptive` for HLS playback |
| Resolve timeout (s) | 25 | How long to wait when resolving a stream |
| Enable debug logging | Off | Write extra info to the Kodi log for troubleshooting |

---

## 7. Troubleshooting

- **"Cannot connect to server" / "Could not connect"** — this happens when the
  Kodi source points at a direct file (raw) URL or GitHub Pages is not enabled.
  Use the site root URL `https://teenpatti007.github.io/1/` (GitHub Pages source must be set to /docs)
  and make sure GitHub Pages is turned on and `MovieHub/docs/` is pushed.
- **"Cannot install / invalid structure"** — make sure you are installing
  `plugin.video.moviehub.zip` (or the repository zip), not the whole project
  folder. If a broken copy is stuck, restart Kodi and try again.
- **Code not accepted** — double-check the 4 digits. Codes are single-device; a
  code already used on another Kodi will be rejected. Ask your provider for a
  fresh code.
- **HLS / `.m3u8` won't play** — ensure `inputstream.adaptive` is installed and
  enabled, and *Use InputStream Adaptive* is On in settings.
- **No sources / "unresolved"** — the source site may be temporarily down or
  blocked by your ISP. Try another source, or use a VPN in your region.
- **Site unreachable** — some networks block these domains; a VPN may be
  required.

---

## 8. Disclaimer

MovieHub is a personal streaming tool for public movie websites. Stream
availability, quality, and legality depend on your jurisdiction and the source
sites, which change often. The author is not affiliated with any source site.
Streaming copyrighted content may be illegal in your country — use at your own
risk, for personal use only.
