# 3. Recherche lexicale par défaut, index dense en option

**Statut** : accepté

## Contexte

Le corpus est un seul règlement : 113 articles et 13 annexes, soit quelques centaines
d'extraits. Le vocabulaire juridique est précis et les questions reprennent souvent les
termes du texte (« déployeur », « notation sociale », « hypertrucage »).

## Options étudiées

| Option | Pour | Contre |
|---|---|---|
| Base vectorielle (Qdrant, pgvector, Azure AI Search) | Recherche sémantique, passe à l'échelle | Un service de plus à déployer et à sécuriser pour quelques centaines d'extraits |
| BM25 en mémoire | Aucune infrastructure, démarrage instantané, résultats explicables | Échoue quand la question n'emploie pas les mots du texte |
| BM25 et embeddings en mémoire, fusionnés | Couvre les deux cas | Téléchargement d'un modèle d'embeddings |

## Décision

BM25 par défaut. Un index dense s'active avec `DENSE_MODEL` et les deux classements sont
fusionnés par Reciprocal Rank Fusion.

## Conséquences

- Le projet se lance sans rien installer d'autre, y compris en CI.
- La recherche est mesurée (`make eval`) : le choix pourra être révisé sur des chiffres.
- À partir de plusieurs textes (RGPD, lignes directrices, documents internes), une base
  vectorielle avec filtrage par source deviendra nécessaire. L'interface `Retriever.search`
  est le seul point à remplacer.
