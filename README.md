# Flights Over Me pour Home Assistant

[![Validation](https://github.com/tataille/homeassistant-flightsoverme/actions/workflows/validate.yml/badge.svg)](https://github.com/tataille/homeassistant-flightsoverme/actions/workflows/validate.yml)
[![Licence Apache 2.0](https://img.shields.io/badge/Licence-Apache%202.0-blue)](LICENSE)
[![Home Assistant 2024.4+](https://img.shields.io/badge/Home%20Assistant-2024.4%2B-18BCF2)](https://www.home-assistant.io/)
[![Dernière version](https://img.shields.io/github/v/release/tataille/homeassistant-flightsoverme)](https://github.com/tataille/homeassistant-flightsoverme/releases)
[![Téléchargements des releases](https://img.shields.io/github/downloads/tataille/homeassistant-flightsoverme/total?label=t%C3%A9l%C3%A9chargements%20des%20releases)](https://github.com/tataille/homeassistant-flightsoverme/releases)

*Le compteur indique les téléchargements des fichiers joints aux releases GitHub. Il ne mesure pas le nombre d’installations et ne compte pas les archives de sources générées automatiquement.*

**Découvrez les avions détectés près de votre domicile directement dans Home Assistant.**

Flights Over Me récupère les positions ADS-B proches de la maison et les présente dans une carte Lovelace dédiée. Choisissez une scène météo ou un radar, consultez les informations du vol le plus proche et sélectionnez un autre appareil lorsqu’il y en a plusieurs.

L’intégration lit la latitude et la longitude configurées dans Home Assistant. Elle s’installe depuis l’interface, sans YAML ni clé API.

## Ce que vous obtenez

- Une carte Lovelace en mode **Maison** : avion de profil, ciel météo et détails du vol.
- Un mode **Radar** : domicile au centre, orientation nord et avions positionnés selon leur direction et leur distance.
- Un thème jour/nuit automatique, piloté par `sun.sun` ou, si cette entité manque, par l’heure locale.
- Jusqu’à quatre appareils proches affichés : touchez un avion ou une ligne pour le mettre en vedette.
- Les données de vol disponibles : destination estimée, origine, compagnie, type, altitude, vitesse, distance et cap.
- Un visuel d’avion issu d’un modèle 3D correspondant au code type ICAO, sans livrée commerciale sur la cellule.

La carte est enregistrée automatiquement par l’intégration. À partir de Home Assistant **2026.5**, vous pouvez aussi créer un tableau de bord prérempli avec la stratégie Flights Over Me.

## Aperçu des illustrations d’avions

![Aperçu des illustrations des modèles d’avion inclus](www/aircraft-png-preview.png)

*Aperçu des PNG de la bibliothèque, pas une capture de la carte Home Assistant. Les silhouettes proviennent de modèles 3D réels, sont rendues en blanc avec des contours de type croquis et restent sans livrée. Le logo de la compagnie est affiché séparément lorsqu’il est disponible.*

## Avant de commencer

- Home Assistant **2024.4 ou plus récent**.
- Une latitude et une longitude renseignées dans **Paramètres → Système → Général**.
- Un accès Internet pour interroger ADSB.lol et, si disponibles, les services de métadonnées des vols.
- HACS pour l’installation guidée, ou un accès au dossier de configuration pour l’installation manuelle.

Les positions sont interrogées toutes les **15 secondes**. Le rayon est réglable de 1 à 100 km et vaut 20 km par défaut. Il représente la distance horizontale entre le domicile et la position ADS-B reçue ; l’altitude de l’avion n’entre pas dans ce calcul.

## Installer avec HACS

[![Ouvrir dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tataille&repository=homeassistant-flightsoverme&category=integration)

HACS doit déjà être installé. Vous pouvez aussi ajouter le dépôt manuellement dans HACS :

1. Ouvrez **HACS → Intégrations → ⋮ → Dépôts personnalisés**.
2. Ajoutez `https://github.com/tataille/homeassistant-flightsoverme` avec la catégorie **Intégration**.
3. Recherchez **Flights Over Me**, puis téléchargez l’intégration.
4. Redémarrez Home Assistant.
5. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration** et recherchez **Flights Over Me**.

## Installer manuellement

1. [Téléchargez le projet](https://github.com/tataille/homeassistant-flightsoverme/archive/refs/heads/main.zip) et décompressez l’archive.
2. Copiez `custom_components/flights_over_me` dans le dossier de configuration de Home Assistant.
3. Vérifiez que le fichier `/config/custom_components/flights_over_me/manifest.json` existe.
4. Redémarrez Home Assistant et ajoutez **Flights Over Me** depuis **Paramètres → Appareils et services**.

Avec Home Assistant Docker, copiez le dossier dans le répertoire de l’hôte monté sur `/config`. Les fichiers de la carte et les illustrations d’avions sont déjà inclus dans l’intégration.

### Passage depuis le prototype `avion_domicile`

Cette version utilise le domaine technique `flights_over_me`. Supprimez l’ancienne entrée **avion_domicile** dans **Appareils et services**, retirez son ancien dossier `custom_components/avion_domicile`, puis installez et ajoutez **Flights Over Me**. Il s’agit d’un prototype : la configuration précédente n’est pas migrée automatiquement.

## Configurer l’intégration

À l’ajout de l’intégration, choisissez un visuel et un rayon de recherche de **1 à 100 km** (20 km par défaut). Le rayon définit la zone de détection dans les deux modes ; en mode Radar, il fixe aussi l’échelle de la mire. Vous pourrez modifier ces paramètres plus tard dans le menu de l’intégration avec **Reconfigurer**.

| Mode | Présentation |
|---|---|
| Maison | Vue de profil de l’avion, fond météo et détails du vol sélectionné. Le jour et la nuit adaptent automatiquement les couleurs de la scène. |
| Radar | Mire orientée au nord, domicile au centre et appareils répartis selon leur cap et leur distance. La portée correspond au rayon choisi. |

La météo utilise par défaut `weather.forecast_maison`. Pour une autre entité, indiquez `weather_entity` dans la configuration YAML de la carte. Les états de pluie, neige, brouillard, nuages, orage, vent ou éclaircies modifient le ciel illustré ; la température et la condition courante sont également affichées.

## Afficher la carte

La carte est chargée automatiquement après l’installation de l’intégration.

Avec Home Assistant **2026.5 ou plus récent**, créez un tableau de bord contenant la carte depuis **Paramètres → Tableaux de bord → Ajouter un tableau de bord → Tableaux de bord communautaires → Flights Over Me**. Cela crée un nouveau tableau de bord ; un tableau déjà existant n’est pas modifié.

Sur les versions antérieures, ajoutez manuellement une carte **Manuelle** dans le tableau de bord :

```yaml
type: custom:avion-domicile-card
entity: sensor.flights_over_me_avion_le_plus_proche
weather_entity: weather.forecast_maison
```

Home Assistant choisit l’identifiant exact du capteur à la création. Si l’exemple ne correspond pas à votre installation, retrouvez l’entité **Avion le plus proche** dans **Outils de développement → États** et remplacez `entity`. Après une mise à jour, rechargez la page du tableau de bord si la carte n’apparaît pas.

## Comprendre les informations de vol

L’intégration crée un capteur **Avion le plus proche**. Ses attributs incluent :

| Attribut | Contenu |
|---|---|
| `aircraft_count` | Nombre d’appareils détectés dans le rayon choisi |
| `aircraft` | Liste des appareils reçus et leurs données disponibles |
| `nearest` | Appareil actuellement le plus proche |
| `radius_km` | Rayon de recherche en kilomètres |
| `home_latitude`, `home_longitude` | Coordonnées du domicile utilisées par l’intégration |
| `display_mode` | `house` ou `radar` |
| `data_source` | Source des positions, `ADSB.lol` |

Un appareil peut également fournir son indicatif, son immatriculation, son code ICAO, son type, sa position, son altitude, sa vitesse sol, son cap et l’âge de la mesure. La compagnie et l’itinéraire sont des informations complémentaires : elles ne sont pas diffusées par tous les vols.

## Données, illustrations et limites

Les positions proviennent de l’API ouverte [ADSB.lol](https://api.adsb.lol/docs). Les informations complémentaires sur le type et la compagnie sont recherchées auprès d’[ADSBDB](https://github.com/mrjackwills/adsbdb). Une route probable est recherchée auprès d’ADSB.lol à partir de l’indicatif ; la destination affichée reste une estimation et peut manquer ou être erronée.

La bibliothèque contient 33 rendus PNG associés aux codes ICAO du catalogue. Les modèles 3D proviennent de [Flightradar24/fr24-3d-models](https://github.com/Flightradar24/fr24-3d-models), qui crédite FlightGear et FGMEMBERS et indique la licence GPL-2.0 pour les modèles d’avion. Consultez les [crédits](www/aircraft-png/ATTRIBUTION.txt) et la [licence des illustrations](www/aircraft-png/LICENSE-GPL-2.0.txt). Le code de l’intégration est sous licence [Apache 2.0](LICENSE).

La couverture ADS-B dépend des récepteurs de la source et n’est pas garantie partout. Un avion sans transpondeur ADS-B actif, sans position récente ou non reçu par le réseau peut ne pas apparaître. Le rayon ne correspond pas à une observation visuelle ni à la distance verticale. Le logo n’est affiché que si la compagnie est reconnue et si son image est disponible. Les avions inconnus ont un pictogramme de remplacement ; les appareils classés militaires sans modèle dédié ont une silhouette générique, sans logo commercial.

## Dépannage

**Aucun avion n’apparaît alors qu’un appareil vient de passer.**

Vérifiez `aircraft_count`, `radius_km`, `home_latitude` et `home_longitude` dans les attributs du capteur. Comparez les coordonnées à celles de **Paramètres → Système → Général** et vérifiez que le rayon englobe la position horizontale estimée de l’avion. L’API est interrogée toutes les 15 secondes, mais un passage peut encore être manqué si aucune position ADS-B n’est reçue. Consultez **Paramètres → Système → Journaux** pour repérer une erreur `flights_over_me` ou ADSB.lol.

**Le tableau de bord ou la carte n’apparaît pas.**

Vérifiez que l’intégration est chargée, redémarrez Home Assistant et rechargez le navigateur. Le tableau de bord par stratégie est disponible à partir de Home Assistant 2026.5 ; sur une version plus ancienne, ajoutez la carte manuellement.

**La destination, la compagnie ou le logo est absent.**

Ces informations dépendent des bases externes et de l’indicatif reçu. Certains vols privés, charters ou non réguliers n’ont pas d’itinéraire reconnu. L’absence de métadonnées n’empêche pas l’affichage de la position ADS-B.

## Mise à jour

Avec HACS, téléchargez la version proposée puis redémarrez Home Assistant. En installation manuelle, remplacez `custom_components/flights_over_me` par le dossier de la version mise à jour, puis redémarrez Home Assistant. Ne supprimez pas l’entrée de l’intégration lors d’une mise à jour normale de Flights Over Me.

## Contribuer et obtenir de l’aide

Pour signaler un problème ou proposer une amélioration, ouvrez une [issue GitHub](https://github.com/tataille/homeassistant-flightsoverme/issues). Indiquez la version de Home Assistant, la version de l’intégration, le rayon choisi et les messages de journal pertinents. Évitez de publier vos coordonnées personnelles.

Les rendus existants sont visibles dans [`www/aircraft-png-preview.png`](www/aircraft-png-preview.png). Pour en générer d’autres, consultez le [guide des illustrations](AIRCRAFT_ILLUSTRATION_SPEC.md) et le script [`tools/render_aircraft_3d_profiles.py`](tools/render_aircraft_3d_profiles.py). Ces outils de création ne sont pas nécessaires au fonctionnement de Home Assistant.

Licence du code : [Apache 2.0](LICENSE). Les modèles 3D et illustrations conservent les licences indiquées dans leurs fichiers d’attribution.
