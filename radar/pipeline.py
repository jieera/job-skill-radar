import copy
from .analysis import enrich


def merge(previous, results, now):
    """Only complete crawls increment absence; partial crawls preserve unobserved jobs."""
    old = {j["id"]: copy.deepcopy(j) for j in previous.get("jobs", [])}
    sources = []
    old_sources = {s["id"]: s for s in previous.get("sources", [])}
    for result in results:
        source = {k: v for k, v in result.items() if k != "jobs"}
        last = old_sources.get(source["id"], {})
        source["last_success"] = last.get("last_success")
        if source["status"] in {"ok", "partial"}:
            if source["status"] == "ok":
                source["last_success"] = now
            seen = set()
            for raw in result["jobs"]:
                job = enrich(copy.deepcopy(raw))
                seen.add(job["id"])
                former = old.get(job["id"], {})
                if not job["categories"] or not job["markets"] or job["seniority"] == "experienced":
                    old.pop(job["id"], None)
                    continue
                job.update({"first_seen": former.get("first_seen", now), "last_seen": now,
                    "updated_at": now if former.get("description_hash") != job["description_hash"] else former.get("updated_at", now),
                    "active": True, "missing_runs": 0})
                old[job["id"]] = job
            for job in old.values():
                if source["status"] == "ok" and job["source"] == source["id"] and job["id"] not in seen:
                    job["missing_runs"] = job.get("missing_runs", 0) + 1
                    job["active"] = job["missing_runs"] < 2
        source["job_count"] = sum(j["source"] == source["id"] and j["active"] for j in old.values())
        sources.append(source)
    # Preserve unselected sources during targeted updates.
    selected = {s["id"] for s in sources}
    sources += [s for s in previous.get("sources", []) if s["id"] not in selected]
    return {"schema_version": 1, "generated_at": now, "sources": sources,
            "jobs": sorted(old.values(), key=lambda j: (j["first_seen"], j["id"]), reverse=True)}
