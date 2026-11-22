# 4. Une interface LLM unique et un modèle factice pour les tests

**Statut** : accepté

## Contexte

Le choix du fournisseur de modèle dépend de l'organisation (contrat cloud, localisation des
données). Les tests, eux, doivent tourner sans clé, sans réseau et donner toujours le même
résultat.

## Décision

Le graphe ne dépend que de `LLM.complete(task, system, user)`. Trois implémentations :

- `AnthropicLLM` et `AzureOpenAILLM` pour l'usage réel ;
- `FakeLLM`, déterministe, pour la démonstration hors ligne ;
- `ScriptedLLM`, dans les tests, qui renvoie des sorties écrites à l'avance. Il permet de
  simuler une citation inventée ou une sortie JSON illisible.

Le paramètre `task` nomme l'étape appelante. Il est écrit dans le journal d'audit avec la
durée de l'appel.

## Conséquences

- Les 30 tests tournent hors ligne en moins de 2 secondes.
- Les branches d'erreur (citation inventée, JSON illisible) sont testées, ce qui serait
  impossible à provoquer de façon fiable avec un vrai modèle.
- Les deux implémentations réelles ne sont pas couvertes par la CI. Elles sont volontairement
  courtes pour limiter ce risque.
- Les sorties structurées reposent sur du JSON demandé dans les instructions, et non sur les
  fonctions natives de chaque fournisseur. C'est portable mais moins strict : une sortie
  illisible est gérée par un repli prudent.
