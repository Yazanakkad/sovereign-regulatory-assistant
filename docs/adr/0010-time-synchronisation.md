# ADR-0010: Time synchronisation on the lab VM

- **Status:** Accepted
- **Date:** 2026-10-26
- **Related:** ADR-0001 (Hyper-V VM), ADR-0009 (logs and journald)

## Context

Correct time is required for JWT validation (`exp`, `nbf`; Stage 2), TLS certificate validity
(Step 16) and correlating logs. On 2026-10-26 the VM clock was wrong for most of a session:

- chrony logged "System clock wrong by 2153 seconds" (36 min slow) after the VM was paused
  with its host, but Ubuntu's default `makestep 1 3` only allows steps during the first three
  updates, so chrony could only slew — a correction that takes hours.
- Linux copied the wrong time into the VM's hardware clock, so the error survived a reboot.
- At boot, Hyper-V Time Synchronization set the VM to the Windows host's time, which was
  189 s fast: the host is domain-joined and had not reached its domain controller
  (`WAK-AD.WAK.local`) for five days. chrony then stepped the clock back 189 s. Two writers
  produced out-of-order journal entries.

## Decision

1. **chrony is the only writer of the VM clock.** Hyper-V Time Synchronization is disabled
   for this VM (`Disable-VMIntegrationService -Name "Time Synchronization"`).
2. **Source:** Ubuntu's default internet NTS servers (authenticated NTP).
3. **Step on any error above 1 s:** drop-in `/etc/chrony/conf.d/10-regassist-makestep.conf`
   with `makestep 1 -1`. `confdir` is read after the stock `makestep 1 3` in `chrony.conf`, so
   the drop-in wins without editing the package's own config file.
4. **The Windows host clock is not reconfigured** — it is managed by the employer's domain.
   `w32tm /resync` is run when the laptop is on the corporate network or VPN.
5. **Code rule:** durations and latencies are measured with a monotonic clock
   (`time.monotonic()`), never wall-clock time.

## Alternatives considered

- **Keep both Hyper-V sync and chrony:** rejected — two writers with different truths.
- **chrony with the Hyper-V PTP clock (`refclock PHC /dev/ptp_hyperv`):** rejected on the
  laptop, because it would import the host's error. It is Microsoft's recommended setup on
  Azure, where the host clock is accurate — use it in Stage 8.
- **Edit `/etc/chrony/chrony.conf` directly:** rejected — a modified package config file
  can stall unattended upgrades of chrony.
- **Default slew-only behaviour:** rejected — a laptop sleep leaves the clock wrong for hours.

## Consequences

- The clock may step, including backwards, at any time; journal entries can occasionally
  appear out of order. Acceptable for a lab VM.
- After a host sleep or VM pause, the clock is correct within about one chrony poll.
- The host clock can still drift while off the corporate network. Kerberos allows 5 minutes
  of skew, so domain logins on the laptop may fail until it resyncs.

## Verification (2026-10-26)

| Check | Result |
|---|---|
| Merged configuration (`chronyd -p`) | `makestep 1 3` then `makestep 1 -1` (last wins) |
| Hyper-V integration service | Time Synchronization `Enabled: False` |
| Drill: clock set back 120 s | "wrong by 120.01 s" → "stepped by 120.01 s" within 15 s |
