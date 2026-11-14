"""Paths and pinned versions. Every input is pinned: the pipeline refuses to run on a different version."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT / ".env")

DATA_DIR = Path(os.environ.get("DATA_DIR") or (PROJECT.parent / "data")).expanduser().resolve()
GRAPH_PARQUET = DATA_DIR / "graph_parquet"
GRAPH_RAW = DATA_DIR / "raw" / "graph"
UNDERLAY_RAW = DATA_DIR / "raw" / "underlay"
CACHE_DB = DATA_DIR / "cache" / "ground_truth.duckdb"

WEB_DATA = PROJECT / "web" / "data"
OUT = PROJECT / "out"

UNDERLAY_API = "https://www.underlay.org/api"
UNDERLAY_WEB = "https://www.underlay.org"

# alias -> (owner/slug, semver, expected version id)
COLLECTIONS = {
    "eh": ("nyc/environment-health", "v1.0.0",
           "ulv3:cd96b9507b2f4e362ac4d7dbbf40a8c00ef01cc7787bb7d5d7758951e3c2352e"),
    "geo": ("nyc/geographies", "v1.0.0",
            "ulv3:5406699a873a2f9ec89abbfa691a631c6876b1826eed5605709e31d66ca0950c"),
    "trees": ("nyc/street-trees", "v1.0.0",
              "ulv3:7cd6d86ebcfbe1d514139bf8d6650885ec34c82816d6bfdb742aab5d0bb0477d"),
    "complaints": ("nyc/heat-complaints", "v1.0.0",
                   "ulv3:4ce37f3ea3f54c5e0fb80267ef04026d6da61b324d851aee92aa6311c8312f48"),
    "weather": ("noaa/nyc-daily-weather", "v1.0.0",
                "ulv3:4ff0c069903f66a9d1de596658d54745f1487ad74c5178b6a1213dcd18ede656"),
}
# The graph is read from the Dataverse release; Underlay's copy has identical record ids, so we cite it.
GRAPH = ("system/public-graph", "v1.0.0",
         "ulv3:cf73c4f9d7452909fa2b796791feac01a99de09eeb21b277744b0e5e96f272e0")

DATAVERSE_DOI = "doi:10.7910/DVN/7V6JDO"
DATAVERSE_FILES = {  # Dataverse file id, filename, md5, parquet name
    14061020: ("system-public-graph-v1-associations.csv", "c884dd1132957f69ffea45404f29db61", "associations"),
    14061025: ("system-public-graph-v1-relationships.csv", "f955dc9dd9f41cb4fcf95a9a14373d4c", "relationships"),
    14061021: ("system-public-graph-v1-concepts.tab", "c902b288797545dcc801edd3a55a4f0d", "concepts"),
    14061022: ("system-public-graph-v1-studies.tab", "558e7529ee5545c7504bf412288694cc", "studies"),
    14061023: ("system-public-graph-v1-variables.tab", "aacff399861e8d5374308f34a21c1e6b", "variables"),
}
GRAPH_CITATION = ("System, Inc. (2026). System Public Graph (Version 2.1) [Data set]. "
                  "Harvard Dataverse. https://doi.org/10.7910/DVN/7V6JDO")

# Where we publish our own claims
CLAIMS_OWNER = os.environ.get("CLAIMS_OWNER", "system-community")
CLAIMS_SLUG = os.environ.get("CLAIMS_SLUG", "ground-truth-heat")

# Statistics: false discovery rate across all city tests, bootstrap draws
FDR = 0.10
BOOTSTRAP = 2000
SEED = 7
