/* Neutral real-geometry profile PNGs; ICAO codes without an exact asset have no fallback. */
const AIRCRAFT_PNG_CATALOG = {
  "A318": { model: "Airbus A318", src: "/flights_over_me/static/aircraft-png/A318.png" },
  "A319": { model: "Airbus A319", src: "/flights_over_me/static/aircraft-png/A319.png" },
  "A320": { model: "Airbus A320", src: "/flights_over_me/static/aircraft-png/A320.png" },
  "A321": { model: "Airbus A321", src: "/flights_over_me/static/aircraft-png/A321.png" },
  "A332": { model: "Airbus A330-200", src: "/flights_over_me/static/aircraft-png/A332.png" },
  "A333": { model: "Airbus A330-300", src: "/flights_over_me/static/aircraft-png/A333.png" },
  "A343": { model: "Airbus A340-300", src: "/flights_over_me/static/aircraft-png/A343.png" },
  "A346": { model: "Airbus A340-600", src: "/flights_over_me/static/aircraft-png/A346.png" },
  "A359": { model: "Airbus A350-900", src: "/flights_over_me/static/aircraft-png/A359.png" },
  "A388": { model: "Airbus A380-800", src: "/flights_over_me/static/aircraft-png/A388.png" },
  "AT45": { model: "ATR 42-500", src: "/flights_over_me/static/aircraft-png/AT45.png" },
  "B736": { model: "Boeing 737-600", src: "/flights_over_me/static/aircraft-png/B736.png" },
  "B737": { model: "Boeing 737-700", src: "/flights_over_me/static/aircraft-png/B737.png" },
  "B738": { model: "Boeing 737-800", src: "/flights_over_me/static/aircraft-png/B738.png" },
  "B739": { model: "Boeing 737-900", src: "/flights_over_me/static/aircraft-png/B739.png" },
  "B744": { model: "Boeing 747-400", src: "/flights_over_me/static/aircraft-png/B744.png" },
  "B748": { model: "Boeing 747-8 Intercontinental", src: "/flights_over_me/static/aircraft-png/B748.png" },
  "B752": { model: "Boeing 757-200", src: "/flights_over_me/static/aircraft-png/B752.png" },
  "B753": { model: "Boeing 757-300", src: "/flights_over_me/static/aircraft-png/B753.png" },
  "B762": { model: "Boeing 767-200", src: "/flights_over_me/static/aircraft-png/B762.png" },
  "B763": { model: "Boeing 767-300", src: "/flights_over_me/static/aircraft-png/B763.png" },
  "B764": { model: "Boeing 767-400", src: "/flights_over_me/static/aircraft-png/B764.png" },
  "B772": { model: "Boeing 777-200", src: "/flights_over_me/static/aircraft-png/B772.png" },
  "B773": { model: "Boeing 777-300", src: "/flights_over_me/static/aircraft-png/B773.png" },
  "B788": { model: "Boeing 787-8", src: "/flights_over_me/static/aircraft-png/B788.png" },
  "B789": { model: "Boeing 787-9", src: "/flights_over_me/static/aircraft-png/B789.png" },
  "BCS1": { model: "Airbus A220-100 (CS100)", src: "/flights_over_me/static/aircraft-png/BCS1.png" },
  "BCS3": { model: "Airbus A220-300 (CS300)", src: "/flights_over_me/static/aircraft-png/BCS3.png" },
  "CRJ7": { model: "Bombardier CRJ700", src: "/flights_over_me/static/aircraft-png/CRJ7.png" },
  "CRJ9": { model: "Bombardier CRJ900", src: "/flights_over_me/static/aircraft-png/CRJ9.png" },
  "DH8D": { model: "De Havilland Canada Dash 8-400", src: "/flights_over_me/static/aircraft-png/DH8D.png" },
  "E170": { model: "Embraer E170", src: "/flights_over_me/static/aircraft-png/E170.png" },
  "E190": { model: "Embraer E190", src: "/flights_over_me/static/aircraft-png/E190.png" },
};

export function aircraftPngForType(type) {
  const code = String(type || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  const item = AIRCRAFT_PNG_CATALOG[code];
  return item ? { ...item, code, supported: true } : { code, model: code || "Type non identifié", src: null, supported: false };
}

export function listAircraftPngProfiles() {
  return Object.entries(AIRCRAFT_PNG_CATALOG).map(([code, item]) => ({ code, ...item }));
}
