#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstruit glossaire/_index-termes.yml à partir de glossaire/entrees.qmd.

glossaire/entrees.qmd fait autorité : les entrées y sont ajoutées et corrigées
à la main. Ce script en relit les titres et régénère l'index des termes, sans
jamais toucher au .qmd ni à aucun .docx. C'est le pendant léger de
convertir-glossaire.py, qui lui régénère tout depuis Word et n'a plus lieu de
servir tant que le .docx reste un export.

Le seul fichier écrit est glossaire/_index-termes.yml. Sans effet de bord et
relançable.

Usage :
    python3 outils/indexer-glossaire.py            # écrit l'index
    python3 outils/indexer-glossaire.py --verifier  # ne compare, n'écrit pas

Code de sortie : 0 si tout va bien ; 1 si --verifier détecte un index périmé ;
2 si une anomalie structurelle est trouvée (ancre en double, source absente).
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "glossaire" / "entrees.qmd"
INDEX = RACINE / "glossaire" / "_index-termes.yml"

ENTETE = "# Généré automatiquement — ne pas éditer à la main\ntermes:\n"

# Titre d'entrée : « ## TERME {#ancre} », niveau 2 uniquement.
RE_ENTREE = re.compile(r"^## (.+?) \{#([a-z0-9-]+)\}\s*$", re.M)
# Précision entre parenthèses en fin de titre : « LLM (LARGE LANGUAGE MODEL) ».
PARENTHESE_FINALE = re.compile(r"^(.*?)\s*\((.+)\)\s*$")


def slug(texte: str) -> str:
    """Identique à convertir-glossaire.py : l'ancre doit rester stable."""
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def scinder_parenthese(terme: str) -> str:
    """Le terme indexé exclut la précision finale entre parenthèses, comme le
    fait convertir-glossaire.py : l'index liste « LLM », pas
    « LLM (LARGE LANGUAGE MODEL) »."""
    m = PARENTHESE_FINALE.match(terme)
    return m.group(1).strip(" ,") if m else terme


def relever(chemin: Path) -> list[tuple[str, str]]:
    texte = chemin.read_text(encoding="utf-8")
    return [(scinder_parenthese(t), a) for t, a in RE_ENTREE.findall(texte)]


def rendre(entrees: list[tuple[str, str]]) -> str:
    return ENTETE + "".join(
        f'  - terme: "{t}"\n    ancre: "{a}"\n' for t, a in entrees
    )


def controler(entrees: list[tuple[str, str]]) -> list[str]:
    """Anomalies qui rendraient l'index ou les liens internes incohérents."""
    anomalies = []
    ancres = [a for _, a in entrees]
    for a in sorted({a for a in ancres if ancres.count(a) > 1}):
        anomalies.append(f"ancre en double : #{a}")
    for terme, ancre in entrees:
        if slug(terme) != ancre:
            anomalies.append(
                f"ancre non conforme au terme : « {terme} » → #{ancre} "
                f"(attendu #{slug(terme)})"
            )
    return anomalies


def main() -> int:
    verifier_seulement = "--verifier" in sys.argv[1:]

    if not SOURCE.is_file():
        print(f"Source introuvable : {SOURCE}", file=sys.stderr)
        return 2

    entrees = relever(SOURCE)
    if not entrees:
        print(f"Aucune entrée trouvée dans {SOURCE.relative_to(RACINE)}.", file=sys.stderr)
        return 2

    anomalies = controler(entrees)
    for a in anomalies:
        print(f"⚠ {a}", file=sys.stderr)

    attendu = rendre(entrees)
    actuel = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else None

    if verifier_seulement:
        if actuel == attendu:
            print(f"Index à jour — {len(entrees)} entrées.")
            return 0
        print(f"Index périmé — {len(entrees)} entrées dans "
              f"{SOURCE.relative_to(RACINE)}. Relancer sans --verifier.",
              file=sys.stderr)
        return 1

    if actuel == attendu:
        print(f"Index déjà à jour — {len(entrees)} entrées, rien à écrire.")
        return 0

    INDEX.write_text(attendu, encoding="utf-8")
    print(f"✓ {len(entrees)} entrées écrites dans {INDEX.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
