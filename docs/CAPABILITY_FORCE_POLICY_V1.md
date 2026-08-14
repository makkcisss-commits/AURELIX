# Politique de force de capacité V1

## Règle

AURELIX ne doit jamais transformer une capacité inconnue en succès fictif.

Lorsqu'un agent rencontre une capacité qu'il ne sait pas exécuter de façon validée :

1. l'action est bloquée ou reste en état d'attente selon son risque ;
2. le manque est enregistré comme **lacune de capacité** ;
3. la lacune est envoyée à l'Académie via `CapabilityEscalator` ;
4. l'Académie crée un objectif d'étude dans `ContinuousIntelligence` ;
5. les preuves, expériences et évaluations alimentent l'apprentissage ;
6. seule une capacité ensuite validée peut revenir vers le flux d'opportunités ;
7. aucune étape d'apprentissage n'autorise directement une exécution.

## Déduplication

Deux demandes identiques (même capacité et même raison normalisées) produisent une seule lacune et un seul objectif d'étude.

## Principe de vérité

Une capacité non validée n'est pas une capacité disponible.
Une connaissance candidate n'est pas une connaissance opérationnelle.
Une opportunité candidate n'est pas une opportunité validée.
Une estimation de revenu n'est pas un revenu observé.

Cette politique transforme l'ignorance en travail d'apprentissage traçable au lieu de la transformer en hallucination ou en action non autorisée.
