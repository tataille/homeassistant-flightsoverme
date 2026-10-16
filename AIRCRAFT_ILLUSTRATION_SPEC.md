# Spécification de la bibliothèque PNG d’avions

## Rendu

- Un PNG transparent dérivé d’un vrai modèle 3D et associé à un code type ICAO exact.
- Vue de profil, nez orienté vers la droite dans le fichier source ; la carte conserve cette orientation. Le cap réel est indiqué séparément par la boussole.
- Aucun logo ni couleur de compagnie dans le PNG. Le logo détecté est rendu indépendamment dans un cartouche au coin inférieur droit du visuel, au-dessus de la séparation avec les détails.
- La carte utilise le PNG exact lorsqu’un modèle ICAO est disponible. Si un appareil est signalé militaire mais n’a pas de rendu dédié, elle affiche une silhouette neutre d’avion militaire, sans prétendre identifier sa forme exacte ni afficher de logo de compagnie. Pour une cible dont le type reste inconnu et qui n’est pas classée militaire, elle conserve l’OVNI comme pictogramme clairement étiqueté « type inconnu ».
- La cellule est blanche, avec des contours graphite et des hachures légères façon croquis. Les volumes et le contour restent issus du modèle 3D ; le traitement ne reconstruit pas l’avion.

## Source et licence

Les images sont rendues par `tools/render_aircraft_3d_profiles.py` depuis les modèles exacts du dépôt [Flightradar24/fr24-3d-models](https://github.com/Flightradar24/fr24-3d-models). Le README de ce dépôt crédite FlightGear et FGMEMBERS et indique la licence GPLv2 pour les modèles d’avion. Les détails de chaque PNG, sa source et sa licence sont listés dans `www/aircraft-png/catalog.json`; les crédits et le texte de licence sont dans `www/aircraft-png/ATTRIBUTION.txt` et `www/aircraft-png/LICENSE-GPL-2.0.txt`. Le script nécessite un dossier local de modèles GLB v2 ainsi que `numpy<2`, `trimesh`, `pyrender`, `Pillow` et `PyOpenGL`; ces dépendances ne sont pas utilisées par l’intégration Home Assistant.

## Codes ICAO couverts par les PNG fournis

`A318`, `A319`, `A320`, `A321`, `A332`, `A333`, `A343`, `A346`, `A359`, `A388`, `AT45`, `B736`, `B737`, `B738`, `B739`, `B744`, `B748`, `B752`, `B753`, `B762`, `B763`, `B764`, `B772`, `B773`, `B788`, `B789`, `BCS1`, `BCS3`, `CRJ7`, `CRJ9`, `DH8D`, `E170`, `E190`.

La liste est volontairement limitée aux types pour lesquels une géométrie exacte est disponible dans la source. Ajouter un autre code uniquement après avoir acquis et vérifié un modèle source dédié ; ne pas réutiliser le PNG d’une famille par simple préfixe.
