# 2. Vérifier les citations par du code, pas par un second modèle

**Statut** : accepté

## Contexte

Un modèle peut citer un article qu'on ne lui a pas fourni, de mémoire ou par invention. Dans
un outil de conformité, une référence fausse est l'erreur la plus coûteuse.

## Options étudiées

| Option | Pour | Contre |
|---|---|---|
| Faire confiance aux instructions | Rien à écrire | Aucune garantie |
| Un second appel au modèle qui juge la réponse | Peut juger aussi la fidélité du sens | Coût et latence doublés, résultat non déterministe, difficile à tester |
| Extraction des références par expression régulière et comparaison aux extraits fournis | Déterministe, instantané, gratuit, testable | Ne vérifie que l'existence de la référence, pas le sens |

## Décision

Vérification par le code. Le modèle doit citer sous la forme `[Article N]` ou `[Annexe N]`.
Une référence absente des extraits, ou l'absence de toute citation, déclenche une nouvelle
rédaction avec la correction à faire, puis une relecture humaine au deuxième échec.

## Conséquences

- Aucune réponse automatique ne peut citer un article qui n'a pas été lu.
- La fidélité du sens reste non vérifiée (voir `docs/limites.md`). Un juge par modèle pourra
  être ajouté comme étape supplémentaire, sans remplacer celle-ci.
- Le format de citation est imposé. Une citation écrite autrement (« l'article 5 ») n'est pas
  comptée, ce qui pousse la réponse en nouvelle rédaction : l'erreur va dans le sens prudent.
