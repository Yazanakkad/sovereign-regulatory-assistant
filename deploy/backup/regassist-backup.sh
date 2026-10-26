#!/bin/bash
# regassist-backup: archive the service's state (data + config), verify it, keep the newest N.
# Installed as a root-owned copy at /usr/local/sbin/regassist-backup (see ADR-0011).
# Exit codes (contract): 0 ok · 1 backup failed · 2 bad configuration · 3 another run holds the lock.
# An unexpected failure (e.g. tar's own exit 2) is reported as 1; its original code is logged.
set -euo pipefail
umask 077

readonly BACKUP_DIR="${REGASSIST_BACKUP_DIR:-/var/backups/regassist}"
readonly KEEP="${REGASSIST_BACKUP_KEEP:-7}"
readonly SOURCE_ROOT="${REGASSIST_BACKUP_SOURCE_ROOT:-/}"
readonly SOURCES=(srv/regassist/data etc/regassist)
readonly PREFIX="regassist-"
readonly SUFFIX=".tar.gz"

tmp_archive=""
tmp_sum=""
exit_code=""      # set only by fail(): a deliberate exit with a contract code
failed_line=""    # set by the ERR trap: where an unexpected failure happened
failed_command=""

log() {
    # log <syslog priority 0-7> <logfmt message>; journald reads the <N> prefix.
    local priority=$1
    shift
    if [[ -n ${JOURNAL_STREAM:-} ]]; then
        printf '<%s>%s\n' "$priority" "$*" >&2
    else
        printf '%s\n' "$*" >&2
    fi
}

fail() {
    # fail <contract exit code> <logfmt message>
    exit_code=$1
    shift
    log 3 "$*"
    exit "$exit_code"
}

finish() {
    local rc=$?
    if [[ -n $tmp_archive && -e $tmp_archive ]]; then rm -f -- "$tmp_archive"; fi
    if [[ -n $tmp_sum && -e $tmp_sum ]]; then rm -f -- "$tmp_sum"; fi
    if ((rc == 0)); then return; fi
    if [[ -n $exit_code ]]; then
        log 3 "event=backup_failed exit=${rc}"
        return
    fi
    log 3 "event=backup_failed exit=1 cause_exit=${rc} line=${failed_line} command=\"${failed_command//\"/\\\"}\""
    exit 1
}
trap 'failed_line=$LINENO; failed_command=$BASH_COMMAND' ERR
trap finish EXIT

# --- configuration ---------------------------------------------------------
[[ $KEEP =~ ^[1-9][0-9]*$ ]] || fail 2 "event=config_error reason=\"REGASSIST_BACKUP_KEEP must be a positive integer, got '${KEEP}'\""
[[ -d $BACKUP_DIR ]] || fail 2 "event=config_error reason=\"backup directory ${BACKUP_DIR} does not exist\""
[[ -d $SOURCE_ROOT ]] || fail 2 "event=config_error reason=\"source root ${SOURCE_ROOT} does not exist\""

for src in "${SOURCES[@]}"; do
    [[ -e ${SOURCE_ROOT%/}/${src} ]] || fail 1 "event=source_missing path=${SOURCE_ROOT%/}/${src}"
done

# --- one run at a time -----------------------------------------------------
exec 9>"${BACKUP_DIR}/.lock"
flock --nonblock 9 || fail 3 "event=backup_skipped reason=\"another run holds the lock\""

# --- create, verify, publish -------------------------------------------------
started=$SECONDS
name="${PREFIX}$(date -u +%Y%m%dT%H%M%SZ)${SUFFIX}"
final="${BACKUP_DIR}/${name}"
[[ ! -e $final ]] || fail 1 "event=archive_exists archive=${name}"

log 6 "event=backup_started archive=${name} sources=$(IFS=,; printf '%s' "${SOURCES[*]}")"
tmp_archive=$(mktemp "${BACKUP_DIR}/.incoming.XXXXXX")
tar --create --gzip --file "$tmp_archive" --directory "$SOURCE_ROOT" "${SOURCES[@]}"
tar --list --gzip --file "$tmp_archive" >/dev/null # reads the whole stream: catches truncation/corruption

digest=$(sha256sum -- "$tmp_archive" | cut -d' ' -f1)
tmp_sum=$(mktemp "${BACKUP_DIR}/.incoming.XXXXXX")
printf '%s  %s\n' "$digest" "$name" >"$tmp_sum"

mv -- "$tmp_archive" "$final"
tmp_archive=""
mv -- "$tmp_sum" "${final}.sha256"
tmp_sum=""
sync -- "$final" "${final}.sha256" "$BACKUP_DIR"

log 6 "event=backup_done archive=${name} bytes=$(stat -c %s -- "$final") sha256=${digest} seconds=$((SECONDS - started))"

# --- retention: only after success; never prune the archive just written -----
mapfile -t others < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "${PREFIX}*${SUFFIX}" ! -name "$name" -printf '%f\n' | sort -r)
for old in "${others[@]:KEEP-1}"; do
    rm -f -- "${BACKUP_DIR}/${old}" "${BACKUP_DIR}/${old}.sha256"
    log 6 "event=backup_pruned archive=${old}"
done
log 6 "event=retention_done keep=${KEEP}"
