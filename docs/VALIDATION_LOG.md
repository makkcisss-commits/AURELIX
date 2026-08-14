# Journal de validation AURELIX

## Baseline validée — 2026-08-14

### Référence
- Branche : `feat/full-system-smoke-v2`
- Commit de référence : `20d45bf97c9f15a2274aa2411c399318f2044855`
- Contrat opérationnel : `docs/OPERATING_MODEL.md`

### Validations
- AURELIX System Regression #142 : **succès**
- AURELIX CI #797 : **succès**

### Chaîne actuellement couverte
`recherche → preuves → qualification → gouvernance → capacités → exécution → résultat → revenu observé → apprentissage`

### Invariants
- Une capacité inconnue ne doit pas être exécutée comme si elle était maîtrisée.
- Une capacité candidate apprise ne crée pas automatiquement une permission.
- Une opportunité estimée ne constitue pas un revenu réel.
- Une action sensible doit être autorisée et traçable.
- Une erreur critique doit pouvoir bloquer, diagnostiquer et déclencher la récupération.
- Les doublons certains doivent converger vers une responsabilité canonique.
- Les simulations doivent rester identifiées comme simulations.

### Surveillance permanente à construire/valider
La surveillance doit couvrir fonctionnalité, opérations, facteurs humains, sécurité, conformité et impacts, conformément aux catégories identifiées par NIST AI 800-4. Les métriques de production doivent être comparées aux références de test et les dérives doivent alimenter le cycle de correction et d'amélioration.

### Règle de progression
Chaque nouvelle correction doit :
1. identifier la cause ;
2. corriger le contrat ou le composant canonique ;
3. ajouter ou renforcer un test ;
4. exécuter les validations pertinentes ;
5. documenter le résultat ;
6. conserver le dernier état vert comme référence.

### Sources externes
- NIST AI 800-4 — surveillance post-déploiement : https://www.nist.gov/news-events/news/2026/03/new-report-challenges-monitoring-deployed-ai-systems
- NIST AI RMF — Measure : https://airc.nist.gov/airmf-resources/playbook/measure/
- NIST AI RMF — Manage : https://airc.nist.gov/airmf-resources/playbook/manage/
