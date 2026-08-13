#!/usr/bin/env bash
#
# publier-pdf.sh — produit les PDF livrables et les remet au niveau des sources.
#
# POURQUOI CE SCRIPT EXISTE
#
#   `quarto render` complet NE MET PAS À JOUR les PDF suivis par git. Il ne
#   produit même aucun PDF : le profil `_quarto-pdf.yml` n'est pas activé sans
#   `--profile pdf`, et le workflow GitHub n'installe pas LaTeX.
#
#   Et `quarto render <fichier> --to pdf --profile pdf` dépose sa sortie dans
#   `_site/`, qui est ignoré par git. Le fichier suivi — `cv.pdf`,
#   `recherche.pdf`… — reste donc à sa version précédente, et c'est lui que le
#   CI publie. L'écart est silencieux : le PDF est correct en local, périmé en
#   ligne. L'oubli de la recopie a déjà produit un 404 sur fdprudhomme.com.
#
#   Ce script est le seul chemin correct pour publier un PDF. Il rend, recopie,
#   et vérifie. Il ne commite pas : `git add` reste à votre main.
#
# USAGE
#
#   ./outils/publier-pdf.sh                 les quatre documents
#   ./outils/publier-pdf.sh recherche       un seul
#
#   Clés : cv · cv-en · recherche · recherche-en
#
set -euo pipefail

# ── Se placer à la racine du dépôt, quel que soit le répertoire d'appel ──────
# La racine est déduite de l'emplacement du script, non du répertoire courant :
# « git rev-parse » seul échouerait dès qu'on appelle le script depuis ailleurs,
# ce que l'énoncé demande précisément de permettre.
ici=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
racine=$(git -C "$ici" rev-parse --show-toplevel 2>/dev/null) || {
  echo "Erreur : $0 ne se trouve pas dans un dépôt git." >&2
  exit 1
}
cd "$racine"

# ── Table des documents : clé | source | sortie du rendu | destination suivie ─
# Pas de tableau associatif : bash 3.2, livré avec macOS, n'en dispose pas.
DOCUMENTS=(
  "cv|cv.qmd|_site/cv.pdf|cv.pdf"
  "cv-en|en/cv.qmd|_site/en/cv.pdf|en/cv.pdf"
  "recherche|recherche.qmd|_site/recherche.pdf|recherche.pdf"
  "recherche-en|en/research.qmd|_site/en/research.pdf|en/research.pdf"
)

# ── Portabilité macOS / Linux ────────────────────────────────────────────────
# GNU d'abord, BSD ensuite : sur Linux, « stat -f » ne provoque pas d'erreur —
# il affiche l'état du système de fichiers — et un repli dans ce sens ne se
# déclencherait jamais. « stat -c » en revanche est refusé par le stat de macOS.
horodatage() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1"; }
taille()     { wc -c < "$1" | tr -d ' '; }

# Le nombre de pages est un confort, jamais une condition de réussite : un
# pdfinfo absent ou en échec ne doit pas interrompre le script. D'où la garde
# explicite — sous « set -o pipefail », l'échec de pdfinfo ferait autrement
# échouer tout le pipeline, et « set -e » abandonnerait après la recopie.
pages() {
  local n=""
  if command -v pdfinfo >/dev/null 2>&1; then
    n=$(pdfinfo "$1" 2>/dev/null | awk '/^Pages:/ {print $2}') || n=""
  fi
  if [ -n "$n" ]; then
    echo "$n"
  else
    echo "?"
  fi
}

# ── Sélection ────────────────────────────────────────────────────────────────
filtre=${1:-}
selection=()
for entree in "${DOCUMENTS[@]}"; do
  cle=${entree%%|*}
  if [ -z "$filtre" ] || [ "$filtre" = "$cle" ]; then
    selection+=("$entree")
  fi
done

if [ ${#selection[@]} -eq 0 ]; then
  echo "Erreur : clé inconnue « $filtre »." >&2
  echo "Clés disponibles : cv · cv-en · recherche · recherche-en" >&2
  exit 1
fi

command -v quarto >/dev/null 2>&1 || {
  echo "Erreur : quarto est introuvable. Installer Quarto, puis TinyTeX" >&2
  echo "         par « quarto install tinytex »." >&2
  exit 1
}

# Instant de référence : tout PDF antérieur signale un rendu qui n'a pas eu
# lieu. Aucune tolérance — la comparaison est stricte (« antérieur à »), donc
# un fichier écrit dans la même seconde que le lancement passe, tandis qu'un
# résidu de l'exécution précédente est rejeté.
debut=$(date +%s)

recapitulatif=()
avertissements=0

for entree in "${selection[@]}"; do
  IFS='|' read -r cle source sortie destination <<< "$entree"

  echo
  echo "── $cle : $source"

  [ -f "$source" ] || { echo "Erreur : $source est introuvable." >&2; exit 1; }

  # 1. Rendre. set -e interrompt le script si quarto échoue ; le message de
  #    quarto reste visible, et rien n'est recopié.
  quarto render "$source" --to pdf --profile pdf

  # 2. Contrôler la sortie AVANT de recopier.
  if [ ! -f "$sortie" ]; then
    echo "Erreur : le rendu n'a produit aucun $sortie." >&2
    echo "         La destination $destination n'est pas modifiée." >&2
    exit 1
  fi

  if [ ! -s "$sortie" ]; then
    echo "Erreur : $sortie est vide. Recopie annulée." >&2
    exit 1
  fi

  if [ "$(horodatage "$sortie")" -lt "$debut" ]; then
    echo "Erreur : $sortie est antérieur au lancement du script." >&2
    echo "         Le rendu a été ignoré ; le fichier est un résidu périmé." >&2
    echo "         La destination $destination n'est pas modifiée." >&2
    exit 1
  fi

  # 3. Recopier, puis vérifier la destination.
  mkdir -p "$(dirname "$destination")"
  cp "$sortie" "$destination"

  if [ ! -s "$destination" ]; then
    echo "Erreur : $destination est absent ou vide après recopie." >&2
    exit 1
  fi

  echo "   → $destination"
  recapitulatif+=("$destination|$(taille "$destination")|$(pages "$destination")")
done

# ── Récapitulatif ────────────────────────────────────────────────────────────
echo
echo "────────────────────────────────────────────────────────────"
printf "%-22s %10s %8s\n" "FICHIER" "OCTETS" "PAGES"
for ligne in "${recapitulatif[@]}"; do
  IFS='|' read -r f o p <<< "$ligne"
  printf "%-22s %10s %8s\n" "$f" "$o" "$p"
done
echo "────────────────────────────────────────────────────────────"

if ! command -v pdfinfo >/dev/null 2>&1; then
  echo "Note : pdfinfo absent, le nombre de pages n'a pas pu être lu."
  avertissements=$((avertissements + 1))
fi

echo
echo "Les PDF sont à jour au niveau des sources mais PAS indexés."
echo "Pour les publier :"
printf '    git add'
for ligne in "${recapitulatif[@]}"; do printf ' %s' "${ligne%%|*}"; done
printf '\n'

exit 0
