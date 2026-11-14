"""Corridor definitions for the pedestrian-injury check (fixed before any post-October-2019 crash is read).

Each corridor is a crosstown street between Ninth and Third Avenues, given by the coordinates of its two
end intersections. A crash belongs to a corridor when its
location is within BUF metres of the segment, measured perpendicular to the street, and its projection
falls on the segment (with 20 m extension at each end, to include the end intersections).
Crashes are NYPD Motor Vehicle Collisions (h9gi-nx95) with at least one pedestrian injured or killed.
"""
from __future__ import annotations

import numpy as np

CORRIDORS = {
    # End points: median location of geocoded crashes recorded at the 9th Avenue and 3rd Avenue
    # intersections of each street before October 2019.
    "14th": ((40.74094, -74.00537), (40.73329, -73.98718)),
    "23rd": ((40.74649, -74.00132), (40.73883, -73.98315)),
    "34th": ((40.75339, -73.99630), (40.74573, -73.97812)),
    "42nd": ((40.75843, -73.99263), (40.75077, -73.97444)),
    "57th": ((40.76792, -73.98571), (40.76022, -73.96746)),
}
TREATED = "14th"
BUF = 30.0
EXT = 20.0
BBOX = (40.728, 40.772, -74.010, -73.963)


def assign(lat, lon):
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    out = np.full(lat.shape, None, dtype=object)
    for name, ((a_lat, a_lon), (b_lat, b_lon)) in CORRIDORS.items():
        ky = 111_000.0
        kx = 111_000.0 * np.cos(np.radians(40.75))
        ax, ay, bx, by = a_lon * kx, a_lat * ky, b_lon * kx, b_lat * ky
        px, py = lon * kx, lat * ky
        dx, dy = bx - ax, by - ay
        L = np.hypot(dx, dy)
        t = ((px - ax) * dx + (py - ay) * dy) / L
        d = np.abs((px - ax) * dy - (py - ay) * dx) / L
        hit = (d <= BUF) & (t >= -EXT) & (t <= L + EXT)
        out[hit & (out == None)] = name  # noqa: E711
    return out
