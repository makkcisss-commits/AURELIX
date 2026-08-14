# Fermeture fonctionnelle du système AURELIX V1

## But

AURELIX doit fonctionner comme une seule machine : une composition canonique, un runtime durable, un Gouverneur, des rôles spécialisés, une boucle économique et un diagnostic transversal.

## Chaîne canonique

1. Observation et recherche.
2. Preuves traçables et vérification des sources.
3. Qualification de l'opportunité.
4. Analyse business : demande, client, offre, coût, risque, marge potentielle.
5. Décision du Gouverneur et contrôle des permissions.
6. Exécution uniquement via les frontières autorisées.
7. Observation du résultat réel.
8. Attribution économique et mesure du revenu réellement réalisé.
9. Apprentissage uniquement à partir des résultats vérifiés.
10. Réutilisation de cet apprentissage dans le cycle suivant.

## Règles de vérité

- Une estimation de revenu n'est jamais un revenu réalisé.
- Une opportunité de développement n'est jamais présentée comme une opportunité de marché réelle.
- Le mode développement utilise des données synthétiques et doit être diagnostiqué comme tel.
- Une opportunité économique ne peut entrer dans le pipeline de revenu sans qualification fondée sur des preuves.
- Un résultat financier vérifié doit avoir une source, une décision du Gouverneur et une référence externe ou une preuve équivalente.

## Règle de composition

`EngineFactory` est la racine de composition. Les chemins système et autonomie doivent réutiliser les mêmes moteurs, le même `EngineStore`, le même `MessageFabric` et le même runtime. Une seconde composition fonctionnelle du même rôle constitue un défaut d'intégrité.

## Déduplication

Une responsabilité doit avoir une implémentation canonique et une documentation canonique.

- doublon certain : suppression ou remplacement par la source canonique ;
- doublon ambigu : diagnostic bloquant, aucune suppression automatique ;
- document historique : explicitement marqué historique et jamais utilisé comme autorité normative ;
- workflows concurrents pour la même responsabilité : diagnostic de conflit.

## Diagnostic de fermeture

Le diagnostic doit vérifier au minimum :

- runtime durable accessible ;
- composition canonique partagée ;
- cohérence du retour économique ;
- disponibilité d'une recherche réelle en production ;
- fournisseurs configurés et sains ;
- dépôt de connaissance accessible ;
- chaîne des rôles spécialisée complète ;
- contrôle développeur présent ;
- absence de revenu déclaré vérifié sans revenu observé.

## Tests de fermeture

Une fermeture V1 n'est acceptable que lorsque les tests unitaires, les tests d'intégration, la régression système, le smoke test empaqueté et les contrôles de sécurité passent ensemble.

Un système qui ne possède qu'un fournisseur de développement peut être fonctionnel pour le développement, mais il n'est pas encore capable de détecter de vraies opportunités économiques. Cette différence doit rester visible dans le diagnostic.

## Références externes

La conception suit les principes modernes de sécurité agentique : limitation des permissions et de l'autonomie, séparation des outils, vérification des sorties, évaluation intégrée et contrôle des interactions entre agents. Voir NIST CAISI et OWASP Agentic Security Initiative.
