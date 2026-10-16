import { aircraftPngForType } from "./aircraft-png-library.js";

/* Lovelace card: per-ICAO neutral profile PNG, selectable nearby flights, and live weather. */
class AvionDomicileCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Ajoutez l'entité sensor.avion_au_dessus_du_domicile_avion_le_plus_proche");
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    const count = this._hass?.states?.[this.config?.entity]?.attributes?.aircraft?.length || 1;
    return 3 + Math.min(Math.max(count - 1, 0), 3);
  }

  render() {
    if (!this.config || !this._hass) return;
    const state = this._hass.states[this.config.entity];
    const attrs = state?.attributes || {};
    const radarMode = attrs.display_mode === "radar";
    const radiusKm = Number(attrs.radius_km) || 20;
    const allAircraft = Array.isArray(attrs.aircraft) ? attrs.aircraft : [];
    const nearest = attrs.nearest || allAircraft[0];
    const selected = this._selectedAircraftKey
      ? allAircraft.find(item => aircraftKey(item) === this._selectedAircraftKey)
      : null;
    if (this._selectedAircraftKey && !selected) this._selectedAircraftKey = null;
    const plane = selected || nearest;
    const otherAircraft = allAircraft.filter(item => aircraftKey(item) !== aircraftKey(plane)).slice(0, 3);
    const additionalAircraftCount = Math.max(0, allAircraft.length - 1 - otherAircraft.length);
    const weatherEntity = this.config.weather_entity || "weather.forecast_maison";
    const weather = this._hass.states[weatherEntity] || Object.values(this._hass.states).find(item => item.entity_id.startsWith("weather."));
    const condition = weather?.state || "unknown";
    const weatherClass = weatherProfile(condition);
    const sun = this._hass.states["sun.sun"];
    const localHour = new Date().getHours();
    const isNight = sun?.state === "below_horizon"
      ? true
      : sun?.state === "above_horizon"
        ? false
        : localHour < 7 || localHour >= 20;
    const timeMode = isNight ? "time-night" : "time-day";
    const timeLabel = isNight ? "NUIT" : "JOUR";
    const weatherText = weatherLabel(condition);
    const temperature = weather?.attributes?.temperature;
    const temperatureUnit = weather?.attributes?.temperature_unit || this._hass.config?.unit_system?.temperature || "°C";
    const numericTemperature = Number(temperature);
    const weatherReading = temperature != null && Number.isFinite(numericTemperature) ? `${Math.round(numericTemperature)}${temperatureUnit}` : "";
    const weatherSummary = [weatherReading, weatherText].filter(Boolean).join(" · ");
    const flight = plane?.flight || state?.state || "En attente des données";
    const origin = plane?.origin_city || plane?.origin_iata || "";
    const destination = plane?.destination_city || plane?.destination_iata || "";
    const routeTitle = origin && destination ? `${origin} → ${destination}` : destination ? `Destination · ${destination}` : "Destination inconnue";
    const routeCodes = [plane?.origin_iata, plane?.destination_iata].filter(Boolean).join(" → ");
    const altitude = plane?.altitude_m != null ? `${Math.round(plane.altitude_m).toLocaleString("fr-FR")} m d’altitude` : "Altitude indisponible";
    const speed = plane?.ground_speed_kmh != null ? `${Math.round(plane.ground_speed_kmh)} km/h` : "Vitesse indisponible";
    const distance = plane?.distance_km != null ? `${plane.distance_km.toLocaleString("fr-FR")} km du domicile` : "";
    const model = [plane?.aircraft_manufacturer, plane?.aircraft_type || plane?.description || plane?.type].filter(Boolean).join(" ") || plane?.registration || "Type d’avion non identifié";
    const airline = plane?.airline_name || "Compagnie non identifiée";
    const logo = safeImageUrl(plane?.airline_logo);
    const count = attrs.aircraft_count ?? 0;
    const heading = Number.isFinite(Number(plane?.heading)) ? Number(plane.heading) : 0;
    const freshness = plane?.seen_seconds != null ? `vu il y a ${Math.max(0, Math.round(plane.seen_seconds))} s` : "Données ADS-B en direct";
    const aircraftTypeCode = plane?.aircraft_icao_type || plane?.type;
    const aircraftArtwork = plane && aircraftTypeCode ? aircraftPngForType(aircraftTypeCode) : null;
    const mark = (plane?.airline_iata || plane?.airline_icao || airline.slice(0, 2)).toUpperCase();
    const aircraftImage = aircraftArtwork?.src
      ? `<img class="aircraft-png" src="${escapeHtml(aircraftArtwork.src)}" alt="${escapeHtml(aircraftArtwork.model)} de profil, nez vers la droite">`
      : "";
    const skyAirlineLogo = logo
      ? `<img src="${escapeHtml(logo)}" alt="Logo ${escapeHtml(airline)}">`
      : `<span>${escapeHtml(mark)}</span>`;
    const aircraftRows = otherAircraft.map(item => {
      const itemRoute = [item.origin_iata || item.origin_city, item.destination_iata || item.destination_city].filter(Boolean).join(" → ");
      const itemModel = item.aircraft_type || item.description || item.type || "Type inconnu";
      const itemTitle = itemRoute || item.flight || item.registration || "Vol sans indicatif";
      const itemCompany = item.airline_name || item.flight || item.registration || "Compagnie inconnue";
      const itemDistance = item.distance_km != null ? `${Number(item.distance_km).toLocaleString("fr-FR")} km` : "Distance inconnue";
      return `<button class="traffic-item" type="button" data-aircraft-key="${escapeHtml(aircraftKey(item))}" aria-label="Afficher ${escapeHtml(itemTitle)}, ${escapeHtml(itemModel)}, à ${escapeHtml(itemDistance)}"><span class="traffic-route">${escapeHtml(itemTitle)}</span><span class="traffic-meta">${escapeHtml(itemCompany)} · ${escapeHtml(itemModel)}</span><span class="traffic-distance">${escapeHtml(itemDistance)} ›</span></button>`;
    }).join("");
    const radarTargets = allAircraft.map(item => {
      const position = radarCoordinates(item, attrs.home_latitude, attrs.home_longitude, radiusKm);
      const itemLabel = item.flight || item.registration || item.hex || "Avion détecté";
      const selectedClass = aircraftKey(item) === aircraftKey(plane) ? " is-selected" : "";
      return `<button class="radar-target${selectedClass}" type="button" data-aircraft-key="${escapeHtml(aircraftKey(item))}" style="left:${position.x.toFixed(2)}%;top:${position.y.toFixed(2)}%" title="${escapeHtml(itemLabel)} · ${Number(item.distance_km || 0).toLocaleString("fr-FR")} km" aria-label="Afficher ${escapeHtml(itemLabel)}, à ${Number(item.distance_km || 0).toLocaleString("fr-FR")} kilomètres"><span></span></button>`;
    }).join("");
    const weatherBadge = `<div class="weather-reading"><span class="weather-icon">${weatherGlyph(condition)}</span>${escapeHtml(weatherSummary || "Météo indisponible")}</div>`;
    const houseVisual = `<div class="sky ${weatherClass}">
      <div class="sky-label">LE CIEL AU-DESSUS DE CHEZ VOUS</div>
      <div class="live"><span></span> LIVE · ${timeLabel} · ${new Date().toLocaleTimeString("fr-FR", {hour:"2-digit", minute:"2-digit"})}</div>
      ${weatherBadge}
      <div class="sun"></div><div class="cloud cloud-a"></div><div class="cloud cloud-b"></div><div class="precipitation"></div><div class="fog"></div>
      ${aircraftImage ? `<div class="aircraft-wrap">${aircraftImage}</div>` : plane ? `<div class="ufo-fallback" role="img" aria-label="Avion non identifié, illustration OVNI de remplacement"><div class="ufo-beam"></div><div class="ufo"><div class="ufo-dome"></div><div class="ufo-disc"><i></i><i></i><i></i></div></div><div class="ufo-label">TYPE D’AVION INCONNU · ${escapeHtml(aircraftTypeCode || "ICAO INDISPONIBLE")}</div></div>` : `<div class="aircraft-empty">En attente d’un avion détecté</div>`}
    </div>`;
    const radarVisual = `<div class="radar-display">
      <div class="radar-heading">RADAR DU DOMICILE · ${timeLabel}</div>
      <div class="radar-live"><span></span> ${count} CONTACT${count > 1 ? "S" : ""} · ${new Date().toLocaleTimeString("fr-FR", {hour:"2-digit", minute:"2-digit"})}</div>
      <div class="radar-range">PORTÉE ${radiusKm} km</div>
      <div class="radar-scope">
        <div class="radar-ring ring-outer"></div><div class="radar-ring ring-middle"></div><div class="radar-ring ring-inner"></div>
        <div class="radar-axis radar-axis-v"></div><div class="radar-axis radar-axis-h"></div><div class="radar-sweep"></div>
        <div class="radar-home" title="Domicile">⌂</div>${radarTargets}
      </div>
      ${weatherBadge}
    </div>`;
    const logoMarkup = plane && (logo || mark) ? `<div class="sky-airline-logo" aria-label="Compagnie ${escapeHtml(airline)}">${skyAirlineLogo}</div>` : "";

    this.innerHTML = `
      <ha-card>
        <div class="frame">
          <div class="visual ${radarMode ? "visual-radar" : "visual-house"} ${timeMode}">
            ${radarMode ? radarVisual : houseVisual}
            ${logoMarkup}
            <div class="horizon"></div>
          </div>
          <div class="info">
            <div class="eyebrow">${escapeHtml(airline)} · ${count} ${count > 1 ? "AVIONS À PROXIMITÉ" : "AVION À PROXIMITÉ"}</div>
            <div class="flight-row">
              <div class="route">
                <div class="route-title">${escapeHtml(routeTitle)}</div>
                <div class="route-meta">${routeCodes ? `${escapeHtml(routeCodes)} · ` : ""}${escapeHtml(flight)}</div>
              </div>
            </div>
            <div class="aircraft-model">${escapeHtml(model)}</div>
            <div class="details"><span>${altitude}</span><span>${speed}</span>${distance ? `<span>${escapeHtml(distance)}</span>` : ""}</div>
            <div class="footer"><span>${escapeHtml(freshness)}</span><span class="compass"><span style="transform:rotate(${heading}deg)">▲</span></span></div>
          </div>
          ${aircraftRows ? `<div class="traffic"><div class="traffic-heading">AUTRES VOLS À PROXIMITÉ</div><div class="traffic-list">${aircraftRows}</div>${additionalAircraftCount ? `<div class="traffic-more">+ ${additionalAircraftCount} autre${additionalAircraftCount > 1 ? "s" : ""} dans le rayon</div>` : ""}</div>` : ""}
        </div>
      </ha-card>
      <style>
        ha-card{overflow:hidden;border-radius:18px;background:#f2f0e8;color:#222;box-shadow:0 5px 22px #0002}
        .frame{padding:12px}.visual{height:220px;position:relative;overflow:hidden;border-radius:11px 11px 0 0}.sky{height:100%;position:relative;overflow:hidden;border-radius:inherit;background:linear-gradient(180deg,#91b4cf 0%,#c6d8e1 56%,#dce0df 57%,#ebebe5 100%);transition:background .6s ease}
        .sky-label,.live{position:absolute;z-index:4;top:16px;font:600 9px/1.2 monospace;letter-spacing:1.4px;color:#31414d}.sky-label{left:18px}.live{right:16px;letter-spacing:.8px}.live span{display:inline-block;width:7px;height:7px;border-radius:50%;background:#d85849;margin-right:4px}
        .weather-reading{position:absolute;z-index:4;left:16px;bottom:12px;padding:5px 8px;border-radius:12px;background:#ffffffb8;color:#283843;font:600 10px/1.2 system-ui,sans-serif;letter-spacing:.2px;box-shadow:0 1px 5px #33445522}.weather-icon{margin-right:5px;font-size:13px}
        .radar-display{position:absolute;inset:0;overflow:hidden;background:radial-gradient(ellipse at center,#184239 0%,#102b2c 58%,#0b2025 100%);color:#a9e3b0}.radar-display:after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,#b4edba08 0 1px,transparent 1px 4px)}.radar-heading,.radar-live,.radar-range{position:absolute;z-index:4;top:14px;font:700 9px/1.2 monospace;letter-spacing:1px;color:#c3e8c1}.radar-heading{left:16px}.radar-live{right:14px;letter-spacing:.5px}.radar-live span{display:inline-block;width:6px;height:6px;border-radius:50%;background:#74e38b;margin-right:4px;box-shadow:0 0 7px #74e38b}.radar-range{top:31px;left:16px;color:#89ba9a;font-size:8px}.radar-scope{position:absolute;left:50%;top:53%;width:min(54vw,168px);aspect-ratio:1;transform:translate(-50%,-50%);border:1px solid #86d59b99;border-radius:50%;background:radial-gradient(circle,transparent 0 33%,#5cbd7817 34% 35%,transparent 36% 66%,#5cbd7817 67% 68%,transparent 69%);box-shadow:0 0 22px #4bce7222,inset 0 0 18px #4bce7212}.radar-ring{position:absolute;border:1px solid #86d59b70;border-radius:50%;pointer-events:none}.ring-outer{inset:0}.ring-middle{inset:16.5%}.ring-inner{inset:33%}.radar-axis{position:absolute;background:#86d59b55;pointer-events:none}.radar-axis-v{left:50%;top:0;bottom:0;width:1px}.radar-axis-h{top:50%;left:0;right:0;height:1px}.radar-sweep{position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 0deg,transparent 0deg 298deg,#6be98b08 315deg,#6be98b70 360deg);animation:radar-rotate 5s linear infinite;pointer-events:none}@keyframes radar-rotate{to{transform:rotate(360deg)}}.radar-home{position:absolute;z-index:4;left:50%;top:50%;width:16px;height:16px;transform:translate(-50%,-50%);border:1px solid #ecedb2;border-radius:50%;background:#40583c;color:#f4efb3;text-align:center;font:700 11px/14px system-ui,sans-serif;box-shadow:0 0 9px #d6df9a88}.radar-target{position:absolute;z-index:5;width:20px;height:20px;padding:0;transform:translate(-50%,-50%);border:0;border-radius:50%;background:transparent;cursor:pointer}.radar-target span{display:block;position:absolute;left:6px;top:6px;width:8px;height:8px;border-radius:50%;background:#a3f6a5;box-shadow:0 0 8px 2px #84f598aa}.radar-target.is-selected span{width:11px;height:11px;left:4.5px;top:4.5px;background:#fff3a6;box-shadow:0 0 0 4px #fff3a633,0 0 13px 3px #fff3a6}.radar-target:focus-visible{outline:2px solid white;outline-offset:1px}.visual-radar .weather-reading{background:#173b35d9;color:#d9f2d8;border:1px solid #84c99c55;box-shadow:none}.visual-radar.time-day .radar-display{background:radial-gradient(ellipse at center,#205746 0%,#143b39 58%,#10272d 100%)}.visual-radar.time-night .radar-display{background:radial-gradient(ellipse at center,#182548 0%,#101a35 58%,#090f20 100%)}.visual-radar.time-night .radar-ring,.visual-radar.time-night .radar-scope{border-color:#8da9ed88}.visual-radar.time-night .radar-axis{background:#8da9ed44}.visual-radar.time-night .radar-range{color:#a5b7e0}.visual-radar.time-night .weather-reading{background:#151f3bd9;color:#e0e7ff;border-color:#8da9ed55}.sky.time-night{background:linear-gradient(180deg,#15243b 0%,#394a64 56%,#65707a 57%,#939794 100%)}.sky.time-night .sky-label,.sky.time-night .live{color:#f4f1e8}.sky.time-night .sun{background:#f1edda;border-color:#eee8d7;box-shadow:0 0 20px #eef2ff88}.sky.time-night .cloud{opacity:.25}.sky.time-night .weather-reading{background:#18263ac9;color:#f7f4e9}.sky.time-day.weather-night{background:linear-gradient(180deg,#94b5cb 0%,#c5d6dd 56%,#dce0df 57%,#ebebe5 100%)}.sky.time-day.weather-night .sun{background:#f2bd3c;border-color:#383936;box-shadow:0 0 22px #fff8}.sky.time-day.weather-night .cloud{opacity:.45}
        .sun{position:absolute;width:47px;height:47px;border-radius:50%;background:#f2bd3c;border:2px solid #383936;left:58%;top:53px;box-shadow:0 0 22px #fff8;transition:all .5s ease}
        .cloud{position:absolute;height:30px;background:#f7f6f0;opacity:.42;border-radius:50%;filter:blur(1px);transition:all .5s ease}.cloud-a{width:180px;top:103px;left:-25px}.cloud-b{width:220px;top:133px;right:-40px}
        .aircraft-wrap{position:absolute;z-index:3;left:50%;top:47%;width:min(90%,390px);height:160px;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;pointer-events:none}.aircraft-png{display:block;width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 2px 2px #182a3822)}.aircraft-empty{position:absolute;z-index:3;top:50%;left:50%;transform:translate(-50%,-50%);color:#344653;font:600 12px/1.4 system-ui,sans-serif;text-align:center}.sky-airline-logo{position:absolute;z-index:5;right:16px;bottom:12px;min-width:46px;height:24px;max-width:66px;padding:2px 4px;display:flex;align-items:center;justify-content:center;border:1px solid #d5d8d5;border-radius:5px;background:#ffffffed;box-shadow:0 2px 5px #22334422}.sky-airline-logo img{display:block;max-width:100%;max-height:100%;object-fit:contain}.sky-airline-logo span{font:800 9px/1 system-ui,sans-serif;letter-spacing:.3px;color:#17345a}
        .ufo-fallback{position:absolute;z-index:3;left:50%;top:47%;transform:translate(-50%,-50%);width:min(76%,300px);height:150px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px}.ufo{position:relative;width:112px;height:62px;filter:drop-shadow(0 3px 2px #243b4822)}.ufo-dome{position:absolute;z-index:2;left:35px;top:0;width:42px;height:32px;border:2px solid #34434a;border-bottom:0;border-radius:28px 28px 8px 8px;background:linear-gradient(135deg,#c5e5dd,#73a9a2)}.ufo-disc{position:absolute;z-index:3;left:0;bottom:8px;width:108px;height:32px;border:2px solid #34434a;border-radius:50%;background:linear-gradient(180deg,#edf0ec 0%,#aab6b5 55%,#718187 100%);display:flex;justify-content:space-evenly;align-items:flex-end;padding-bottom:6px;box-sizing:border-box}.ufo-disc i{display:block;width:7px;height:4px;border-radius:50%;background:#e8c95b;box-shadow:0 0 5px #f1d978}.ufo-beam{position:absolute;z-index:1;top:80px;width:125px;height:55px;background:linear-gradient(180deg,#b4d5bd66,transparent);clip-path:polygon(42% 0,58% 0,100% 100%,0 100%)}.ufo-label{padding:5px 8px;border:1px solid #c7d0c9;border-radius:10px;background:#ffffffc9;color:#344b45;font:700 9px/1.2 monospace;letter-spacing:.4px;text-align:center}.aircraft-model{margin-top:7px;color:#31312e;font:750 14px/1.35 system-ui,sans-serif;letter-spacing:.1px}.details{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:8px;font:650 12px/1.4 system-ui,sans-serif;color:#42423d}.details span{padding:4px 7px;border-radius:7px;background:#e7e4dc}
        .horizon{position:absolute;z-index:2;bottom:0;height:3px;background:#44433d;left:7%;right:7%}.visual-radar .horizon{background:#87c597}
        .weather-cloudy{background:linear-gradient(180deg,#899ba8 0%,#b2bec4 56%,#d1d4d1 57%,#e2e2dc 100%)}.weather-cloudy .sun{opacity:0;transform:scale(.75)}.weather-cloudy .cloud{opacity:.76;transform:scale(1.25)}
        .weather-partly{background:linear-gradient(180deg,#94b5cb 0%,#c5d6dd 56%,#dce0df 57%,#ebebe5 100%)}.weather-partly .cloud{opacity:.65}.weather-partly .sun{opacity:.88}
        .weather-rain,.weather-storm{background:linear-gradient(180deg,#697d8d 0%,#9daab1 56%,#c3c9c8 57%,#d8d9d4 100%)}.weather-rain .sun,.weather-storm .sun{opacity:0}.weather-rain .cloud,.weather-storm .cloud{opacity:.86;transform:scale(1.35)}
        .precipitation{display:none;position:absolute;z-index:2;inset:74px 0 0;pointer-events:none}.weather-rain .precipitation,.weather-storm .precipitation{display:block;background:repeating-linear-gradient(108deg,transparent 0 17px,#e6f1f688 18px 19px,transparent 20px 36px);opacity:.48}.weather-snow .precipitation{display:block;background:radial-gradient(circle,#fff 1.3px,transparent 2px) 0 0/26px 24px,radial-gradient(circle,#fff 1px,transparent 2px) 12px 11px/34px 31px;opacity:.75}
        .weather-storm .precipitation{opacity:.7}.weather-storm:after{content:"";position:absolute;inset:0;background:#dce8f755;animation:flash 5s infinite;pointer-events:none;z-index:1}@keyframes flash{0%,90%,100%{opacity:0}92%{opacity:.6}94%{opacity:0}96%{opacity:.35}}
        .weather-fog{background:linear-gradient(180deg,#b7c1c3 0%,#d1d5d3 54%,#e1e2de 55%,#e9e8e1 100%)}.weather-fog .sun{opacity:.12}.weather-fog .cloud{opacity:.75;filter:blur(12px);transform:scale(1.6)}.fog{display:none;position:absolute;z-index:2;inset:80px 0 0;background:repeating-linear-gradient(0deg,transparent 0 18px,#f4f5f0a8 19px 26px,transparent 27px 40px);filter:blur(5px)}.weather-fog .fog{display:block}
        .weather-snow{background:linear-gradient(180deg,#a9c1d0 0%,#d3e0e4 56%,#e2e4e1 57%,#f0f0ed 100%)}.weather-snow .sun{opacity:.28}
        .weather-windy{background:linear-gradient(180deg,#8ca7b7 0%,#bccbd0 56%,#d4d8d5 57%,#e4e4de 100%)}.weather-windy .cloud{transform:translateX(18px);opacity:.68}
        .info{padding:13px 16px 10px;background:#f2f0e8}.eyebrow{font:600 9px/1.4 monospace;letter-spacing:1.25px;color:#66645c;text-transform:uppercase;overflow-wrap:anywhere}.flight-row{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:3px}.route{min-width:0}.route-title{font:800 clamp(18px,4.5vw,27px)/1.12 system-ui,sans-serif;letter-spacing:.1px;overflow-wrap:anywhere;text-transform:uppercase}.route-meta{margin-top:3px;font:600 10px/1.25 monospace;letter-spacing:.8px;color:#6e6b63}
        .aircraft-model{margin-top:3px;color:#4c4b46;font:600 11px/1.35 monospace;letter-spacing:.4px}.details{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:7px;font:500 11px/1.4 monospace;color:#5f5d56}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:10px;padding-top:8px;border-top:1px solid #c8c5ba;font:500 10px monospace;color:#77756d}.compass{width:30px;height:30px;border:1.5px solid #54534e;border-radius:50%;display:grid;place-items:center;color:#c84a48}.compass span{display:block;font-size:17px;transform-origin:center}
        .traffic{padding:8px 16px 14px;background:#f2f0e8}.traffic-heading{margin-bottom:6px;font:700 9px/1.3 monospace;letter-spacing:1px;color:#68665e}.traffic-list{display:grid;gap:5px}.traffic-item{width:100%;min-height:46px;padding:6px 9px;border:1px solid #dedbd1;border-radius:9px;background:#fffefa;color:#252522;text-align:left;display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-rows:auto auto;column-gap:8px;align-items:center;cursor:pointer}.traffic-item:active{background:#e9eef1;transform:scale(.995)}.traffic-route{font:750 12px/1.25 system-ui,sans-serif;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.traffic-meta{font:500 9px/1.3 system-ui,sans-serif;color:#65635c;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.traffic-distance{grid-column:2;grid-row:1/3;font:700 10px/1 system-ui,sans-serif;color:#475965;white-space:nowrap}.traffic-more{padding:7px 2px 0;font:600 10px/1.3 system-ui,sans-serif;color:#68665e}
        @media(max-width:420px){.visual{height:190px}.aircraft-wrap,.ufo-fallback{width:94%;height:120px;top:47%}.radar-scope{width:min(52vw,145px)}.sky-airline-logo{right:12px;bottom:12px;max-width:58px;height:22px}.details{gap:5px;font-size:10px}.traffic{padding-right:12px;padding-left:12px}}
      </style>`;
    const logoImage = this.querySelector(".sky-airline-logo img");
    if (logoImage) logoImage.addEventListener("error", () => { logoImage.remove(); const fallback = document.createElement("span"); fallback.textContent = mark; this.querySelector(".sky-airline-logo")?.append(fallback); }, {once:true});
    this.querySelectorAll(".traffic-item, .radar-target").forEach(button => button.addEventListener("click", () => {
      this._selectedAircraftKey = button.dataset.aircraftKey;
      this.render();
    }));
  }
}

