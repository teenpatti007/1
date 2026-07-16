# -*- coding: utf-8 -*-
"""Generic movie site scraper (dooplay WordPress, JS search -> sitemap)."""
import re
import urllib.parse
import os

from scraper import SiteScraper
from common import log, clean_text
from sites._utils import (slug_to_title, title_from_text, thumb_after, clean_movie,
                           is_media_embed, host_label)

BASE = "https://hdmovie2a.top"
SITEMAP = BASE + "/movies-sitemap.xml"


class Movies(SiteScraper):
    id = "movies"
    name = "Movies"
    base_url = BASE
    latest_url = BASE + "/movies/"

    def __init__(self):
        super().__init__()
        self._sitemap_cache = None

    # ------------------------------------------------------------------
    def _sitemap_urls(self):
        if self._sitemap_cache is not None:
            return self._sitemap_cache
        try:
            xml = self._get(SITEMAP)
            urls = re.findall(r"<loc>([^<]+)</loc>", xml)
            self._sitemap_cache = urls
        except Exception as e:
            log("sitemap error: %s" % e, "error")
            self._sitemap_cache = []
        return self._sitemap_cache

    def _extract_poster_links(self, html):
        movies = []
        seen = set()
        # <a class="poster-link" href="..." aria-label="TITLE">
        for m in re.finditer(
            r'<a class="poster-link" href="([^"]+)"[^>]*aria-label="([^"]*)"', html
        ):
            url = self._abs(m.group(1), BASE)
            if url in seen:
                continue
            seen.add(url)
            title = clean_text(m.group(2)) or slug_to_title(url)
            year = ""
            my = re.search(r"\((\d{4})\)", title)
            if my:
                year = my.group(1)
                title = title.replace("(%s)" % year, "").strip()
            pos = m.start()
            thumb = thumb_after(html, pos)
            movies.append(clean_movie(url, title, thumb, year))
        return movies

    # ------------------------------------------------------------------
    def _page_url(self, url, page):
        """Build a paginated URL. Page 1 == the base url; page N == /page/N/."""
        if not page or page <= 1:
            return url
        base = re.sub(r"/page/\d+/?", "", url)
        if not base.endswith("/"):
            base += "/"
        return "%spage/%d/" % (base, page)

    def search(self, query, page=1):
        q = query.lower()
        out = []
        for u in self._sitemap_urls():
            if q in u.lower():
                out.append(clean_movie(u, slug_to_title(u), "", ""))
        return out[:50]

    def latest(self, page=1):
        url = self._page_url(self.latest_url, page)
        try:
            html = self._get(url)
        except Exception as e:
            log("latest error: %s" % e, "error")
            return []
        return self._extract_poster_links(html)

    def genres(self):
        return [
            ("Bollywood", BASE + "/genre/bollywood/"),
            ("Hollywood", BASE + "/genre/hollywood/"),
            ("Hindi Dubbed", BASE + "/genre/hindi-dubbed/"),
            ("Netflix", BASE + "/genre/netflix/"),
            ("South Hindi Dubbed", BASE + "/genre/south-hindi-dubbed/"),
            ("Web Series", BASE + "/genre/web-series/"),
            ("Action", BASE + "/genre/action/"),
        ]

    def browse(self, url, page=1):
        url = self._page_url(url, page)
        try:
            html = self._get(url)
        except Exception as e:
            log("browse error: %s" % e, "error")
            return []
        movies = self._extract_poster_links(html)
        if not movies:
            # fallback: any /movies/ link
            for m in re.finditer(r'href="(%s/movies/[^"]+/)"' % re.escape(BASE), html):
                u = m.group(1)
                movies.append(clean_movie(u, slug_to_title(u), "", ""))
        return movies

    # ------------------------------------------------------------------
    def get_sources(self, movie_url):
        try:
            html = self._get(movie_url)
        except Exception as e:
            log("sources error: %s" % e, "error")
            return []
        sources = []
        seen = set()
        # primary player links
        for emb in re.findall(r'https://hdm2\.ink/play\?v=[^"\'\s<>]+', html):
            if emb not in seen:
                seen.add(emb)
                sources.append({"label": "Server", "url": emb, "host": "hdm2.ink"})
        # generic data-embed / data-link / iframe
        for emb in re.findall(r'data-(?:embed|link)=["\']([^"\']+)["\']', html):
            emb = self._abs(emb, movie_url)
            if is_media_embed(emb) and emb not in seen:
                seen.add(emb)
                sources.append({"label": host_label(emb), "url": emb, "host": host_label(emb)})
        for ifr in re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I):
            ifr = self._abs(ifr, movie_url)
            if is_media_embed(ifr) and ifr not in seen:
                seen.add(ifr)
                sources.append({"label": host_label(ifr), "url": ifr, "host": host_label(ifr)})
        return sources
