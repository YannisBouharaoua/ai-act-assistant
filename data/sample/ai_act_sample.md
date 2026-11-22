# Extrait de démonstration — Règlement (UE) 2024/1689 (AI Act)

> Résumés non officiels, rédigés pour les tests et la démonstration.
> Ils ne remplacent pas le texte publié au Journal officiel de l'Union européenne.
> Pour charger le texte complet : `python scripts/fetch_corpus.py`.

Article 3
Définitions
Un système d'IA est un système automatisé conçu pour fonctionner à différents niveaux d'autonomie, qui peut s'adapter après son déploiement et qui déduit, à partir des entrées qu'il reçoit, la manière de générer des sorties telles que des prédictions, du contenu, des recommandations ou des décisions.
Le fournisseur est la personne ou l'organisme qui développe ou fait développer un système d'IA ou un modèle d'IA à usage général et le met sur le marché ou le met en service sous son propre nom ou sa propre marque.
Le déployeur est la personne ou l'organisme qui utilise un système d'IA sous sa propre autorité, sauf lorsque l'utilisation relève d'une activité personnelle à caractère non professionnel.

Article 5
Pratiques interdites en matière d'IA
Sont interdits les systèmes d'IA qui recourent à des techniques subliminales ou délibérément manipulatrices altérant substantiellement le comportement d'une personne et lui causant un préjudice important.
Sont interdits les systèmes qui exploitent les vulnérabilités d'une personne dues à son âge, à un handicap ou à sa situation sociale ou économique.
Est interdite la notation sociale des personnes conduisant à un traitement préjudiciable injustifié ou disproportionné.
Est interdite l'évaluation du risque qu'une personne commette une infraction pénale sur la seule base de son profilage ou de ses traits de personnalité.
Est interdite la constitution de bases de données de reconnaissance faciale par moissonnage non ciblé d'images sur internet ou de vidéosurveillance.
Est interdite l'inférence des émotions d'une personne sur le lieu de travail et dans les établissements d'enseignement, sauf pour des raisons médicales ou de sécurité.
Est interdite la catégorisation biométrique visant à déduire des caractéristiques sensibles comme l'origine, les opinions politiques, les convictions religieuses ou l'orientation sexuelle.
Est interdite, sauf exceptions strictement encadrées, l'identification biométrique à distance en temps réel dans des espaces accessibles au public à des fins répressives.

Article 6
Règles de classification des systèmes d'IA à haut risque
Un système d'IA est à haut risque lorsqu'il est un composant de sécurité d'un produit couvert par la législation d'harmonisation de l'Union listée à l'annexe I, ou constitue lui-même un tel produit, et que ce produit est soumis à une évaluation de conformité par un tiers.
Les systèmes d'IA relevant des domaines listés à l'annexe III sont également considérés comme à haut risque.
Par dérogation, un système relevant de l'annexe III n'est pas à haut risque s'il ne présente pas de risque important pour la santé, la sécurité ou les droits fondamentaux, par exemple lorsqu'il accomplit une tâche procédurale étroite ou une tâche préparatoire.
Un système relevant de l'annexe III qui effectue un profilage de personnes physiques est toujours considéré comme à haut risque.
Le fournisseur qui estime que son système relevant de l'annexe III n'est pas à haut risque documente son évaluation avant la mise sur le marché.

Article 9
Système de gestion des risques
Un système de gestion des risques est établi, mis en œuvre, documenté et tenu à jour pour les systèmes d'IA à haut risque.
Il s'agit d'un processus itératif continu, mené tout au long du cycle de vie du système, qui comprend l'identification et l'analyse des risques connus et raisonnablement prévisibles, leur évaluation et l'adoption de mesures de gestion appropriées.
Les systèmes à haut risque sont testés afin de déterminer les mesures de gestion des risques les plus appropriées.

Article 10
Données et gouvernance des données
Les systèmes d'IA à haut risque qui font appel à l'entraînement de modèles sont développés à partir de jeux de données d'entraînement, de validation et de test répondant à des critères de qualité.
Ces jeux de données sont pertinents, suffisamment représentatifs et, dans toute la mesure du possible, exempts d'erreurs et complets au regard de la finalité visée.
Les pratiques de gouvernance couvrent notamment la collecte des données, leur préparation et l'examen des biais éventuels susceptibles de porter atteinte aux droits fondamentaux.

