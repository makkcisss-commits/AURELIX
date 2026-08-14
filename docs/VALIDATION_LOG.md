# Journal de validation AURELIX

## Référence validée

- Commit : `229348a0db3f79f27f48b2ad917094693ce889f7`
- AURELIX CI #799 : **succès**
- AURELIX System Regression #143 : **succès**

## Contrat opérationnel

La machine suit une boucle unique :

`observer → rechercher → prouver → qualifier → gouverner → vérifier les capacités → exécuter → observer le résultat → mesurer → apprendre → retester → reprendre`

Une proposition, une preuve ou une capacité candidate ne donne jamais implicitement une permission d'exécution.

## Règles de vérité

- Une estimation reste une estimation.
- Un résultat d'exécution reste un résultat.
- Un revenu n'est comptabilisé comme réel qu'avec une observation et une provenance identifiables.
- Les simulations sont explicitement marquées comme telles.
- Une information insuffisamment prouvée ne devient pas une vérité simplement parce qu'un agent l'affirme.

## Règles de sécurité

- Action sensible : décision → politique → autorisation → admission → exécution → résultat → preuve.
- Condition critique non vérifiable : blocage ou escalade.
- Capacité inconnue : blocage → lacune dédupliquée → apprentissage → évaluation → validation.
- L'apprentissage ne crée jamais automatiquement une permission.
- Les doublons exacts doivent être éliminés de manière déterministe et idempotente ; les conflits ambigus doivent être signalés.

## Surveillance permanente

Les prochaines validations doivent continuer à couvrir au minimum :

- fonctionnalité ;
- infrastructure et runtime ;
- qualité des résultats ;
- sécurité et permissions ;
- cohérence inter-agents ;
- provenance et qualité des preuves ;
- dérive ;
- dépendances externes ;
- résultats économiques réels ;
- lacunes d'apprentissage.

Une dégradation doit produire un diagnostic traçable et conduire à une correction puis à un retest complet avant réactivation.

## Référence externe

NIST AI 800-4 recommande le monitoring post-déploiement pour vérifier le fonctionnement réel, détecter les comportements inattendus et réinjecter les observations dans l'amélioration du système. Le rapport distingue notamment surveillance fonctionnelle, opérationnelle, facteurs humains, sécurité, conformité et impacts à grande échelle.

## État

Cette référence est **verte**. Toute modification ultérieure doit préserver les invariants ci-dessus et ajouter une validation adaptée au risque introduit.
