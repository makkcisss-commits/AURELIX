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

Le diagnostic transversal doit couvrir au minimum :

- fonctionnalité et disponibilité ;
- runtime, files et tâches ;
- erreurs, retries et délais ;
- qualité, fraîcheur et provenance des preuves ;
- sécurité, identité et permissions ;
- cohérence inter-agents et communications ;
- qualité des décisions et résultats ;
- dérive des performances ;
- doublons et responsabilités canoniques ;
- dépendances externes ;
- résultats économiques réels ;
- lacunes d'apprentissage.

Une anomalie critique doit pouvoir empêcher l'action concernée, produire un diagnostic traçable et déclencher le chemin de récupération/apprentissage.

## 4. Capacités

`capacité inconnue → blocage → lacune dédupliquée → objectif d'étude → apprentissage → évaluation → validation → disponibilité opérationnelle`

L'apprentissage ne doit jamais créer implicitement une permission.

## 5. Vérité économique

Une opportunité candidate n'est pas un revenu.

- estimation = estimation ;
- résultat d'exécution = résultat ;
- paiement ou revenu observé avec une source identifiable = revenu observé.

Les données synthétiques doivent rester explicitement marquées comme simulation et ne peuvent pas alimenter un indicateur présenté comme revenu réel.

Les métriques économiques à suivre sont notamment :

`opportunités détectées → opportunités qualifiées → actions autorisées → actions exécutées → résultats → revenus observés → marge → apprentissage`

## 6. Déduplication

Chaque responsabilité doit avoir une implémentation canonique. Les doublons exacts peuvent être supprimés automatiquement. Les conflits ambigus doivent être signalés et bloqués plutôt que supprimés arbitrairement.

La déduplication doit être déterministe, idempotente et testée.

## 7. Contrôle des actions

Chaque action sensible doit être reconstruisible à partir de :

`demande → décision → politique → autorisation → admission → exécution → résultat → preuve`

L'absence d'autorisation ou de preuve critique entraîne un refus ou une escalade.

## 8. Récupération

`détection → classification → isolement → diagnostic → correction → retest complet → nouvelle référence`

Une correction ne doit pas être considérée comme réussie avant le passage des tests applicatifs, système, sécurité et intégration pertinents.

## 9. Documentation vivante

Chaque changement important doit laisser une trace dans le dépôt :

- contrat concerné ;
- problème observé ;
- cause ;
- correction ;
- test ajouté ou exécuté ;
- résultat de validation ;
- impact sur les autres composants ;
- limites restantes.

Ce document est le contrat opérationnel de référence. Il doit évoluer avec le système, sans créer une seconde architecture concurrente.

## 10. Références externes

Cette organisation s'aligne sur les principes de surveillance post-déploiement décrits par NIST AI 800-4 : surveillance fonctionnelle, opérationnelle, facteurs humains, sécurité, conformité et impacts, avec détection de dérive et amélioration continue.

Elle prend également en compte les principes d'observabilité agentique d'OWASP : agents instrumentables, traçables et inspectables, ainsi que la vérification continue de la sécurité pendant tout le cycle de vie.
