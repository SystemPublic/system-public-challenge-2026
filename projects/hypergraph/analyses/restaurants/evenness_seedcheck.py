"""Rule 9 check for restaurants-nta-harshness: the permutation p with 100,000 draws and four other
seeds. Reuses evenness_test.py unchanged except for NDRAW and SEED; writes evenness_seedcheck.json."""
import json
import evenness_test as e
import common as c

out = []
for seed, n in ((20261113, 100_000), (1, 10_000), (2, 10_000), (3, 10_000), (4, 10_000)):
    e.NDRAW, e.SEED = n, seed
    c.write_json, saved = (lambda *a, **k: None), c.write_json
    e.pd.DataFrame.to_csv, saved_csv = (lambda *a, **k: None), e.pd.DataFrame.to_csv
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e.main()
    c.write_json, e.pd.DataFrame.to_csv = saved, saved_csv
    r = json.loads(buf.getvalue())
    out.append({"seed": seed, "draws": n, "harshness_p": r["harshness"]["p"], "frequency_p": r["frequency"]["p"]})
    print(out[-1], flush=True)
c.write_json("evenness_seedcheck.json", out)
