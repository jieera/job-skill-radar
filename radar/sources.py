"""Source-specific adapters. A failed page/detail invalidates the full crawl."""
import json
import re
from urllib.parse import urlencode
from .analysis import markets
from .http import SourceError


def pages(fetch, rows_key, total_key, identity, page_size=20, start=0, offset=True):
    """Reject premature empty/repeated pages; Workday omits total after page 1."""
    seen = set()
    target = None
    page = start
    for _ in range(250):
        data = fetch(page, page_size)
        rows = data[rows_key]
        if target is None:
            target = int(data[total_key])
            if target < 0:
                raise SourceError("Invalid source total")
        if not isinstance(rows, list):
            raise SourceError("Unexpected list response")
        if not rows:
            if len(seen) < target:
                raise SourceError("Pagination ended before advertised total")
            return
        fresh = [r for r in rows if str(r[identity]) not in seen]
        if not fresh:
            raise SourceError("Repeated pagination page")
        for row in fresh:
            seen.add(str(row[identity]))
            yield row
        if len(seen) >= target:
            return
        page += len(rows) if offset else 1
    raise SourceError("Pagination safety limit reached; crawl incomplete")


def workday(source, client):
    api = source["api"]
    def fetch(offset, limit):
        data = client.json(api + "/jobs", {"appliedFacets": source["facets"],
                           "limit": limit, "offset": offset, "searchText": ""})
        for row in data["jobPostings"]:
            row["identity"] = row.get("externalPath") or str(row.get("bulletFields"))
        return data
    for row in pages(fetch, "jobPostings", "total", "identity"):
        if not row.get("externalPath"):
            yield {"unavailable": True, "reason": "Workday returned a job ID without a title or detail URL"}
            continue
        # Multi-location rows require detail lookup to resolve the country.
        location = row.get("locationsText", "")
        if not markets(location) and not re.search(r"\d+ Locations", location):
            continue
        info = client.json(api + row["externalPath"])["jobPostingInfo"]
        locations = [info.get("location") or location, *(info.get("additionalLocations") or [])]
        yield {"id": "nvidia:" + info.get("jobReqId", info["id"]), "source": source["id"],
               "company": source["name"], "title": info["title"], "location": " · ".join(locations),
               "url": source["url"] + row["externalPath"], "posted_at": info.get("startDate"),
               "level_hint": info.get("workerSubType", ""), "description": info["jobDescription"]}


def apple_state(html):
    match = re.search(r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\((".*?")\);', html)
    if not match:
        raise SourceError("Apple page no longer exposes expected server-rendered data")
    return json.loads(json.loads(match.group(1)))["loaderData"]


def apple(source, client):
    def fetch(page, limit):
        return apple_state(client.text(source["url"] + "&page=" + str(page)))["search"]
    for row in pages(fetch, "searchResults", "totalRecords", "id", start=1, offset=False):
        url = "https://jobs.apple.com/en-us/details/" + row["positionId"] + "/" + row["transformedPostingTitle"]
        info = apple_state(client.text(url))["jobDetails"]["jobsData"]
        details = info.get("localizations", {}).get("en_US", {}).get("posting", info)
        description = "\n".join(["Job description", details.get("jobSummary", ""),
            details.get("description", ""), "Minimum qualifications",
            details.get("minimumQualifications", ""), details.get("keyQualifications", ""),
            "Preferred qualifications", details.get("preferredQualifications", "")])
        if not details.get("description"):
            raise SourceError("Missing Apple job description")
        yield {"id": "apple:" + row["positionId"], "source": source["id"],
               "company": source["name"], "title": info["postingTitle"], "url": url,
               "location": " · ".join(dict.fromkeys(
                   f"{loc.get('name', '')}, {loc.get('countryName', '')}" for loc in info["locations"])),
               "posted_at": info.get("postingDateMeta"), "level_hint": "intern",
               "description": description}


def tencent(source, client):
    def fetch(page, limit):
        result = client.json(source["url"] + "/api/v1/position/searchPosition",
                             {"keyword": "", "pageIndex": page, "pageSize": limit})
        if result.get("status") != 0:
            raise SourceError("Tencent search returned a non-success status")
        return result["data"]
    for row in pages(fetch, "positionList", "count", "postId", page_size=100, start=1, offset=False):
        if row.get("positionFamily") != 2 or not markets(row.get("workCities", "")):
            continue
        result = client.json(source["url"] + "/api/v1/jobDetails/getJobDetailsByPostId?" +
                             urlencode({"postId": row["postId"]}))
        if result.get("status") != 0 or not result.get("data"):
            raise SourceError("Tencent detail unavailable")
        info = result["data"]
        if not info.get("request"):
            raise SourceError("Missing Tencent requirements")
        yield {"id": "tencent:" + str(row["postId"]), "source": source["id"],
               "company": source["name"], "title": info["title"],
               "location": " · ".join(info.get("workCityList") or []) or row["workCities"],
               "url": source["url"] + "/jobdesc.html?" + urlencode({"postId": row["postId"]}),
               "posted_at": None, "level_hint": row.get("recruitLabelName", row.get("projectName", "")),
               "description": "岗位职责\n" + info.get("desc", "") + "\n任职要求\n" + info["request"]}


ADAPTERS = {"workday": workday, "apple": apple, "tencent": tencent}
