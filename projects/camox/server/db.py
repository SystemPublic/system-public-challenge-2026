"""The product database (Postgres on Neon, DATABASE_URL): profiles, projects and runs.
User keys are stored as Fernet(KEY_SECRET) over a JSON dict; only key names ever leave this module."""
import json
import os

import psycopg
from cryptography.fernet import Fernet
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCHEMA = """
create table if not exists profiles(id serial primary key, name text not null, role text, organisation text,
    about text, keys bytea, created_at timestamptz default now());
create table if not exists projects(id serial primary key, profile_id int references profiles on delete cascade,
    title text not null, created_at timestamptz default now());
alter table projects add column if not exists goals text not null default '';
alter table projects add column if not exists dashboard jsonb;
alter table projects add column if not exists dashboard_status text;
update projects set dashboard_status = 'failed' where dashboard_status like 'building%';  -- a restart ends builds
alter table projects add column if not exists reports jsonb not null default '[]';
alter table projects add column if not exists report_status text;
update projects set report_status = 'failed' where report_status like 'building%';
create table if not exists runs(id serial primary key, project_id int references projects on delete cascade,
    query text not null, agents text[], status text not null default 'running', answer jsonb,
    events jsonb not null default '[]', created_at timestamptz default now(), finished_at timestamptz);
create table if not exists threads(id serial primary key, project_id int references projects on delete cascade,
    title text not null, created_at timestamptz default now());
alter table runs add column if not exists thread_id int references threads on delete cascade;
"""
EXAMPLES = [
    ("Amara Okafor", "Jobs analyst", "World Bank",
     "Example profile. Analyses labour markets and jobs programmes in low- and middle-income countries."),
    ("Lucia Mendes", "Malaria researcher", "PATH",
     "Example profile. Works on malaria prevention and vaccine roll-out in sub-Saharan Africa."),
    ("Tom Hartley", "Childhood obesity policy lead", "Nesta",
     "Example profile. Leads policy work on reducing childhood obesity in the UK."),
]
PROFILE_COLS = "id, name, role, organisation, about"


_conn = None


def q(sql, args=None, one=False):
    """Run one statement on the shared connection (reopened once if Neon dropped it);
    return the rows (or the first row) as dicts."""
    global _conn
    for attempt in (1, 2):
        try:
            if _conn is None or _conn.closed:
                _conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True, row_factory=dict_row)
            cur = _conn.execute(sql, args)
            rows = cur.fetchall() if cur.description else []
            return (rows[0] if rows else None) if one else rows
        except psycopg.OperationalError:
            _conn = None
            if attempt == 2:
                raise


def init():
    q(SCHEMA)
    if not q("select 1 from profiles limit 1"):
        for row in EXAMPLES:
            q("insert into profiles(name, role, organisation, about) values (%s, %s, %s, %s)", row)


# Profiles and keys
def _fernet():
    return Fernet(os.environ["KEY_SECRET"])


def _decrypt(blob) -> dict:
    return json.loads(_fernet().decrypt(bytes(blob))) if blob else {}


def _public(row):
    row["key_names"] = sorted(_decrypt(row.pop("keys")))
    return row


def list_profiles():
    return [_public(r) for r in q(f"select {PROFILE_COLS}, keys from profiles order by id")]


def get_profile(profile_id):
    return q(f"select {PROFILE_COLS} from profiles where id = %s", (profile_id,), one=True)


def create_profile(name, role, organisation, about):
    return _public(q(f"insert into profiles(name, role, organisation, about) values (%s, %s, %s, %s) "
                     f"returning {PROFILE_COLS}, keys", (name, role, organisation, about), one=True))


def profile_keys(profile_id) -> dict:
    """Decrypted keys for a profile, for the tools that need them."""
    row = q("select keys from profiles where id = %s", (profile_id,), one=True)
    return _decrypt(row["keys"]) if row else {}


def set_keys(profile_id, updates: dict):
    keys = {**profile_keys(profile_id), **updates}
    keys = {k: v for k, v in keys.items() if v}
    q("update profiles set keys = %s where id = %s", (_fernet().encrypt(json.dumps(keys).encode()), profile_id))
    return sorted(keys)


# Projects
def list_projects(profile_id):
    return q("select p.id, p.title, p.goals, p.created_at, count(r.id)::int as n_runs from projects p "
             "left join runs r on r.project_id = p.id where p.profile_id = %s group by p.id order by p.id desc",
             (profile_id,))


