"""Configurazione di una migrazione e validazione della name convention DH.

Schema URL DH: https://{ambito}.dh.unica.it/{progetto}/...
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DH_DOMAIN = "dh.unica.it"
# Sottodomini riservati alle API (vedi Name convention.pdf): non ospitano minisiti.
API_AMBITI = frozenset({"geo", "xdams"})
SLUG_PROGETTO_RE = re.compile(r"^[a-z0-9]+$")
SLUG_PAGINA_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ConfigError(ValueError):
    """Configurazione non valida o non conforme alla name convention."""


@dataclass(frozen=True)
class PageMap:
    source_slug: str
    target_slug: str
    parent: str | None = None  # source_slug della pagina genitore; None = radice progetto
    title: str | None = None  # override del titolo
    menu_label: str | None = None  # se presente, la pagina è una voce di sottomenu del progetto
    image_width: int | None = None  # larghezza uniforme (px) per le immagini di contenuto


@dataclass(frozen=True)
class MenuConfig:
    """Posizione del progetto nel menu globale del portale (confermata dall'utente)."""

    location: str = "menu-main"  # location del tema che individua il menu
    parent: str | None = "Progetti"  # titolo della voce sotto cui inserire il progetto; None = primo livello
    label: str = ""  # etichetta della voce del progetto (default: titolo della radice)


@dataclass(frozen=True)
class HeaderConfig:
    """Testata propria del progetto: sulle pagine del progetto sostituisce titolo, menu globale e
    <title> del portale, come un sito a sé dentro il DH (vedi testata.py)."""

    title: str = ""  # default: project.title
    subtitle: str = ""  # sottotitolo sotto il titolo (h3 del tema)
    banner: str | None = None  # URL sorgente dell'immagine di fondo (risolto sui media caricati)
    links: tuple[dict, ...] = ()  # barra alta, es. [{label: Storia Digitale UniCA, url: ...}]
    hide_root_title: bool = True  # radice senza titolo del tema: è già nella testata (e di solito nel banner)


@dataclass(frozen=True)
class SectionNav:
    """Barra di sezione in testa alle pagine del progetto (percorso + menu del progetto)."""

    breadcrumb: tuple[dict, ...] = ()  # voci prima del progetto, es. [{label: Progetti, url: ...}]
    header: HeaderConfig | None = None  # None = solo barra in pagina, testata del portale invariata


@dataclass(frozen=True)
class Partner:
    name: str
    image: str  # URL immagine sorgente
    link: str


@dataclass(frozen=True)
class Config:
    project_slug: str
    project_title: str
    ambito: str
    source_url: str
    target_url: str
    credentials: Path
    pages: tuple[PageMap, ...]
    source_type: str = "wordpress"
    elementor_default_direction: str = "row"
    template: str = "page-fullwidth.php"
    workdir: Path = Path("work")
    partners: tuple[Partner, ...] = field(default_factory=tuple)
    menu: MenuConfig | None = None  # None = non toccare il menu globale
    section_nav: SectionNav | None = None  # None = nessuna barra di sezione
    notes: dict = field(default_factory=dict)

    @property
    def project_dir(self) -> Path:
        return self.workdir / self.project_slug

    @property
    def source_host(self) -> str:
        return re.sub(r"^https?://", "", self.source_url).split("/")[0]

    @property
    def root(self) -> PageMap:
        return next(p for p in self.pages if p.parent is None)

    def page(self, source_slug: str) -> PageMap:
        for p in self.pages:
            if p.source_slug == source_slug:
                return p
        raise KeyError(source_slug)

    def target_path(self, source_slug: str) -> str:
        """Percorso URL di destinazione (es. /progetto/sub/) ricavato dalla gerarchia."""
        parts: list[str] = []
        current: PageMap | None = self.page(source_slug)
        while current is not None:
            parts.append(current.target_slug)
            current = self.page(current.parent) if current.parent else None
        return "/" + "/".join(reversed(parts)) + "/"

    def target_link(self, source_slug: str) -> str:
        return self.target_url.rstrip("/") + self.target_path(source_slug)

    def ordered_pages(self) -> list[PageMap]:
        """Pagine in ordine topologico: ogni genitore prima dei figli."""
        done: list[PageMap] = []
        seen: set[str] = set()
        pending = list(self.pages)
        while pending:
            ready = [p for p in pending if p.parent is None or p.parent in seen]
            if not ready:
                raise ConfigError("ciclo o genitore mancante nella gerarchia delle pagine")
            for p in ready:
                done.append(p)
                seen.add(p.source_slug)
            pending = [p for p in pending if p.source_slug not in seen]
        return done


def validate(cfg: Config) -> list[str]:
    """Restituisce la lista delle violazioni (vuota se la config è valida)."""
    errors: list[str] = []
    if not SLUG_PROGETTO_RE.match(cfg.project_slug):
        errors.append(
            f"slug progetto '{cfg.project_slug}': solo minuscole e cifre, senza separatori"
        )
    if cfg.ambito in API_AMBITI:
        errors.append(f"ambito '{cfg.ambito}' è riservato alle API, non ospita minisiti")
    expected_host = f"{cfg.ambito}.{DH_DOMAIN}"
    target_host = re.sub(r"^https?://", "", cfg.target_url).split("/")[0]
    if target_host != expected_host:
        errors.append(f"target '{target_host}' non corrisponde all'ambito: atteso '{expected_host}'")
    roots = [p for p in cfg.pages if p.parent is None]
    if len(roots) != 1:
        errors.append(f"serve esattamente una pagina radice, trovate {len(roots)}")
    elif roots[0].target_slug != cfg.project_slug:
        errors.append("la pagina radice deve avere target_slug uguale allo slug di progetto")
    slugs = [p.source_slug for p in cfg.pages]
    if len(slugs) != len(set(slugs)):
        errors.append("source_slug duplicati")
    for p in cfg.pages:
        if not SLUG_PAGINA_RE.match(p.target_slug):
            errors.append(f"target_slug non valido: '{p.target_slug}'")
        if p.parent is not None and p.parent not in slugs:
            errors.append(f"genitore '{p.parent}' di '{p.source_slug}' non definito")
    siblings: dict[tuple[str | None, str], int] = {}
    for p in cfg.pages:
        key = (p.parent, p.target_slug)
        siblings[key] = siblings.get(key, 0) + 1
    errors.extend(
        f"slug '{slug}' duplicato sotto lo stesso genitore" for (_, slug), n in siblings.items() if n > 1
    )
    if cfg.elementor_default_direction not in {"row", "column"}:
        errors.append("elementor_default_direction deve essere 'row' o 'column'")
    return errors


def _section_nav(raw: dict | None) -> SectionNav | None:
    if not raw:
        return None
    header = raw.get("header")
    if header:
        header = HeaderConfig(**{**header, "links": tuple(header.get("links", []))})
    return SectionNav(tuple(raw.get("breadcrumb", [])), header or None)


def load_config(path: str | Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    try:
        project, source, target = raw["project"], raw["source"], raw["target"]
        cfg = Config(
            project_slug=project["slug"],
            project_title=project["title"],
            ambito=project["ambito"],
            source_url=source["url"].rstrip("/"),
            source_type=source.get("type", "wordpress"),
            elementor_default_direction=source.get("elementor_default_direction", "row"),
            target_url=target["url"].rstrip("/"),
            credentials=Path(target["credentials"]).expanduser(),
            template=target.get("template", "page-fullwidth.php"),
            workdir=Path(raw.get("workdir", "work")),
            pages=tuple(PageMap(**p) for p in raw["pages"]),
            partners=tuple(Partner(**p) for p in raw.get("partners", [])),
            menu=MenuConfig(**raw["menu"]) if raw.get("menu") else None,
            section_nav=_section_nav(raw.get("section_nav")),
            notes=raw.get("notes", {}),
        )
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"config incompleta o malformata: {exc}") from exc
    errors = validate(cfg)
    if errors:
        raise ConfigError("; ".join(errors))
    return cfg
