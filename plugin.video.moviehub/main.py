# -*- coding: utf-8 -*-
"""
main.py - MovieHub Kodi plugin entry point.

Routing (plugin://plugin.video.moviehub/?mode=...):
  root                      -> list enabled sites (+ Search All)
  site&site=X               -> site menu (Search / Latest / Genres)
  search&site=X             -> prompt query, list results
  searchall                 -> prompt query, search every enabled site
  latest&site=X             -> latest movies
  genres&site=X             -> genre list
  browse&site=X&url=Y       -> movies in a genre/category
  movie&site=X&url=Y        -> extract sources, list them
  resolve&embed=URL         -> resolve embed -> play
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.error

# Make sure resources/lib is importable (Kodi only adds the addon root to path)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

try:
    import xbmc
    import xbmcgui
    import xbmcplugin
    import xbmcaddon
    _KODI = True
except ImportError:
    xbmc = xbmcgui = xbmcplugin = xbmcaddon = None
    _KODI = False

from common import log, notify, get_setting, set_setting, Progress, Net, get_device_id
from scraper import get_enabled_sites, get_site
from resolver import resolve

ADDON_ID = "plugin.video.moviehub"

# Module-level access token. Set by ensure_access() after a valid code is
# verified. Source-listing and playback require it, so simply deleting the
# passcode prompt cannot unlock the addon (playback stays blocked).
_ACCESS = None


# ---------------------------------------------------------------------------
# URL building / params
# ---------------------------------------------------------------------------
def build_url(params):
    base = "plugin://%s/" % ADDON_ID
    if not params:
        return base
    return base + "?" + urllib.parse.urlencode(params)


def get_params():
    if len(sys.argv) > 2 and sys.argv[2]:
        return dict(urllib.parse.parse_qsl(sys.argv[2].lstrip("?")))
    return {}


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def add_dir(handle, label, params, thumb="", is_folder=True, info=None):
    if _KODI:
        li = xbmcgui.ListItem(label)
        if thumb:
            li.setArt({"thumb": thumb, "icon": thumb})
        if info:
            li.setInfo("video", info)
        xbmcplugin.addDirectoryItem(handle, build_url(params), li, is_folder)
    else:
        print("DIR:", label, params)


def make_playable(label, path, thumb="", info=None, properties=None):
    if _KODI:
        li = xbmcgui.ListItem(label)
        li.setProperty("IsPlayable", "true")
        if thumb:
            li.setArt({"thumb": thumb, "icon": thumb})
        if info:
            li.setInfo("video", info)
        for k, v in (properties or {}).items():
            li.setProperty(k, v)
        return li
    return None


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------
def list_root(handle):
    xbmcplugin.setContent(handle, "videos")
    add_dir(handle, "[COLOR gold]🔍 Search All Sites[/COLOR]", {"mode": "searchall"})
    for site in get_enabled_sites():
        add_dir(handle, site.name, {"mode": "site", "site": site.id},
                info={"plot": "Browse %s" % site.name})
    add_dir(handle, "[COLOR gray]⚙ Settings[/COLOR]", {"mode": "settings"})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_site_menu(handle, site_id):
    site = get_site(site_id)
    if not site:
        return
    xbmcplugin.setContent(handle, "videos")
    add_dir(handle, "[COLOR gold]🔍 Search %s[/COLOR]" % site.name,
            {"mode": "search", "site": site_id})
    add_dir(handle, "🆕 Latest", {"mode": "latest", "site": site_id})
    add_dir(handle, "🎭 Genres / Categories", {"mode": "genres", "site": site_id})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_genres(handle, site_id):
    site = get_site(site_id)
    if not site:
        return
    xbmcplugin.setContent(handle, "videos")
    for label, url in site.genres():
        add_dir(handle, label, {"mode": "browse", "site": site_id, "url": url})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_movies(handle, movies, site_id, end=True):
    xbmcplugin.setContent(handle, "movies")
    for m in movies:
        info = {"title": m["title"]}
        if m.get("year"):
            info["year"] = int(m["year"]) if str(m["year"]).isdigit() else None
        add_dir(handle, m["title"], {"mode": "movie", "site": site_id, "url": m["url"]},
                thumb=m.get("thumb", ""), info=info)
    if _KODI and end:
        xbmcplugin.endOfDirectory(handle)


def do_search(handle, site_id=None):
    if _KODI:
        kb = xbmcgui.Dialog().input("Search", type=xbmcgui.INPUT_ALPHANUM)
        if not kb:
            return
        query = kb
    else:
        query = input("Search: ")
    sites = [get_site(site_id)] if site_id else get_enabled_sites()
    all_movies = []
    prog = Progress("Searching...")
    total = len(sites)
    for i, site in enumerate(sites):
        prog.update((i * 100) // total, "Searching %s" % site.name)
        try:
            res = site.search(query)
        except Exception as e:
            log("search %s failed: %s" % (site.name, e), "error")
            res = []
        all_movies += res
        if prog.is_canceled():
            break
    prog.close()
    if not all_movies:
        notify("No results found")
    list_movies(handle, all_movies, site_id or "")


def do_latest(handle, site_id, page=1):
    site = get_site(site_id)
    if not site:
        return
    try:
        movies = site.latest(page)
    except Exception as e:
        log("latest failed: %s" % e, "error")
        movies = []
    if not movies:
        notify("No items found")
    list_movies(handle, movies, site_id, end=False)
    if movies:
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1),
                {"mode": "latest", "site": site_id, "page": page + 1})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def do_browse(handle, site_id, url, page=1):
    site = get_site(site_id)
    if not site:
        return
    try:
        movies = site.browse(url, page)
    except Exception as e:
        log("browse failed: %s" % e, "error")
        movies = []
    if not movies:
        notify("No items found")
    list_movies(handle, movies, site_id, end=False)
    if movies:
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1),
                {"mode": "browse", "site": site_id, "url": url, "page": page + 1})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


# ---------------------------------------------------------------------------
# Sources + playback
# ---------------------------------------------------------------------------
def list_sources(handle, site_id, movie_url):
    site = get_site(site_id)
    if not site:
        return
    if not _ACCESS:
        notify("Access required. Enter your 4-digit code.", "MovieHub")
        if _KODI:
            xbmcplugin.endOfDirectory(handle)
        return
    xbmcplugin.setContent(handle, "videos")
    try:
        sources = site.get_sources(movie_url)
    except Exception as e:
        log("get_sources failed: %s" % e, "error")
        sources = []
    if not sources:
        notify("No playable sources found for this title.\n"
               "The site uses a JavaScript-only player that cannot be\n"
               "resolved by a static scraper.", "MovieHub")
        if _KODI:
            xbmcplugin.endOfDirectory(handle)
        return
    # limit
    max_s = get_setting("max_sources", 20)
    try:
        max_s = int(max_s)
    except Exception:
        max_s = 20
    sources = sources[:max_s]
    for s in sources:
        label = "[COLOR cyan]▶ %s[/COLOR]" % s.get("label", s.get("host", "Source"))
        params = {"mode": "resolve", "embed": s["url"]}
        if s.get("referer"):
            params["referer"] = s["referer"]
        li = make_playable(label, build_url(params),
                           info={"title": s.get("label", "Source")})
        if _KODI:
            xbmcplugin.addDirectoryItem(handle, build_url(params), li, False)
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def _open_external(url):
    """Best-effort: open an unresolved embed in the device web browser so
    JS-only players can still play. Falls back to showing the URL."""
    if not _KODI:
        print("OPEN EXTERNAL BROWSER:", url)
        return
    # Android: open via a VIEW intent (system default browser)
    try:
        xbmc.executebuiltin('StartAndroidActivity("", "android.intent.action.VIEW", "%s")' % url)
        return
    except Exception:
        pass
    # Desktop: open with the OS default handler
    try:
        import subprocess, sys, os
        if sys.platform.startswith("win"):
            os.startfile(url)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        return
    except Exception:
        pass
    # Last resort: show the URL so the user can copy it
    try:
        xbmcgui.Dialog().textviewer("Open this URL in your browser", url)
    except Exception:
        pass


def play_resolved(handle, embed_url, referer=""):
    if not _ACCESS:
        notify("Access required. Enter your 4-digit code.", "MovieHub")
        if _KODI:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return
    preferred = get_setting("prefer_quality", "Auto")
    try:
        result = resolve(embed_url, preferred=preferred, referer=referer)
    except Exception as e:
        log("resolve error: %s" % e, "error")
        result = {"url": embed_url, "resolved": False, "kind": "unresolved", "referer": referer}

    if not result.get("resolved"):
        notify("This source could not be resolved.\nOpening it in your browser instead.", "MovieHub")
        _open_external(result["url"])
        if _KODI:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return

    url = result["url"]
    kind = result["kind"]
    referer = result.get("referer", "")
    extra = result.get("headers", {}) or {}
    log("Playing: %s (%s)" % (url, kind))

    if _KODI:
        li = xbmcgui.ListItem("", "", url)
        if kind == "m3u8":
            use_isa = get_setting("use_inputstream", True)
            li.setMimeType("application/vnd.apple.mpegurl")
            li.setContentLookup(False)
            if use_isa:
                li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                hdr = "Referer: %s\r\nUser-Agent: %s" % (referer, get_setting("user_agent", ""))
                for k, v in extra.items():
                    if k.lower() == "referer":
                        continue
                    hdr += "\r\n%s: %s" % (k, v)
                hdr += "\r\nAccept: */*"
                li.setProperty("inputstream.adaptive.manifest_headers", hdr)
                li.setProperty("inputstream.adaptive.stream_headers", hdr)
            elif referer:
                li.setProperty("Referer", referer)
        elif kind == "mp4":
            li.setMimeType("video/mp4")
            if referer:
                li.setProperty("Referer", referer)
        elif kind == "youtube":
            # delegate to YouTube addon
            xbmcplugin.setResolvedUrl(handle, True, li)
            return
        xbmcplugin.setResolvedUrl(handle, True, li)


# ---------------------------------------------------------------------------
# Subscription passcode (Firebase-backed, device-locked)
# ---------------------------------------------------------------------------
def get_device_mac():
    """Deprecated: mobile Kodi reports a hopping MAC. Use get_device_id()."""
    return get_device_id()


def _fb_get(code, fb):
    url = "%s/passcodes/%s.json" % (fb.rstrip("/"), code)
    data, _, _ = Net().get(url, headers={"Accept": "application/json"})
    if not data or data.strip() in ("", "null"):
        return None
    return json.loads(data)


def _fb_patch(code, fb, payload):
    url = "%s/passcodes/%s.json" % (fb.rstrip("/"), code)
    net = Net()
    net.request(url, method="PATCH", data=json.dumps(payload),
                headers={"Content-Type": "application/json"})


def validate_passcode(code, device, fb):
    """Validate (and on first use register) a 4-digit passcode.

    Returns one of: "ok", "invalid", "used_elsewhere", "paused", "expired",
    "rules_denied", "neterr".
    A code is locked to the first device id that activates it, so the same
    code cannot be used on a second device.
    """
    if not code or not fb:
        return "invalid"
    try:
        obj = _fb_get(code, fb)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            log("firebase read denied (rules not applied): %s" % e, "error")
            return "rules_denied"
        log("passcode check HTTP error: %s" % e, "error")
        return "neterr"
    except Exception as e:
        log("passcode check error: %s" % e, "error")
        return "neterr"
    if not isinstance(obj, dict) or obj.get("active", True) is False:
        return "invalid"
    if obj.get("paused"):
        return "paused"
    exp = obj.get("expiry")
    if exp and isinstance(exp, (int, float)) and int(time.time() * 1000) > int(exp):
        return "expired"
    registered = obj.get("device") or obj.get("mac")
    if registered and registered != device:
        return "used_elsewhere"
    if not registered:
        # first activation on this device -> lock the code to this device id
        try:
            _fb_patch(code, fb, {"device": device, "activated": int(time.time())})
        except Exception as e:
            log("passcode register error: %s" % e, "error")
            return "invalid"
    return "ok"


def ensure_access():
    """Gate the addon behind a 4-digit subscription passcode.

    On success sets the module-level _ACCESS token; the playback/source
    functions require it, so simply deleting this dialog cannot unlock
    playback (the addon refuses to list/play sources without a valid code).
    Wrapped in try/except so a network/import failure can never crash the
    addon silently - the user always gets a clear message (and the prompt).
    """
    global _ACCESS
    try:
        fb = get_setting("firebase_url", "").strip().rstrip("/")
        if not fb:
            notify("Set your Firebase Database URL in addon settings first.", "MovieHub")
            if _KODI:
                try:
                    xbmcaddon.Addon().openSettings()
                except Exception:
                    pass
            return False

        dev = get_device_id()
        stored = get_setting("passcode", "").strip()
        if stored:
            res = validate_passcode(stored, dev, fb)
            if res == "ok":
                _ACCESS = dev
                return True
            if res == "used_elsewhere":
                notify("This code is already linked to another device.", "MovieHub")
                set_setting("passcode", "")
            elif res == "paused":
                notify("This subscription is paused. Contact your provider.", "MovieHub")
                set_setting("passcode", "")
            elif res == "expired":
                notify("This subscription has expired. Contact your provider.", "MovieHub")
                set_setting("passcode", "")

        if _KODI:
            code = xbmcgui.Dialog().input(
                "Enter your 4-digit access code",
                type=xbmcgui.INPUT_NUMERIC,
            )
        else:
            try:
                code = input("Enter your 4-digit access code: ").strip()
            except Exception:
                code = ""
        if not code or not code.isdigit() or len(code) != 4:
            notify("A valid 4-digit code is required to continue.", "MovieHub")
            return False
        res = validate_passcode(code, dev, fb)
        if res == "ok":
            set_setting("passcode", code)
            _ACCESS = dev
            notify("Access granted. Enjoy!", "MovieHub")
            return True
        if res == "used_elsewhere":
            notify("This code is already linked to another device.", "MovieHub")
            return False
        if res == "paused":
            notify("This subscription is paused. Contact your provider.", "MovieHub")
            return False
        if res == "expired":
            notify("This subscription has expired. Contact your provider.", "MovieHub")
            return False
        if res == "rules_denied":
            notify("Firebase read blocked. In Firebase console -> Realtime Database -> Rules, paste database.rules.json and Publish.", "MovieHub")
            return False
        if res == "neterr":
            notify("Cannot reach Firebase. Check your internet connection.", "MovieHub")
            return False
        notify("Invalid or expired code. Generate a code in the admin panel first.", "MovieHub")
        return False
    except Exception as e:
        log("ensure_access crashed: %s" % e, "error")
        notify("MovieHub error: %s" % e, "MovieHub")
        return False


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def run():
    if not ensure_access():
        return
    try:
        params = get_params()
        mode = params.get("mode", "root")
        handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0

        if mode == "root":
            list_root(handle)
        elif mode == "site":
            list_site_menu(handle, params.get("site", ""))
        elif mode == "genres":
            list_genres(handle, params.get("site", ""))
        elif mode == "search":
            do_search(handle, params.get("site"))
        elif mode == "searchall":
            do_search(handle, None)
        elif mode == "latest":
            do_latest(handle, params.get("site", ""), int(params.get("page", 1) or 1))
        elif mode == "browse":
            do_browse(handle, params.get("site", ""), params.get("url", ""), int(params.get("page", 1) or 1))
        elif mode == "movie":
            list_sources(handle, params.get("site", ""), params.get("url", ""))
        elif mode == "resolve":
            play_resolved(handle, params.get("embed", ""), params.get("referer", ""))
        elif mode == "settings":
            if _KODI:
                xbmcaddon.Addon().openSettings()
        else:
            list_root(handle)
    except Exception as e:
        log("run() crashed: %s" % e, "error")
        notify("MovieHub error: %s" % e, "MovieHub")


if __name__ == "__main__":
    run()
