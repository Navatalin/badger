# BadgeCluster device capability gate

No badge is attached to this cloud workspace. Before enabling networking or
inviting participants, record the firmware version and measured results here.
Follow `hardware/USB_SERIAL.md` for serial and USB Disk Mode operations.

- Verify `os.urandom(16)`, independent random streams across launches, 25-point
  slice duration, 250 samples/minute, and responsive LEFT/RIGHT on both pages.
- Verify BACK/HOME cleanup and re-open: no computation or communication after
  exit. Test both physical orientations and capacitive/physical controls.
- Identify calibrated battery percentage API; compare readings on USB and
  battery. Wire the core policy only after verification: >60% 60 seconds,
  30–60% 120 seconds, <=30% paused, <20% networking disabled. No USB boost.
- Identify Wi-Fi configuration using the existing device settings. Never
  commit credentials. Inspect TLS CA validation, hostname verification, DNS,
  handshake, socket timeouts, and resource cleanup on the actual firmware.
- Implement a cooperative transport state machine only after proving DNS,
  connection, TLS and reads cannot block the renderer. A timeout on a synchronous
  HTTPS request alone does not prove UI responsiveness. No background thread.
- Bound a request to 5 seconds end to end; limit response size and per-frame
  network work. Test AP loss, DNS failure, TLS rejection, delayed/partial
  responses, response loss after acceptance, retries and exit during sync.
- Confirm counters acknowledged by the coordinator match immutable snapshots;
  retain pending snapshots on failure and display cached values as stale.
- Compare idle, connected-idle and Eco compute battery consumption over equal
  intervals with identical brightness; document duration and charge readings.
- Verify icon installation and launcher rendering, following the menu patch
  instructions if stock firmware ignores custom icons.

Simulator/static/host tests are useful but cannot close these hardware gates.

## Hosting decision

User instruction selects Azure App Service instead of the Container Apps example
in spec v0.1. Keep service code, infrastructure and dashboard in a separate repo.
