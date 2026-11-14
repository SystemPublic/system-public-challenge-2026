# Forecast map geometry

Source: Natural Earth (https://www.naturalearthdata.com/), public domain.
Files: ne_50m_admin_0_countries, ne_10m_populated_places_simple (geojson from github.com/nvkelso/natural-earth-vector).
Projected by hand with Equal Earth, Antarctica dropped. No map library, no tiles.

Regenerate:

    mkdir -p /tmp/ne && cd /tmp/ne
    B=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
    curl -L -A resistance-observatory-hackathon/0.1 -o countries.geojson $B/ne_50m_admin_0_countries.geojson
    curl -L -A resistance-observatory-hackathon/0.1 -o places.geojson $B/ne_10m_populated_places_simple.geojson
    cd <repo> && node scripts/forecast/build-geo.mjs /tmp/ne/countries.geojson /tmp/ne/places.geojson data/forecast/geo 0.3

The last argument is the point-dropping threshold in map units (default 0.3).
