# Site personnel — mode d'emploi

Site Quarto, publié automatiquement sur GitHub Pages à chaque `git push`.

---

## 1. Installation (une seule fois)

1. **Quarto** — <https://quarto.org/docs/get-started/> (installateur `.pkg` sur macOS,
   `.msi` sur Windows).
2. **Git** — inclus avec Quarto sur macOS via les outils Xcode ; sinon
   <https://git-scm.com>.
3. **Pandoc** — déjà inclus dans Quarto, rien à faire.
4. Un compte **GitHub** (gratuit).

Vérifier : `quarto --version` doit répondre.

## 2. Mise en ligne (une seule fois)

```bash
cd site-fdp
git init && git add -A && git commit -m "Première version"
git branch -M main
git remote add origin https://github.com/TON-COMPTE/site.git
git push -u origin main
```

Puis sur GitHub : **Settings → Pages → Source : GitHub Actions**.
Le site est en ligne deux à trois minutes plus tard.

Pour le domaine personnalisé : **Settings → Pages → Custom domain**, y entrer le
domaine, et chez le registraire créer un enregistrement `CNAME` pointant
`www` vers `TON-COMPTE.github.io`, plus quatre enregistrements `A` sur l'apex
(`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`). Le fichier `CNAME`
à la racine du dépôt contient déjà le domaine — le corriger.

## 3. Le cycle de travail quotidien

```bash
quarto preview          # aperçu local, se rafraîchit à chaque sauvegarde
```

Modifier un `.qmd` dans n'importe quel éditeur de texte, sauvegarder, regarder.
Quand c'est bon :

```bash
git add -A
git commit -m "Ajout de l'entrée CLÔTURE PRÉMATURÉE"
git push
```

C'est tout. Trois commandes, toujours les mêmes.

## 4. Mettre à jour le glossaire

Le fichier `glossaire/entrees.qmd` **fait autorité** depuis août 2026 : on y
écrit directement, et le `.docx` n'en est plus qu'un export ponctuel.

**Ajouter ou corriger une entrée**
Éditer `glossaire/entrees.qmd` à la main, en respectant les balises ci-dessous
et l'ordre alphabétique (accents ignorés). Puis :

```bash
python3 outils/indexer-glossaire.py    # reconstruit l'index des termes
python3 outils/verifier-liens.py       # signale les renvois sans ancre
quarto preview
```

`indexer-glossaire.py` relit les titres de `entrees.qmd` et régénère
`glossaire/_index-termes.yml`. Il n'écrit que ce fichier. L'option `--verifier`
compare sans écrire, ce qui convient à un contrôle avant commit.

**Produire un `.docx` quand une revue en réclame un**

```bash
quarto render glossaire/entrees.qmd --to docx
```

**Réimporter depuis Word** (hérité, à éviter)
`convertir-glossaire.py` régénère toute la page depuis un `.docx` — il
**écrase** `entrees.qmd`. Il refuse donc de tourner si le `.docx` est plus
ancien que le `.qmd`, et ne cède qu'avec `--force`, au prix des ajouts faits
depuis. Ce chemin n'a de sens que pour repartir d'un Word réellement plus à
jour que le dépôt, ce qui n'est plus le cas.

### Balises disponibles dans une entrée

```markdown
## TERME {#terme}

[sous-titre en petites capitales]{.sous-titre}

[à valider]{.statut}

::: {.punchline}
La formule en une phrase.
:::

::: {.definition}
La définition formelle.
:::

### Sous-section

Corps de texte.

::: {.voir-aussi}
**Voir aussi** — [autre terme](#autre-terme) · [encore un](#encore-un)
:::
```

### Renvoyer au glossaire depuis les autres pages

Ce que le lien englobe dépend de ce que la page fait du terme. Deux règles,
une par contexte.

**`glossaire/index.qmd` — la carte.** L'item de liste est une unité autonome :
article et emphase passent **à l'intérieur** du lien, qui couvre l'item entier.

```markdown
- [l'espace transitionnel](entrees.qmd#espace-transitionnel)
- [le *Ma*](entrees.qmd#ma-semiotique)
```

**`recherche.qmd` — la prose.** Le lien ne couvre que le terme : article et
attribution restent **hors** des crochets, l'emphase reste **dedans**.
L'italique marque les termes introduits dans la phrase, pas les simples
rappels.

```markdown
l'[émancipation](glossaire/entrees.qmd#emancipation) (Rancière)
le [*visible-pensant*](glossaire/entrees.qmd#visible-pensant)
```

Dans les deux cas, l'emphase se place toujours à l'intérieur des crochets :
jamais `*[terme](…)*`.

## 5. Les PDF (CV et projet de recherche)

