from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

from core.bootstrap.discovery.platform import detect_platform
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore
from core.security.capability_router import build_live_plan


class BountyAgentError(ValueError):
    pass


def _default_db() -> Path:
    root = os.environ.get("JARVIS_RUNTIME_ROOT")
    if root:
        return Path(root) / "bounty_agent" / "r6.sqlite"
    return Path.home() / ".local/share/jarvis/bounty_agent/r6.sqlite"


def _flatten_strings(value):
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            out.append(str(k))
            out.extend(_flatten_strings(v))
    elif isinstance(value, (list, tuple)):
        for v in value:
            out.extend(_flatten_strings(v))
    return out


def _score_httpx_evidence(evidence: dict) -> dict:
    from core.bounty_agent.scoring_r61 import analyze_http_evidence_only
    return analyze_http_evidence_only(evidence)


class BountyAgent:
    def __init__(self, path=None, authorization_store=None, live_store=None):
        self.path = Path(path or _default_db()).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.authorization_store = authorization_store or AuthorizationStore()
        self.live_store = live_store or LiveMissionStore(
            authorization_store=self.authorization_store
        )
        self._init()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _init(self):
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions(
                id TEXT PRIMARY KEY,
                authorization TEXT NOT NULL,
                mission TEXT NOT NULL,
                program TEXT NOT NULL,
                root_target TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                updated REAL NOT NULL,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS options(
                id TEXT PRIMARY KEY,
                session TEXT NOT NULL,
                target TEXT NOT NULL,
                score INTEGER NOT NULL,
                priority TEXT NOT NULL,
                risk TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                reviewed REAL,
                reviewer TEXT,
                analysis TEXT NOT NULL,
                FOREIGN KEY(session) REFERENCES sessions(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS option_target_unique
                ON options(session,target);
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT
            );

            CREATE TABLE IF NOT EXISTS investigation_plans(
                id TEXT PRIMARY KEY,
                option_id TEXT NOT NULL UNIQUE,
                session TEXT NOT NULL,
                target TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                updated REAL NOT NULL,
                plan_json TEXT NOT NULL,
                FOREIGN KEY(option_id) REFERENCES options(id),
                FOREIGN KEY(session) REFERENCES sessions(id)
            );

            CREATE INDEX IF NOT EXISTS
                investigation_plan_session
                ON investigation_plans(session);
            """)

    def _event(self, db, session, kind, detail=""):
        db.execute(
            "INSERT INTO events(session,at,kind,detail) VALUES(?,?,?,?)",
            (session, time.time(), kind, detail),
        )

    def create(self, authorization, root_target, *, budget=100):
        if detect_platform() != "kali":
            raise BountyAgentError(
                "Live bounty-agent recon is enabled only on Kali. "
                "Use Ubuntu for intelligence/review, not live execution."
            )

        scope = self.authorization_store.live_scope(authorization)

        discovery_enabled = (
            "subdomain_discovery"
            in scope.logical_capabilities
        )

        dns_enabled = (
            "dns_resolution"
            in scope.logical_capabilities
        )

        if discovery_enabled:
            # Existing discovery-seed mode.
            root_target = scope.require(
                root_target,
                "subfinder",
            )

        elif dns_enabled:
            # R9.10L.3 explicit-seed mode.
            #
            # No discovery capability is authorized, so the supplied
            # root must already be an exact reviewed hostname. A
            # wildcard match is deliberately insufficient here.
            scope.require_capability(
                "dns_resolution"
            )
            scope.require_capability(
                "http_probe"
            )

            seed_plan = build_live_plan(
                [
                    "dns_resolution",
                    "http_probe",
                ],
                allowed_providers=(
                    scope.approved_providers
                ),
            )

            seed_providers = {
                route.capability:
                    route.provider
                for route in seed_plan
            }

            dns_provider = (
                seed_providers[
                    "dns_resolution"
                ]
            )

            root_target = scope.require(
                root_target,
                dns_provider,
            )

            explicit_hosts = {
                value
                for value in scope.include
                if not value.startswith("*.")
            }

            if root_target not in explicit_hosts:
                raise BountyAgentError(
                    "Seed-target mode requires an "
                    "explicitly reviewed hostname"
                )

        else:
            raise BountyAgentError(
                "Authorization provides neither "
                "subdomain discovery nor DNS seed "
                "resolution"
            )

        mission = self.live_store.create(authorization, budget=budget)
        session = str(uuid.uuid4())
        now = time.time()

        with self.db() as db:
            db.execute(
                """INSERT INTO sessions(
                    id,authorization,mission,program,root_target,
                    state,created,updated,error
                ) VALUES(?,?,?,?,?,'authorized',?,?,NULL)""",
                (session, authorization, mission, scope.program, root_target, now, now),
            )
            self._event(db, session, "authorized", f"Program={scope.program} target={root_target} mission={mission}")

        return session

    def _set_state(self, session, state, error=None):
        with self.db() as db:
            found = db.execute("SELECT id FROM sessions WHERE id=?", (session,)).fetchone()
            if not found:
                raise BountyAgentError("Unknown agent session")
            db.execute(
                "UPDATE sessions SET state=?,updated=?,error=? WHERE id=?",
                (state, time.time(), error, session),
            )
            self._event(db, session, state, error or "")

    def _session(self, session):
        with self.db() as db:
            row = db.execute("SELECT * FROM sessions WHERE id=?", (session,)).fetchone()
        if not row:
            raise BountyAgentError("Unknown agent session")
        return dict(row)

    def run_recon(self, session):
        current = self._session(session)

        if current["state"] not in {
            "authorized",
            "failed",
        }:
            raise BountyAgentError(
                "Session cannot start recon from state "
                f"{current['state']}"
            )

        scope = self.authorization_store.live_scope(
            current["authorization"]
        )

        # R8.8B
        #
        # subdomain_discovery and http_probe remain the
        # baseline reconnaissance capabilities.
        #
        # DNS becomes an intermediate gate only when the
        # reviewed authorization explicitly permits it.
        discovery_enabled = (
            "subdomain_discovery"
            in scope.logical_capabilities
        )

        dns_enabled = (
            "dns_resolution"
            in scope.logical_capabilities
        )

        requested_capabilities = []

        if discovery_enabled:
            requested_capabilities.append(
                "subdomain_discovery"
            )

        if dns_enabled:
            requested_capabilities.append(
                "dns_resolution"
            )

        requested_capabilities.append(
            "http_probe"
        )

        # WHAT may Jarvis do?
        for capability in requested_capabilities:
            scope.require_capability(
                capability
            )

        # WHICH approved provider may perform it?
        plan = build_live_plan(
            requested_capabilities,
            allowed_providers=(
                scope.approved_providers
            ),
        )

        providers = {
            route.capability: route.provider
            for route in plan
        }

        subdomain_provider = providers.get(
            "subdomain_discovery"
        )

        dns_provider = providers.get(
            "dns_resolution"
        )

        http_provider = providers[
            "http_probe"
        ]

        if discovery_enabled:
            # Existing discovery-seed authorization check.
            scope.require(
                current["root_target"],
                subdomain_provider,
            )

        else:
            # Explicit-seed mode must start from a hostname
            # literally present in reviewed include scope.
            if not dns_enabled or not dns_provider:
                raise BountyAgentError(
                    "Explicit-seed mode requires "
                    "authorized DNS resolution"
                )

            seed_target = scope.require(
                current["root_target"],
                dns_provider,
            )

            explicit_hosts = {
                value
                for value in scope.include
                if not value.startswith("*.")
            }

            if seed_target not in explicit_hosts:
                raise BountyAgentError(
                    "Seed-target mode requires an "
                    "explicitly reviewed hostname"
                )

        self._set_state(
            session,
            "recon_running",
        )

        try:
            # ------------------------------------------------
            # STAGE 1 — SUBDOMAIN DISCOVERY
            # ------------------------------------------------

            discovered_targets = set()
            subfinder_task = None

            if discovery_enabled:
                subfinder_task = self.live_store.queue(
                    current["mission"],
                    subdomain_provider,
                    current["root_target"],
                )

                subfinder_evidence = (
                    self.live_store.run(
                        subfinder_task
                    )
                )

                if (
                    subfinder_evidence
                    .get("result", {})
                    .get("state")
                    != "completed"
                ):
                    raise BountyAgentError(
                        "Subdomain discovery did not complete"
                    )

                discovered_targets = set(
                    subfinder_evidence
                    .get("result", {})
                    .get("accepted", [])
                )

            httpx_evidence = []
            httpx_targets = set()

            # ------------------------------------------------
            # R8.8B NATIVE PATH
            #
            # DNS-enabled authorizations:
            #
            # discovery
            #     ↓
            # dns_resolution
            #     ↓
            # resolved hosts only
            #     ↓
            # http_probe
            #
            # We intentionally do NOT create direct HTTPX
            # proposals from Subfinder in this branch because
            # that would bypass the DNS gate.
            # ------------------------------------------------

            if dns_enabled:
                # R9.1.2
                #
                # The mission budget is a TARGET budget.
                # Always preserve the explicitly reviewed root,
                # then deterministically select only enough
                # discovered hosts to remain within that limit.
                mission_report = (
                    self.live_store.report(
                        current["mission"]
                    )
                )

                target_budget = int(
                    mission_report[
                        "mission"
                    ]["budget"]
                )

                root_target = (
                    current["root_target"]
                )

                ordered_candidates = [
                    root_target
                ]

                ordered_candidates.extend(
                    target
                    for target in sorted(
                        discovered_targets
                    )
                    if target != root_target
                )

                candidate_targets = (
                    ordered_candidates[
                        :target_budget
                    ]
                )

                resolved_targets = set()

                for candidate in candidate_targets:
                    # Recheck provider + host authorization
                    # before the task enters the live store.
                    candidate = scope.require(
                        candidate,
                        dns_provider,
                    )

                    dns_task = self.live_store.queue(
                        current["mission"],
                        dns_provider,
                        candidate,
                    )

                    dns_evidence = (
                        self.live_store.run(
                            dns_task
                        )
                    )

                    result = (
                        dns_evidence.get(
                            "result",
                            {},
                        )
                    )

                    accepted = set(
                        result.get(
                            "accepted",
                            [],
                        )
                    )

                    if (
                        result.get("state")
                        == "completed"
                        and
                        result.get("returncode")
                        == 0
                        and candidate in accepted
                    ):
                        resolved_targets.add(
                            candidate
                        )

                # Only DNS-surviving hosts may reach HTTPX.
                for target in sorted(
                    resolved_targets
                ):
                    target = scope.require(
                        target,
                        http_provider,
                    )

                    http_task = (
                        self.live_store.queue(
                            current["mission"],
                            http_provider,
                            target,
                        )
                    )

                    evidence = (
                        self.live_store.run(
                            http_task
                        )
                    )

                    evidence_target = (
                        evidence
                        .get("result", {})
                        .get("target")
                        or evidence.get("target")
                    )

                    if (
                        evidence_target
                        and
                        evidence_target
                        in httpx_targets
                    ):
                        continue

                    httpx_evidence.append(
                        evidence
                    )

                    if evidence_target:
                        httpx_targets.add(
                            evidence_target
                        )

            # ------------------------------------------------
            # LEGACY R5 / R8.7 PATH
            #
            # Authorizations without dns_resolution retain the
            # already-tested Subfinder → HTTPX behavior.
            # ------------------------------------------------

            else:
                proposal_ids = (
                    self.live_store
                    .propose_httpx_from_subfinder(
                        subfinder_task
                    )
                )

                # R8.5 root-seed preservation.
                try:
                    root_httpx_target = (
                        scope.require(
                            current["root_target"],
                            http_provider,
                        )
                    )
                except Exception:
                    root_httpx_target = None

                if (
                    root_httpx_target
                    and root_httpx_target
                    not in discovered_targets
                ):
                    root_httpx_task = (
                        self.live_store.queue(
                            current["mission"],
                            http_provider,
                            root_httpx_target,
                        )
                    )

                    root_httpx_evidence = (
                        self.live_store.run(
                            root_httpx_task
                        )
                    )

                    httpx_evidence.append(
                        root_httpx_evidence
                    )

                    httpx_targets.add(
                        root_httpx_target
                    )

                for proposal_id in proposal_ids:
                    # Preserve the existing R6 reviewed
                    # proposal path for legacy Subfinder
                    # discoveries.
                    task_id = (
                        self.live_store
                        .approve_proposal(
                            proposal_id,
                            "jarvis-recon-policy-r6",
                        )
                    )

                    evidence = (
                        self.live_store.run(
                            task_id
                        )
                    )

                    target = (
                        evidence
                        .get("result", {})
                        .get("target")
                        or evidence.get("target")
                    )

                    if (
                        target
                        and target in httpx_targets
                    ):
                        continue

                    httpx_evidence.append(
                        evidence
                    )

                    if target:
                        httpx_targets.add(
                            target
                        )

            # Authorization must still be alive before
            # committing scoring/options.
            self.authorization_store.live_scope(
                current["authorization"]
            )

            analyses = []

            with self.db() as db:
                for evidence in httpx_evidence:
                    analysis = (
                        _score_httpx_evidence(
                            evidence
                        )
                    )

                    analyses.append(
                        analysis
                    )

                    option_id = str(
                        uuid.uuid4()
                    )

                    try:
                        db.execute(
                            """INSERT INTO options(
                                id,session,target,score,
                                priority,risk,state,
                                created,reviewed,reviewer,
                                analysis
                            ) VALUES(
                                ?,?,?,?,?,?,
                                'awaiting_human',
                                ?,NULL,NULL,?
                            )""",
                            (
                                option_id,
                                session,
                                analysis["target"],
                                analysis["score"],
                                analysis["priority"],
                                analysis["risk"],
                                time.time(),
                                json.dumps(
                                    analysis,
                                    sort_keys=True,
                                ),
                            ),
                        )

                    except sqlite3.IntegrityError:
                        db.execute(
                            """UPDATE options
                               SET
                                   score=?,
                                   priority=?,
                                   risk=?,
                                   state='awaiting_human',
                                   created=?,
                                   reviewed=NULL,
                                   reviewer=NULL,
                                   analysis=?
                               WHERE
                                   session=?
                                   AND target=?""",
                            (
                                analysis["score"],
                                analysis["priority"],
                                analysis["risk"],
                                time.time(),
                                json.dumps(
                                    analysis,
                                    sort_keys=True,
                                ),
                                session,
                                analysis["target"],
                            ),
                        )

                db.execute(
                    """UPDATE sessions
                       SET
                           state='options_ready',
                           updated=?,
                           error=NULL
                       WHERE id=?""",
                    (
                        time.time(),
                        session,
                    ),
                )

                mode = (
                    "DNS-gated"
                    if dns_enabled
                    else "legacy"
                )

                self._event(
                    db,
                    session,
                    "options_ready",
                    (
                        f"{len(analyses)} analyzed HTTP "
                        f"targets · {mode}"
                    ),
                )

            return self.report(
                session
            )

        except Exception as exc:
            self._set_state(
                session,
                "failed",
                str(exc),
            )

    def _build_investigation_plan(
        self,
        option,
        reviewer,
    ):
        """
        R9.2A

        Build a planning artifact from already-collected
        reconnaissance evidence.

        A pursuit plan is advisory only. It cannot execute
        tools, create live tasks, expand authorization, or
        validate vulnerabilities.
        """
        analysis = option.get("analysis") or {}

        suggested = list(
            analysis.get(
                "suggested_actions",
                [],
            )
        )

        actions = []

        for index, label in enumerate(
            suggested,
            1,
        ):
            text = str(label).strip()

            if not text:
                continue

            lower = text.lower()

            if "map" in lower:
                required = "web_crawling"
            elif (
                "application" in lower
                or "api" in lower
                or "deeper" in lower
            ):
                required = "manual_web_testing"
            else:
                required = "human_review"

            actions.append(
                {
                    "id":
                        f"step-{index}",
                    "action":
                        text,
                    "capability_required":
                        required,
                    "rationale":
                        (
                            "Derived from the R6.1 "
                            "recon analysis for this "
                            "specific target."
                        ),
                    "execution_allowed":
                        False,
                    "approval_state":
                        "not_approved",
                }
            )

        return {
            "schema":
                "jarvis-bounty-investigation-plan-r9.2a",
            "option_id":
                option["id"],
            "session":
                option["session"],
            "target":
                option["target"],
            "decision":
                "pursue",
            "reviewer":
                str(reviewer).strip(),
            "state":
                "awaiting_action_approval",

            "evidence_basis": {
                "score":
                    option["score"],
                "priority":
                    option["priority"],
                "risk":
                    option["risk"],
                "reasons":
                    list(
                        analysis.get(
                            "reasons",
                            [],
                        )
                    ),
                "recommendation":
                    analysis.get(
                        "recommendation"
                    ),
                "evidence_summary":
                    analysis.get(
                        "evidence_summary",
                        {},
                    ),
                "score_type":
                    analysis.get(
                        "score_type"
                    ),
            },

            "proposed_actions":
                actions,

            # Hard R9.2A boundary.
            "scope_expansion_allowed":
                False,
            "automatic_execution_allowed":
                False,
            "vulnerability_validation_allowed":
                False,
            "report_submission_allowed":
                False,
        }

    def _persist_investigation_plan(
        self,
        db,
        option,
        reviewer,
    ):
        plan = self._build_investigation_plan(
            option,
            reviewer,
        )

        now = time.time()

        existing = db.execute(
            """
            SELECT id
            FROM investigation_plans
            WHERE option_id=?
            """,
            (option["id"],),
        ).fetchone()

        raw = json.dumps(
            plan,
            sort_keys=True,
            separators=(",", ":"),
        )

        if existing:
            plan_id = existing["id"]

            db.execute(
                """
                UPDATE investigation_plans
                SET reviewer=?,
                    state=?,
                    updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    str(reviewer).strip(),
                    "awaiting_action_approval",
                    now,
                    raw,
                    plan_id,
                ),
            )
        else:
            plan_id = str(uuid.uuid4())

            db.execute(
                """
                INSERT INTO investigation_plans(
                    id,
                    option_id,
                    session,
                    target,
                    reviewer,
                    state,
                    created,
                    updated,
                    plan_json
                )
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    plan_id,
                    option["id"],
                    option["session"],
                    option["target"],
                    str(reviewer).strip(),
                    "awaiting_action_approval",
                    now,
                    now,
                    raw,
                ),
            )

        self._event(
            db,
            option["session"],
            "investigation_plan_created",
            (
                f"{option['target']} "
                f"plan={plan_id} "
                "awaiting_action_approval"
            ),
        )

        return plan_id

    def investigation_plans(
        self,
        session,
    ):
        with self.db() as db:
            rows = db.execute(
                """
                SELECT *
                FROM investigation_plans
                WHERE session=?
                ORDER BY created,id
                """,
                (session,),
            ).fetchall()

        plans = []

        for row in rows:
            item = dict(row)
            item["plan"] = json.loads(
                item.pop("plan_json")
            )
            plans.append(item)

        return plans

    def investigation_plan(
        self,
        plan_id,
    ):
        with self.db() as db:
            row = db.execute(
                """
                SELECT *
                FROM investigation_plans
                WHERE id=?
                """,
                (plan_id,),
            ).fetchone()

        if not row:
            raise BountyAgentError(
                "Unknown investigation plan"
            )

        item = dict(row)

        item["plan"] = json.loads(
            item.pop("plan_json")
        )

        return item

    def review_plan_action_evidence(
        self,
        plan_id,
        action_id,
        reviewer,
    ):
        """
        R9.5

        Review evidence that already exists in the completed
        reconnaissance mission.

        This method performs no network requests and creates
        no live mission tasks.
        """
        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        wrapper = self.investigation_plan(
            plan_id
        )

        plan = wrapper["plan"]

        selected = None

        for action in plan.get(
            "proposed_actions",
            [],
        ):
            if (
                str(action.get("id"))
                == str(action_id)
            ):
                selected = action
                break

        if selected is None:
            raise BountyAgentError(
                "Unknown investigation action"
            )

        if (
            selected.get("approval_state")
            != "approved"
        ):
            raise BountyAgentError(
                "Action must be approved before "
                "evidence review"
            )

        proposal = selected.get(
            "execution_proposal"
        )

        if not proposal:
            raise BountyAgentError(
                "Build an R9.4 proposal before "
                "evidence review"
            )

        if (
            proposal.get("proposal_state")
            != "ready_for_manual_review"
        ):
            raise BountyAgentError(
                "Action is not ready for manual review"
            )

        session_id = plan["session"]
        target = plan["target"]

        report = self.report(
            session_id
        )

        tasks = [
            task
            for task in report["mission"]["tasks"]
            if task.get("target") == target
        ]

        dns_tasks = [
            task
            for task in tasks
            if task.get("capability") == "dnsx"
        ]

        http_tasks = [
            task
            for task in tasks
            if task.get("capability") == "httpx"
        ]

        observations = []
        evidence_refs = []

        dns_records = []

        for task in dns_tasks:
            result = (
                task.get("evidence", {})
                .get("result", {})
            )

            for record in result.get(
                "records",
                [],
            ):
                dns_records.append(record)

            evidence_refs.append(
                {
                    "task_id": task.get("id"),
                    "capability": "dnsx",
                    "evidence_sha256":
                        task.get("evidence_sha256"),
                }
            )

        if dns_records:
            addresses = sorted({
                str(address)
                for record in dns_records
                for address in record.get("a", [])
            })

            cnames = sorted({
                str(cname)
                for record in dns_records
                for cname in record.get(
                    "cname",
                    [],
                )
            })

            observations.append(
                {
                    "kind": "dns_resolution",
                    "fact":
                        "Target resolved successfully.",
                    "addresses": addresses,
                    "cnames": cnames,
                }
            )

        http_records = []

        for task in http_tasks:
            result = (
                task.get("evidence", {})
                .get("result", {})
            )

            records = result.get(
                "records",
                [],
            )

            if records:
                http_records.extend(
                    records
                )
            else:
                # R9.5.1 compatibility:
                # Some existing tests/legacy adapters
                # expose one HTTP result directly rather
                # than under result.records[].
                if any(
                    key in result
                    for key in (
                        "status_code",
                        "status-code",
                        "title",
                        "technology",
                        "tech",
                        "webserver",
                        "content_type",
                    )
                ):
                    http_records.append(
                        result
                    )

            evidence_refs.append(
                {
                    "task_id": task.get("id"),
                    "capability": "httpx",
                    "evidence_sha256":
                        task.get("evidence_sha256"),
                }
            )

        statuses = sorted({
            record.get("status_code")
            for record in http_records
            if record.get("status_code")
            is not None
        })

        titles = sorted({
            str(record.get("title"))
            for record in http_records
            if record.get("title")
        })

        technologies = sorted({
            str(tech)
            for record in http_records
            for tech in (
                record.get("tech")
                or record.get("technology")
                or []
            )
        })

        servers = sorted({
            str(record.get("webserver"))
            for record in http_records
            if record.get("webserver")
        })

        content_types = sorted({
            str(record.get("content_type"))
            for record in http_records
            if record.get("content_type")
        })

        if http_records:
            observations.append(
                {
                    "kind": "http_response",
                    "fact":
                        "Authorized HTTP probe returned "
                        "structured response evidence.",
                    "status_codes": statuses,
                    "titles": titles,
                    "content_types":
                        content_types,
                    "servers": servers,
                    "technologies":
                        technologies,
                }
            )

        hypotheses = []

        if 200 in statuses:
            hypotheses.append(
                {
                    "id": "H1",
                    "statement":
                        "The reachable staging application "
                        "may expose behavior or functionality "
                        "that differs from the public "
                        "production surface.",
                    "basis":
                        "The reviewed staging target returned "
                        "a successful HTTP response.",
                    "confidence": "low",
                    "status": "unvalidated",
                    "requires_new_requests": True,
                    "required_capability":
                        "web_crawling",
                }
            )

        if (
            "Next.js" in technologies
            or "React" in technologies
        ):
            hypotheses.append(
                {
                    "id": "H2",
                    "statement":
                        "Client-side application assets may "
                        "contain additional routes or metadata "
                        "worth reviewing.",
                    "basis":
                        "Technology fingerprinting identified "
                        "a JavaScript application framework.",
                    "confidence": "low",
                    "status": "unvalidated",
                    "requires_new_requests": True,
                    "required_capability":
                        "web_crawling",
                }
            )

        review = {
            "schema":
                "jarvis-bounty-evidence-review-r9.5",

            "plan_id":
                plan_id,

            "action_id":
                str(action_id),

            "session":
                session_id,

            "target":
                target,

            "reviewer":
                reviewer,

            "reviewed_at":
                time.time(),

            "observations":
                observations,

            "hypotheses":
                hypotheses,

            "conclusion":
                (
                    "Interesting authorized staging "
                    "surface, but existing evidence does "
                    "not demonstrate a vulnerability."
                ),

            "classification":
                "recon_lead_not_vulnerability",

            "new_network_traffic":
                False,

            "new_live_tasks_created":
                False,

            "execution_allowed":
                False,

            "recommended_next_state":
                (
                    "hypothesis_selection"
                    if hypotheses
                    else "hold"
                ),

            "evidence_refs":
                evidence_refs,
        }

        selected["evidence_review"] = review
        selected["execution_allowed"] = False

        with self.db() as db:
            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            db.execute(
                """
                UPDATE investigation_plans
                SET updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    time.time(),
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                session_id,
                "investigation_evidence_review",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    "classification="
                    "recon_lead_not_vulnerability "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def opportunity_portfolio(
        self,
        session_id,
        *,
        reviewer=None,
    ):
        """
        R9.8A

        Build an authorization-aware opportunity portfolio from
        evidence already collected for one bounty session.

        No target traffic is created.
        No tools are executed.
        No authorization is expanded.

        Output lanes:
            AUTO_A
            AUTO_B
            MANUAL_A
            MANUAL_B
            BLOCKED
            SKIP
        """

        report = self.report(
            session_id
        )

        options = list(
            report.get(
                "options",
                [],
            )
        )

        plans = list(
            report.get(
                "investigation_plans",
                [],
            )
        )

        plan_by_target = {}

        for wrapper in plans:
            plan = wrapper.get(
                "plan",
                wrapper,
            )

            target = plan.get(
                "target"
            )

            if target:
                plan_by_target[
                    target
                ] = plan

        portfolio = []

        def contains_reason(
            reasons,
            fragment,
        ):
            fragment = fragment.lower()

            return any(
                fragment in str(reason).lower()
                for reason in reasons
            )

        for option in options:
            target = option.get(
                "target",
                "",
            )

            analysis = option.get(
                "analysis",
                {},
            )

            reasons = list(
                analysis.get(
                    "reasons",
                    [],
                )
            )

            suggested_actions = list(
                analysis.get(
                    "suggested_actions",
                    [],
                )
            )

            recon_score = int(
                analysis.get(
                    "score",
                    option.get(
                        "score",
                        0,
                    ),
                )
                or 0
            )

            priority = str(
                analysis.get(
                    "priority",
                    option.get(
                        "priority",
                        "informational",
                    ),
                )
            ).lower()

            state = str(
                option.get(
                    "state",
                    "awaiting_human",
                )
            )

            plan = plan_by_target.get(
                target
            )

            automation_score = 0
            manual_score = 0

            automation_reasons = []
            manual_reasons = []
            blockers = []
            capability_gaps = []

            # -----------------------------
            # Existing evidence value
            # -----------------------------

            automation_score += min(
                recon_score,
                50,
            )

            manual_score += min(
                recon_score,
                50,
            )

            if contains_reason(
                reasons,
                "api-like",
            ):
                automation_score += 14
                manual_score += 18

                automation_reasons.append(
                    "API-like application surface"
                )

                manual_reasons.append(
                    "API-like behavior may reward "
                    "authorization and object-boundary review"
                )

            if contains_reason(
                reasons,
                "2xx",
            ):
                automation_score += 12
                manual_score += 10

                automation_reasons.append(
                    "Reachable application surface"
                )

            if contains_reason(
                reasons,
                "client-error",
            ):
                automation_score += 9
                manual_score += 14

                manual_reasons.append(
                    "Client-error semantics may expose "
                    "interesting application behavior"
                )

            if contains_reason(
                reasons,
                "401/403",
            ):
                automation_score += 5
                manual_score += 12

                manual_reasons.append(
                    "Access-controlled surface may be useful "
                    "for manual authorization testing"
                )

            if contains_reason(
                reasons,
                "redirect",
            ):
                automation_score += 5
                manual_score += 6

            if contains_reason(
                reasons,
                "technology fingerprint",
            ):
                automation_score += 5
                manual_score += 4

            if contains_reason(
                reasons,
                "server fingerprint",
            ):
                automation_score += 3

            # -----------------------------
            # Priority weighting
            # -----------------------------

            if priority == "high":
                automation_score += 18
                manual_score += 18

            elif priority == "medium":
                automation_score += 10
                manual_score += 10

            elif priority == "low":
                automation_score += 3
                manual_score += 4

            # -----------------------------
            # Investigation-plan state
            # -----------------------------

            selected_hypothesis = None
            policy_state = None
            required_capability = None

            if plan:
                for action in plan.get(
                    "proposed_actions",
                    [],
                ):
                    review = action.get(
                        "evidence_review"
                    )

                    if not review:
                        continue

                    for hypothesis in review.get(
                        "hypotheses",
                        [],
                    ):
                        if (
                            hypothesis.get(
                                "selection_state"
                            )
                            == "selected"
                        ):
                            selected_hypothesis = hypothesis

                            required_capability = (
                                hypothesis.get(
                                    "required_capability"
                                )
                            )

                            proposal = hypothesis.get(
                                "validation_authorization_proposal",
                                {},
                            )

                            policy_review = proposal.get(
                                "capability_policy_review",
                                {},
                            )

                            policy_state = (
                                policy_review.get(
                                    "policy_state"
                                )
                                or proposal.get(
                                    "proposal_state"
                                )
                            )

                            break

                    if selected_hypothesis:
                        break

            # -----------------------------
            # Authorization / policy friction
            # -----------------------------

            if policy_state == "capability_policy_unclear":
                automation_score -= 35

                blockers.append(
                    "Required capability policy is unclear"
                )

                capability_gaps.append(
                    required_capability
                    or "unknown"
                )

            elif policy_state == "capability_policy_denied":
                automation_score -= 100

                blockers.append(
                    "Program policy denies the required capability"
                )

                capability_gaps.append(
                    required_capability
                    or "unknown"
                )

            elif (
                policy_state
                == "parent_capability_authorization_required"
            ):
                automation_score -= 30

                blockers.append(
                    "Required capability is not present "
                    "in parent authorization"
                )

                capability_gaps.append(
                    required_capability
                    or "unknown"
                )

            elif policy_state == "capability_policy_reviewed":
                automation_score += 12

                automation_reasons.append(
                    "Required capability policy has been reviewed"
                )

            # -----------------------------
            # Suggested-action friction
            # -----------------------------

            suggestion_text = " ".join(
                str(x).lower()
                for x in suggested_actions
            )

            if "map" in suggestion_text:
                if (
                    "web_crawling"
                    not in capability_gaps
                    and not policy_state
                ):
                    capability_gaps.append(
                        "web_crawling"
                    )

            if "deeper investigation" in suggestion_text:
                manual_score += 5

            # -----------------------------
            # Manual hunt themes
            # -----------------------------

            themes = []

            if contains_reason(
                reasons,
                "api-like",
            ):
                themes.extend([
                    {
                        "theme":
                            "Authorization boundaries",
                        "plain_english":
                            (
                                "Check whether one user, role, "
                                "workspace, or tenant can access "
                                "objects belonging to another."
                            ),
                        "evidence":
                            (
                                "Save both permitted and denied "
                                "request/response comparisons."
                            ),
                    },
                    {
                        "theme":
                            "Object-level access control",
                        "plain_english":
                            (
                                "Compare object identifiers and "
                                "verify that changing an identifier "
                                "does not expose another user's data."
                            ),
                        "evidence":
                            (
                                "Capture object IDs, account roles, "
                                "request method, response status, "
                                "and returned data."
                            ),
                    },
                ])

            if contains_reason(
                reasons,
                "401/403",
            ):
                themes.append(
                    {
                        "theme":
                            "Access-control behavior",
                        "plain_english":
                            (
                                "Compare authenticated and "
                                "unauthenticated behavior without "
                                "attempting prohibited bypasses."
                            ),
                        "evidence":
                            (
                                "Record the expected denied response "
                                "and any inconsistent behavior."
                            ),
                    }
                )

            if contains_reason(
                reasons,
                "redirect",
            ):
                themes.append(
                    {
                        "theme":
                            "Redirect and trust-boundary review",
                        "plain_english":
                            (
                                "Observe where redirects lead and "
                                "whether authentication or sensitive "
                                "state crosses an unexpected boundary."
                            ),
                        "evidence":
                            (
                                "Capture Location headers and the "
                                "source/destination scope status."
                            ),
                    }
                )

            if contains_reason(
                reasons,
                "2xx",
            ):
                themes.append(
                    {
                        "theme":
                            "Application behavior review",
                        "plain_english":
                            (
                                "Explore normal permitted application "
                                "flows and look for inconsistent "
                                "permissions or unintended exposure."
                            ),
                        "evidence":
                            (
                                "Save screenshots plus matching "
                                "HTTP request/response evidence."
                            ),
                    }
                )

            if not themes:
                themes.append(
                    {
                        "theme":
                            "Surface reconnaissance review",
                        "plain_english":
                            (
                                "Review the existing evidence and "
                                "decide whether this surface justifies "
                                "additional human investigation."
                            ),
                        "evidence":
                            (
                                "Preserve status codes, headers, "
                                "titles, technology evidence, "
                                "and scope provenance."
                            ),
                    }
                )

            # -----------------------------
            # Lane classification
            # -----------------------------

            automation_score = max(
                0,
                min(
                    100,
                    automation_score,
                ),
            )

            manual_score = max(
                0,
                min(
                    100,
                    manual_score,
                ),
            )

            if (
                policy_state
                == "capability_policy_denied"
            ):
                lane = "BLOCKED"

            elif blockers:
                if manual_score >= 55:
                    lane = "MANUAL_A"
                elif manual_score >= 35:
                    lane = "MANUAL_B"
                else:
                    lane = "BLOCKED"

            # A capability gap is an authorization boundary.
            # High technical value does not make a target
            # eligible for automatic execution.
            elif capability_gaps:
                if manual_score >= 65:
                    lane = "MANUAL_A"
                elif manual_score >= 45:
                    lane = "MANUAL_B"
                else:
                    lane = "BLOCKED"

            elif automation_score >= 65:
                lane = "AUTO_A"

            elif automation_score >= 45:
                lane = "AUTO_B"

            elif manual_score >= 55:
                lane = "MANUAL_A"

            elif manual_score >= 35:
                lane = "MANUAL_B"

            else:
                lane = "SKIP"

            # If we lack explicit authorization for deeper
            # automated work, never label it executable merely
            # because the score is high.
            automatic_execution_ready = False

            # -----------------------------
            # Operator brief
            # -----------------------------

            operator_brief = {
                "why_this_matters":
                    manual_reasons
                    or [
                        analysis.get(
                            "recommendation",
                            (
                                "Review existing evidence before "
                                "deciding whether to invest time."
                            ),
                        )
                    ],

                "hunt_themes":
                    themes,

                "what_to_capture": [
                    "Exact in-scope target",
                    "Account / role context if applicable",
                    "Request method and URL",
                    "Relevant request headers/body",
                    "Response status and body",
                    "Screenshots for visible application behavior",
                    "Expected behavior",
                    "Observed behavior",
                    "Security impact if demonstrated",
                ],

                "stop_conditions": [
                    "Target leaves reviewed scope",
                    "Required capability is not authorized",
                    "Program policy is unclear or prohibits the action",
                    "Testing would modify another user's data",
                    "Testing could become destructive",
                    "Testing requires credential attacks",
                    "A third-party system is reached",
                ],

                "report_quality_check": [
                    "Reproducible steps",
                    "Clear affected asset",
                    "Concrete security impact",
                    "Minimal necessary testing",
                    "Scope provenance preserved",
                    "No claim stronger than the evidence supports",
                ],
            }

            portfolio.append(
                {
                    "target":
                        target,

                    "recon_score":
                        recon_score,

                    "priority":
                        priority,

                    "decision_state":
                        state,

                    "lane":
                        lane,

                    "automation_viability_score":
                        automation_score,

                    "manual_hunt_viability_score":
                        manual_score,

                    # R9.8A does not yet have a normalized
                    # cross-program bounty feed.
                    "payout_score":
                        None,

                    "payout_data_state":
                        "not_yet_integrated",

                    "policy_state":
                        policy_state,

                    "required_capability":
                        required_capability,

                    "capability_gaps":
                        sorted({
                            x
                            for x in capability_gaps
                            if x
                        }),

                    "blockers":
                        blockers,

                    "automation_reasons":
                        automation_reasons,

                    "manual_reasons":
                        manual_reasons,

                    "automatic_execution_ready":
                        automatic_execution_ready,

                    "operator_brief":
                        operator_brief,

                    "execution_allowed":
                        False,

                    "scope_expansion_allowed":
                        False,
                }
            )

        lane_order = {
            "AUTO_A": 0,
            "AUTO_B": 1,
            "MANUAL_A": 2,
            "MANUAL_B": 3,
            "BLOCKED": 4,
            "SKIP": 5,
        }

        portfolio.sort(
            key=lambda item: (
                lane_order.get(
                    item["lane"],
                    99,
                ),
                -max(
                    item[
                        "automation_viability_score"
                    ],
                    item[
                        "manual_hunt_viability_score"
                    ],
                ),
                -item["recon_score"],
                item["target"],
            )
        )

        counts = {}

        for item in portfolio:
            counts[item["lane"]] = (
                counts.get(
                    item["lane"],
                    0,
                )
                + 1
            )

        return {
            "schema":
                "jarvis-bounty-opportunity-portfolio-r9.8a",

            "session":
                session_id,

            "program":
                report.get(
                    "session",
                    {},
                ).get(
                    "program"
                )
                or report.get(
                    "mission",
                    {},
                ).get(
                    "program"
                ),

            "reviewer":
                reviewer,

            "generated_at":
                time.time(),

            "source":
                "existing_authorized_recon_evidence",

            "new_network_traffic":
                False,

            "tools_executed":
                False,

            "automatic_execution_enabled":
                False,

            "payout_ranking_enabled":
                False,

            "payout_ranking_note":
                (
                    "R9.8A ranks technical viability only. "
                    "R9.8B will integrate program bounty "
                    "ranges and automation-policy metadata."
                ),

            "lane_counts":
                counts,

            "opportunities":
                portfolio,
        }

    def review_validation_capability_policy(
        self,
        plan_id,
        action_id,
        hypothesis_id,
        reviewer,
        *,
        decision,
        policy_source,
        policy_evidence,
        constraints=None,
    ):
        """
        R9.7D

        Record a human review of whether program policy
        permits the capability required by a selected
        validation hypothesis.

        This records policy interpretation only.

        It does NOT:
        - modify the parent R5 authorization
        - authorize validation
        - execute tools
        - create target traffic
        """
        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        decision = str(
            decision or ""
        ).strip().lower()

        if decision not in {
            "permit",
            "deny",
            "unclear",
        }:
            raise BountyAgentError(
                "Policy decision must be "
                "permit, deny, or unclear"
            )

        policy_source = str(
            policy_source or ""
        ).strip()

        if not policy_source:
            raise BountyAgentError(
                "Policy source is required"
            )

        policy_evidence = str(
            policy_evidence or ""
        ).strip()

        if not policy_evidence:
            raise BountyAgentError(
                "Policy evidence is required"
            )

        wrapper = self.investigation_plan(
            plan_id
        )

        plan = wrapper["plan"]

        action = None

        for item in plan.get(
            "proposed_actions",
            [],
        ):
            if (
                str(item.get("id"))
                == str(action_id)
            ):
                action = item
                break

        if action is None:
            raise BountyAgentError(
                "Unknown investigation action"
            )

        review = action.get(
            "evidence_review"
        )

        if not review:
            raise BountyAgentError(
                "R9.5 evidence review is required"
            )

        hypothesis = None

        for item in review.get(
            "hypotheses",
            [],
        ):
            if (
                str(item.get("id"))
                == str(hypothesis_id)
            ):
                hypothesis = item
                break

        if hypothesis is None:
            raise BountyAgentError(
                "Unknown evidence hypothesis"
            )

        if (
            hypothesis.get("selection_state")
            != "selected"
        ):
            raise BountyAgentError(
                "Hypothesis must be selected first"
            )

        proposal = hypothesis.get(
            "validation_authorization_proposal"
        )

        if not proposal:
            raise BountyAgentError(
                "R9.7 validation authorization "
                "proposal is required first"
            )

        required_capability = proposal.get(
            "required_capability"
        )

        now = time.time()

        state_map = {
            "permit":
                "capability_policy_reviewed",
            "deny":
                "capability_policy_denied",
            "unclear":
                "capability_policy_unclear",
        }

        policy_review = {
            "schema":
                "jarvis-bounty-capability-policy-review-r9.7d",

            "plan_id":
                plan_id,

            "action_id":
                str(action_id),

            "hypothesis_id":
                str(hypothesis_id),

            "target":
                plan.get("target"),

            "required_capability":
                required_capability,

            "decision":
                decision,

            "policy_source":
                policy_source,

            "policy_evidence":
                policy_evidence,

            "constraints":
                list(constraints or []),

            "reviewer":
                reviewer,

            "reviewed_at":
                now,

            "policy_state":
                state_map[decision],

            # These remain locked regardless of policy
            # interpretation.
            "parent_authorization_modified":
                False,

            "validation_authorized":
                False,

            "execution_allowed":
                False,

            "automatic_execution_allowed":
                False,

            "scope_expansion_allowed":
                False,

            "report_submission_allowed":
                False,
        }

        proposal[
            "capability_policy_review"
        ] = policy_review

        proposal[
            "proposal_state"
        ] = state_map[decision]

        proposal[
            "validation_authorized"
        ] = False

        proposal[
            "execution_allowed"
        ] = False

        hypothesis[
            "validation_state"
        ] = state_map[decision]

        hypothesis[
            "validation_authorized"
        ] = False

        hypothesis[
            "execution_allowed"
        ] = False

        action[
            "execution_allowed"
        ] = False

        plan[
            "scope_expansion_allowed"
        ] = False

        plan[
            "automatic_execution_allowed"
        ] = False

        plan[
            "vulnerability_validation_allowed"
        ] = False

        plan[
            "report_submission_allowed"
        ] = False

        with self.db() as db:
            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            db.execute(
                """
                UPDATE investigation_plans
                SET updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    now,
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                plan["session"],
                "validation_capability_policy_review",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    f"hypothesis={hypothesis_id} "
                    f"capability={required_capability} "
                    f"decision={decision} "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def propose_validation_authorization(
        self,
        plan_id,
        action_id,
        hypothesis_id,
        reviewer,
        *,
        request_budget=10,
        ttl=1800,
    ):
        """
        R9.7A

        Build a narrowly bounded validation authorization
        proposal for a selected hypothesis.

        This does NOT grant execution authority.
        """

        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        if (
            type(request_budget) is not int
            or not 1 <= request_budget <= 25
        ):
            raise BountyAgentError(
                "Validation request budget must be 1..25"
            )

        if (
            type(ttl) is not int
            or not 60 <= ttl <= 3600
        ):
            raise BountyAgentError(
                "Validation TTL must be 60..3600 seconds"
            )

        wrapper = self.investigation_plan(
            plan_id
        )

        plan = wrapper["plan"]

        action = None

        for item in plan.get(
            "proposed_actions",
            [],
        ):
            if (
                str(item.get("id"))
                == str(action_id)
            ):
                action = item
                break

        if action is None:
            raise BountyAgentError(
                "Unknown investigation action"
            )

        review = action.get(
            "evidence_review"
        )

        if not review:
            raise BountyAgentError(
                "R9.5 evidence review is required"
            )

        hypothesis = None

        for item in review.get(
            "hypotheses",
            [],
        ):
            if (
                str(item.get("id"))
                == str(hypothesis_id)
            ):
                hypothesis = item
                break

        if hypothesis is None:
            raise BountyAgentError(
                "Unknown evidence hypothesis"
            )

        if (
            hypothesis.get("selection_state")
            != "selected"
        ):
            raise BountyAgentError(
                "Hypothesis must be selected first"
            )

        if (
            hypothesis.get("validation_state")
            != "awaiting_validation_authorization"
        ):
            raise BountyAgentError(
                "Hypothesis is not awaiting "
                "validation authorization"
            )

        session_id = plan["session"]
        target = plan["target"]

        report = self.report(
            session_id
        )

        mission = report.get(
            "mission",
            {}
        )

        parent_auth_id = mission.get(
            "authorization"
        )

        required_capability = (
            hypothesis.get(
                "required_capability"
            )
        )

        active_capabilities = []
        active_providers = []

        # Prefer capability state already captured
        # in the approved R9.4 proposal.
        execution_proposal = action.get(
            "execution_proposal",
            {}
        )

        active_capabilities = list(
            execution_proposal.get(
                "active_logical_capabilities",
                [],
            )
        )

        active_providers = list(
            execution_proposal.get(
                "active_approved_providers",
                [],
            )
        )

        capability_authorized = (
            required_capability
            in active_capabilities
        )

        now = time.time()

        proposal_state = (
            "ready_for_validation_authorization"
            if capability_authorized
            else
            "parent_capability_authorization_required"
        )

        proposal = {
            "schema":
                "jarvis-bounty-validation-authorization-r9.7a",

            "plan_id":
                plan_id,

            "action_id":
                str(action_id),

            "hypothesis_id":
                str(hypothesis_id),

            "session":
                session_id,

            "parent_authorization_id":
                parent_auth_id,

            "target":
                target,

            "hypothesis":
                hypothesis.get("statement"),

            "required_capability":
                required_capability,

            "capability_authorized":
                capability_authorized,

            "proposal_state":
                proposal_state,

            "allowed_methods": [
                "GET",
                "HEAD",
            ],

            "request_budget":
                request_budget,

            "ttl_seconds":
                ttl,

            "created_at":
                now,

            "expires_at":
                now + ttl,

            "reviewer":
                reviewer,

            "scope": {
                "include": [
                    target,
                ],
                "scope_expansion_allowed":
                    False,
                "cross_scope_redirect_following":
                    False,
            },

            "prohibited": [
                "authentication_bypass",
                "credential_attacks",
                "account_modification",
                "destructive_actions",
                "production_targets",
                "scope_expansion",
            ],

            "active_logical_capabilities":
                active_capabilities,

            "active_approved_providers":
                active_providers,

            "validation_authorized":
                False,

            "execution_allowed":
                False,

            "automatic_execution_allowed":
                False,

            "report_submission_allowed":
                False,

            "note":
                (
                    "R9.7A creates a bounded validation "
                    "authorization proposal only. "
                    "It does not grant execution authority."
                ),
        }

        hypothesis[
            "validation_authorization_proposal"
        ] = proposal

        hypothesis[
            "validation_authorized"
        ] = False

        hypothesis[
            "execution_allowed"
        ] = False

        hypothesis[
            "validation_state"
        ] = proposal_state

        action[
            "execution_allowed"
        ] = False

        plan[
            "automatic_execution_allowed"
        ] = False

        plan[
            "scope_expansion_allowed"
        ] = False

        plan[
            "vulnerability_validation_allowed"
        ] = False

        plan[
            "report_submission_allowed"
        ] = False

        with self.db() as db:
            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            db.execute(
                """
                UPDATE investigation_plans
                SET updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    now,
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                session_id,
                "validation_authorization_proposal",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    f"hypothesis={hypothesis_id} "
                    f"capability={required_capability} "
                    f"state={proposal_state} "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def decide_evidence_hypothesis(
        self,
        plan_id,
        action_id,
        hypothesis_id,
        decision,
        reviewer,
    ):
        """
        R9.6A

        Persist a human decision for one hypothesis created by
        the R9.5 evidence review.

        This does not authorize or execute validation.
        """
        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        decision = str(
            decision or ""
        ).strip().lower()

        if decision not in {
            "select",
            "hold",
            "reject",
        }:
            raise BountyAgentError(
                "Decision must be select, hold, or reject"
            )

        wrapper = self.investigation_plan(
            plan_id
        )

        plan = wrapper["plan"]

        selected_action = None

        for action in plan.get(
            "proposed_actions",
            [],
        ):
            if (
                str(action.get("id"))
                == str(action_id)
            ):
                selected_action = action
                break

        if selected_action is None:
            raise BountyAgentError(
                "Unknown investigation action"
            )

        review = selected_action.get(
            "evidence_review"
        )

        if not review:
            raise BountyAgentError(
                "R9.5 evidence review is required first"
            )

        selected_hypothesis = None

        for hypothesis in review.get(
            "hypotheses",
            [],
        ):
            if (
                str(hypothesis.get("id"))
                == str(hypothesis_id)
            ):
                selected_hypothesis = hypothesis
                break

        if selected_hypothesis is None:
            raise BountyAgentError(
                "Unknown evidence hypothesis"
            )

        now = time.time()

        state_map = {
            "select": "selected",
            "hold": "held",
            "reject": "rejected",
        }

        selected_hypothesis[
            "selection_state"
        ] = state_map[decision]

        selected_hypothesis[
            "selected_by"
        ] = reviewer

        selected_hypothesis[
            "selected_at"
        ] = now

        selected_hypothesis[
            "validation_state"
        ] = (
            "awaiting_validation_authorization"
            if decision == "select"
            else "not_requested"
        )

        selected_hypothesis[
            "validation_authorized"
        ] = False

        selected_hypothesis[
            "execution_allowed"
        ] = False

        selected_hypothesis[
            "scope_expansion_allowed"
        ] = False

        selected_hypothesis[
            "automatic_execution_allowed"
        ] = False

        selected_hypothesis[
            "report_submission_allowed"
        ] = False

        selected_hypothesis[
            "decision"
        ] = decision

        review[
            "hypothesis_decision_state"
        ] = (
            "selection_made"
            if decision == "select"
            else "reviewed"
        )

        if decision == "select":
            review[
                "selected_hypothesis_id"
            ] = str(
                hypothesis_id
            )

            review[
                "recommended_next_state"
            ] = (
                "validation_authorization_required"
            )

        selected_action[
            "execution_allowed"
        ] = False

        plan[
            "automatic_execution_allowed"
        ] = False

        plan[
            "scope_expansion_allowed"
        ] = False

        plan[
            "vulnerability_validation_allowed"
        ] = False

        plan[
            "report_submission_allowed"
        ] = False

        with self.db() as db:
            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            db.execute(
                """
                UPDATE investigation_plans
                SET updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    now,
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                plan["session"],
                "investigation_hypothesis_decision",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    f"hypothesis={hypothesis_id} "
                    f"decision={decision} "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def propose_plan_action(
        self,
        plan_id,
        action_id,
        reviewer,
    ):
        """
        R9.4

        Translate an already-approved investigation action
        into a bounded execution proposal.

        This method NEVER executes a tool, creates a live
        mission task, or expands authorization.
        """
        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        with self.db() as db:
            row = db.execute(
                """
                SELECT *
                FROM investigation_plans
                WHERE id=?
                """,
                (plan_id,),
            ).fetchone()

            if not row:
                raise BountyAgentError(
                    "Unknown investigation plan"
                )

            plan = json.loads(
                row["plan_json"]
            )

            selected = None

            for action in plan.get(
                "proposed_actions",
                [],
            ):
                if (
                    str(action.get("id"))
                    == str(action_id)
                ):
                    selected = action
                    break

            if selected is None:
                raise BountyAgentError(
                    "Unknown investigation action"
                )

            if (
                selected.get("approval_state")
                != "approved"
            ):
                raise BountyAgentError(
                    "Action must be approved before "
                    "an execution proposal can be built"
                )

            session_row = db.execute(
                """
                SELECT *
                FROM sessions
                WHERE id=?
                """,
                (row["session"],),
            ).fetchone()

            if not session_row:
                raise BountyAgentError(
                    "Investigation session no longer exists"
                )

            scope = (
                self.authorization_store.live_scope(
                    session_row["authorization"]
                )
            )

            required = str(
                selected.get(
                    "capability_required"
                )
                or "human_review"
            )

            logical = set(
                scope.logical_capabilities
            )

            providers = set(
                scope.approved_providers
            )

            if required == "human_review":
                proposal_state = (
                    "ready_for_manual_review"
                )

                capability_authorized = True
                authorization_required = False
                new_tool_execution_required = False

                provider = None

                rationale = (
                    "The approved action can be completed "
                    "using evidence already collected by "
                    "the authorized reconnaissance pipeline."
                )

            elif required in logical:
                proposal_state = (
                    "authorized_capability_available"
                )

                capability_authorized = True
                authorization_required = False
                new_tool_execution_required = True

                provider = None

                rationale = (
                    "The required logical capability is "
                    "present in the active authorization, "
                    "but R9.4 does not select or execute "
                    "a provider."
                )

            else:
                proposal_state = (
                    "authorization_required"
                )

                capability_authorized = False
                authorization_required = True
                new_tool_execution_required = True

                provider = None

                rationale = (
                    "The required capability is not present "
                    "in the active reviewed authorization. "
                    "Execution remains blocked."
                )

            proposal = {
                "schema":
                    "jarvis-bounty-action-proposal-r9.4",

                "plan_id":
                    plan_id,

                "action_id":
                    str(action_id),

                "target":
                    plan.get("target"),

                "action":
                    selected.get("action"),

                "capability_required":
                    required,

                "proposal_state":
                    proposal_state,

                "capability_authorized":
                    capability_authorized,

                "authorization_required":
                    authorization_required,

                "new_tool_execution_required":
                    new_tool_execution_required,

                "provider_selected":
                    provider,

                "active_logical_capabilities":
                    sorted(logical),

                "active_approved_providers":
                    sorted(providers),

                "reviewer":
                    reviewer,

                "created_at":
                    time.time(),

                "rationale":
                    rationale,

                # R9.4 hard boundary.
                "execution_allowed":
                    False,

                "automatic_execution_allowed":
                    False,

                "scope_expansion_allowed":
                    False,
            }

            selected[
                "execution_proposal"
            ] = proposal

            selected[
                "execution_allowed"
            ] = False

            plan[
                "automatic_execution_allowed"
            ] = False

            plan[
                "scope_expansion_allowed"
            ] = False

            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            now = time.time()

            db.execute(
                """
                UPDATE investigation_plans
                SET updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    now,
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                row["session"],
                "investigation_action_proposal",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    f"state={proposal_state} "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def decide_plan_action(
        self,
        plan_id,
        action_id,
        decision,
        reviewer,
    ):
        """
        R9.3

        Record an explicit human decision for one proposed
        investigation action.

        Approval does NOT authorize execution.
        It only makes the action eligible for a future,
        separately gated execution workflow.
        """
        decision = str(
            decision
        ).strip().lower()

        if decision not in {
            "approve",
            "reject",
        }:
            raise BountyAgentError(
                "Action decision must be approve or reject"
            )

        reviewer = str(
            reviewer or ""
        ).strip()

        if not reviewer:
            raise BountyAgentError(
                "Reviewer identity is required"
            )

        action_id = str(
            action_id or ""
        ).strip()

        if not action_id:
            raise BountyAgentError(
                "Action id is required"
            )

        with self.db() as db:
            row = db.execute(
                """
                SELECT *
                FROM investigation_plans
                WHERE id=?
                """,
                (plan_id,),
            ).fetchone()

            if not row:
                raise BountyAgentError(
                    "Unknown investigation plan"
                )

            plan = json.loads(
                row["plan_json"]
            )

            actions = plan.get(
                "proposed_actions",
                [],
            )

            selected = None

            for action in actions:
                if (
                    str(action.get("id"))
                    == action_id
                ):
                    selected = action
                    break

            if selected is None:
                raise BountyAgentError(
                    "Unknown investigation action"
                )

            now = time.time()

            selected[
                "approval_state"
            ] = (
                "approved"
                if decision == "approve"
                else "rejected"
            )

            selected[
                "reviewer"
            ] = reviewer

            selected[
                "reviewed_at"
            ] = now

            # R9.3 hard boundary:
            # approval is NOT execution authority.
            selected[
                "execution_allowed"
            ] = False

            unresolved = [
                action
                for action in actions
                if (
                    action.get(
                        "approval_state"
                    )
                    == "not_approved"
                )
            ]

            if unresolved:
                plan_state = (
                    "awaiting_action_approval"
                )
            else:
                plan_state = (
                    "action_decisions_complete"
                )

            plan["state"] = plan_state

            # Preserve global R9.2/R9.3 boundaries.
            plan[
                "automatic_execution_allowed"
            ] = False

            plan[
                "scope_expansion_allowed"
            ] = False

            plan[
                "vulnerability_validation_allowed"
            ] = False

            plan[
                "report_submission_allowed"
            ] = False

            raw = json.dumps(
                plan,
                sort_keys=True,
                separators=(",", ":"),
            )

            db.execute(
                """
                UPDATE investigation_plans
                SET state=?,
                    updated=?,
                    plan_json=?
                WHERE id=?
                """,
                (
                    plan_state,
                    now,
                    raw,
                    plan_id,
                ),
            )

            self._event(
                db,
                row["session"],
                "investigation_action_decision",
                (
                    f"plan={plan_id} "
                    f"action={action_id} "
                    f"decision={decision} "
                    f"reviewer={reviewer}"
                ),
            )

        return self.investigation_plan(
            plan_id
        )

    def decide(self, option_id, decision, reviewer):
        decision = str(decision).strip().lower()
        if decision not in {"pursue", "hold", "reject"}:
            raise BountyAgentError("Decision must be pursue, hold, or reject")
        if not reviewer or not str(reviewer).strip():
            raise BountyAgentError("Reviewer identity is required")

        with self.db() as db:
            row = db.execute(
                "SELECT * FROM options WHERE id=?",
                (option_id,),
            ).fetchone()

            if not row:
                raise BountyAgentError(
                    "Unknown option"
                )

            db.execute(
                """
                UPDATE options
                SET state=?,reviewed=?,reviewer=?
                WHERE id=?
                """,
                (
                    decision,
                    time.time(),
                    str(reviewer).strip(),
                    option_id,
                ),
            )

            self._event(
                db,
                row["session"],
                "human_decision",
                (
                    f"{decision}:{row['target']} "
                    f"by {reviewer}"
                ),
            )

            if decision == "pursue":
                option = dict(row)
                option["analysis"] = json.loads(
                    option["analysis"]
                )

                self._persist_investigation_plan(
                    db,
                    option,
                    reviewer,
                )

        return self.option(option_id)

    def option(self, option_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM options WHERE id=?", (option_id,)).fetchone()
        if not row:
            raise BountyAgentError("Unknown option")
        item = dict(row)
        item["analysis"] = json.loads(item["analysis"])
        return item

    def report(self, session):
        current = self._session(session)
        live_report = self.live_store.report(current["mission"])
        with self.db() as db:
            option_rows = db.execute(
                "SELECT * FROM options WHERE session=? ORDER BY score DESC,target",
                (session,),
            ).fetchall()
            events = [dict(x) for x in db.execute(
                "SELECT * FROM events WHERE session=? ORDER BY id", (session,)
            ).fetchall()]

        options = []
        for row in option_rows:
            item = dict(row)
            item["analysis"] = json.loads(item["analysis"])
            options.append(item)

        return {
            "schema": "jarvis-bounty-agent-r6",
            "session": current,
            "mission": live_report,
            "options": options,
            "investigation_plans":
                self.investigation_plans(
                    session
                ),
            "events": events,
            "orchestration": {
                "planner": "capability-router-r8.9",
                "logical_capabilities": (
                    [
                        "subdomain_discovery",
                        "dns_resolution",
                        "http_probe",
                    ]
                    if any(
                        task.get("capability") == "dnsx"
                        for task in live_report.get(
                            "tasks",
                            [],
                        )
                    )
                    else [
                        "subdomain_discovery",
                        "http_probe",
                    ]
                ),
            },
            "human_gate": {
                "required_for": [
                    "deeper target-specific investigation",
                    "vulnerability validation",
                    "report submission",
                ],
                "automatic_recon_capabilities": ["subfinder", "httpx"],
            },
        }

    def list_sessions(self, limit=50):
        limit = max(1, min(int(limit), 200))
        with self.db() as db:
            rows = db.execute(
                "SELECT * FROM sessions ORDER BY updated DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(x) for x in rows]
