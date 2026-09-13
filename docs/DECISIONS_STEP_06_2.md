# Décisions — STEP 06.2

## ADR-045 — Templates contrôlés, pas de HTML libre

L'établissement choisit parmi des mises en page connues :

```text
CLASSIC
MODERN
COMPACT
SECONDARY_LANDSCAPE
```

et configure les options autorisées.

Aucun HTML/CSS arbitraire n'est exécuté.

## ADR-046 — Modèles par cycle

Un établissement peut définir un modèle général et des exceptions par cycle.

Cela évite de forcer un primaire et un secondaire à utiliser la même densité
de bulletin.

## ADR-047 — Le template est copié dans le snapshot

Un snapshot ne dépend jamais du modèle mutable en base pour reconstruire son
apparence.

## ADR-048 — Un bulletin officiel doit tenir sur une seule feuille A4

Le moteur peut compacter automatiquement le rendu.

S'il n'arrive toujours pas à produire une seule page, la publication est
refusée plutôt que de créer un document officiel cassé.

## ADR-049 — Prévisualiser ne publie rien

L'aperçu A4 est temporaire et marqué explicitement comme non officiel.