Article 13
Transparence et fourniture d'informations aux déployeurs
Les systèmes d'IA à haut risque sont conçus de manière à ce que leur fonctionnement soit suffisamment transparent pour permettre aux déployeurs d'interpréter les sorties et de les utiliser de manière appropriée.
Ils sont accompagnés d'une notice d'utilisation qui décrit notamment les caractéristiques, les capacités, les limites de performance et les mesures de contrôle humain.

Article 14
Contrôle humain
Les systèmes d'IA à haut risque sont conçus de manière à pouvoir être effectivement supervisés par des personnes physiques pendant leur période d'utilisation.
Le contrôle humain vise à prévenir ou à réduire au minimum les risques pour la santé, la sécurité ou les droits fondamentaux.
Les personnes chargées du contrôle doivent pouvoir comprendre les capacités et les limites du système, rester conscientes du biais d'automatisation, interpréter correctement les sorties, décider de ne pas utiliser le système et interrompre son fonctionnement.

Article 26
Obligations incombant aux déployeurs de systèmes d'IA à haut risque
Les déployeurs utilisent les systèmes d'IA à haut risque conformément à la notice d'utilisation.
Ils confient le contrôle humain à des personnes physiques qui disposent des compétences, de la formation et de l'autorité nécessaires.
Ils surveillent le fonctionnement du système et informent le fournisseur en cas de risque ou d'incident grave.
Ils conservent les journaux générés automatiquement par le système pendant une période adaptée, d'au moins six mois.
Les employeurs informent les représentants des travailleurs et les travailleurs concernés avant de mettre en service un système d'IA à haut risque sur le lieu de travail.

Article 50
Obligations de transparence pour les fournisseurs et les déployeurs de certains systèmes d'IA
Les personnes physiques sont informées qu'elles interagissent avec un système d'IA, par exemple un agent conversationnel, sauf si cela ressort clairement du contexte.
Les contenus audio, image, vidéo ou texte générés par l'IA sont marqués dans un format lisible par machine et identifiables comme générés ou manipulés artificiellement.
Les déployeurs d'un système de reconnaissance des émotions ou de catégorisation biométrique informent les personnes qui y sont exposées.
Les déployeurs qui génèrent ou manipulent des contenus constituant un hypertrucage indiquent que ces contenus ont été générés ou manipulés artificiellement.

Article 99
Sanctions
Le non-respect de l'interdiction des pratiques visées à l'article 5 fait l'objet d'amendes administratives pouvant aller jusqu'à 35 000 000 EUR ou, pour une entreprise, jusqu'à 7 % de son chiffre d'affaires annuel mondial, le montant le plus élevé étant retenu.
Le non-respect des autres obligations applicables aux opérateurs fait l'objet d'amendes pouvant aller jusqu'à 15 000 000 EUR ou 3 % du chiffre d'affaires annuel mondial.
La fourniture d'informations inexactes, incomplètes ou trompeuses aux autorités fait l'objet d'amendes pouvant aller jusqu'à 7 500 000 EUR ou 1 % du chiffre d'affaires annuel mondial.
Pour les PME et les jeunes pousses, chaque amende est plafonnée au plus faible des deux montants.

ANNEXE III
Systèmes d'IA à haut risque visés à l'article 6, paragraphe 2
Biométrie : identification biométrique à distance, catégorisation biométrique et reconnaissance des émotions, lorsque leur utilisation est autorisée.
Infrastructures critiques : composants de sécurité dans la gestion du trafic routier et de la fourniture d'eau, de gaz, de chauffage et d'électricité.
Éducation et formation professionnelle : admission, évaluation des acquis et surveillance des examens.
Emploi et gestion des travailleurs : recrutement, tri des candidatures, décisions de promotion ou de licenciement, répartition des tâches et suivi des performances.
Accès aux services essentiels : évaluation de la solvabilité et notation de crédit des personnes physiques, évaluation des risques et tarification en assurance vie et santé, éligibilité aux prestations publiques, tri des appels d'urgence.
Répression, migration, asile et contrôle aux frontières, administration de la justice et processus démocratiques.
