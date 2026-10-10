"""Lettura dei fogli di stile Elementor (post-<id>.css).

Dall'HTML non si capisce se un container è a righe o a colonne, né quale immagine di sfondo
abbia: lo dicono solo le regole CSS per `.elementor-element-<id>`.
Le regole dentro @media (responsive) vengono ignorate: interessa il layout desktop.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ELEMENT_ID_RE = re.compile(r"\.elementor-element-([0-9a-f]{6,8})\b")
DIRECTION_RE = re.compile(r"(?:--)?flex-direction\s*:\s*(row|column)(?:-reverse)?")
BACKGROUND_RE = re.compile(r"background-image\s*:\s*url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


@dataclass
class ElementorStyles:
    directions: dict[str, str] = field(default_factory=dict)
    backgrounds: dict[str, str] = field(default_factory=dict)

    def merge(self, other: "ElementorStyles") -> "ElementorStyles":
        return ElementorStyles({**self.directions, **other.directions}, {**self.backgrounds, **other.backgrounds})


def strip_at_blocks(css: str) -> str:
    """Rimuove i blocchi @media/@supports (annidati) lasciando le regole di primo livello."""
    out: list[str] = []
    i, n = 0, len(css)
    while i < n:
        if css.startswith("@media", i) or css.startswith("@supports", i):
            brace = css.find("{", i)
            if brace == -1:
                break
            depth, j = 1, brace + 1
            while j < n and depth:
                depth += {"{": 1, "}": -1}.get(css[j], 0)
                j += 1
            i = j
        else:
            out.append(css[i])
            i += 1
    return "".join(out)


def parse(css: str) -> ElementorStyles:
    styles = ElementorStyles()
    for selector, decls in re.findall(r"([^{}]+)\{([^{}]*)\}", strip_at_blocks(css)):
        ids = set(ELEMENT_ID_RE.findall(selector))
        if not ids:
            continue
        direction = DIRECTION_RE.search(decls)
        background = BACKGROUND_RE.search(decls)
        for element_id in ids:
            if direction:
                styles.directions[element_id] = direction.group(1)
            if background:
                styles.backgrounds[element_id] = background.group(1)
    return styles
