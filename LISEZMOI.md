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

Le fichier `glossaire/entrees.qmd` est **généré**. Deux façons de travailler :

**A. Continuer dans Word** (transition douce)
Déposer la nouvelle version du `.docx` dans `outils/source/`, puis :

```bash
python3 outils/convertir-glossaire.py outils/source/GLOSSAIRE_IA_MaJ_v6.docx
quarto preview
```

Le script régénère la page, recrée les ancres et transforme les lignes
« Voir aussi » en liens internes. Il signale en fin d'exécution les termes
renvoyés qui n'ont pas d'entrée correspondante.

**B. Basculer la source dans le dépôt** (recommandé à terme)
Une fois la première conversion satisfaisante, éditer directement
`glossaire/entrees.qmd` et supprimer l'étape Word. Pour regénérer un `.docx`
quand une revue en réclame un :

```bash
quarto render glossaire/entrees.qmd --to docx
```

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

## 5. Le CV en PDF

```bash
quarto render cv.qmd --to pdf
```

Nécessite LaTeX : `quarto install tinytex` (une fois, 100 Mo).
Le PDF est produit à côté du `.html` ; le lien de téléchargement existe déjà
dans `cv.qmd`.

## 6. Citations

Placer les références dans `references.bib` (export Zotero → BibTeX, ou
mieux : extension **Better BibTeX** avec export automatique vers ce fichier).
Citer avec `[@auteur2024]` dans le texte.

Pour le style Chicago : télécharger
`chicago-note-bibliography.csl` depuis <https://www.zotero.org/styles>, le
déposer à la racine, et décommenter la ligne `csl:` dans `_quarto.yml`.

## 7. Rendre le glossaire citable (DOI)

Une fois le dépôt public :

1. Se connecter à <https://zenodo.org> avec le compte GitHub.
2. Activer le dépôt dans l'onglet GitHub de Zenodo.
3. Sur GitHub : **Releases → Draft a new release**, tag `glossaire-v6`.

Zenodo archive la version et attribue un DOI. Chaque version publiée devient
citable :

> Prud'homme, François David. *Glossaire de la sémiose algorithmique*,
> version 6, 2026. DOI : 10.5281/zenodo.XXXXXXX

Ajouter ensuite le fichier `CITATION.cff` proposé par Zenodo à la racine.

## 8. À personnaliser avant la première mise en ligne

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
├── index.qmd                accueil
├── cv.qmd  recherche.qmd  publications.qmd
├── glossaire/
│   ├── index.qmd            carte des trois gestes
│   ├── entrees.qmd          GÉNÉRÉ — corps alphabétique
│   └── _index-termes.yml    GÉNÉRÉ — index des ancres
├── en/                      version anglaise
├── outils/
│   ├── convertir-glossaire.py
│   └── source/              .docx sources (hors dépôt Git)
├── assets/                  images, PDF, favicon
└── .github/workflows/publier.yml
```
