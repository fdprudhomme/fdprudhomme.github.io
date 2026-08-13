--[[
  titre-courant.lua — titre courant paramétrable, pour la seule sortie LaTeX.

  Le profil PDF est partagé par tous les documents. Un titre courant écrit en
  dur dans son préambule convient au CV — « Prud'homme — 3/5 » sur un dossier
  qui se lit désagrafé — mais détonne sur un résumé de projet, où l'on attend
  le titre du document.

  Le filtre lit le champ `titre-courant` de l'en-tête YAML et se rabat sur
  « Prud'homme » en son absence, ce qui laisse les deux CV inchangés.

      titre-courant: "La coopération interprétative à l'ère de la sémiose algorithmique"

  Mise en œuvre : la commande est injectée comme premier bloc du corps, et non
  par `header-includes`. Les deux voies mènent au même préambule, mais
  `include-in-header` — que le profil emploie déjà pour la fonte et la
  pagination — écrase la métadonnée `header-includes` qu'un filtre y déposerait.
  Vérifié sous pandoc : l'un ou l'autre survit, jamais les deux.

  \ohead* posé dans le corps prend effet dès la page suivante ; la page de
  titre n'en porte pas, son style étant fixé à `empty` par le profil.

  Usage : format: pdf: filters: [outils/titre-courant.lua]
]]

local DEFAUT = "Prud'homme"
local titre = DEFAUT

function Meta(meta)
  if meta['titre-courant'] then
    titre = pandoc.utils.stringify(meta['titre-courant'])
  end
end

function Pandoc(doc)
  local tex = '\\ohead*{' .. titre .. ' — \\thepage/\\pageref{LastPage}}'
  table.insert(doc.blocks, 1, pandoc.RawBlock('latex', tex))
  return doc
end

if not FORMAT:match('latex') then
  return {}
end

return { { Meta = Meta }, { Pandoc = Pandoc } }