function aircraftKey(plane) {
  if (!plane) return "";
  return String(plane.hex || plane.registration || plane.flight || `${plane.lat ?? ""},${plane.lon ?? ""}`).trim().toLowerCase();
}

function radarCoordinates(plane, homeLatitude, homeLongitude, radiusKm) {
  const latitude = Number(plane?.lat);
  const longitude = Number(plane?.lon);
  const homeLat = Number(homeLatitude);
  const homeLon = Number(homeLongitude);
  if (![latitude, longitude, homeLat, homeLon].every(Number.isFinite)) return {x: 50, y: 50};

  const radians = Math.PI / 180;
  const phi1 = homeLat * radians;
  const phi2 = latitude * radians;
  const deltaLongitude = (longitude - homeLon) * radians;
  const bearing = Math.atan2(
    Math.sin(deltaLongitude) * Math.cos(phi2),
    Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLongitude),
  );
  const distance = Number.isFinite(Number(plane.distance_km)) ? Number(plane.distance_km) : 0;
  const rangeFraction = Math.min(Math.max(distance / Math.max(radiusKm, 1), 0), 1);
  const offset = 46 * rangeFraction;
  return {
    x: 50 + Math.sin(bearing) * offset,
    y: 50 - Math.cos(bearing) * offset,
  };
}

