# System Integration Audit V1 — clôture globale

## Résultat

L'audit porte sur AURELIX comme une seule machine : composition, orchestration, runtime, scheduler, Gouverneur, autonomie, intelligence, économie, apprentissage, provenance, récupération et contrôle d'accès.

## Constats corrigés dans la branche de travail

### Autorisation d'exécution

`AurelixSystem.submit()` passe maintenant par le Gouverneur avant d'appeler le Runtime. Les soumissions à risque élevé sont bloquées avant leur mise en file. Le Runtime reste le moteur d'exécution durable et ne constitue pas une autorité concurrente.

### Composition unique

`EngineFactory` est la composition canonique. `AutonomyFabric`, `EnterpriseLoop` et `SystemOrchestrator` partagent les mêmes moteurs et le même état durable dans cette composition. `AurelixSystem` agit comme façade longue durée.

### Boucle économique

La boucle distingue : opportunité détectée, opportunité qualifiée et revenu réalisé. La qualification exige des preuves pour la demande, le chemin de monétisation et la réalité de la source. Un revenu réalisé n'est reconnu qu'après observation authentique.

Le résultat économique vérifié alimente ensuite le contexte du cycle suivant. En l'absence d'observation positive, le système ne déclare pas de revenu vérifié.

### Diagnostic et intégrité

Le diagnostic système vérifie la composition, le runtime, le stockage, l'EnterpriseLoop et le contrôle développeur. Un contrôle d'intégrité de dépôt détecte les doublons exacts de fichiers et est maintenant une étape de CI.

### Ancienne RuntimeService

`src/aurelix_runtime/service.py` reste une compatibilité historique testée. Elle ne constitue pas la composition canonique utilisée par `EngineFactory`. Sa présence est explicitement documentée comme héritée afin d'éviter de la confondre avec le runtime principal.

## Contrat de fermeture

La fermeture V1 est atteinte lorsque :

- la composition est unique ;
- les chemins d'exécution passent par le Gouverneur ;
- les travaux sont durables, bornés et récupérables ;
- les messages et transitions sont audités ;
- les preuves et la provenance sont conservées ;
- les opportunités économiques sont qualifiées avant admission au revenu ;
- estimation et revenu réel restent séparés ;
- le feedback économique revient au cycle suivant ;
- les doublons exacts sont refusés par CI ;
- les tests Python, PostgreSQL, conteneur, contrôle d'accès, production et Web passent ;
- les intégrations réelles restent explicitement distinguées des simulations.

## Limites restantes hors code

La protection de la branche `main`, la visibilité privée du dépôt, les secrets réels, les fournisseurs de recherche/modèle, les paiements, les contrats commerciaux, l'identité de production, l'observabilité externe et les données financières réelles doivent être configurés dans l'environnement de déploiement. Ils ne doivent pas être simulés dans le code pour déclarer le système rentable.
