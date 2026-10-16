# Avion au-dessus du domicile — Home Assistant

[![Validation](https://github.com/tataille/homeassistant-flightsoverme/actions/workflows/validate.yml/badge.svg)](https://github.com/tataille/homeassistant-flightsoverme/actions/workflows/validate.yml) [![Dernière version](https://img.shields.io/github/v/release/tataille/homeassistant-flightsoverme)](https://github.com/tataille/homeassistant-flightsoverme/releases)

Intégration personnalisée et carte Lovelace inspirée de la référence fournie. À l'installation, choisissez le visuel maison (avion de profil et fond météo) ou le radar (mire circulaire orientée nord, domicile au centre et contacts positionnés selon leur direction et distance). Le rayon choisi détermine aussi l'échelle de la mire. La carte affiche les informations du vol sélectionné : destination et origine si elles sont reconnues, indicatif, compagnie et logo si identifiés, constructeur/type, altitude, vitesse sol, distance, cap et nombre d'appareils détectés. Jusqu'à trois autres vols proches apparaissent dans une liste sélectionnable sous la carte ; toucher une ligne ou un point radar affiche cet appareil en vedette. La sélection reste active tant que le vol est détecté, puis revient automatiquement à l'avion le plus proche. Les avions sont des rendus issus de modèles 3D réels, en PNG blanc avec un traitement croquis au trait, en vue de profil et le nez à droite. En mode maison, le logo de la compagnie est ajouté séparément au bas à droite du visuel ; aucune livrée n'est dessinée sur la cellule. Le cap reste indiqué par la boussole, sans faire pivoter la vue de profil.

## Source et limites des données

Les positions proviennent de l'API ouverte [ADSB.lol](https://api.adsb.lol/docs), interrogée toutes les 60 secondes. L'intégration consulte également, toutes les 10 minutes, la liste ADSB.lol des appareils militaires pour qualifier les contacts proches correspondants. Pour les quatre appareils les plus proches, elle complète les informations de type et de compagnie via l'API publique [ADSBDB](https://github.com/mrjackwills/adsbdb), et recherche l'itinéraire avec le point de route `/api/0/routeset` d'ADSB.lol, en mettant les résultats en cache 30 minutes. Les métadonnées déjà trouvées restent disponibles tant que l'appareil est détecté. La bibliothèque comprend 33 rendus PNG provenant des modèles 3D associés aux codes ICAO listés dans `www/aircraft-png/catalog.json`. Les modèles viennent du dépôt [Flightradar24/fr24-3d-models](https://github.com/Flightradar24/fr24-3d-models), qui crédite FlightGear et FGMEMBERS et indique la licence GPL-2.0 pour ces avions. Les couleurs originales sont supprimées ; la cellule est rendue blanche, puis les contours et hachures sont renforcés pour donner un aspect croquis au crayon. La géométrie reste issue du modèle 3D. Les PNG sont transparents pour laisser apparaître le fond météo de la carte. Si un appareil identifié militaire n'a pas de rendu exact, la carte présente une silhouette neutre d'avion et masque le logo commercial. Pour les autres contacts sans illustration ICAO, l'OVNI reste un pictogramme de remplacement explicitement étiqueté « type inconnu » ; il ne prétend pas représenter le modèle réel. La classification militaire dépend de la base ADSB.lol et peut ne pas couvrir tous les appareils. Voir `www/aircraft-png/ATTRIBUTION.txt` et `www/aircraft-png/LICENSE-GPL-2.0.txt` pour les crédits et la licence. La destination est une estimation basée sur l'indicatif et peut manquer ou être erronée, notamment pour les vols privés, charters, repositionnements ou non réguliers. Le logo, quand un code IATA est disponible, est chargé depuis le service d'images Kiwi.com. Ces compléments sont facultatifs : leur indisponibilité ne bloque pas les données ADS-B et la carte affiche « Destination inconnue » si aucune route n'est trouvée.

Le fond météo utilise l'état courant d'une entité `weather` de Home Assistant, par défaut `weather.forecast_maison`. Le thème passe automatiquement du jour à la nuit selon l'état de `sun.sun` (lever et coucher du soleil) ; si cette entité manque, la carte se rabat sur l'heure locale (nuit avant 7 h et à partir de 20 h). Le mode radar adapte aussi sa palette à la période, tout en gardant les contacts visibles. Pluie, neige, brouillard, nuages, orage, vent, nuit et éclaircies modifient le ciel illustré. La température et la condition courante sont affichées sur la carte. La météo se met à jour automatiquement au rythme de mise à jour de l'entité Home Assistant. Pour utiliser une autre entité, précisez `weather_entity` dans le YAML de la carte.

La position du domicile est lue depuis **Paramètres → Système → Général** de Home Assistant. Elle est transmise à ADSB.lol dans la requête de proximité; aucun compte ni clé API n'est demandé.

Le service fournit des positions ADS-B reçues par son réseau. La couverture n'est pas garantie partout et les appareils sans transpondeur ADS-B actif ne seront pas visibles. Les champs d'altitude, de vitesse, de type, d'indicatif et de compagnie peuvent manquer. L'affichage du logo dépend de la disponibilité d'un code IATA correspondant.

## Installation manuelle

1. Avec HACS, installez le dépôt comme intégration. En installation manuelle, copiez uniquement `custom_components/avion_domicile` vers `<config>/custom_components/avion_domicile` ; les fichiers de la carte et les images sont maintenant inclus dans ce dossier.
2. Redémarrez Home Assistant, puis dans **Paramètres → Appareils et services → Ajouter une intégration**, cherchez **Avion au-dessus du domicile**. Choisissez le visuel **Maison** ou **Radar**, puis un rayon de 1 à 100 km (20 km par défaut). Une limite de 100 km évite une mire trop chargée ; le même rayon sert aux deux visuels.
3. L'intégration enregistre et charge automatiquement la ressource Lovelace. Avec Home Assistant **2026.5 ou plus récent**, crée le tableau de bord prérempli depuis **Paramètres → Tableaux de bord → Ajouter un tableau de bord → Tableaux de bord communautaires → Avions au-dessus du domicile**. Home Assistant crée alors un nouveau tableau de bord contenant la carte.

Sur les versions Home Assistant antérieures à 2026.5, ajoute la carte manuellement au tableau de bord :

```yaml
type: custom:avion-domicile-card
entity: sensor.avion_au_dessus_du_domicile_avion_le_plus_proche
weather_entity: weather.forecast_maison
```

La génération crée un tableau de bord séparé ; elle ne modifie pas un tableau de bord existant. Vérifiez l'identifiant exact du capteur sous **Paramètres → Appareils et services → Entités** si Home Assistant lui a attribué un autre nom. Dans le menu de l'intégration, choisissez **Reconfigurer** pour changer ensuite le mode ou le rayon. Après installation ou mise à jour, actualise le navigateur si la carte n'apparaît pas.

La carte met en évidence le modèle, l'altitude, la vitesse et la distance. Le logo de la compagnie (ou son sigle si aucun logo ne peut être chargé) s'affiche dans le ciel juste au-dessus de la séparation avec les détails. Un appareil classé militaire sans illustration dédiée reçoit une silhouette générique d'avion et aucun logo de compagnie ; les autres contacts sans PNG exact gardent l'OVNI de remplacement avec une mention explicite.

## Données exposées

L'entité capteur contient les attributs `nearest`, `aircraft`, `aircraft_count`, `radius_km` et `data_source`. Chaque appareil peut inclure son indicatif, son immatriculation, son type, sa position, altitude, vitesse sol, cap, taux vertical et ancienneté de la mesure. Les quatre appareils les plus proches peuvent aussi contenir `aircraft_manufacturer`, `aircraft_icao_type`, `airline_name`, `airline_logo`, `airline_iata`, `origin_city`, `destination_city`, `origin_iata` et `destination_iata`. Les vitesses sont converties en km/h et les altitudes en mètres pour l'affichage.

## Développement

Le composant est autonome et n'installe aucune dépendance Python supplémentaire. Les appels utilisent la session HTTP partagée de Home Assistant.

Les rendus existants peuvent être parcourus dans `www/aircraft-png-preview.png`. Pour en générer de nouveaux, fournissez à `tools/render_aircraft_3d_profiles.py` un dossier de modèles GLB v2 issus du dépôt source, après conversion des GLB v1 avec `gltf-pipeline`. L'outil de rendu s'appuie sur `numpy<2`, `trimesh`, `pyrender`, `Pillow` et `PyOpenGL`; ces bibliothèques servent uniquement à créer les PNG et ne sont pas nécessaires sur Home Assistant.
