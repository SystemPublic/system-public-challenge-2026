"""One command: fetch anything missing, build verdicts and site data, write the local Underlay collection.

    python -m pipeline.run            # add --push to publish to Underlay (needs UNDERLAY_API_KEY)
"""
import sys

from . import build, data, publish

if __name__ == "__main__":
    data.fetch_all()
    build.main()
    sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a == "--push"]
    publish.main()
