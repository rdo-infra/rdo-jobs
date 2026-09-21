#!/usr/bin/env python3
"""Parse timestamped ping output and report packet-loss windows.

Accepted reply formats:

    [2026-09-20 17:39:36.605 UTC]  64 bytes from 192.168.122.21: icmp_seq=2587 ttl=63 time=0.687 ms
    [1726853976.605123] 64 bytes from 192.168.122.21: icmp_seq=2587 ttl=63 time=0.687 ms

The second form is ``ping -D`` (unix epoch), which adoption tests use.

A drop is a gap in icmp_seq. The reported window is:

    after  last successful reply before the gap
    before first successful reply after the gap

That window is what you correlate with other event logs.
"""

from __future__ import annotations

import argparse
import glob as globmod
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, TextIO


REPLY_RE = re.compile(
    r"""
    \[
      (?P<ts>
          \d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?
        | \d+(?:\.\d+)?
      )
      (?:\s+(?P<tz>[A-Za-z/_+-]\S*))?
    \]
    .*
    bytes\ from
    .*
    icmp_seq=(?P<seq>\d+)
    """,
    re.VERBOSE,
)

TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
)
UNIX_TS_RE = re.compile(r"^\d+(?:\.\d+)?$")
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
ANSIBLE_LINE_RE = re.compile(
    r"""
    ^\[
      (?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)
      (?:\s+(?P<tz>[A-Za-z/_+-]\S*))?
    \]\s*
    (?P<rest>.*)$
    """,
    re.VERBOSE,
)
ANSIBLE_BANNER_RE = re.compile(
    r"^(?P<kind>TASK|RUNNING HANDLER|HANDLER|PLAY(?!\s+RECAP))\s+"
    r"\[(?P<name>[^\]]+)\]"
)


@dataclass(frozen=True)
class Reply:
    seq: int
    ts: datetime
    raw_ts: str
    line_no: int


@dataclass(frozen=True)
class DropWindow:
    first_missing: int
    last_missing: int
    after_ts: str | None
    before_ts: str | None
    after_seq: int | None
    before_seq: int | None
    duration_s: float | None
    lost: int
    after_dt: datetime | None = None
    before_dt: datetime | None = None


@dataclass(frozen=True)
class AnsibleEvent:
    kind: str
    name: str
    start: datetime
    end: datetime | None
    line: str


def format_utc(dt: datetime) -> str:
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"


def parse_timestamp(raw: str, tz_name: str | None) -> datetime:
    if UNIX_TS_RE.fullmatch(raw):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)

    for fmt in TS_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"unrecognized timestamp: {raw!r}")

    if tz_name in (None, "UTC", "Z", "GMT"):
        return dt.replace(tzinfo=timezone.utc)
    return dt.replace(tzinfo=timezone.utc)


def iter_replies(stream: TextIO) -> Iterable[Reply]:
    seen: dict[int, Reply] = {}
    for line_no, line in enumerate(stream, start=1):
        match = REPLY_RE.search(line)
        if not match:
            continue
        seq = int(match.group("seq"))
        ts = parse_timestamp(match.group("ts"), match.group("tz"))
        reply = Reply(seq=seq, ts=ts, raw_ts=format_utc(ts), line_no=line_no)
        if seq in seen:
            continue
        seen[seq] = reply
        yield reply


def drop_windows(replies: list[Reply]) -> list[DropWindow]:
    if not replies:
        return []

    ordered = sorted(replies, key=lambda r: r.seq)
    windows: list[DropWindow] = []
    prev = ordered[0]

    for reply in ordered[1:]:
        gap = reply.seq - prev.seq
        if gap > 1:
            lost = gap - 1
            duration = (reply.ts - prev.ts).total_seconds()
            windows.append(
                DropWindow(
                    first_missing=prev.seq + 1,
                    last_missing=reply.seq - 1,
                    after_ts=prev.raw_ts,
                    before_ts=reply.raw_ts,
                    after_seq=prev.seq,
                    before_seq=reply.seq,
                    duration_s=duration,
                    lost=lost,
                    after_dt=prev.ts,
                    before_dt=reply.ts,
                )
            )
        prev = reply

    max_seq = ordered[-1].seq
    min_seq = ordered[0].seq
    expected = set(range(min_seq, max_seq + 1))
    present = {r.seq for r in ordered}
    missing = expected - present
    covered = set()
    for window in windows:
        covered.update(range(window.first_missing, window.last_missing + 1))
    leftover = missing - covered
    if leftover:
        for seq in sorted(leftover):
            windows.append(
                DropWindow(
                    first_missing=seq,
                    last_missing=seq,
                    after_ts=None,
                    before_ts=None,
                    after_seq=None,
                    before_seq=None,
                    duration_s=None,
                    lost=1,
                )
            )
        windows.sort(key=lambda w: w.first_missing)
    return windows


def format_window(window: DropWindow) -> str:
    if window.first_missing == window.last_missing:
        seqs = f"icmp_seq={window.first_missing}"
    else:
        seqs = f"icmp_seq={window.first_missing}-{window.last_missing}"

    after = window.after_ts or "unknown"
    before = window.before_ts or "unknown"
    duration = (
        f"{window.duration_s:.3f}s" if window.duration_s is not None else "unknown"
    )
    return (
        f"{seqs}  lost={window.lost}  "
        f"after={after} (seq={window.after_seq})  "
        f"before={before} (seq={window.before_seq})  "
        f"window={duration}"
    )