function weatherProfile(condition) {
  if (["sunny", "exceptional"].includes(condition)) return "weather-sunny";
  if (condition === "partlycloudy") return "weather-partly";
  if (["cloudy", "windy-variant"].includes(condition)) return "weather-cloudy";
  if (["rainy", "pouring", "hail", "snowy-rainy"].includes(condition)) return "weather-rain";
  if (condition === "lightning" || condition === "lightning-rainy") return "weather-storm";
  if (condition === "snowy") return "weather-snow";
  if (condition === "fog") return "weather-fog";
  if (condition === "windy") return "weather-windy";
  if (condition === "clear-night" || condition.endsWith("-night")) return "weather-night";
  return "weather-cloudy";
}

function weatherLabel(condition) {
  return ({sunny:"Ensoleillé", "clear-night":"Nuit claire", partlycloudy:"Éclaircies", cloudy:"Nuageux", rainy:"Pluie", pouring:"Forte pluie", snowy:"Neige", "snowy-rainy":"Neige et pluie", fog:"Brouillard", lightning:"Orage", "lightning-rainy":"Orage et pluie", windy:"Venteux", "windy-variant":"Vent et nuages", hail:"Grêle", exceptional:"Météo exceptionnelle"})[condition] || "Météo";
}

function weatherGlyph(condition) {
  if (["sunny", "exceptional"].includes(condition)) return "☀";
  if (condition === "clear-night") return "☾";
  if (["rainy", "pouring", "lightning-rainy", "snowy-rainy"].includes(condition)) return "☂";
  if (condition === "snowy") return "❄";
  if (["lightning", "hail"].includes(condition)) return "⚡";
  if (condition === "fog") return "≋";
  if (condition === "windy") return "〰";
  return "☁";
}

function safeImageUrl(value) {
  if (!value) return "";
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" && parsed.hostname === "images.kiwi.com" ? parsed.href : "";
  } catch { return ""; }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
}

customElements.define("avion-domicile-card", AvionDomicileCard);
window.customCards = window.customCards || [];
window.customCards.push({type:"avion-domicile-card", name:"Avion au-dessus du domicile", description:"Affiche les avions proches avec météo et thèmes jour/nuit automatiques."});
