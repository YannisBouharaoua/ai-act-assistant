# 1. Un graphe LangGraph avec interruption pour la relecture humaine

**Statut** : accepté

## Contexte

Une qualification de système (« haut risque », « interdit ») ne doit jamais partir sans
validation humaine. Le relecteur peut répondre des heures plus tard. Il faut donc suspendre
un traitement, garder son état, et le reprendre.

## Options étudiées

| Option | Pour | Contre |
|---|---|---|
| Fonctions Python enchaînées et table « à relire » en base | Aucune dépendance | Il faut écrire soi-même la sauvegarde et la reprise de l'état. Chaque nouvelle branche complique le code |
| LangGraph avec `interrupt()` et point de reprise | Suspension et reprise fournies. Le graphe est lisible et chaque nœud se teste seul | Dépendance supplémentaire. Le nœud interrompu est rejoué à la reprise |
| Moteur de workflow (Temporal) | Reprise robuste, relances, délais | Infrastructure lourde pour un seul processus |

## Décision

LangGraph, avec `SqliteSaver` comme point de reprise.

## Conséquences

- La relecture survit à un redémarrage (voir `tests/test_persistence.py`).
- Un nœud interrompu est rejoué depuis son début à la reprise. Aucun effet de bord ne doit
  précéder `interrupt()`. L'événement `review_requested` est donc écrit par la couche
  service.
- Passer à plusieurs instances demandera de remplacer `SqliteSaver` par `PostgresSaver`, sans
  toucher au graphe.
