"""Testata propria del progetto: il minisito si presenta come un sito a sé dentro il portale DH.

Con la sola barra di sezione il visitatore vede due livelli di navigazione (menu globale del portale
sopra, menu del progetto sotto) e non capisce se è nel sito del progetto o in quello del DH. Il
modello è «Colonizzazioni interne» (storia.dh.unica.it/colonizzazioninterne/):

  Università degli Studi di Cagliari          Storia Digitale UniCA | DH UniCA   ← barra alta, ritorno al portale
  [banner] La ricchezza della Chiesa e dei Luoghi pii in Italia                   ← titolo del progetto
  Home | Il Progetto | Equipe | Eventi | Pubblicazioni | Contatti                 ← menu del progetto

Il tema del portale (design-italia) è classico e da admin di sito non si possono aggiungere template:
la testata del tema viene riscritta lato client da uno script dentro il pattern sincronizzato, quindi
solo sulle pagine del progetto, riusando le classi del tema (stile e menu mobile compresi). Lo script
gira appena dopo la testata, prima che il resto della pagina sia analizzato. Senza JavaScript resta la
testata del portale e torna visibile la barra di sezione in pagina.
"""
from __future__ import annotations

import json

from .config import Config

SCRIPT = """<script>
(function () {
  var d = document, el = d.getElementById('dh-testata-dati');
  if (!el) return;
  var cfg = JSON.parse(el.textContent), h = d.getElementById('header');
  if (!h) return;
  var radice = location.pathname.replace(/\/?$/, '/') === new URL(cfg.home).pathname;
  d.documentElement.className += ' dh-testata' + (radice && cfg.hide_root_title ? ' dh-testata-radice' : '');
  function link(item) {
    var a = d.createElement('a');
    a.href = item.url;
    a.textContent = item.label;
    return a;
  }
  var slim = h.querySelector('.it-header-slim-wrapper-content');
  if (slim && cfg.links.length) {
    var nav = d.createElement('nav');
    nav.className = 'dh-testata-portali';
    nav.setAttribute('aria-label', 'Portali');
    cfg.links.forEach(function (item) { nav.appendChild(link(item)); });
    slim.appendChild(nav);
  }
  var brand = h.querySelector('.it-brand-wrapper a');
  if (brand) {
    var site = brand.getAttribute('title') || '';
    var t = brand.querySelector('h2'), s = brand.querySelector('h3');
    brand.href = cfg.home;
    brand.title = cfg.title;
    if (t) t.textContent = cfg.title;
    if (s) { s.textContent = cfg.subtitle; s.hidden = !cfg.subtitle; }
    if (site && d.title.indexOf(site) >= 0) {
      var nuovo = d.title.replace(site, cfg.title);  // in home titolo pagina = titolo progetto: niente doppione
      d.title = nuovo.indexOf(cfg.title) !== nuovo.lastIndexOf(cfg.title) ? cfg.title : nuovo;
    }
  }
  var ul = h.querySelector('#menu-menu-principale') || h.querySelector('.menu-main ul.nav');
  if (ul) {
    var path = location.pathname.replace(/\\/?$/, '/');
    var home = new URL(cfg.home).pathname;
    ul.innerHTML = '';
    cfg.items.forEach(function (item) {
      var p = new URL(item.url).pathname, li = d.createElement('li'), a = link(item);
      var current = p === path || (p !== home && path.indexOf(p) === 0);
      li.className = 'menu-item' + (current ? ' current-menu-item' : '');
      if (p === path) a.setAttribute('aria-current', 'page');
      li.appendChild(a);
      ul.appendChild(li);
    });
    ul.setAttribute('aria-label', 'Menu del progetto ' + cfg.title);
  }
})();
</script>"""


def header_data(cfg: Config, media_map: dict) -> dict:
    """Dati della testata: voci del menu del progetto (radice compresa), titoli, banner, link al portale."""
    header = cfg.section_nav.header
    items = [{"label": page.menu_label, "url": cfg.target_link(page.source_slug)}
             for page in cfg.pages if page.menu_label and (page.parent is None or page.parent == cfg.root.source_slug)]
    banner = (media_map.get(header.banner) or {}).get("url") if header.banner else None
    return {"home": cfg.target_link(cfg.root.source_slug), "title": header.title or cfg.project_title,
            "subtitle": header.subtitle, "banner": banner, "links": [dict(link) for link in header.links],
            "hide_root_title": header.hide_root_title, "items": items}


def css_url(url: str) -> str:
    """URL sicuro dentro url("…") in un <style>: niente entità HTML (il CSS non le decodifica)."""
    for char, code in (('"', "%22"), ("\\", "%5C"), ("<", "%3C"), (">", "%3E"), ("\n", ""), ("\r", "")):
        url = url.replace(char, code)
    return url


def header_css(banner: str | None) -> str:
    fondo = ""
    if banner:
        fondo = ("html.dh-testata #header .it-header-center-wrapper{background:linear-gradient(rgba(8,44,34,.78),"
                 f"rgba(8,44,34,.62)),url(\"{css_url(banner)}\") center 30%/cover}}")
    return f"""<style>
html.dh-testata .dh-progetto-nav{{display:none}}
html.dh-testata .entry-content a{{overflow-wrap:anywhere}}
html.dh-testata-radice #content header.header{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
html.dh-testata #header .it-brand-wrapper .icon,html.dh-testata #header .it-socials{{display:none!important}}
.dh-testata-portali{{margin-left:auto;display:flex;gap:1.5rem}}
.dh-testata-portali a{{color:#fff;font-size:.9rem;text-decoration:none}}
.dh-testata-portali a:hover{{text-decoration:underline}}
@media (max-width:575px){{html.dh-testata .header-slim-img{{max-width:130px;height:auto}}
.dh-testata-portali{{gap:.75rem}}.dh-testata-portali a{{font-size:.75rem}}}}
{fondo}
</style>"""


def header_html(cfg: Config, media_map: dict) -> str:
    data = header_data(cfg, media_map)
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")  # mai '</script>' letterale
    return "\n".join([header_css(data["banner"]),
                      f'<script type="application/json" id="dh-testata-dati">{payload}</script>', SCRIPT])
