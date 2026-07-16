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
| `docs/` | GitHub Pages site (landing page + admin panel) and Kodi repo files |
| `repository.moviehub/` | Optional Kodi repository addon for auto-updates |
| `database.rules.json` | Firebase Realtime Database security rules |
| `build.py` | Builds the addon zip + `docs/addons.xml` |
| `test_passcode.py` | Unit test for the device-locked passcode logic |

---

## 1. Firebase setup (one time)

The passcode system is backed by **Firebase Realtime Database**.

1. Create a project at <https://console.firebase.google.com> (the config used
   by the admin panel is already in `docs/js/firebase-config.js` — replace it
   with your own if you create a new project).
2. **Build** → **Realtime Database** → create a database. Note its URL, e.g.
   `https://<project>-default-rtdb.firebaseio.com`.
3. **Realtime Database** → **Rules** → paste the contents of
   `database.rules.json` and publish. These rules let the addon (no login)
   register a code to a device, while only signed-in admins can create/revoke
   codes.
4. **Authentication** → **Sign-in method** → enable **Email/Password**.
5. **Authentication** → **Users** → **Add user** and create the admin
   email + password you will use to log into the admin panel. (There is no
   public sign-up — only accounts you create manually.)

> The addon's **Firebase Realtime Database URL** is set in the addon
> settings (`Subscription → Firebase Realtime Database URL`). It already
> defaults to the project used here; change it if you use your own project.

---

## 2. Publish the website (GitHub Pages)

1. Push this folder to a GitHub repo named e.g. `MovieHub`.
2. Repo **Settings** → **Pages** → Source = **Deploy from a branch** →
   branch `main` (or `master`) → folder **`/docs`** → Save.
3. Your site is now at `https://<your-username>.github.io/MovieHub/`.
   - `index.html` — public landing / install guide
   - `admin.html` — **admin panel** (sign in with the admin email/password)

### Admin panel
1. Open `admin.html` and sign in.
2. Click **Generate 4-digit code** — a random code is written to Firebase as
   `passcodes/<CODE> = { active: true }`.
3. Give that code to your user. The first Kodi device that enters it locks the
   code to its MAC address.
4. The table shows each code's status, the device MAC it is linked to, and an
   activation time. **Revoke** deactivates a code; you can then regenerate the
   same number.

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

## 4. How the passcode lock works

- Admin issues a code → Firebase `passcodes/<CODE> = { active: true }`.
- User enters the code in Kodi. The addon reads the device MAC
  (`uuid.getnode()`) and, on first use, **PATCHes** `mac` + `activated` onto
  the code (allowed by the database rules because the code is active and has no
  MAC yet).
- On every launch the addon re-validates: the stored code must exist, be
  active, and its `mac` must match the current device. A different device gets
  `used_elsewhere` and is blocked.
- Revoking in the admin panel sets `active: false`, which invalidates the code
  everywhere.

---

## Notes
- The addon requires the `inputstream.adaptive` add-on (built into most Kodi
  installs) for HLS playback.
- Streaming copyrighted content may be illegal in your country — use at your own
  risk, for personal use only.
