# -*- coding: utf-8 -*-
"""Build the MovieHub Kodi addon zip and the GitHub Pages / Kodi-repo files."""
import os, zipfile, shutil, hashlib, re

ROOT = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(ROOT, "plugin.video.moviehub")
ZIP = os.path.join(ROOT, "plugin.video.moviehub.zip")
DOCS = os.path.join(ROOT, "docs")
DOCS_ZIP = os.path.join(DOCS, "plugin.video.moviehub.zip")

EXCLUDE_DIRS = {"__pycache__", "tests", ".moviehub_data", "device_data"}
EXCLUDE_EXT = {".pyc", ".pyo"}


def zip_addon():
    if os.path.exists(ZIP):
        os.remove(ZIP)
    seen_dirs = set()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(ADDON):
            dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
            rel_dir = os.path.relpath(dp, ROOT).replace("\\", "/")
            if rel_dir != ".":
                dir_entry = rel_dir + "/"
                if dir_entry not in seen_dirs:
                    seen_dirs.add(dir_entry)
                    z.writestr(dir_entry, "")
            for fn in fns:
                if os.path.splitext(fn)[1] in EXCLUDE_EXT:
                    continue
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, ROOT).replace("\\", "/")
                z.write(full, rel)
    print("addon zip:", ZIP)


def make_addons_xml():
    with open(os.path.join(ADDON, "addon.xml"), encoding="utf-8") as f:
        content = f.read()
    # strip the xml declaration line
    lines = [l for l in content.splitlines() if not l.strip().startswith("<?xml")]
    body = "\n".join(lines).strip()
    addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + body + "\n</addons>\n"
    out = os.path.join(DOCS, "addons.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(addons)
    md5 = hashlib.md5(addons.encode("utf-8")).hexdigest()
    with open(os.path.join(DOCS, "addons.xml.md5"), "w") as f:
        f.write(md5)
    print("addons.xml + md5 written")


def zip_repo():
    repo_src = os.path.join(ROOT, "repository.moviehub")
    repo_zip = os.path.join(DOCS, "repository.moviehub.zip")
    if os.path.exists(repo_zip):
        os.remove(repo_zip)
    with zipfile.ZipFile(repo_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(repo_src):
            for fn in fns:
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel)
    print("repository zip ->", repo_zip)


def stage_repo_page():
    # A browsable "repo" page (served via GitHub Pages) that Kodi's file
    # manager can parse for zip links, so users can add it as a Kodi source
    # and install from zip file (like other GitHub-Pages-hosted Kodi repos).
    repo_dir = os.path.join(DOCS, "repo")
    os.makedirs(repo_dir, exist_ok=True)
    for name in ("repository.moviehub.zip", "plugin.video.moviehub.zip",
                 "addons.xml", "addons.xml.md5"):
        src = os.path.join(DOCS, name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(repo_dir, name))
    html = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8" />\n'
        '  <title>MovieHub Kodi Repository</title>\n'
        '</head>\n'
        '<body>\n'
        '  <h1>MovieHub Kodi Repository</h1>\n'
        '  <p>Install in Kodi: Settings -> Add-ons -> Install from zip file -> this source.</p>\n'
        '  <ul>\n'
        '    <li><a href="repository.moviehub.zip">repository.moviehub.zip</a> (install this first)</li>\n'
        '    <li><a href="plugin.video.moviehub.zip">plugin.video.moviehub.zip</a> (the addon)</li>\n'
        '    <li><a href="addons.xml">addons.xml</a></li>\n'
        '    <li><a href="addons.xml.md5">addons.xml.md5</a></li>\n'
        '  </ul>\n'
        '</body>\n'
        '</html>\n'
    )
    with open(os.path.join(repo_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("staged repo page ->", os.path.join(repo_dir, "index.html"))


def stage_repo_zips():
    # Kodi repositories expect each addon zip at:
    #   <datadir>/<addonid>/<addonid>-<version>.zip
    with open(os.path.join(ADDON, "addon.xml"), encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'<addon id="plugin\.video\.moviehub"[^>]*?version="([^"]+)"', content, re.S)
    ver = m.group(1) if m else "1.0.0"
    addon_dir = os.path.join(DOCS, "plugin.video.moviehub")
    os.makedirs(addon_dir, exist_ok=True)
    versioned = os.path.join(addon_dir, "plugin.video.moviehub-%s.zip" % ver)
    shutil.copyfile(ZIP, versioned)
    print("staged repo zip ->", versioned)


def main():
    zip_addon()
    shutil.copyfile(ZIP, DOCS_ZIP)
    print("copied zip -> docs/")
    make_addons_xml()
    stage_repo_zips()
    zip_repo()
    stage_repo_page()
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist()
    assert names[0].startswith("plugin.video.moviehub/"), "bad top folder"
    assert "plugin.video.moviehub/addon.xml" in names
    print("OK: valid addon zip with %d entries" % len(names))


if __name__ == "__main__":
    main()
