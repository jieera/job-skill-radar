import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from .analysis import ROOT
from .http import Client
from .pipeline import merge
from .sources import ADAPTERS


def collect(source):
    base = {k: source[k] for k in ("id", "name", "market", "url", "scope")}
    base["checked_at"] = datetime.now(timezone.utc).isoformat()
    if source["adapter"] not in ADAPTERS:
        return {**base, "status": "pending", "message": source["reason"], "jobs": []}
    jobs = []
    unavailable = 0
    try:
        for job in ADAPTERS[source["adapter"]](source, Client()):
            if job.get("unavailable"):
                unavailable += 1
                continue
            jobs.append(job)
            if len(jobs) % 25 == 0:
                print(f"{source['id']}: {len(jobs)} details read", flush=True)
        print(f"{source['id']}: complete ({len(jobs)} details)", flush=True)
        return {**base, "status": "partial" if unavailable else "ok",
                "message": f"{unavailable} incomplete source records; valid rows refreshed, no jobs expired" if unavailable else "Complete crawl", "jobs": jobs}
    except Exception as exc:
        # Already parsed records remain usable, but a partial run never expires old jobs.
        message = f"{type(exc).__name__}: {str(exc)[:240]}"
        print(f"{source['id']}: {message}", file=sys.stderr, flush=True)
        return {**base, "status": "partial" if jobs else "error", "message": message, "jobs": jobs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "web/public/data/snapshot.json")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--sources", nargs="+")
    parser.add_argument("--review-output", type=Path, help="Local-only raw descriptions for annotation; do not publish")
    args = parser.parse_args()
    config = json.loads((ROOT / "config/sources.json").read_text())
    if args.sources:
        if set(args.sources) - {s["id"] for s in config}:
            parser.error("Unknown source ID")
        config = [s for s in config if s["id"] in args.sources]
    previous_file = args.previous or args.output
    previous = json.loads(previous_file.read_text()) if previous_file.exists() else {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(collect, config))
    now = datetime.now(timezone.utc).isoformat()
    snapshot = merge(previous, results, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(".tmp")
    temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    temp.replace(args.output)
    if args.review_output:
        args.review_output.parent.mkdir(parents=True, exist_ok=True)
        args.review_output.write_text(json.dumps([j for r in results for j in r["jobs"]], ensure_ascii=False, indent=2))
    print(f"Wrote {len(snapshot['jobs'])} relevant jobs to {args.output}")
    # Snapshot is still usable after source errors; CI publishes status then reports failure.
    return 2 if any(r["status"] in {"error", "partial"} for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
