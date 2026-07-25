# Day 8 — Monitoring & Load Test Notes

## Uptime Monitoring
- Tool: UptimeRobot (free tier)
- Target: backend /health endpoint, exposed temporarily via ngrok for testing
  (ngrok URL: https://joeann-unabetted-unexceptionably.ngrok-free.dev/health)
- Status: confirmed UP

## Issues found and fixed along the way
1. UptimeRobot's free tier only sends HEAD requests, but /health only
   accepted GET — caused every check to fail with 405. Fixed by Intern 2
   updating the route to accept both GET and HEAD.
2. ngrok free-tier tunnels are fragile — die if the terminal closes or
   the session times out. Had to restart the tunnel and re-sync the
   monitor URL multiple times during setup.
3. Monitor's URL was initially pointing at the root path (/) instead of
   /health specifically — fixed via UptimeRobot's API (editMonitor).

## Conclusion
ngrok is a fine stand-in for proving the monitoring pattern works, but
is not reliable for ongoing use. Once Fly.io deployment (Day 9) is live,
this monitor will be repointed at the permanent URL.

## Load Test Results
Tool: Apache Bench (ab)
Command: ab -n 100 -c 10 http://localhost:8000/health

- Complete requests: 100
- Failed requests: 0
- Requests per second: 325.67 [#/sec] (mean)
- Time per request: 30.706 ms (mean)
- Time per request: 3.071 ms (mean, across all concurrent requests)
- Response time range: 15ms min - 57ms max
- 95% of requests served within 51ms

Conclusion: backend handled 10 concurrent users with zero failures and
consistent sub-60ms response times, well within the SRS's ~1-2 second
target for AI prediction responses (this endpoint is much simpler than
the prediction endpoint, so this is a healthy baseline).
