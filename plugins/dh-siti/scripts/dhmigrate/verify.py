"""Fase 4 - VERIFY: controlli automatici sulla destinazione e report Markdown.

Controlli bloccanti (FAIL): pagina raggiungibile, URL attesa, parità testo, nessun residuo del
dominio sorgente, immagini servite dalla destinazione e raggiungibili.
Controlli informativi (WARN): link esterni non raggiungibili.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import Config
from .http import TIMEOUT
from .load import State, state_path
from .wp_client import WPClient

MIN_COVERAGE = 0.98


@dataclass
class PageCheck:
    slug: str
    url: str
    status: str = "draft"
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    coverage: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.failures


def words(html: str) -> Counter:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "form", "noscript"]):
        tag.decompose()
    return Counter(re.findall(r"\w+", htmllib.unescape(soup.get_text(" ")).lower()))


def coverage(source_html: str, target_html: str, title: str = "") -> tuple[float, list[str]]:
    src = words(source_html)
    dst = words(target_html) + words(title)
    missing = src - dst
    total = sum(src.values()) or 1
    return 1 - sum(missing.values()) / total, [w for w, _ in missing.most_common(10)]


def url_status(session: requests.Session, url: str) -> int:
    try:
        resp = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code in (403, 405, 501) or resp.status_code >= 500:
            resp = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
            resp.close()
        return resp.status_code
    except requests.RequestException:
        return 0


def check_page(cfg: Config, slug: str, source: dict, target: dict, public: requests.Session,
               link_cache: dict[str, int]) -> PageCheck:
    expected = cfg.target_link(slug)
    check = PageCheck(slug, expected, target.get("status", "draft"))
    rendered = target["content"]["rendered"]

    if check.status == "publish":
        if target.get("link", "").rstrip("/") != expected.rstrip("/"):
            check.failures.append(f"URL {target.get('link')} diversa da quella attesa {expected}")
        code = url_status(public, expected)
        if code != 200:
            check.failures.append(f"la pagina pubblica risponde HTTP {code}")

    check.coverage, missing = coverage(source["content"]["rendered"], rendered, target["title"]["rendered"])
    if check.coverage < MIN_COVERAGE:
        check.failures.append(f"copertura testo {check.coverage:.1%} < {MIN_COVERAGE:.0%}; mancano: {missing}")

    soup = BeautifulSoup(rendered, "html.parser")
    source_host = cfg.source_host.removeprefix("www.")
    target_host = urlparse(cfg.target_url).netloc
    for tag, attr in (("a", "href"), ("img", "src"), ("iframe", "src")):
        for el in soup.find_all(tag):
            value = el.get(attr, "")
            if source_host in value:
                check.failures.append(f"riferimento residuo al dominio sorgente: <{tag} {attr}={value}>")

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if urlparse(src).netloc != target_host:
            check.failures.append(f"immagine non servita dalla destinazione: {src}")
            continue
        if src not in link_cache:
            link_cache[src] = url_status(public, src)
        if link_cache[src] != 200:
            check.failures.append(f"immagine non raggiungibile (HTTP {link_cache[src]}): {src}")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http") or urlparse(href).netloc == target_host:
            continue
        if href not in link_cache:
            link_cache[href] = url_status(public, href)
        code = link_cache[href]
        if not (200 <= code < 400):
            check.warnings.append(f"link esterno HTTP {code}: {href}")
    return check


def verify(cfg: Config, client: WPClient, public: requests.Session) -> list[PageCheck]:
    state = State.load(state_path(cfg))
    sources = {p["slug"]: p for p in json.loads((cfg.project_dir / "extract" / "pages.json").read_text())}
    cache: dict[str, int] = {}
    checks = []
    for pmap in cfg.ordered_pages():
        entry = state.pages.get(pmap.source_slug)
        if entry is None:
            checks.append(PageCheck(pmap.source_slug, cfg.target_link(pmap.source_slug),
                                    failures=["pagina non presente in state.json (load non eseguito?)"]))
            continue
        target = client.get_page(entry["id"], context="view")
        checks.append(check_page(cfg, pmap.source_slug, sources[pmap.source_slug], target, public, cache))
    write_report(cfg, checks)
    return checks


def write_report(cfg: Config, checks: list[PageCheck]) -> str:
    ok = sum(c.ok for c in checks)
    lines = [
        f"# Report di verifica: {cfg.project_slug}",
        "",
        f"Sorgente: {cfg.source_url}  ",
        f"Destinazione: {cfg.target_link(cfg.root.source_slug)}",
        "",
        f"**Esito: {ok}/{len(checks)} pagine superano i controlli bloccanti.**",
        "",
        "| Pagina | URL | Stato | Copertura testo | Esito |",
        "|---|---|---|---:|---|",
    ]
    for c in checks:
        lines.append(f"| {c.slug} | {c.url} | {c.status} | {c.coverage:.1%} | {'OK' if c.ok else 'FAIL'} |")
    details = [c for c in checks if c.failures or c.warnings]
    if details:
        lines += ["", "## Dettagli", ""]
        for c in details:
            lines.append(f"### {c.slug}")
            lines += [f"- FAIL: {f}" for f in c.failures]
            lines += [f"- WARN: {w}" for w in c.warnings]
            lines.append("")
    report = "\n".join(lines) + "\n"
    (cfg.project_dir / "verify-report.md").write_text(report, encoding="utf-8")
    return report
