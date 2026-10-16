# Contribuer

## Commits

Utilisez les messages [Conventional Commits](https://www.conventionalcommits.org/) :

- `feat:` pour une fonctionnalité (version mineure) ;
- `fix:` pour une correction (version corrective) ;
- `feat!:` ou un pied de commit `BREAKING CHANGE:` pour une rupture (version majeure) ;
- `docs:`, `test:`, `ci:`, `refactor:` et `chore:` pour les autres changements.

## Pull requests

La validation automatique vérifie les fichiers Python, JavaScript, JSON, le catalogue des avions et les fichiers PNG. Toute pull request vers `main` doit passer ces contrôles.

## Releases et versions

La version de référence est `custom_components/flights_over_me/manifest.json`. Release Please prépare automatiquement une pull request de release à partir des commits Conventional Commits fusionnés dans `main`; cette pull request met à jour le manifeste et le changelog. La fusion de la pull request crée le tag SemVer `vX.Y.Z` et la release GitHub. Le workflow joint alors l'archive Home Assistant à cette release.

Le manifeste `.release-please-manifest.json` utilise `2.7.0` comme point de départ uniquement pour que l'import initial (`feat:`) prépare la première release `2.8.0`, version du plugin importé. Après cette release, les deux manifestes sont synchronisés automatiquement. Ne modifiez pas manuellement la version dans le manifeste Home Assistant pour une release normale.
