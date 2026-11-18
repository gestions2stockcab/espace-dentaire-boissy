# Espace dentaire Boissy — site et avis Google

Site statique de l’Espace dentaire Boissy (Boissy-Saint-Léger).

## Avis Google (`.github/workflows/avis.yml`, toutes les 3 heures)
- `avis.py` lit les avis de la fiche Google, écrit `avis-boissy.json` (affiché sur l’accueil) et ouvre un ticket GitHub à chaque nouvel avis (avec une proposition de réponse pour les avis à 3 étoiles ou moins).
- `reponses.py` répond automatiquement aux avis à 4-5 étoiles sans réponse : messages courts et variés, sans détail de soin ni de praticien, jamais sous 4 étoiles, réponses existantes jamais modifiées.
  Activé le 18/11/2026 par le Dr Atlan (mêmes règles que Savigny et Malakoff : 4-5 étoiles uniquement, aucune donnée médicale).

Secrets à créer dans le dépôt : `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (compte Google qui gère la fiche).
