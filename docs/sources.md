# Source verification

Verified on 2026-10-06 UTC from the development environment. A verified entry page is not proof of a working collector.

| Company | Entry and method | Observed status | Collection scope |
| --- | --- | --- | --- |
| NVIDIA | [Workday](https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite), public CXS POST list / GET details | Pagination and details readable; some list records contain only a requisition ID | Intern / New College Graduate facets, US and China locations |
| Apple | [Internships](https://jobs.apple.com/en-us/search?location=united-states-USA&team=internships-STDNT-INTRN), server-rendered router data | First and second list pages and detail fields verified | US internship team; not all Apple graduate jobs |
| Tencent | [Campus careers](https://join.qq.com), published `/api/v1/position/searchPosition` and job-details endpoint | Pagination and detail requirements readable | Technical job family from campus campaigns |
| Microsoft | [Students](https://careers.microsoft.com/v2/global/en/students) | Entry page readable; current job-system adapter pending | Not collected |
| ByteDance | [Campus jobs](https://jobs.bytedance.com/campus/position) | Entry page readable; tested search endpoint returned HTTP 405 | Not collected |
| Huawei | [Campus careers](https://career.huawei.com/cn/campus-recruitment) | Entry page and search assets readable; dynamic job API not validated | Not collected |

Collectors do not sign in, solve CAPTCHAs or submit applications. Requests use verified TLS, timeouts, retries and per-source pacing. Pagination has duplicate/early-empty detection and a safety bound. A hard failure or incomplete crawl is exposed in the snapshot, not hidden as an empty healthy source.

No browser dependency is needed for the three connected adapters. A Playwright adapter remains future work for a dynamic source only after its public list, pagination and detail behavior can be verified. Adding a company means adding an adapter, fixture tests, source configuration and a documented scope; marking an untested URL as connected is not sufficient.
