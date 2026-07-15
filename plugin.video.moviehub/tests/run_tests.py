# -*- coding: utf-8 -*-
"""Offline test harness (run with plain python, no Kodi needed)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "resources", "lib")
sys.path.insert(0, os.path.abspath(LIB))

from scraper import get_all_sites, get_enabled_sites
from resolver import resolve, resolve_all


def banner(t):
    print("\n" + "=" * 70 + "\n" + t + "\n" + "=" * 70)


def test_site(site):
    banner("SITE: %s (%s)" % (site.name, site.id))
    # latest
    try:
        movies = site.latest()
        print("[latest] found %d movies" % len(movies))
        for m in movies[:3]:
            print("   -", m["title"], "|", m["url"])
    except Exception as e:
        print("[latest] ERROR:", e)

    # sources on first movie (or a known url)
    test_url = None
    if movies:
        test_url = movies[0]["url"]
    if site.id == "moviesbazar" and not test_url:
        test_url = "https://www.moviesbazar.tv/watch/movie/moana/27419466"
    if site.id == "watchindianmovie" and not test_url:
        test_url = "https://watchindianmovie.com/bollywood/92-veera-dheera-sooran-part-2.html"
    if site.id == "hdmovie2" and not test_url:
        test_url = "https://hdmovie2a.top/movies/ride-or-die-2026-hindi-season-1-complete-amzn/"
    if site.id == "moviehax" and not test_url:
        test_url = "https://moviehax.watch/movies/generation-iron-2013-full-documentary-hd/"

    if test_url:
        try:
            sources = site.get_sources(test_url)
            print("[sources] found %d embeds for %s" % (len(sources), test_url))
            for s in sources[:5]:
                print("   -", s["label"], "->", s["url"])
            # try to resolve first couple
            if sources:
                res = resolve_all([s["url"] for s in sources[:3]])
                for r in res:
                    print("   [resolve]", r["resolved"], r["kind"], r["url"][:90])
        except Exception as e:
            print("[sources] ERROR:", e)


def test_resolver_direct():
    banner("RESOLVER: moviesbazar direct m3u8")
    # a known m3u8 pattern from earlier analysis
    url = ("https://cdn30092.slash423kix.com/stream2/i-arch-400/"
           "d1704cbd2424a14017d21d010d25c7f3/"
           "MJTMsp1RshGTygnMNRUR2N2MSlnWXZEdMNDZzQWe5MDZzMmdZJTO1R2RWVHZDljekhkSsl1VwYnWtx2cihVT25keBdXT6FEeaRkTtlleNJjTUpEaZpnUs1ERGlWWyoEbNRVTw4keRd3THlUP:1783798318:152.58.181.172:1cc39d8a4d5eb3d12848749953fb2e1c8fc2a5adf66d382ab489af022e1fab58:=0EVVlHTqVFNMpWR000U0gnT6lUP/index.m3u8?skip=68")
    r = resolve(url)
    print("direct m3u8 ->", r)


def main():
    sites = get_enabled_sites()
    print("Enabled sites:", [s.id for s in sites])
    for site in sites:
        test_site(site)
    test_resolver_direct()
    banner("DONE")


if __name__ == "__main__":
    main()
