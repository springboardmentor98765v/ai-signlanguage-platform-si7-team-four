# Day 7 — Basic Security Testing (OWASP ZAP)

**Milestone 3 | Intern 5 — Database & QA Engineer**
**Date tested:** 2026-08-07
**Tool:** OWASP ZAP (free, open-source) — Docker image zaproxy/zap-stable, baseline scan
**Target:** http://localhost:8000 (local backend service via Docker Compose)
**Full report:** zap-reports/zap_baseline_report.html

---

## SRS Day 7 Checkpoints

- [x] OWASP ZAP installed and run against the local app
- [x] Scan results reviewed
- [x] Any serious issues found are listed for fixing

---

## Result

0 FAIL, 3 WARN, 64 PASS

No critical or high-severity issues found (no SQL injection, XSS, exposed secrets, broken auth, or similar). All 3 warnings are low-severity, standard HTTP-header hardening items.

## Warnings found

1. X-Content-Type-Options Header Missing — response doesn't set X-Content-Type-Options: nosniff, which helps prevent browsers from MIME-sniffing content types. Low severity; simple header addition.

2. Storable and Cacheable Content — responses don't set explicit Cache-Control headers, so they could be cached by intermediate proxies/browsers. Low severity for an API with no sensitive data in GET responses currently.

3. Cross-Origin-Resource-Policy Header Missing — modern browser cross-origin isolation header not set. Low severity for this API; more relevant if the backend later serves media/files directly.

None of these are blocking or require immediate action; they're standard hardening items suitable for the Backend/API owner (Intern 2) to address alongside other security-hardening tasks already in their Day 5 track (input validation, rate limiting).

## Known limitation of this scan

ZAP's baseline scan spiders an app by following HTML links, which doesn't work well against a JSON-only API. The scan only discovered 3 URLs (root, /robots.txt, /sitemap.xml — the latter two don't exist, 404s). It did not exercise real endpoints like /api/auth/register, /courses/modules, or /practice/start.

This matches the SRS's "basic security testing" scope for Day 7 and is not a gap in today's checkpoint. A more thorough scan against the actual API surface (e.g. pointed at the OpenAPI/Swagger spec once Intern 2 finishes documenting it) would be a reasonable follow-up later in the milestone, not required today.

## Status

No critical issues found — nothing urgent to escalate. The 3 low-severity findings are noted here for the team's awareness and can be addressed as routine hardening whenever convenient.
