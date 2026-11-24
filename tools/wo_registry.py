#!/usr/bin/env python3
"""Decentralized Work-Order Validator and Deterministic Register Rebuilder.

Stdlib-only CLI implementing Operating Protocol v4 (`CONTROL/protocol_v4.md`):
- Partitioned ID lanes (`git-1`, `aistudio`, `git-2`, `reserve`)
- Structured per-WO metadata validation (`<!-- WO_META_START --> ... <!-- WO_META_END -->`)
- Canonical target-scope locking and overlap detection
- Dependency unblocking (`BLOCKED` -> `READY` when prerequisites are `CLOSED`)
- Soft lease expiry flagging (`CLAIMED` age > `lease_hours`)
- Deterministic regeneration of `CONTROL/WO_LIVE_INDEX.md` and fenced
  dashboard injection into `CONTROL/active_work_orders.md`
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import pathlib
import re
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONTROL_DIR = ROOT_DIR / "CONTROL"
DEFAULT_PINS_PATH = DEFAULT_CONTROL_DIR / "registry_pins.json"

META_RE = re.compile(
    r"<!--\s*WO_META_START\s*-->\s*(.*?)\s*<!--\s*WO_META_END\s*-->",
    re.DOTALL,
)
AUTO_BLOCK_START = "<!-- WO_AUTO_DASHBOARD_START -->"
AUTO_BLOCK_END = "<!-- WO_AUTO_DASHBOARD_END -->"

WO_FILE_RE = re.compile(r"^WO(\d+)\.md$")
WO_ID_RE = re.compile(r"^WO(\d+)$")
TITLE_RE = re.compile(r"^#\s*WO(\d+)\s*[—–\-:]\s*(.+)$", re.M)
KV_LINE_RE = lambda key: re.compile(rf"^\*\*{re.escape(key)}:\*\*\s*(.+)$", re.M)

ALLOWED_STATUSES = {"RESERVED", "CLAIMED", "BLOCKED", "CLOSED"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
NON_LOCKING_KEYS = {"docs-only", "non-locking", "meta-only"}

HEX_SINGLE_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{4,8})$")
HEX_RANGE_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{4,8})\s*[-–..]+\s*(?:0x)?([0-9a-fA-F]{4,8})$")


@dataclass
class ScopeToken:
    raw: str
    kind: str  # "range" | "key" | "exempt"
    lo: int = 0
    hi: int = 0
    key: str = ""

    @property
    def canonical(self) -> str:
        if self.kind == "range":
            if self.lo == self.hi:
                return f"0x{self.lo:08X}"
            return f"0x{self.lo:08X}-0x{self.hi:08X}"
        return self.key


@dataclass
class WorkOrderRecord:
    path: pathlib.Path
    wo_id: str
    num_id: int
    title: str
    status: str
    priority: str
    owner: str
    lane: str
    claimed_at: Optional[str]
    lease_hours: int
    target_scope: List[str]
    depends_on: List[str]
    branch: str
    has_meta: bool
    meta_raw: Dict[str, Any] = field(default_factory=dict)
    meta_error: Optional[str] = None
    raw_status_text: str = ""


def load_pins(pins_path: pathlib.Path = DEFAULT_PINS_PATH) -> Dict[str, Any]:
    if not pins_path.exists():
        raise FileNotFoundError(f"Missing pins file: {pins_path}")
    return json.loads(pins_path.read_text(encoding="utf-8"))


def parse_iso_utc(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_scope_token(raw: str) -> ScopeToken:
    s = raw.strip()
    low = s.lower()
    if low in NON_LOCKING_KEYS:
        return ScopeToken(raw=s, kind="exempt", key=low)

    m_range = HEX_RANGE_RE.match(s)
    if m_range:
        lo = int(m_range.group(1), 16)
        hi = int(m_range.group(2), 16)
        if lo > hi:
            lo, hi = hi, lo
        return ScopeToken(raw=s, kind="range", lo=lo, hi=hi)

    m_single = HEX_SINGLE_RE.match(s)
    if m_single:
        val = int(m_single.group(1), 16)
        return ScopeToken(raw=s, kind="range", lo=val, hi=val)

    return ScopeToken(raw=s, kind="key", key=low)


def scopes_overlap(a: ScopeToken, b: ScopeToken) -> bool:
    if a.kind == "exempt" or b.kind == "exempt":
        return False
    if a.kind == "range" and b.kind == "range":
        return a.lo <= b.hi and b.lo <= a.hi
    if a.kind == "key" and b.kind == "key":
        return a.key == b.key
    return False


def normalize_legacy_status(raw_status: str) -> str:
    up = raw_status.upper()
    if any(tok in up for tok in ("CLOSED", "COMPLETE", "MERGED", "VERIFIED", "SUPERSEDED", "EXHAUSTED")):
        return "CLOSED"
    if "BLOCKED" in up:
        return "BLOCKED"
    if any(tok in up for tok in ("CLAIMED", "IN PROGRESS", "INVESTIGATING", "ACTIVE")):
        return "CLAIMED"
    if "RESERVED" in up or "UNCLAIMED" in up or "NOT STARTED" in up:
        return "RESERVED"
    return "CLOSED" if up else "UNKNOWN"


def extract_field(text: str, key: str) -> str:
    m = KV_LINE_RE(key).search(text)
    return m.group(1).strip() if m else ""


def infer_lane(num_id: int, pins: Dict[str, Any]) -> str:
    for lane_name, bounds in pins.get("lanes", {}).items():
        if int(bounds["min_id"]) <= num_id <= int(bounds["max_id"]):
            return lane_name
    return "legacy"


def parse_wo_file(path: pathlib.Path, pins: Dict[str, Any]) -> Optional[WorkOrderRecord]:
    m_fn = WO_FILE_RE.match(path.name)
    if not m_fn:
        return None
    num_id = int(m_fn.group(1))
    default_wo_id = f"WO{num_id}"
    text = path.read_text(encoding="utf-8", errors="replace")

    m_meta = META_RE.search(text)
    if m_meta:
        try:
            meta = json.loads(m_meta.group(1))
            if not isinstance(meta, dict):
                raise ValueError("WO_META block must be a JSON object")
        except Exception as exc:
            return WorkOrderRecord(
                path=path,
                wo_id=default_wo_id,
                num_id=num_id,
                title=default_wo_id,
                status="UNKNOWN",
                priority="P2",
                owner="",
                lane=infer_lane(num_id, pins),
                claimed_at=None,
                lease_hours=int(pins.get("default_lease_hours", 24)),
                target_scope=[],
                depends_on=[],
                branch="",
                has_meta=True,
                meta_raw={},
                meta_error=f"Invalid JSON in WO_META block: {exc}",
            )

        return WorkOrderRecord(
            path=path,
            wo_id=str(meta.get("wo_id", "")),
            num_id=num_id,
            title=str(meta.get("title", "")),
            status=str(meta.get("status", "")).upper(),
            priority=str(meta.get("priority", "")).upper(),
            owner=str(meta.get("owner", "")),
            lane=str(meta.get("lane", "")),
            claimed_at=meta.get("claimed_at") or None,
            lease_hours=int(meta.get("lease_hours", pins.get("default_lease_hours", 24)))
            if isinstance(meta.get("lease_hours", 24), int)
            else -1,
            target_scope=list(meta.get("target_scope", []))
            if isinstance(meta.get("target_scope"), list)
            else [],
            depends_on=list(meta.get("depends_on", []))
            if isinstance(meta.get("depends_on"), list)
            else [],
            branch=str(meta.get("branch", "")),
            has_meta=True,
            meta_raw=meta,
            raw_status_text=str(meta.get("status", "")),
        )

    # Legacy-tolerant parse
    m_title = TITLE_RE.search(text)
    title = m_title.group(2).strip() if m_title else default_wo_id
    raw_status = extract_field(text, "Status")
    raw_priority = extract_field(text, "Priority")
    prio_m = re.search(r"\b(P[0-3])\b", raw_priority.upper())
    priority = prio_m.group(1) if prio_m else ("P1" if "P1" in raw_priority else "P2")
    owner = extract_field(text, "Owner")
    branch = extract_field(text, "Branch").strip("`")
    issued = extract_field(text, "Issued") or extract_field(text, "Issued / Closed")
    return WorkOrderRecord(
        path=path,
        wo_id=default_wo_id,
        num_id=num_id,
        title=title,
        status=normalize_legacy_status(raw_status),
        priority=priority,
        owner=owner,
        lane=infer_lane(num_id, pins),
        claimed_at=issued if re.match(r"^\d{4}-\d{2}-\d{2}", issued) else None,
        lease_hours=int(pins.get("default_lease_hours", 24)),
        target_scope=[],
        depends_on=[],
        branch=branch,
        has_meta=False,
        raw_status_text=raw_status,
    )


def load_all_wos(control_dir: pathlib.Path, pins: Dict[str, Any]) -> List[WorkOrderRecord]:
    records: List[WorkOrderRecord] = []
    for p in sorted(control_dir.glob("WO*.md")):
        rec = parse_wo_file(p, pins)
        if rec is not None:
            records.append(rec)
    records.sort(key=lambda r: r.num_id)
    return records


def is_strict_record(rec: WorkOrderRecord, pins: Dict[str, Any], forced_files: Sequence[str]) -> bool:
    if rec.has_meta:
        return True
    if rec.num_id > int(pins.get("legacy_cutoff_id", 65163)):
        return True
    norm_forced = {pathlib.Path(f).as_posix() for f in forced_files}
    try:
        rel = rec.path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        rel = rec.path.name
    return rel in norm_forced or rec.path.name in norm_forced


def validate_repo(
    control_dir: pathlib.Path,
    pins: Dict[str, Any],
    changed_files: Optional[Sequence[str]] = None,
    forbid_register_edit: bool = False,
    allow_pins_edit: bool = False,
    strict_all: bool = False,
) -> List[str]:
    errors: List[str] = []
    changed = [pathlib.Path(f).as_posix() for f in (changed_files or [])]

    if forbid_register_edit and changed:
        protected = {pathlib.Path(p).as_posix() for p in pins.get("protected_generated_files", [])}
        if not allow_pins_edit:
            protected.add("CONTROL/registry_pins.json")
        for f in changed:
            if f in protected:
                errors.append(
                    f"Worker branch/PR modified protected auto-generated file `{f}`. "
                    "Only GitHub Actions rebuilds protected registers on `main`."
                )

    records = load_all_wos(control_dir, pins)
    seen_ids: Dict[str, pathlib.Path] = {}
    banned_owners = {t.strip().lower() for t in pins.get("banned_owner_tokens", [])}
    lanes = pins.get("lanes", {})

    for rec in records:
        if rec.wo_id in seen_ids:
            errors.append(f"Duplicate WO ID {rec.wo_id} in {rec.path.name} and {seen_ids[rec.wo_id].name}")
        seen_ids[rec.wo_id] = rec.path

        strict = strict_all or is_strict_record(rec, pins, changed)
        if not strict:
            continue

        if rec.meta_error:
            errors.append(f"{rec.path.name}: {rec.meta_error}")
            continue
        if not rec.has_meta:
            errors.append(
                f"{rec.path.name}: missing required <!-- WO_META_START --> JSON block for strict v4 validation"
            )
            continue

        required = (
            "wo_id",
            "title",
            "lane",
            "status",
            "priority",
            "owner",
            "claimed_at",
            "lease_hours",
            "target_scope",
            "depends_on",
            "branch",
        )
        for key in required:
            if key not in rec.meta_raw:
                errors.append(f"{rec.path.name}: missing required metadata field `{key}`")

        expected_id = f"WO{rec.num_id}"
        if rec.wo_id != expected_id:
            errors.append(f"{rec.path.name}: `wo_id` ({rec.wo_id!r}) must match filename ({expected_id})")

        if not rec.title.strip():
            errors.append(f"{rec.path.name}: `title` must be non-empty")

        if rec.status not in ALLOWED_STATUSES:
            errors.append(f"{rec.path.name}: invalid `status` {rec.status!r} (expected {sorted(ALLOWED_STATUSES)})")

        if rec.priority not in ALLOWED_PRIORITIES:
            errors.append(
                f"{rec.path.name}: invalid `priority` {rec.priority!r} (expected {sorted(ALLOWED_PRIORITIES)})"
            )

        if rec.lane not in lanes:
            errors.append(f"{rec.path.name}: unknown `lane` {rec.lane!r} (valid: {sorted(lanes)})")
        else:
            lo = int(lanes[rec.lane]["min_id"])
            hi = int(lanes[rec.lane]["max_id"])
            if not (lo <= rec.num_id <= hi):
                errors.append(
                    f"{rec.path.name}: ID {rec.num_id} is outside lane `{rec.lane}` range [{lo}..{hi}]"
                )

        owner_clean = rec.owner.strip().lower()
        if rec.status in {"CLAIMED", "CLOSED"}:
            if not owner_clean or owner_clean in banned_owners or "current session" in owner_clean or "this session" in owner_clean or owner_clean == "unclaimed":
                errors.append(
                    f"{rec.path.name}: ambiguous or missing `owner` ({rec.owner!r}); "
                    "use a concrete session/worker ID (never `current session`)"
                )
        elif rec.status == "RESERVED":
            if owner_clean in banned_owners:
                errors.append(f"{rec.path.name}: banned placeholder `owner` ({rec.owner!r})")

        if rec.status in {"CLAIMED", "CLOSED"}:
            if not rec.claimed_at or parse_iso_utc(rec.claimed_at) is None:
                errors.append(
                    f"{rec.path.name}: `claimed_at` must be an ISO-8601 timestamp (e.g. 2026-11-21T19:45:00Z)"
                )

        if not isinstance(rec.meta_raw.get("lease_hours"), int) or rec.lease_hours <= 0:
            errors.append(f"{rec.path.name}: `lease_hours` must be a positive integer")

        if not isinstance(rec.meta_raw.get("target_scope"), list) or not rec.target_scope:
            errors.append(f"{rec.path.name}: `target_scope` must be a non-empty list of scope tokens")

        if not isinstance(rec.meta_raw.get("depends_on"), list):
            errors.append(f"{rec.path.name}: `depends_on` must be a list")
        else:
            for dep in rec.depends_on:
                if not isinstance(dep, str) or not WO_ID_RE.match(dep):
                    errors.append(f"{rec.path.name}: invalid `depends_on` entry {dep!r}")
                elif dep == rec.wo_id:
                    errors.append(f"{rec.path.name}: cannot depend on self ({dep})")

    # Pairwise scope lock conflict check among active CLAIMED WOs
    claimed = [r for r in records if r.has_meta and not r.meta_error and r.status == "CLAIMED"]
    for i in range(len(claimed)):
        a = claimed[i]
        tokens_a = [normalize_scope_token(str(t)) for t in a.target_scope]
        for j in range(i + 1, len(claimed)):
            b = claimed[j]
            if b.wo_id in a.depends_on or a.wo_id in b.depends_on:
                continue
            tokens_b = [normalize_scope_token(str(t)) for t in b.target_scope]
            overlaps: List[str] = []
            for ta in tokens_a:
                for tb in tokens_b:
                    if scopes_overlap(ta, tb):
                        overlaps.append(f"{ta.canonical} <-> {tb.canonical}")
            if overlaps:
                errors.append(
                    f"Target-scope lock collision between CLAIMED {a.wo_id} ({a.owner}) "
                    f"and {b.wo_id} ({b.owner}): {', '.join(sorted(set(overlaps)))}"
                )

    return errors


def fetch_remote_wo_ids(repo: str, branch: str) -> Optional[List[int]]:
    url = f"https://api.github.com/repos/{repo}/contents/CONTROL?ref={branch}"
    req = urllib.request.Request(url, headers={"User-Agent": "el19a-wo-registry"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            items = json.loads(resp.read().decode("utf-8"))
        ids: List[int] = []
        for it in items:
            m = WO_FILE_RE.match(it.get("name", ""))
            if m:
                ids.append(int(m.group(1)))
        return ids
    except Exception:
        return None


def compute_next_id(
    control_dir: pathlib.Path,
    pins: Dict[str, Any],
    lane: str,
    use_remote: bool = False,
) -> Tuple[int, List[WorkOrderRecord]]:
    lanes = pins.get("lanes", {})
    if lane not in lanes:
        raise ValueError(f"Unknown lane {lane!r}. Valid lanes: {sorted(lanes)}")
    lo = int(lanes[lane]["min_id"])
    hi = int(lanes[lane]["max_id"])

    records = load_all_wos(control_dir, pins)
    used_ids = {r.num_id for r in records if lo <= r.num_id <= hi}
    if use_remote:
        remote_ids = fetch_remote_wo_ids(
            pins.get("repository", "ihatealladvertising/EL19A-"),
            pins.get("authority_branch", "main"),
        )
        if remote_ids is not None:
            used_ids.update(i for i in remote_ids if lo <= i <= hi)

    candidate = (max(used_ids) + 1) if used_ids else lo
    if candidate > hi:
        raise RuntimeError(f"Lane `{lane}` exhausted ({lo}..{hi})")
    active_claimed = [r for r in records if r.has_meta and r.status == "CLAIMED"]
    return candidate, active_claimed


def build_dashboard_markdown(
    control_dir: pathlib.Path,
    pins: Dict[str, Any],
    now_dt: Optional[datetime] = None,
) -> str:
    records = load_all_wos(control_dir, pins)
    by_id: Dict[str, WorkOrderRecord] = {r.wo_id: r for r in records}

    # Deterministic reference clock: explicit --now, else latest claimed_at among v4 records
    if now_dt is None:
        v4_times = [
            dt for r in records if r.has_meta and r.claimed_at for dt in [parse_iso_utc(r.claimed_at)] if dt is not None
        ]
        now_dt = max(v4_times) if v4_times else datetime(2026, 11, 21, 0, 0, tzinfo=timezone.utc)

    v4_records = [r for r in records if r.has_meta]
    active_claimed = [r for r in v4_records if r.status == "CLAIMED"]
    blocked = [r for r in v4_records if r.status == "BLOCKED"]
    reserved = [r for r in v4_records if r.status == "RESERVED"]
    closed_v4 = sorted([r for r in v4_records if r.status == "CLOSED"], key=lambda r: -r.num_id)

    lines: List[str] = [
        "# EL19A — Auto-Generated Work-Order Ownership Dashboard",
        "",
        "> **Do not hand-edit this view.** Generated deterministically from `CONTROL/WO*.md` and `CONTROL/registry_pins.json` by `tools/wo_registry.py`.",
        "",
        f"- **Repository:** `{pins.get('repository')}` · **Authority branch:** `{pins.get('authority_branch')}`",
        f"- **Current Workbook:** `{pins.get('current_workbook')}` ({pins.get('current_workbook_sheets')} sheets)",
        f"- **XML Baseline:** `{pins.get('current_xml_baseline')}` + `{pins.get('current_xml_fragment')}`",
        f"- **Catalog Staging:** `{pins.get('discovery_staging')}`",
        f"- **Parsed Records:** `{len(records)}` total (`{len(v4_records)}` structured v4, `{len(records) - len(v4_records)}` legacy)",
        "",
        "## Lane Allocation (Zero-Collision Prefixes)",
        "",
        "| Lane | ID Range | Highest Used | Next Free | Session Assignment |",
        "|---|---|---|---|---|",
    ]

    for lane_name, bounds in pins.get("lanes", {}).items():
        lo = int(bounds["min_id"])
        hi = int(bounds["max_id"])
        in_lane = sorted(r.num_id for r in records if lo <= r.num_id <= hi)
        highest = f"`WO{in_lane[-1]}`" if in_lane else "—"
        nxt = (in_lane[-1] + 1) if in_lane else lo
        nxt_str = f"`WO{nxt}`" if nxt <= hi else "EXHAUSTED"
        lines.append(
            f"| `{lane_name}` | `WO{lo}`–`WO{hi}` | {highest} | {nxt_str} | {bounds.get('description', '')} |"
        )

    lines.extend(["", "## Active Claims & Lease Health", ""])
    if active_claimed:
        lines.extend([
            "| WO | Lane | Priority | Owner | Claimed At | Lease Health | Target Scope |",
            "|---|---|---|---|---|---|---|",
        ])
        for r in active_claimed:
            lease_health = "LEGACY"
            if r.has_meta and r.claimed_at:
                cdt = parse_iso_utc(r.claimed_at)
                if cdt is not None:
                    age_h = (now_dt - cdt).total_seconds() / 3600.0
                    if age_h > r.lease_hours:
                        lease_health = f"STALE ({age_h:.1f}h > {r.lease_hours}h)"
                    else:
                        lease_health = f"OK ({max(age_h, 0.0):.1f}h / {r.lease_hours}h)"
            scope_str = ", ".join(f"`{normalize_scope_token(s).canonical}`" for s in r.target_scope) or "—"
            owner_str = f"`{r.owner}`" if r.owner else "`unassigned`"
            lines.append(
                f"| [{r.wo_id}]({r.wo_id}.md) | `{r.lane}` | {r.priority} | {owner_str} | `{r.claimed_at or '—'}` | {lease_health} | {scope_str} |"
            )
    else:
        lines.append("_No active CLAIMED work orders._")

    lines.extend(["", "## Target Scope Lock Table", ""])
    lock_rows: List[Tuple[str, str, str, str]] = []
    for r in active_claimed:
        for raw_tok in r.target_scope:
            tok = normalize_scope_token(raw_tok)
            if tok.kind == "exempt":
                continue
            lock_rows.append((tok.canonical, r.wo_id, r.owner or "unassigned", r.lane))
    if lock_rows:
        lines.extend([
            "| Canonical Scope Lock | Held By | Owner | Lane |",
            "|---|---|---|---|",
        ])
        for canon, wid, own, ln in sorted(lock_rows):
            lines.append(f"| `{canon}` | [{wid}]({wid}.md) | `{own}` | `{ln}` |")
    else:
        lines.append("_No active hex/key scope locks held._")

    lines.extend(["", "## Structured Queue & Dependency Unblocking", ""])
    queue_items = blocked + reserved
    if queue_items:
        lines.extend([
            "| WO | Declared Status | Effective State | Priority | Depends On | Title |",
            "|---|---|---|---|---|---|",
        ])
        for r in queue_items:
            deps_done = all(
                (dep in by_id and by_id[dep].status == "CLOSED")
                for dep in r.depends_on
            )
            if r.status == "BLOCKED":
                eff = "**READY (deps CLOSED)**" if deps_done else "BLOCKED"
            else:
                eff = "READY" if deps_done else "WAITING_DEPS"
            deps_str = ", ".join(f"`{d}`" for d in r.depends_on) or "—"
            lines.append(
                f"| [{r.wo_id}]({r.wo_id}.md) | `{r.status}` | {eff} | {r.priority} | {deps_str} | {r.title} |"
            )
    else:
        lines.append("_No queued v4 RESERVED/BLOCKED work orders._")

    lines.extend(["", "## Recent Closed Structured Work Orders", ""])
    if closed_v4:
        lines.extend([
            "| WO | Lane | Priority | Owner | Closed/Claimed Timestamp | Title |",
            "|---|---|---|---|---|---|",
        ])
        for r in closed_v4[:25]:
            lines.append(
                f"| [{r.wo_id}]({r.wo_id}.md) | `{r.lane}` | {r.priority} | `{r.owner}` | `{r.claimed_at or '—'}` | {r.title} |"
            )
    else:
        lines.append("_No closed structured v4 work orders yet._")

    lines.append("")
    return "\n".join(lines)


def inject_dashboard_into_register(register_path: pathlib.Path, dashboard_md: str) -> str:
    existing = register_path.read_text(encoding="utf-8")
    block = f"{AUTO_BLOCK_START}\n{dashboard_md.strip()}\n{AUTO_BLOCK_END}"
    if AUTO_BLOCK_START in existing and AUTO_BLOCK_END in existing:
        pattern = re.compile(
            re.escape(AUTO_BLOCK_START) + r".*?" + re.escape(AUTO_BLOCK_END),
            re.DOTALL,
        )
        return pattern.sub(lambda _: block, existing, count=1)

    # Inject immediately after the top title/metadata block (before ## Concurrency protocol or first ##)
    m_sec = re.search(r"^##\s+", existing, re.M)
    if m_sec:
        idx = m_sec.start()
        return existing[:idx].rstrip() + "\n\n" + block + "\n\n" + existing[idx:].lstrip()
    return existing.rstrip() + "\n\n" + block + "\n"


def render_init_wo(
    wo_id: str,
    title: str,
    lane: str,
    owner: str,
    priority: str,
    scope: List[str],
    depends_on: List[str],
    branch: str,
    claimed_at: str,
    status: str = "CLAIMED",
    lease_hours: int = 24,
) -> str:
    meta = {
        "wo_id": wo_id,
        "title": title,
        "lane": lane,
        "status": status,
        "priority": priority,
        "owner": owner,
        "claimed_at": claimed_at,
        "lease_hours": lease_hours,
        "target_scope": scope,
        "depends_on": depends_on,
        "branch": branch,
    }
    meta_json = json.dumps(meta, indent=2)
    return (
        f"# {wo_id} — {title}\n\n"
        f"<!-- WO_META_START -->\n{meta_json}\n<!-- WO_META_END -->\n\n"
        f"**Status:** {status}  \n"
        f"**Priority:** {priority}  \n"
        f"**Owner:** `{owner}` (`{lane}` lane)  \n"
        f"**Claimed:** {claimed_at} (lease {lease_hours}h)  \n"
        f"**Target Scope:** {', '.join(f'`{s}`' for s in scope)}  \n\n"
        "## Objective\n\n"
        "- State bounded question and stop condition.\n\n"
        "## Evidence & Findings\n\n"
        "- Record verified PC/ROM/RAM findings here.\n\n"
        "## Deliverables & Integration State\n\n"
        "- No edits to shared registers (`CONTROL/active_work_orders.md`, `CONTROL/WO_LIVE_INDEX.md`) or immutable artifacts.\n"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="EL19A Work-Order Ownership Validator & Register Builder")
    parser.add_argument("--control-dir", type=pathlib.Path, default=DEFAULT_CONTROL_DIR)
    parser.add_argument("--pins", type=pathlib.Path, default=DEFAULT_PINS_PATH)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate v4 work orders, ownership, and scope locks")
    p_val.add_argument("--changed-files", nargs="*", default=[])
    p_val.add_argument("--forbid-register-edit", action="store_true")
    p_val.add_argument("--allow-pins-edit", action="store_true")
    p_val.add_argument("--strict-all", action="store_true")

    p_reb = sub.add_parser("rebuild", help="Deterministically rebuild live index and/or register dashboard")
    p_reb.add_argument("--out", type=pathlib.Path, default=DEFAULT_CONTROL_DIR / "WO_LIVE_INDEX.md")
    p_reb.add_argument("--inject-register", type=pathlib.Path, default=None)
    p_reb.add_argument("--now", type=str, default=None, help="Override UTC reference clock (ISO-8601)")

    p_next = sub.add_parser("next-id", help="Show next free WO ID in a lane and active scope locks")
    p_next.add_argument("--lane", required=True)
    p_next.add_argument("--remote", action="store_true", help="Also query GitHub main branch over HTTPS")

    p_init = sub.add_parser("init", help="Create a compliant structured v4 WO file in an assigned lane")
    p_init.add_argument("--lane", required=True)
    p_init.add_argument("--owner", required=True)
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--priority", default="P1", choices=sorted(ALLOWED_PRIORITIES))
    p_init.add_argument("--scope", nargs="+", required=True)
    p_init.add_argument("--depends-on", nargs="*", default=[])
    p_init.add_argument("--status", default="CLAIMED", choices=sorted(ALLOWED_STATUSES))
    p_init.add_argument("--wo-id", default=None, help="Explicit WOxxxxx ID (auto-allocated if omitted)")
    p_init.add_argument("--branch", default=None)
    p_init.add_argument("--remote", action="store_true")

    args = parser.parse_args(argv)
    pins = load_pins(args.pins)

    if args.cmd == "validate":
        errs = validate_repo(
            args.control_dir,
            pins,
            changed_files=args.changed_files,
            forbid_register_edit=args.forbid_register_edit,
            allow_pins_edit=args.allow_pins_edit,
            strict_all=args.strict_all,
        )
        if errs:
            print(f"VALIDATION FAILED ({len(errs)} error(s)):", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("VALIDATION PASS: all checked v4 work orders, lanes, owners, and scope locks are valid.")
        return 0

    if args.cmd == "rebuild":
        now_dt = parse_iso_utc(args.now) if args.now else None
        dash = build_dashboard_markdown(args.control_dir, pins, now_dt=now_dt)
        args.out.write_text(dash, encoding="utf-8")
        print(f"Wrote {args.out} ({len(dash)} chars)")
        if args.inject_register is not None:
            updated = inject_dashboard_into_register(args.inject_register, dash)
            args.inject_register.write_text(updated, encoding="utf-8")
            print(f"Updated auto-dashboard block in {args.inject_register} ({len(updated)} chars)")
        return 0

    if args.cmd == "next-id":
        nxt, active = compute_next_id(args.control_dir, pins, args.lane, use_remote=args.remote)
        print(f"NEXT_ID=WO{nxt} (lane={args.lane})")
        print(f"ACTIVE_CLAIMED={len(active)}")
        for r in active:
            print(f"  {r.wo_id} owner={r.owner or 'legacy'} scope={r.target_scope}")
        return 0

    if args.cmd == "init":
        if args.wo_id:
            m = WO_ID_RE.match(args.wo_id)
            if not m:
                print(f"Invalid --wo-id {args.wo_id!r}", file=sys.stderr)
                return 2
            num_id = int(m.group(1))
        else:
            num_id, _ = compute_next_id(args.control_dir, pins, args.lane, use_remote=args.remote)
        wo_id = f"WO{num_id}"
        target = args.control_dir / f"{wo_id}.md"
        if target.exists():
            print(f"Refusing to overwrite existing {target}", file=sys.stderr)
            return 2
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        branch = args.branch or f"{args.lane}/{wo_id.lower()}"
        content = render_init_wo(
            wo_id=wo_id,
            title=args.title,
            lane=args.lane,
            owner=args.owner,
            priority=args.priority,
            scope=args.scope,
            depends_on=args.depends_on,
            branch=branch,
            claimed_at=now_str,
            status=args.status,
            lease_hours=int(pins.get("default_lease_hours", 24)),
        )
        target.write_text(content, encoding="utf-8")
        errs = validate_repo(args.control_dir, pins)
        if errs:
            target.unlink(missing_ok=True)
            print("Created WO failed validation:", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print(f"Created valid {target}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
