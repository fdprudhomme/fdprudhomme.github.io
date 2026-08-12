--[[
  liens-absolus.lua — réécrit les liens internes en URL absolues, pour la
  seule sortie LaTeX.

  Un PDF circule détaché du site : « glossaire/entrees.qmd#semiose-algorithmique »
  n'y désigne rien. Le filtre transforme toute cible interne en URL complète
  sur https://fdprudhomme.com, et l'extension .qmd en .html.

  Sont laissées intactes :
    · les URL absolues (http:, https:)
    · les adresses (mailto:)
    · les ancres internes au document (#geste-1), qui restent valides en PDF

  Le chemin est résolu depuis le répertoire du document source, faute de quoi
  « research.qmd » appelé depuis en/ pointerait vers la racine du site. Les
  remontées « ../ » sont normalisées, de même que les chemins en « / ».

  Usage : format: pdf: filters: [outils/liens-absolus.lua]
]]

local BASE = "https://fdprudhomme.com/"

-- Répertoire du document, relatif à la racine du projet : "", "en", "glossaire".
local function repertoire_source()
  local entree, racine

  -- Sous Quarto : chemins absolus, dont on retire la racine du projet.
  if quarto and quarto.doc and quarto.doc.input_file then
    entree = quarto.doc.input_file
    if quarto.project and quarto.project.directory then
      racine = quarto.project.directory
    end
  -- Sous pandoc seul (tests) : le chemin passé en argument.
  elseif PANDOC_STATE and PANDOC_STATE.input_files
         and PANDOC_STATE.input_files[1] then
    entree = PANDOC_STATE.input_files[1]
  end

  if not entree then return "" end
  entree = entree:gsub("\\", "/")

  if racine then
    racine = racine:gsub("\\", "/"):gsub("/$", "")
    entree = entree:gsub("^" .. racine:gsub("%p", "%%%0") .. "/", "")
  end

  return entree:match("^(.*)/[^/]*$") or ""
end

-- Réduit « a/b/../c » en « a/c » et supprime les « ./ ».
local function normaliser(chemin)
  local segments = {}
  for segment in chemin:gmatch("[^/]+") do
    if segment == ".." then
      table.remove(segments)
    elseif segment ~= "." then
      table.insert(segments, segment)
    end
  end
  return table.concat(segments, "/")
end

local REPERTOIRE = nil

local function absolutiser(cible)
  if cible == "" then return cible end
  -- Protocoles et ancres locales : rien à faire.
  if cible:match("^%a[%w+.-]*:") or cible:sub(1, 1) == "#" then
    return cible
  end

  local chemin, fragment = cible:match("^([^#]*)(#?.*)$")
  if chemin == "" then return cible end

  if chemin:sub(1, 1) == "/" then
    -- Chemin depuis la racine du site.
    chemin = chemin:sub(2)
  else
    REPERTOIRE = REPERTOIRE or repertoire_source()
    if REPERTOIRE ~= "" then
      chemin = REPERTOIRE .. "/" .. chemin
    end
  end

  chemin = normaliser(chemin):gsub("%.qmd$", ".html")
  return BASE .. chemin .. fragment
end

if FORMAT:match("latex") then
  return {
    { Link  = function(el) el.target = absolutiser(el.target); return el end },
    { Image = function(el) return el end },  -- les images restent locales
  }
end

return {}
