// Written by tools/strip_from_diff.py. Do not edit by hand.
const COMICS_GENERATED = {
 "metas": [
  {
   "owner": "system-community",
   "slug": "nyc-concordance-claims",
   "from": "v1.0.0",
   "to": "v1.1.0",
   "from_hash": "ulv3:39269fcb2e3c3ab88a3d15cf7a2c45492165a4b3091d4fd57c47adfc3ec41143",
   "to_hash": "ulv3:9d878b52aa00865390e446de212c2720b6f245ac83e2a66b40be4edecd73fef2",
   "added": 9,
   "updated": 0,
   "removed": 0,
   "compare": "https://www.underlay.org/system-community/nyc-concordance-claims/versions/compare?from=v1.0.0&to=v1.1.0"
  },
  {
   "owner": "system-community",
   "slug": "nyc-concordance-claims",
   "from": "v1.1.0",
   "to": "v1.2.0",
   "from_hash": "ulv3:9d878b52aa00865390e446de212c2720b6f245ac83e2a66b40be4edecd73fef2",
   "to_hash": "ulv3:e7a37134d08b94bb9bbb7363fe73f97da383422abebb20bd617430acbd7bc792",
   "added": 3,
   "updated": 0,
   "removed": 0,
   "compare": "https://www.underlay.org/system-community/nyc-concordance-claims/versions/compare?from=v1.1.0&to=v1.2.0"
  }
 ],
 "strips": [
  {
   "id": "diff-heat-inside-outside-2006",
   "generated": true,
   "pair": "v1.0.0..v1.1.0",
   "title": "Generated from the Underlay: daily temperature and shootings, v1.0.0 to v1.1.0",
   "lede": "Drawn by tools/strip_from_diff.py from the difference between two versions of system-community/nyc-concordance-claims: 9 records added, 0 updated, 0 removed. Numbers, verdicts and the revision reason are read from the records; only the two variable names are supplied by hand. The same difference on the Underlay: https://www.underlay.org/system-community/nyc-concordance-claims/versions/compare?from=v1.0.0&to=v1.1.0",
   "sources": [
    {
     "text": "Outcome heat-shootings in system-community/nyc-concordance-claims v1.0.0.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.0.0/records/Outcome/heat-shootings",
     "link": "record"
    },
    {
     "text": "Outcome heat-inside-outside-2006 in v1.1.0, added in this difference. Registration sha256 7e134210eb08.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.1.0/records/Outcome/heat-inside-outside-2006",
     "link": "record"
    },
    {
     "text": "Revision heat-inside-outside-2006/r1 in v1.1.0: critique/referee_2026-11-14_moon_inside.md.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.1.0/records/Revision/heat-inside-outside-2006%2Fr1",
     "link": "record"
    }
   ],
   "frames": [
    {
     "head": "Version 1.0.0",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 120
      },
      {
       "id": "B",
       "label": "shootings",
       "x": 326,
       "y": 120
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.15",
       "refs": [
        1
       ],
       "lo": -14
      }
     ],
     "cap": "Version 1.0.0 of the collection holds 275 records. On this edge it has claim heat-shootings: 1.15 (1.13 to 1.16), confirmed."
    },
    {
     "head": "Version 1.1.0 adds",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 96
      },
      {
       "id": "B",
       "label": "shootings",
       "x": 326,
       "y": 96
      },
      {
       "id": "M",
       "label": "inside,\nnot outside",
       "x": 198,
       "y": 236,
       "state": "new"
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.15",
       "lo": -14
      }
     ],
     "mods": [
      {
       "from": "M",
       "onto": "ab",
       "ev": "obs",
       "w": 2,
       "state": "new",
       "city": true,
       "label": "×0.86",
       "refs": [
        2
       ],
       "lx": 40,
       "ly": 0
      }
     ],
     "cap": "Version 1.1.0 adds claim heat-inside-outside-2006, registered on 2026-11-14 and scored confirmed: 0.86 (0.83 to 0.90). Claim heat-inside-outside repeats it on another window: 0.86 (0.79 to 0.94)."
    },
    {
     "head": "A revision",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 96
      },
      {
       "id": "B",
       "label": "shootings",
       "x": 326,
       "y": 96
      },
      {
       "id": "M",
       "label": "inside,\nnot outside",
       "x": 198,
       "y": 236
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.15",
       "lo": -14
      }
     ],
     "mods": [
      {
       "from": "M",
       "onto": "ab",
       "ev": "obs",
       "w": 2,
       "state": "kept",
       "city": true,
       "label": "×0.86",
       "refs": [
        2
       ],
       "lx": 40,
       "ly": 0
      }
     ],
     "cap": "The same version holds a revision record. <b>Referee found the registered standard error too small and the mechanism sentence too strong; verdict unchanged.</b>",
     "texts": [
      {
       "text": "interval 0.84 to 0.88, now 0.83 to 0.90",
       "x": 198,
       "y": 277,
       "state": "new",
       "size": 12.5,
       "refs": [
        3
       ]
      }
     ]
    }
   ]
  },
  {
   "id": "diff-moon-full-emergencies",
   "generated": true,
   "pair": "v1.0.0..v1.1.0",
   "title": "Generated from the Underlay: full moon and injury crashes, v1.0.0 to v1.1.0",
   "lede": "Drawn by tools/strip_from_diff.py from the difference between two versions of system-community/nyc-concordance-claims: 9 records added, 0 updated, 0 removed. Numbers, verdicts and the revision reason are read from the records; only the two variable names are supplied by hand. The same difference on the Underlay: https://www.underlay.org/system-community/nyc-concordance-claims/versions/compare?from=v1.0.0&to=v1.1.0",
   "sources": [
    {
     "text": "system-community/nyc-concordance-claims v1.0.0, 275 records.",
     "href": "https://www.underlay.org/system-community/nyc-concordance-claims/versions",
     "link": "versions"
    },
    {
     "text": "Outcome moon-full-emergencies in v1.1.0, added in this difference. Registration sha256 e9097b4a39e7.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.1.0/records/Outcome/moon-full-emergencies",
     "link": "record"
    },
    {
     "text": "Revision moon-full-emergencies/r1 in v1.1.0: critique/referee_2026-11-14_moon_inside.md.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.1.0/records/Revision/moon-full-emergencies%2Fr1",
     "link": "record"
    }
   ],
   "frames": [
    {
     "head": "Version 1.0.0",
     "nodes": [
      {
       "id": "A",
       "label": "full\nmoon",
       "x": 70,
       "y": 150
      },
      {
       "id": "B",
       "label": "injury\ncrashes",
       "x": 326,
       "y": 150
      }
     ],
     "edges": [],
     "texts": [
      {
       "text": "no record\non this edge",
       "x": 198,
       "y": 150,
       "size": 13
      }
     ],
     "cap": "Version 1.0.0 of the collection holds 275 records. It has no claim on this edge."
    },
    {
     "head": "Version 1.1.0 adds",
     "nodes": [
      {
       "id": "A",
       "label": "full\nmoon",
       "x": 70,
       "y": 150
      },
      {
       "id": "B",
       "label": "injury\ncrashes",
       "x": 326,
       "y": 150
      }
     ],
     "edges": [
      {
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "state": "new",
       "city": true,
       "label": "×1.00",
       "refs": [
        2
       ],
       "lo": -14,
       "labelT": 0.36,
       "mark": "0",
       "markT": 0.7
      }
     ],
     "cap": "Version 1.1.0 adds claim moon-full-emergencies, registered on 2026-11-14 and scored confirmed: 1.00 (0.99 to 1.02)."
    },
    {
     "head": "A revision",
     "nodes": [
      {
       "id": "A",
       "label": "full\nmoon",
       "x": 70,
       "y": 150
      },
      {
       "id": "B",
       "label": "injury\ncrashes",
       "x": 326,
       "y": 150
      }
     ],
     "edges": [
      {
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "state": "kept",
       "city": true,
       "label": "×1.00",
       "refs": [
        2
       ],
       "lo": -14,
       "labelT": 0.36,
       "mark": "0",
       "markT": 0.7
      }
     ],
     "cap": "The same version holds a revision record. <b>Referee corrected the comparison with the Japanese crash finding and raised rule 11; verdict unchanged.</b>"
    }
   ]
  },
  {
   "id": "diff-transfer-chicago-inside-outside",
   "generated": true,
   "pair": "v1.1.0..v1.2.0",
   "title": "Generated from the Underlay: daily temperature and shootings in Chicago, v1.1.0 to v1.2.0 (Chicago)",
   "lede": "Drawn by tools/strip_from_diff.py from the difference between two versions of system-community/nyc-concordance-claims: 3 records added, 0 updated, 0 removed. Numbers, verdicts and the revision reason are read from the records; only the two variable names are supplied by hand. The same difference on the Underlay: https://www.underlay.org/system-community/nyc-concordance-claims/versions/compare?from=v1.1.0&to=v1.2.0",
   "sources": [
    {
     "text": "Outcome transfer-chicago-heat-shootings in system-community/nyc-concordance-claims v1.1.0.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.1.0/records/Outcome/transfer-chicago-heat-shootings",
     "link": "record"
    },
    {
     "text": "Outcome transfer-chicago-inside-outside in v1.2.0, added in this difference. Registration sha256 dcf2869a78e6.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.2.0/records/Outcome/transfer-chicago-inside-outside",
     "link": "record"
    },
    {
     "text": "Revision transfer-chicago-inside-outside/r1 in v1.2.0: critique/referee_2026-11-14_chicago_inside.md.",
     "href": "https://www.underlay.org/api/collections/system-community/nyc-concordance-claims/versions/v1.2.0/records/Revision/transfer-chicago-inside-outside%2Fr1",
     "link": "record"
    }
   ],
   "frames": [
    {
     "head": "Version 1.1.0",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 120
      },
      {
       "id": "B",
       "label": "shootings\nin Chicago",
       "x": 326,
       "y": 120
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.13",
       "refs": [
        1
       ],
       "lo": -14
      }
     ],
     "cap": "Version 1.1.0 of the collection holds 284 records. On this edge it has claim transfer-chicago-heat-shootings: 1.13 (1.12 to 1.14), confirmed."
    },
    {
     "head": "Version 1.2.0 adds",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 96
      },
      {
       "id": "B",
       "label": "shootings\nin Chicago",
       "x": 326,
       "y": 96
      },
      {
       "id": "M",
       "label": "inside,\nnot outside",
       "x": 198,
       "y": 236,
       "state": "new"
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.13",
       "lo": -14
      }
     ],
     "mods": [
      {
       "from": "M",
       "onto": "ab",
       "ev": "obs",
       "w": 2,
       "state": "new",
       "city": true,
       "label": "×0.97",
       "refs": [
        2
       ],
       "lx": 40,
       "ly": 0
      }
     ],
     "cap": "Version 1.2.0 adds claim transfer-chicago-inside-outside, registered on 2026-11-14 and scored confirmed: 0.97 (0.94 to 0.99). In New York, claim heat-inside-outside-2006 gave 0.86 (0.83 to 0.90)."
    },
    {
     "head": "A revision",
     "nodes": [
      {
       "id": "A",
       "label": "daily\ntemperature",
       "x": 70,
       "y": 96
      },
      {
       "id": "B",
       "label": "shootings\nin Chicago",
       "x": 326,
       "y": 96
      },
      {
       "id": "M",
       "label": "inside,\nnot outside",
       "x": 198,
       "y": 236
      }
     ],
     "edges": [
      {
       "id": "ab",
       "a": "A",
       "b": "B",
       "ev": "obs",
       "w": 3,
       "city": true,
       "label": "×1.13",
       "lo": -14
      }
     ],
     "mods": [
      {
       "from": "M",
       "onto": "ab",
       "ev": "obs",
       "w": 2,
       "state": "kept",
       "city": true,
       "label": "×0.97",
       "refs": [
        2
       ],
       "lx": 40,
       "ly": 0
      }
     ],
     "cap": "The same version holds a revision record. <b>Referee corrected the interval (a statsmodels scale error) and counted 37% of inside incidents as ambiguously classed; verdict unchanged.</b>",
     "texts": [
      {
       "text": "interval 0.942 to 0.995, now 0.943 to 0.994",
       "x": 198,
       "y": 277,
       "state": "new",
       "size": 12.5,
       "refs": [
        3
       ]
      }
     ]
    }
   ]
  }
 ]
};
if (typeof COMICS !== 'undefined') COMICS.strips.push(...COMICS_GENERATED.strips);
