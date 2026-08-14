# Audit d'intégration système V2

## Constat
La composition racine doit rester unique : Governor → Orchestrator → Runtime → agents. Les agents doivent partager le Message Fabric de la composition racine.

## Règles
- Une seule frontière Governor pour soumettre du travail.
- L'Orchestrator est le point de sélection des capacités.
- Le Runtime est le mécanisme durable d'exécution, pas un décideur.
- Le pipeline autonome réutilise le Message Fabric racine.
- Une capacité autonome doit être enregistrée auprès de l'Orchestrator avant d'être soumise.
- Les résultats Business restent non approuvés par défaut.

## Vérifications
Les tests d'intégration vérifient la composition racine, le passage Governor → Orchestrator → Runtime et l'identité du Message Fabric partagé par le pipeline autonome.