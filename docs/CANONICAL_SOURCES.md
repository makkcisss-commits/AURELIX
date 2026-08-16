# Sources canoniques V1

Une responsabilité = une source canonique. Les fichiers spécialisés peuvent expliquer une partie du système, mais ne doivent pas créer une seconde définition normative.

| Domaine | Source canonique | Rôle |
|---|---|---|
| Constitution | `constitution/SYSTEM_CONSTITUTION.md` | principes supérieurs |
| Autonomie | `constitution/AUTONOMY_POLICY.md` | limites d'autonomie |
| Sécurité | `constitution/SECURITY_POLICY.md` | règles de sécurité |
| Gouvernance | `src/aurelix_core/governor.py` | décision d'autorisation |
| Composition | `src/aurelix_core/engine_factory.py` | assemblage unique |
| Runtime | `src/aurelix_runtime/runtime.py` | exécution durable |
| Système | `src/aurelix_runtime/system.py` | façade longue durée |
| Messages | `src/aurelix_runtime/message_fabric.py` | communication structurée |
| Opportunités | `src/aurelix_core/opportunities.py` | modèle d'opportunité |
| Qualification économique | `src/aurelix_core/economic_opportunity_validation.py` | preuve avant revenu |
| Revenu | `src/aurelix_core/revenue.py` + `src/aurelix_core/durable_revenue_portfolio.py` | observation vérifiée et portefeuille persistant |
| Apprentissage économique | `src/aurelix_core/economic_feedback.py` | retour économique vérifié |
| Contrôle d'accès | `src/aurelix_core/identity.py` + politiques | identité et permissions |
| API | `src/aurelix_core/private_api.py` / `server.py` | surface contrôlée |
| Diagnostic | `src/aurelix_runtime/system_diagnostics.py` + `system_doctor.py` | état et anomalies |
| Tests | `tests/` | preuve automatisée |

## Règle de déduplication

Un document portant un suffixe historique (`V1`, `V2`, date, etc.) reste historique s'il n'est pas la source canonique. Il ne doit pas être utilisé comme seconde autorité. Les doublons de contenu exact sont des erreurs d'intégrité.
