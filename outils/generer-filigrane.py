#!/usr/bin/env python3
"""Génère _filigrane-topo.html — les courbes de niveau du coin inférieur droit.

Le motif n'est pas dessiné à la main : quatorze courbes fermées concentriques,
chacune un cercle déformé par une somme de quatre sinusoïdes de fréquences et
de phases tirées au sort, puis lissée en spline Catmull-Rom convertie en Bézier
cubique. L'amplitude de la déformation et la dérive du centre croissent avec le
rayon : les anneaux intérieurs restent presque gigognes, les extérieurs se
croisent. C'est ce gradient qui produit une lecture « carte topographique »
plutôt qu'une lecture « cible ».

La graine est fixe : deux exécutions donnent le même fichier, et le dépôt reste
propre. La changer tire un nouveau relief.

    python3 outils/generer-filigrane.py            # régénère à l'identique
    python3 outils/generer-filigrane.py --graine 7 # un autre relief

Le trait est en currentColor : la couleur et l'opacité vivent dans styles.scss,
section « Filigrane topographique ». Ne rien styler ici.
"""

import argparse
import math
import random
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "_filigrane-topo.html"

COTE = 1000            # côté du viewBox
CX, CY = 520.0, 500.0  # centre nominal, légèrement décentré
ANNEAUX = 14
POINTS = 48            # points par anneau avant lissage — au-delà, le fichier
                       # grossit sans que l'œil y gagne quoi que ce soit

ENTETE = """<!--
  Filigrane topographique — coin inférieur droit. Composant partagé par
  l'accueil et les pages de section (FR et EN), via include-after-body.
  Il vit à la racine parce qu'il n'appartient à aucune page en propre.

  Purement décoratif : aucune dépendance, aucun JS, aucune requête réseau.
  aria-hidden + pointer-events: none (styles.scss) — invisible aux lecteurs
  d'écran, intraversable au clavier comme à la souris, et le bouton « retour
  en haut » qui le recouvre reste cliquable.

  FICHIER GÉNÉRÉ — ne pas éditer les tracés à la main.
  Régénérer : python3 outils/generer-filigrane.py
-->
"""


def anneau(rayon, amplitude, frequences, phases):
    """Un cercle de rayon donné, déformé par une somme de sinusoïdes."""
    poids = (1.0, 0.62, 0.38, 0.22)
    points = []
    for i in range(POINTS):
        t = 2 * math.pi * i / POINTS
        d = sum(p * math.sin(f * t + ph)
                for f, ph, p in zip(frequences, phases, poids))
        r = rayon * (1.0 + amplitude * d)
        points.append((CX + r * math.cos(t), CY + r * math.sin(t)))
    return points


def spline_fermee(points):
    """Catmull-Rom → Bézier cubique, sur un contour fermé."""
    n = len(points)
    d = "M %.1f %.1f" % points[0]
    for i in range(n):
        p0, p1 = points[(i - 1) % n], points[i]
        p2, p3 = points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d += " C %.1f %.1f %.1f %.1f %.1f %.1f" % (c1 + c2 + p2)
    return d + " Z"


def tracer(graine):
    alea = random.Random(graine)
    chemins = []
    for i in range(ANNEAUX):
        f = i / (ANNEAUX - 1)                       # 0 au centre, 1 au bord
        rayon = 48 + 480 * (f ** 1.28)
        amplitude = 0.016 + 0.098 * (f ** 1.9)      # irrégularité croissante
        frequences = (alea.choice([3, 4, 5]), alea.choice([5, 6, 7]),
                      alea.choice([7, 8, 9]), alea.choice([2, 3]))
        phases = [alea.uniform(0, 2 * math.pi) for _ in range(4)]

        # Dérive du centre : sans elle les anneaux seraient parfaitement
        # gigognes, ce qui se lit comme une cible et non comme un relief.
        dx = 26 * f * math.cos(1.7 + 2.2 * f)
        dy = 20 * f * math.sin(0.4 + 2.6 * f)
        points = [(x + dx, y + dy)
                  for x, y in anneau(rayon, amplitude, frequences, phases)]
        chemins.append(spline_fermee(points))
    return chemins


def main():
    ap = argparse.ArgumentParser(description="Génère _filigrane-topo.html")
    ap.add_argument("--graine", type=int, default=20260813,
                    help="graine du tirage (défaut : 20260813)")
    args = ap.parse_args()

    chemins = "\n      ".join('<path d="%s"/>' % c for c in tracer(args.graine))
    svg = (
        '  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d"'
        ' aria-hidden="true" focusable="false">\n'
        '    <g fill="none" stroke="currentColor" stroke-width="1.1"\n'
        '       stroke-linejoin="round" vector-effect="non-scaling-stroke">\n'
        '      %s\n'
        '    </g>\n'
        '  </svg>\n' % (COTE, COTE, chemins)
    )
    SORTIE.write_text(
        ENTETE + '<div class="filigrane-topo" aria-hidden="true">\n'
        + svg + '</div>\n', encoding="utf-8")
    print("%s — %d anneaux, %.1f Ko"
          % (SORTIE.name, ANNEAUX, SORTIE.stat().st_size / 1024))


if __name__ == "__main__":
    main()
