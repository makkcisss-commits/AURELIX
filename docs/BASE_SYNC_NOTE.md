# Synchronisation de fermeture

La livraison finale est reconstruite sur le dernier `main` avant fusion afin d'éviter qu'une divergence historique de branche ne masque les validations actuelles. Les fichiers modifiés sont réappliqués sur l'arbre courant de `main`; aucun ancien historique divergent n'est conservé comme autorité.
