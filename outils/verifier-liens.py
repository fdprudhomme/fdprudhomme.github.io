#!/usr/bin/env python3
"""
Vérificateur d'ancres pour le glossaire — LECTURE SEULE.

Collecte dans glossaire/entrees.qmd :
  - les ancres déclarées, de la forme  {#ancre}  ;
  - les cibles de liens internes, de la forme  [terme affiché](#ancre).

Écrit dans outils/liens-casses.txt chaque cible qui ne correspond à aucune
ancre déclarée, avec le terme affiché et le numéro de ligne — dédoublonné
et trié.

Ce script ne modifie jamais entrees.qmd, ni aucun .docx. Le seul fichier
écrit est outils/liens-casses.txt. Il est sans effet de bord et relançable.

Usage :
    python3 outils/verifier-liens.py [chemin/vers/entrees.qmd]

Code de sortie : 0 si aucun lien cassé, 1 sinon.
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DEFAUT = os.path.join(RACINE, "glossaire", "entrees.qmd")
RAPPORT = os.path.join(RACINE, "outils", "liens-casses.txt")

# {#ancre} — sur un titre ou en attribut de div.
RE_ANCRE = re.compile(r"\{#([A-Za-z0-9_-]+)[^}]*\}")
# [terme affiché](#ancre) — lien interne uniquement, on ignore les URL.
RE_LIEN = re.compile(r"\[([^\]\n]+)\]\(#([A-Za-z0-9_-]+)\)")


def analyser(chemin):
    with open(chemin, encoding="utf-8") as f:
        lignes = f.readlines()

    ancres = set()
    for ligne in lignes:
        ancres.update(RE_ANCRE.findall(ligne))

    liens = []  # (ancre, terme, numéro de ligne)
    for no, ligne in enumerate(lignes, start=1):
        for terme, ancre in RE_LIEN.findall(ligne):
            liens.append((ancre, terme.strip(), no))

    casses = sorted({(a, t, n) for a, t, n in liens if a not in ancres})
    return ancres, liens, casses


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else SOURCE_DEFAUT
    if not os.path.isfile(source):
        print(f"Source introuvable : {source}", file=sys.stderr)
        return 2

    ancres, liens, casses = analyser(source)

    with open(RAPPORT, "w", encoding="utf-8") as f:
        f.write(f"# Liens internes sans ancre correspondante — {os.path.relpath(source, RACINE)}\n")
        f.write(f"# {len(ancres)} ancres declarees, {len(liens)} liens internes, "
                f"{len(casses)} cibles cassees\n")
        if not casses:
            f.write("# (aucune)\n")
        for ancre, terme, no in casses:
            f.write(f"#{ancre}\t{terme}\tl.{no}\n")

    print(f"{len(ancres)} ancres déclarées")
    print(f"{len(liens)} liens internes")
    print(f"{len(casses)} cibles cassées → {os.path.relpath(RAPPORT, RACINE)}")
    return 1 if casses else 0


if __name__ == "__main__":
    sys.exit(main())
