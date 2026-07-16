# MovieHub — Kodi Addon + Subscription System

MovieHub is a Kodi video addon that streams a curated movie & web-series
catalogue. Access is protected by a **4-digit subscription passcode** that is
**locked to a single device** (the code is bound to the Kodi device's MAC
address, so one code works on only one installation).

This repository contains:

| Path | What it is |
|------|------------|
| `plugin.video.moviehub/` | The Kodi addon source |
| `plugin.video.moviehub.zip` | Installable addon zip (built by `build.py`) |

| `repository.moviehub/` | Optional Kodi repository addon for auto-updates |




---

## 3. Install on Kodi

1. Download `plugin.video.moviehub.zip` (from the repo, or the link on the
   website).
2. Kodi → **Settings** → **Add-ons** → **Install from zip file** → select the
   zip.
3. Open **MovieHub**. When prompted, enter the **4-digit access code** you were
   given. The code is linked to this device only — using it on a different
   device is rejected.

### Optional: auto-updates via repository
1. In `repository.moviehub/addon.xml`, replace `YOURUSERNAME` with your GitHub
   username (two occurrences: the `info` and `checksum` URLs, and the
   `datadir`).
2. Zip `repository.moviehub/` and install it in Kodi first, then install
   MovieHub from the repository. Kodi will then update it automatically.

---


---

## Notes
- The addon requires the `inputstream.adaptive` add-on (built into most Kodi
  installs) for HLS playback.
- Streaming copyrighted content may be illegal in your country — use at your own
  risk, for personal use only.
