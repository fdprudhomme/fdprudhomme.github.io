#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit GLOSSAIRE_IA_MaJ_vN.docx en page Quarto (glossaire/entrees.qmd).

Usage :
    python3 outils/convertir-glossaire.py outils/source/GLOSSAIRE_IA_MaJ_v5.docx

Ce que le script fait :
  1. appelle pandoc pour extraire le texte du .docx en Markdown ;
  2. détecte les entrées (titres en CAPITALES) et leur donne une ancre stable ;
  3. reconnaît les blocs typés : statut, punchline, définition, sous-titres ;
  4. transforme chaque ligne « Voir aussi : … » en liens internes vers les
     entrées existantes (les termes sans entrée restent en texte simple et
     sont signalés en fin d'exécution) ;
  5. écrit glossaire/entrees.qmd et glossaire/_index-termes.yml.

Le script ne modifie jamais le .docx source.
"""
from __future__ import annotations
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "glossaire" / "entrees.qmd"
INDEX = RACINE / "glossaire" / "_index-termes.yml"

# Lignes courtes qui sont des sous-titres d'entrée plutôt que du corps de texte.
PREFIXES_SOUS_TITRE = (
    "articulation", "cadre", "pont", "versant", "fondement", "implication",
    "cercle", "distinction", "les ", "le ", "la ", "l'", "usage", "portée",
    "enjeu", "limite", "exemple", "précision", "remarque", "note", "origine",
    "généalogie", "rapport", "lien", "et ", "définition",
)

STATUTS = re.compile(r"^\*+\[(.+?)\]\*+$")
PUNCHLINE = re.compile(r"^\*\*\*(.+?)\*\*\*$", re.S)
DEFINITION = re.compile(r"^\*(?!\*)(.+?)\*$", re.S)
VOIR_AUSSI = re.compile(r"^\*?Voir aussi\s*:\s*(.+?)\.?\*?$", re.I | re.S)
# Les parenthèses sont autorisées dans le titre pour reconnaître des formes
# comme « LLM (LARGE LANGUAGE MODEL) » ou « MÉMOIRE PERSISTANTE (MEMORY) » ;
# scinder_parenthese() les sépare ensuite du terme pour ne pas polluer l'ancre.
TITRE_ENTREE = re.compile(r"^\*{0,3}([A-ZÀ-ÜŒÇ0-9][A-ZÀ-ÜŒÇ0-9 ,''\u2019()\-]{2,})(\s+—\s+(.+?))?\*{0,3}$")
PARENTHESE_FINALE = re.compile(r"^(.*?)\s*\((.+)\)\s*$")

IGNORER = {"GLOSSAIRE IA", "CARTE DU GLOSSAIRE"}


def scinder_parenthese(terme: str) -> tuple[str, str]:
    """Sépare un titre du type « LLM (LARGE LANGUAGE MODEL) » en
    (terme, précision) : le terme seul sert à l'ancre et au slug, la
    précision devient un sous-titre si aucun autre n'a été fourni."""
    m = PARENTHESE_FINALE.match(terme)
    if m:
        return m.group(1).strip(" ,"), m.group(2).strip()
    return terme, ""


def slug(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t


def sans_balises(texte: str) -> str:
    return re.sub(r"[*_`]", "", texte).strip()


def normaliser_setext(md: str) -> str:
    """Convertit les titres setext (soulignés par des ===/---) en titres ATX
    (#/##). Pandoc n'écrit en ATX pour tous les niveaux que si on lui passe
    --markdown-headings=atx (disponible depuis pandoc 2.11.4) ; sans cette
    option — ou si l'option n'est pas supportée par la version installée —
    les Titre1/Titre2 Word ressortent en setext. C'est précisément ce cas
    que le reste du script ne savait pas reconnaître (un bloc setext tient
    sur deux lignes, donc le test `"\\n" in ligne` de est_titre_entree() le
    rejetait silencieusement, et le terme retombait en simple texte)."""
    lignes = md.split("\n")
    sortie: list[str] = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        suivante = lignes[i + 1] if i + 1 < len(lignes) else ""
        if ligne.strip() and not ligne.lstrip().startswith("#") and re.fullmatch(r"=+", suivante.strip()):
            sortie.append(f"# {ligne.strip()}")
            i += 2
            continue
        if ligne.strip() and not ligne.lstrip().startswith("#") and re.fullmatch(r"-{2,}", suivante.strip()):
            sortie.append(f"## {ligne.strip()}")
            i += 2
            continue
        sortie.append(ligne)
        i += 1
    return "\n".join(sortie)


def extraire_markdown(source: Path) -> str:
    """Passe par pandoc si le fichier est un vrai .docx, sinon lit le texte."""
    try:
        with open(source, "rb") as f:
            entete = f.read(2)
    except FileNotFoundError:
        sys.exit(f"Fichier introuvable : {source}")
    if entete != b"PK":
        return normaliser_setext(source.read_text(encoding="utf-8"))

    # "markdown-smart" (et non "markdown") : on désactive la conversion
    # automatique de la ponctuation typographique du .docx (tiret cadratin
    # « — », guillemets courbes) vers ses équivalents ASCII (« --- », etc.).
    # Sans quoi le tiret cadratin qui sépare un terme de son sous-titre
    # (« AGENT — Acteur algorithmique... ») ressort en trois traits d'union,
    # que ni TITRE_ENTREE ni le partition(" — ") plus bas ne reconnaissent :
    # le sous-titre reste alors collé au terme, y compris dans l'ancre.
    commande = ["pandoc", "-f", "docx", "-t", "markdown-smart",
                "--wrap=none", "--markdown-headings=atx", str(source)]
    try:
        resultat = subprocess.run(commande, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("Pandoc introuvable : installez-le avant de relancer le script.")

    if resultat.returncode != 0 and "--markdown-headings" in resultat.stderr:
        # Pandoc < 2.11.4 : l'option n'existe pas. On se rabat sur le
        # comportement par défaut (setext pour Titre1/Titre2) et on
        # normalise nous-mêmes ci-dessous — le résultat final est identique.
        commande = [c for c in commande if not c.startswith("--markdown-headings")]
        resultat = subprocess.run(commande, capture_output=True, text=True)

    if resultat.returncode != 0:
        sys.exit(f"Pandoc a échoué :\n{resultat.stderr}")
    return normaliser_setext(resultat.stdout)


def est_titre_entree(bloc: str) -> tuple[str, str] | None:
    """Renvoie (terme, sous-titre) si le bloc est un titre d'entrée."""
    ligne = bloc.strip()
    if ligne.startswith("#"):                       # pandoc a gardé le style Word
        m = re.match(r"^(#{1,6})\s*(.+?)\s*$", ligne)
        if not m:
            return None
        niveau, texte = len(m.group(1)), m.group(2)
        if niveau != 2:
            # Titre1 (page de titre) ou Titre3+ (sous-section) : ce n'est
            # pas une entrée de premier niveau. Titre3+ retombe plus bas
            # dans main() et reste affiché tel quel (### ...) ; Titre1 est
            # ignoré (ex. « GLOSSAIRE IA »).
            return None
        if len(texte.split()) > 12:
            return None
        nu = sans_balises(texte)
        terme, _, sous = nu.partition(" — ")
        terme, sous = terme.strip(), sous.strip()
        if terme in IGNORER or len(terme) < 3:
            return None
        terme, paren = scinder_parenthese(terme)
        return terme, (sous or paren)
    if len(ligne) > 110 or "\n" in ligne:
        return None
    m = TITRE_ENTREE.match(ligne)
    if not m:
        return None
    terme = m.group(1).strip(" ,")
    if terme in IGNORER or len(terme) < 3:
        return None
    lettres = [c for c in terme if c.isalpha()]
    if not lettres or sum(c.isupper() for c in lettres) / len(lettres) < 0.9:
        return None
    sous = (m.group(3) or "").strip()
    terme, paren = scinder_parenthese(terme)
    return terme, (sous or paren)


def est_sous_titre(bloc: str) -> bool:
    ligne = bloc.strip()
    if not ligne or "\n" in ligne or len(ligne) > 95:
        return False
    if ligne[0] in "*-#>|" or ligne[-1] in ".!?;»":
        return False
    if not ligne[0].isupper():
        return False
    bas = ligne.lower()
    if " : " in ligne and not bas.startswith(PREFIXES_SOUS_TITRE):
        return False
    return True


def lier_renvois(liste: str, table: dict[str, str], manquants: set) -> str:
    sorties = []
    for brut in re.split(r"[,;]", liste):
        terme = sans_balises(brut).strip(" .")
        if not terme:
            continue
        cle = slug(terme)
        cible = table.get(cle)
        if cible is None:
            for k, v in table.items():
                if cle and (cle in k or k in cle) and abs(len(k) - len(cle)) < 8:
                    cible = v
                    break
        if cible:
            sorties.append(f"[{terme}](#{cible})")
        else:
            manquants.add(terme)
            sorties.append(terme)
    return " · ".join(sorties)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = Path(sys.argv[1])
    blocs = [b.strip() for b in extraire_markdown(source).split("\n\n") if b.strip()]

    # Passe 1 : recenser les entrées pour pouvoir résoudre les renvois.
    table: dict[str, str] = {}
    for bloc in blocs:
        t = est_titre_entree(bloc)
        if t:
            table[slug(t[0])] = slug(t[0])

    # Passe 2 : écrire.
    manquants: set[str] = set()
    lignes: list[str] = []
    entrees: list[tuple[str, str]] = []
    dans_entree = False

    for bloc in blocs:
        titre = est_titre_entree(bloc)
        if titre:
            terme, sous = titre
            ancre = slug(terme)
            entrees.append((terme, ancre))
            dans_entree = True
            lignes.append(f"\n## {terme} {{#{ancre}}}\n")
            if sous:
                lignes.append(f"[{sous}]{{.sous-titre}}\n")
            continue

        if not dans_entree:
            continue

        m = STATUTS.match(bloc)
        if m:
            lignes.append(f"[{m.group(1)}]{{.statut}}\n")
            continue

        m = VOIR_AUSSI.match(bloc.replace("\n", " "))
        if m:
            liens = lier_renvois(m.group(1), table, manquants)
            lignes.append("::: {.voir-aussi}\n**Voir aussi** — "
                          f"{liens}\n:::\n")
            continue

        m = PUNCHLINE.match(bloc)
        if m:
            lignes.append(f"::: {{.punchline}}\n{m.group(1).strip()}\n:::\n")
            continue

        m = DEFINITION.match(bloc)
        if m and len(bloc) > 60:
            lignes.append(f"::: {{.definition}}\n{m.group(1).strip()}\n:::\n")
            continue

        if est_sous_titre(bloc):
            lignes.append(f"### {bloc}\n")
            continue

        lignes.append(bloc + "\n")

    entete = """---
title: "Glossaire de la sémiose algorithmique"
subtitle: "Corps alphabétique"
page-layout: full
toc: true
toc-depth: 2
toc-title: "Entrées"
toc-location: left
---

::: {.avertissement}
Glossaire de travail, révisé en continu. Chaque entrée porte, le cas échéant,
son état de validation. La [carte du glossaire](index.qmd) en donne
l'architecture ; la présente page se lit dans l'ordre alphabétique.
:::
"""

    SORTIE.write_text(entete + "\n".join(lignes), encoding="utf-8")
    INDEX.write_text(
        "# Généré automatiquement — ne pas éditer à la main\ntermes:\n"
        + "".join(f'  - terme: "{t}"\n    ancre: "{a}"\n' for t, a in entrees),
        encoding="utf-8",
    )

    print(f"✓ {len(entrees)} entrées écrites dans {SORTIE.relative_to(RACINE)}")
    if manquants:
        print(f"\n⚠ {len(manquants)} renvois sans entrée correspondante "
              "(laissés en texte simple) :")
        for t in sorted(manquants):
            print(f"   · {t}")


if __name__ == "__main__":
    main()