def create_project(profile_id, title, goals=""):
    return q("insert into projects(profile_id, title, goals) values (%s, %s, %s) "
             "returning id, title, goals, profile_id, created_at", (profile_id, title, goals), one=True)


def update_project(project_id, title, goals):
    return q("update projects set title = %s, goals = %s where id = %s returning id, title, goals, profile_id",
             (title, goals, project_id), one=True)


def get_project(project_id):
    project = q("select id, title, goals, profile_id, dashboard, dashboard_status, reports, report_status from projects where id = %s", (project_id,), one=True)
    if project:
        project["runs"] = q("select id, query, status, created_at, answer, thread_id from runs where project_id = %s "
                            "order by id", (project_id,))
    return project


def set_dashboard(project_id, status, dashboard=None):
    """Status is 'building: <progress>', 'done' or 'failed'; a rebuild keeps the old dashboard until the new one lands."""
    q("update projects set dashboard_status = %s, dashboard = coalesce(%s, dashboard) where id = %s",
      (status, Jsonb(dashboard) if dashboard else None, project_id))


def set_report_status(project_id, status):
    q("update projects set report_status = %s where id = %s", (status, project_id))


def add_report(project_id, version):
    """Appends a report version (numbered here, never overwritten) and marks the build done."""
    q("update projects set report_status = 'done', reports = reports || jsonb_build_array(%s || jsonb_build_object("
      "'version', jsonb_array_length(reports) + 1, 'created_at', now())) where id = %s", (Jsonb(version), project_id))


def tool_calls(project_id):
    """Every tool_call event of the project's done runs, for the report's data-provenance appendix."""
    return [r["e"] for r in q("select e from runs r, jsonb_array_elements(r.events) e where r.project_id = %s "
                              "and r.status = 'done' and e->>'type' = 'tool_call'", (project_id,))]


def history(project_id, thread_id=None):
    """Earlier done runs of one thread of a project (None = Main, the runs without a thread), oldest first."""
    return q("select query, answer->>'summary' as summary from runs where project_id = %s and status = 'done' "
             "and thread_id is not distinct from %s order by id", (project_id, thread_id))


# Threads: runs without a thread are the project's Main thread
def list_threads(project_id):
    """Main first (synthetic, id None; the first pass is project-level, not a question), then the real threads."""
    main = q("select count(*)::int as n_runs from runs where project_id = %s and thread_id is null and query not ilike 'first pass%%'",
             (project_id,), one=True)
    return [{"id": None, "title": "Main", **main}] + q("select t.id, t.title, t.created_at, count(r.id)::int as n_runs from threads t left join runs r on r.thread_id = t.id "
             "where t.project_id = %s group by t.id order by t.id", (project_id,))


def create_thread(project_id, title):
    return q("insert into threads(project_id, title) values (%s, %s) returning id, project_id, title, created_at",
             (project_id, title), one=True)


def rename_thread(thread_id, title):
    return q("update threads set title = %s where id = %s returning id, project_id, title", (title, thread_id), one=True)


# Runs
def runs_last_hour(profile_id):
    """(runs by this profile, runs overall) started in the last hour."""
    row = q("select count(*) filter (where p.profile_id = %s)::int as mine, count(*)::int as total from runs r "
            "join projects p on p.id = r.project_id where r.created_at > now() - interval '1 hour'",
            (profile_id,), one=True)
    return row["mine"], row["total"]


def fail_stale_runs():
    """Runs left 'running' by a restart can never finish: mark them failed, with the events the UI expects.
    Only runs older than 10 minutes: another server sharing this database may still be running newer ones."""
    q("""update runs set status = 'failed', finished_at = now(), events = events || jsonb_build_array(
           jsonb_build_object('type', 'error', 'message', 'Interrupted by a server restart.', 't', now()),
           jsonb_build_object('type', 'run_done', 'status', 'failed', 't', now())) where status = 'running'
           and created_at < now() - interval '10 minutes'""")


def create_run(project_id, query, agents, thread_id=None):
    return q("insert into runs(project_id, query, agents, thread_id) values (%s, %s, %s, %s) returning id",
             (project_id, query, agents, thread_id), one=True)["id"]


def append_event(run_id, event):
    q("update runs set events = events || %s where id = %s", (Jsonb([event]), run_id))


def finish_run(run_id, status, answer):
    q("update runs set status = %s, answer = %s, finished_at = now() where id = %s",
      (status, Jsonb(answer) if answer else None, run_id))


def get_run(run_id):
    return q("select id, project_id, query, status, answer, events from runs where id = %s", (run_id,), one=True)
