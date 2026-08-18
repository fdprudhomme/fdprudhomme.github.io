#!/usr/bin/env python3
"""
Script post-render Quarto : localise la barre de navigation, le pied de page
et le lien de retour FR/EN sur les pages du dossier en/ (et corrige le lien
"EN" des pages FR pour qu'il pointe vers la page anglaise équivalente plutôt
que systématiquement vers en/index.html).

Quarto ne propose pas de barre de navigation par langue pour un projet
"website" unique : la config _quarto.yml -> website.navbar est globale et
s'applique telle quelle à toutes les pages, y compris celles sous en/. Ce
script corrige ce point après coup, sur le HTML généré, sans toucher au
rendu Quarto lui-même.

Appelé automatiquement par Quarto via `project.post-render` (voir
_quarto.yml), donc à chaque `quarto render`, en local comme dans l'action
GitHub "Publier le site".
"""

import os

OUTPUT_DIR = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")

LEFT_MARKER = '<ul class="navbar-nav navbar-nav-scroll me-auto">'
RIGHT_MARKER = '<ul class="navbar-nav navbar-nav-scroll ms-auto">'

# Traductions appliquées à l'intérieur du menu de gauche pour les pages en/*.
LEFT_NAV_SUBS = [
    ('href="../index.html"', 'href="index.html"'),
    ('>Accueil<', '>Home<'),
    ('href="../recherche.html"', 'href="research.html"'),
    ('>Recherche<', '>Research<'),
    ('>Glossaire<', '>Glossary (FR)<'),
    ('>Carte du glossaire<', '>Glossary map<'),
    ('>Entrées (A–Z)<', '>Entries (A–Z)<'),
    ('href="../publications.html"', 'href="publications.html"'),
    ('href="../cv.html"', 'href="cv.html"'),
]

# Pages EN <-> page FR équivalente (chemins relatifs à la racine du site).
EN_TO_FR = {
    "en/index.html": "index.html",
    "en/research.html": "recherche.html",
    "en/cv.html": "cv.html",
    "en/publications.html": "publications.html",
}
FR_TO_EN = {fr: en for en, fr in EN_TO_FR.items()}


def fix_en_page(html: str) -> str:
    left_start = html.find(LEFT_MARKER)
    right_start = html.find(RIGHT_MARKER)
    if left_start == -1 or right_start == -1:
        return html

    right_end = html.find("</ul>", right_start)
    right_end = right_end + len("</ul>") if right_end != -1 else right_start

    left_segment = html[left_start:right_start]
    right_segment = html[right_start:right_end]

    for old, new in LEFT_NAV_SUBS:
        left_segment = left_segment.replace(old, new)

    right_segment = right_segment.replace('href="../en/index.html"', 'href="__FR_TARGET__"')
    right_segment = right_segment.replace(">EN<", ">FR<")

    html = html[:left_start] + left_segment + right_segment + html[right_end:]

    # Pied de page : quelques mentions restées en français.
    html = html.replace(
        'Contenu sous licence <a href="https://creativecommons.org/licenses/by/4.0/deed.fr">',
        'Content licensed under <a href="https://creativecommons.org/licenses/by/4.0/deed.en">',
    )
    html = html.replace(">Code source<", ">Source code<")

    # Bouton « retour en haut » (_retour-haut.html) : étiquette accessible.
    html = html.replace(
        'aria-label="Revenir en haut de la page"',
        'aria-label="Back to top of page"',
    )

    return html


def fix_fr_page(html: str, en_target: str) -> str:
    right_start = html.find(RIGHT_MARKER)
    if right_start == -1:
        return html
    right_end = html.find("</ul>", right_start)
    right_end = right_end + len("</ul>") if right_end != -1 else right_start

    right_segment = html[right_start:right_end]
    right_segment = right_segment.replace(
        'href="./en/index.html"', 'href="__EN_TARGET__"'
    ).replace(
        'href="en/index.html"', 'href="__EN_TARGET__"'
    )
    return html[:right_start] + right_segment + html[right_end:]


def main():
    if not os.path.isdir(OUTPUT_DIR):
        return

    for root, _dirs, files in os.walk(OUTPUT_DIR):
        for name in files:
            if not name.endswith(".html"):
                continue
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, OUTPUT_DIR).replace(os.sep, "/")

            with open(full_path, "r", encoding="utf-8") as f:
                html = f.read()

            changed = False

            if rel_path in EN_TO_FR:
                new_html = fix_en_page(html)
                fr_page = EN_TO_FR[rel_path]
                new_html = new_html.replace("__FR_TARGET__", f"../{fr_page}")
                if new_html != html:
                    html = new_html
                    changed = True
            elif rel_path in FR_TO_EN:
                en_page = FR_TO_EN[rel_path]
                new_html = fix_fr_page(html, en_page)
                new_html = new_html.replace("__EN_TARGET__", en_page)
                if new_html != html:
                    html = new_html
                    changed = True

            if changed:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(html)


if __name__ == "__main__":
    main()
