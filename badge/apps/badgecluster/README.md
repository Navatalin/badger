# BadgeCluster

BadgeCluster lends small bursts of badge processing power to a shared estimate of pi.

This build runs offline on Universe 2026 and supports an opt-in host test against the live Azure service.
Open BadgeCluster from the menu. RIGHT opens Stats, LEFT returns to Mona,
and BACK/HOME exits. Both pages share one worker. No extra hardware or Wi-Fi
configuration is needed. The physical app makes **no network requests** until
a device-verified transport adapter is implemented.

The worker schedules 250 Monte Carlo samples every 60 seconds, at most 25
samples and a target 5 ms per frame. Missed intervals never accumulate.
On a physical badge, accepted samples remain zero and pending samples are local
only. In host test mode, the same app renders real acknowledgements, global
values, connectivity and staleness from Azure.
Closing the app stops the worker. Counters live in RAM and reset on launch;
there are no flash writes, LEDs, background threads, or hardware identifiers.
A per-launch random seed comes from `os.urandom`; verify this on the badge.

Battery percentage is intentionally omitted pending device calibration.
Eco mode is used regardless of USB power. The core has a tested battery policy
hook, but it is not connected to unverified firmware telemetry.

`cluster_core.py` also implements immutable cumulative contribution snapshots,
acknowledgement validation, stale status, and capped 30/60/120/300-second retry
backoff for the next integration milestone. The session controller drives an adapter through nonblocking start/poll/cancel
calls with a five-second deadline. The physical adapter defaults to disabled;
the host test adapter performs HTTPS in disposable host subprocesses.
The separate [BadgeCluster repository](https://github.com/dylan-mccarthy/BadgeCluster)
contains the Azure App Service coordinator. The supplied spec and development handoff are under `docs/badgecluster/`
at the repository root.

## Live Azure test mode

From the repository root, install the host test dependency:

```sh
python -m pip install -r tools/requirements-badgecluster.txt
```

Then run:

```sh
python tools/test_badgecluster_azure.py --live --output /tmp/badgecluster-azure-test
```

This runs the **actual app code under CPython with a Pillow graphics adapter**
and real HTTPS to the live Azure coordinator. It is not a MicroPython or
hardware simulator. It contributes 250 genuinely computed samples with random
pseudonymous IDs, drops the first acknowledgement, retries the identical
snapshot, checks accepted-vs-pending counters and page navigation while HTTPS
is in flight, and verifies exit stops further work. Time is accelerated only
for scheduling, not sample computation. It writes screenshots and a JSON report.
Omit `--live` and the command refuses to submit anything. These host test samples
are included in the shared Azure totals. `--base-url` can select another HTTPS
coordinator. Do not use the host adapter on a physical badge.

The Azure test passed with 250 accepted samples and unchanged global totals
across the duplicate request. The UI serviced 198 frames during the two HTTPS
operations. See `docs/badgecluster/azure-testing.md` for the test scope and limits.

## Validation and next milestone

Run `python -m unittest discover -s tests -p 'test_badgecluster*.py'` and
`python .github/skills/hyb26-skill/scripts/validate_app.py badge/apps/badgecluster`.
See `docs/badgecluster/device-spike.md` for the remaining real-device checks.
Host-rendered previews below use a graphics test adapter, not real firmware.

![Mona screen](assets/preview_mona.png)
![Statistics screen](assets/preview_stats.png)

Artwork is original geometric pixel art created for this project, under the
repository's MIT license. The energy sphere is illustrative, not telemetry.
