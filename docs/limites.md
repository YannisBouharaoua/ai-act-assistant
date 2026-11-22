# Limites connues

Ce document liste ce que le projet ne fait pas ou ne garantit pas.

## Sur la justesse des réponses

- **La fidélité des phrases n'est pas vérifiée.** Le code vérifie qu'un article cité a bien
  été fourni au modèle. Il ne vérifie pas que la phrase rédigée dit la même chose que
  l'article. Un modèle peut citer le bon article et en déformer le sens.
- **La qualité des réponses rédigées n'est pas mesurée.** `make eval` mesure la recherche
  seule. Les réponses sont évaluées à part, par
  [agent-eval-bench](https://github.com/YannisBouharaoua/agent-eval-bench).
- **Le tri peut laisser passer une qualification.** Une description de système formulée comme
  une question générale est traitée comme une demande d'information, sans relecture
  obligatoire.
- **Le texte évolue.** Le corpus est une photographie du règlement à la date du
  téléchargement. Les actes délégués, les lignes directrices de la Commission et les
  modifications ultérieures du calendrier d'application n'y figurent pas.
- **L'extrait de démonstration est un résumé non officiel** de 11 articles. Il sert aux tests.

## Sur ce qui est testé

- Les 30 tests tournent avec un modèle factice ou scripté. Les classes `AnthropicLLM` et
  `AzureOpenAILLM` ne sont pas exercées par la CI.
- Le script `scripts/fetch_corpus.py` est testé sur une page HTML d'exemple, pas sur EUR-Lex
  en conditions réelles, qui filtre parfois les téléchargements automatisés.
- Les mesures de recherche portent sur 16 questions et 11 articles. Elles ne se transposent
  pas au règlement complet (113 articles, 13 annexes).
- L'index dense est testé avec un faux modèle d'embeddings.

## Sur la sécurité et les données

- **Le journal d'audit contient les questions en clair.** Une question peut contenir des
  données personnelles. Il n'y a ni masquage ni durée de conservation.
- **Une seule clé pour tous les relecteurs.** Le nom du relecteur est déclaratif. Une vraie
  mise en service demande une authentification individuelle (par exemple Microsoft Entra ID).
- **Le demandeur n'est pas authentifié** et il n'y a pas de limitation de débit.
- **La défense contre l'injection de consignes repose sur les instructions du modèle**, ce
  qui ne suffit pas seul. Aucun filtre n'analyse les entrées.
- Le journal d'audit est en ajout seul par convention, pas par construction : rien n'empêche
  de modifier le fichier.

## Sur le passage à l'échelle

- SQLite et un fichier JSONL conviennent à un seul processus. Plusieurs instances demandent
  PostgreSQL pour les points de reprise et un stockage d'audit partagé.
- Les routes sont synchrones : un appel au modèle occupe un fil d'exécution pendant toute sa
  durée.
- Il n'existe pas de liste des relectures en attente : le relecteur doit connaître
  l'identifiant de la conversation.