def iter_ansible_events(paths: Iterable[str]) -> list[AnsibleEvent]:
    events: list[AnsibleEvent] = []
    play: dict | None = None
    task: dict | None = None

    def close_event(current: dict | None, end: datetime | None) -> None:
        if current is None:
            return
        events.append(
            AnsibleEvent(
                kind=current["kind"],
                name=current["name"],
                start=current["start"],
                end=end,
                line=current["line"],
            )
        )

    def start_event(kind: str, name: str, ts: datetime, rest: str) -> dict:
        return {"kind": kind, "name": name, "start": ts, "line": rest}

    for path in paths:
        play = None
        task = None
        with Path(path).open(encoding="utf-8", errors="replace") as stream:
            for raw in stream:
                line = ANSI_ESCAPE_RE.sub("", raw).strip()
                match = ANSIBLE_LINE_RE.match(line)
                if not match:
                    continue
                ts = parse_timestamp(match.group("ts"), match.group("tz"))
                rest = match.group("rest").strip()
                banner = ANSIBLE_BANNER_RE.match(rest)
                if not banner:
                    continue
                kind = banner.group("kind")
                name = banner.group("name").strip()
                if kind == "PLAY":
                    close_event(task, ts)
                    task = None
                    close_event(play, ts)
                    play = start_event(kind, name, ts, rest)
                else:
                    close_event(task, ts)
                    task = start_event(kind, name, ts, rest)
        close_event(task, None)
        close_event(play, None)
    events.sort(key=lambda event: (event.start, 0 if event.kind == "PLAY" else 1))
    return events


def event_overlaps_window(event: AnsibleEvent, window: DropWindow) -> bool:
    if window.after_dt is None or window.before_dt is None:
        return False
    end = event.end if event.end is not None else window.before_dt
    return event.start < window.before_dt and end > window.after_dt


def format_ansible_event(event: AnsibleEvent, window: DropWindow) -> str:
    started_before = (
        window.after_dt is not None and event.start <= window.after_dt
    )
    suffix = "  (started before window, still running)" if started_before else ""
    return f"    [{format_utc(event.start)}] {event.kind} [{event.name}]{suffix}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find packet-drop timestamps in ping output."
    )
    parser.add_argument(
        "ping_log",
        nargs="?",
        help="Ping log file. Reads stdin when omitted or set to -.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Print CSV instead of human-readable lines.",
    )
    parser.add_argument(
        "--ansible-log",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Ansible log with UTC timestamps (glob allowed). "
            "Repeatable. TASK/PLAY banners overlapping a drop window are listed."
        ),
    )
    return parser.parse_args(argv)


def expand_ansible_logs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        matches = sorted(globmod.glob(pattern))
        if not matches and Path(pattern).is_file():
            matches = [pattern]
        for match in matches:
            if match not in seen:
                seen.add(match)
                paths.append(match)
    return paths


def open_input(path: str | None) -> TextIO:
    if path in (None, "-"):
        return sys.stdin
    return Path(path).open(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with open_input(args.ping_log) as stream:
        replies = list(iter_replies(stream))

    if not replies:
        print("No timestamped ping replies found.", file=sys.stderr)
        return 1

    windows = drop_windows(replies)
    first = min(replies, key=lambda r: r.seq)
    last = max(replies, key=lambda r: r.seq)
    expected = last.seq - first.seq + 1
    received = len({r.seq for r in replies})
    lost = expected - received
    loss_pct = (lost / expected) * 100 if expected else 0.0

    if args.csv:
        print(
            "first_missing,last_missing,lost,after_ts,before_ts,after_seq,before_seq,window_s"
        )
        for window in windows:
            print(
                ",".join(
                    [
                        str(window.first_missing),
                        str(window.last_missing),
                        str(window.lost),
                        window.after_ts or "",
                        window.before_ts or "",
                        "" if window.after_seq is None else str(window.after_seq),
                        "" if window.before_seq is None else str(window.before_seq),
                        "" if window.duration_s is None else f"{window.duration_s:.3f}",
                    ]
                )
            )
        return 0

    print(
        f"Replies: {received} unique seq from {first.seq} to {last.seq} "
        f"(expected {expected}, lost {lost}, {loss_pct:.6f}%)"
    )
    print(f"First reply: {first.raw_ts}  icmp_seq={first.seq}")
    print(f"Last reply:  {last.raw_ts}  icmp_seq={last.seq}")
    print()
    if not windows:
        print("No packet drops detected (icmp_seq is contiguous).")
        return 0

    ansible_paths = expand_ansible_logs(args.ansible_log)
    ansible_events = iter_ansible_events(ansible_paths)
    if args.ansible_log and not ansible_paths:
        print("No Ansible logs matched --ansible-log.", file=sys.stderr)

    print(f"Drop windows: {len(windows)}")
    for window in windows:
        print(format_window(window))
        if not ansible_paths:
            continue
        matching = [
            event for event in ansible_events if event_overlaps_window(event, window)
        ]
        if not matching:
            print("  Ansible tasks in window: (none)")
            continue
        print("  Ansible tasks in window:")
        for event in matching:
            print(format_ansible_event(event, window))
    return 0


if __name__ == "__main__":
    sys.exit(main())
