# Modèle opérationnel AURELIX

## 1. Boucle unique

AURELIX doit fonctionner comme une seule boucle coordonnée :

`observer → rechercher → prouver → qualifier → gouverner → vérifier les capacités → exécuter → observer le résultat → mesurer → apprendre → retester → reprendre`

Une académie, un agent ou un workflow peut produire une proposition, une preuve ou une capacité candidate, mais ne crée pas à lui seul une autorisation d'exécution.

## 2. États du système

- **fonctionnel** : les invariants et contrôles passent ;
- **dégradé** : le service fonctionne mais une métrique sort de sa plage normale ;
- **bloqué** : une condition critique n'est plus satisfaite ;
- **récupération** : diagnostic, correction et retest sont en cours.

Le système doit préférer le blocage explicite à une réussite fictive lorsqu'une condition critique ne peut pas être vérifiée.

## 3. Surveillance permanente

Le diagnostic transversal doit couvrir au minimum : fonctionnalité, runtime, erreurs, preuves, sécurité, cohérence inter-agents, décisions, dérive, doublons, dépendances, résultats économiques et lacunes d'apprentissage.

Une anomalie critique doit pouvoir empêcher l'action concernée, produire un diagnostic traçable et déclencher le chemin de récupération/apprentissage.

## 4. Capacités

`capacité inconnue → blocage → lacune dédupliquée → objectif d'étude → apprentissage → évaluation → validation → disponibilité opérationnelle`

L'apprentissage ne doit jamais créer implicitement une permission.

## 5. Vérité économique

Une opportunité candidate n'est pas un revenu. Une estimation reste une estimation ; un résultat d'exécution reste un résultat ; seul un paiement ou revenu observé avec une source identifiable est un revenu observé.

## 6. Déduplication

Chaque responsabilité doit avoir une implémentation canonique. Les doublons certains peuvent être supprimés automatiquement. Les conflits ambigus doivent être signalés et bloqués.

## 7. Contrôle des actions

Chaque action sensible doit être reconstruisible à partir de : `demande → décision → politique → autorisation → admission → exécution → résultat → preuve`.

## 8. Récupération

`détection → classification → isolement → diagnostic → correction → retest complet → nouvelle référence`

## 9. Documentation vivante

Chaque changement important documente le problème, la cause, la correction, les tests, le résultat, l'impact et les limites restantes.