```bash
./outils/publier-pdf.sh              # les quatre documents
./outils/publier-pdf.sh recherche    # un seul
```

**`quarto render` ne met pas à jour les PDF suivis** — il n'en produit même
aucun, le profil `_quarto-pdf.yml` n'étant pas activé sans `--profile pdf`. Et
un rendu PDF isolé dépose sa sortie dans `_site/`, ignoré par git : le fichier
publié reste alors à sa version précédente, sans que rien le signale. Ce script
est le seul chemin correct : il rend, recopie vers l'emplacement suivi, et
vérifie. Il ne fait pas le `git add`, qu'il rappelle en fin d'exécution.

Nécessite LaTeX : `quarto install tinytex` (une fois, 100 Mo).
Les liens de téléchargement existent déjà dans `cv.qmd` et `recherche.qmd`.

## 6. Citations

Placer les références dans `references.bib` (export Zotero → BibTeX, ou
mieux : extension **Better BibTeX** avec export automatique vers ce fichier).
Citer avec `[@auteur2024]` dans le texte.

Pour le style Chicago : télécharger
`chicago-note-bibliography.csl` depuis <https://www.zotero.org/styles>, le
déposer à la racine, et décommenter la ligne `csl:` dans `_quarto.yml`.

## 7. Le filigrane topographique

Les courbes de niveau du coin inférieur droit sont un composant partagé,
injecté par `include-after-body` dans l'accueil et les pages de section, des
deux côtés de la langue. Une page n'en reçoit pas si son en-tête ne le demande
pas : `glossaire/entrees.qmd`, page longue et dense, en est volontairement
exempte.

Le fichier `_filigrane-topo.html` est **généré**. Ne pas y toucher : régénérer.

```bash
python3 outils/generer-filigrane.py              # à l'identique (graine fixe)
python3 outils/generer-filigrane.py --graine 7   # un autre relief
```

Le style vit dans `styles.scss`, section « Filigrane topographique » — c'est là
qu'on règle la taille (`clamp`), l'opacité et la couleur, qui est `$relief`,
celle-là même des filets et des séparateurs. Le SVG trace en `currentColor` et
ne porte aucune couleur en propre.

Deux choix à ne pas défaire sans raison. Le motif est en `position: fixed`,
comme la trame de points du `body` : les deux appartiennent au même plan
« papier », et un filigrane qui défilerait avec le texte romprait cette unité.
Et il déborde à l'intérieur d'un carré en `overflow: hidden` plutôt que par des
décalages négatifs sur le viewport, qui provoqueraient une barre de défilement
horizontale.

## 8. Rendre le glossaire citable (DOI)

Une fois le dépôt public :

1. Se connecter à <https://zenodo.org> avec le compte GitHub.
2. Activer le dépôt dans l'onglet GitHub de Zenodo.
3. Sur GitHub : **Releases → Draft a new release**, tag `glossaire-v6`.

Zenodo archive la version et attribue un DOI. Chaque version publiée devient
citable :

> Prud'homme, François David. *Glossaire de la sémiose algorithmique*,
> version 6, 2026. DOI : 10.5281/zenodo.XXXXXXX

Ajouter ensuite le fichier `CITATION.cff` proposé par Zenodo à la racine.

## 9. À personnaliser avant la première mise en ligne

- [ ] `_quarto.yml` : `site-url`, adresse courriel, lien GitHub, ORCID
- [ ] `CNAME` : le domaine
- [ ] `cv.qmd` : dates, diplômes, cours, communications
- [ ] `publications.qmd` : titres réels
- [ ] `recherche.qmd` : résumé du projet
- [ ] `assets/favicon.png` : 512 × 512 px
- [ ] `en/cv.qmd` : version anglaise

## Structure

```
site-fdp/
├── _quarto.yml              configuration générale
├── styles.scss              palette, typographie, composants
├── _retour-haut.html        composant — bouton de remontée (pages longues)
├── _filigrane-topo.html     GÉNÉRÉ — courbes de niveau du coin inférieur droit
├── index.qmd                accueil
├── cv.qmd  recherche.qmd  publications.qmd
├── glossaire/
│   ├── index.qmd            carte des trois gestes
│   ├── entrees.qmd          SOURCE — corps alphabétique, édité à la main
│   └── _index-termes.yml    GÉNÉRÉ — index des ancres
├── en/                      version anglaise
├── outils/
│   ├── convertir-glossaire.py   (hérité — import Word, écrase entrees.qmd)
│   ├── indexer-glossaire.py     (reconstruit _index-termes.yml)
│   ├── generer-filigrane.py     (reconstruit _filigrane-topo.html)
│   └── source/              .docx sources (hors dépôt Git)
├── assets/                  images, PDF, favicon
└── .github/workflows/publier.yml
```
