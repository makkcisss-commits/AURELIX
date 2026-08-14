# AURELIX — Contrat de fermeture système V1

## But

Ce document est le contrat de référence pour considérer AURELIX comme une seule machine fonctionnelle. Les documents historiques et spécialisés décrivent des sous-domaines, mais ne créent pas de seconde architecture.

## Chaîne canonique

```text
Propriétaire
  ↓
Identité / autorisation
  ↓
Gouverneur + politiques
  ↓
Orchestrateur
  ↓
EngineFactory (composition canonique)
  ↓
Fabric de messages + Runtime durable + Scheduler
  ↓
Recherche → preuves → connaissance → académie
  ↓
Innovation → expérimentation → évaluation
  ↓
Opportunité → qualification économique
  ↓
Décision Gouverneur → approbation propriétaire si nécessaire
  ↓
Exécution bornée
  ↓
Résultat réel / revenu observé
  ↓
Attribution économique
  ↓
Apprentissage vérifié
  ↓
Contexte économique du cycle suivant
  ↺
```

## Règles de fonctionnement

1. Il n'existe qu'une composition canonique de production : `EngineFactory`.
2. `AurelixSystem` est une façade, pas une seconde composition.
3. `AutonomyFabric`, `EnterpriseLoop`, `SystemOrchestrator` et les agents partagent les mêmes moteurs et le même état durable lorsqu'ils appartiennent à la composition canonique.
4. Le Runtime ne confond jamais une recommandation avec une autorisation.
5. Une opportunité ne devient qualifiée qu'avec des preuves suffisantes pour la demande, la monétisation et la réalité de la source.
6. Une estimation de revenu n'est jamais un revenu réalisé.
7. Seul un résultat financier observé peut alimenter l'apprentissage économique vérifié.
8. Aucun agent ne peut modifier seul les politiques, les permissions, la gouvernance ou les contrôles de sécurité.
9. Toute action protégée est auditable et idempotente lorsque c'est possible.
10. Le système doit pouvoir continuer lorsqu'aucun nouveau travail utilisateur n'arrive : le planificateur lance les travaux autonomes autorisés, bornés et mesurables.

## Objectif économique

Le système ne cherche pas simplement des idées. Pour chaque opportunité candidate, il doit pouvoir répondre :

- Quel problème réel est observé ?
- Quelle preuve confirme la demande ?
- Qui est le prospect, partenaire ou utilisateur identifiable ?
- Comment l'offre crée-t-elle de la valeur ?
- Comment l'argent pourrait-il être encaissé ?
- Quel coût, délai, risque et effort sont nécessaires ?
- Quelle autorisation est nécessaire ?
- Quel test minimal permet de vérifier l'hypothèse ?
- Quel résultat réel a été obtenu ?
- Le résultat confirme-t-il ou invalide-t-il l'hypothèse ?

## Tests de fermeture

La fermeture V1 exige au minimum :

- composition unique ;
- absence de doublons exacts de fichiers ;
- routage Gouverneur → Runtime ;
- refus des soumissions protégées non autorisées ;
- récupération après redémarrage ;
- idempotence des messages et travaux ;
- provenance des preuves ;
- qualification économique ;
- séparation estimation / revenu réalisé ;
- transmission du feedback économique au cycle suivant ;
- smoke de recherche réelle lorsque les secrets sont disponibles ;
- tests API et contrôle d'accès ;
- validation du conteneur et de la configuration de production.

## Doublons

Les doublons exacts de contenu sont interdits. Le contrôle d'intégrité les détecte par empreinte SHA-256. Une suppression automatique n'est autorisée que lorsqu'un manifeste canonique identifie sans ambiguïté le fichier à conserver ; sinon le contrôle échoue et demande une décision humaine. Cela évite de supprimer par erreur deux documents qui ont des noms proches mais des responsabilités différentes.

## Limite importante

Le squelette peut être fermé sans prétendre avoir déjà généré de l'argent. Les vrais revenus nécessitent des intégrations externes réelles, des prospects/clients réels, des moyens de paiement, des contrats et des observations financières authentiques. AURELIX doit démontrer ces résultats au lieu de les fabriquer.
