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
create table if not exists runs(id serial primary key, project_id int references projects on delete cascade,
    query text not null, agents text[], status text not null default 'running', answer jsonb,
    events jsonb not null default '[]', created_at timestamptz default now(), finished_at timestamptz);
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
    project = q("select id, title, goals, profile_id, dashboard, dashboard_status from projects where id = %s", (project_id,), one=True)
    if project:
        project["runs"] = q("select id, query, status, created_at, answer from runs where project_id = %s "
                            "order by id", (project_id,))
    return project


def set_dashboard(project_id, status, dashboard=None):
    """Status is 'building: <progress>', 'done' or 'failed'; a rebuild keeps the old dashboard until the new one lands."""
    q("update projects set dashboard_status = %s, dashboard = coalesce(%s, dashboard) where id = %s",
      (status, Jsonb(dashboard) if dashboard else None, project_id))


def history(project_id):
    """Earlier done runs of a project, oldest first, as the orchestrator expects them."""
    return q("select query, answer->>'summary' as summary from runs where project_id = %s and status = 'done' "
             "order by id", (project_id,))


# Runs
def runs_last_hour(profile_id):
    """(runs by this profile, runs overall) started in the last hour."""
    row = q("select count(*) filter (where p.profile_id = %s)::int as mine, count(*)::int as total from runs r "
            "join projects p on p.id = r.project_id where r.created_at > now() - interval '1 hour'",
            (profile_id,), one=True)
    return row["mine"], row["total"]


def fail_stale_runs():
    """Runs left 'running' by a restart can never finish: mark them failed, with the events the UI expects."""
    q("""update runs set status = 'failed', finished_at = now(), events = events || jsonb_build_array(
           jsonb_build_object('type', 'error', 'message', 'Interrupted by a server restart.', 't', now()),
           jsonb_build_object('type', 'run_done', 'status', 'failed', 't', now())) where status = 'running'""")


def create_run(project_id, query, agents):
    return q("insert into runs(project_id, query, agents) values (%s, %s, %s) returning id",
             (project_id, query, agents), one=True)["id"]


def append_event(run_id, event):
    q("update runs set events = events || %s where id = %s", (Jsonb([event]), run_id))


def finish_run(run_id, status, answer):
    q("update runs set status = %s, answer = %s, finished_at = now() where id = %s",
      (status, Jsonb(answer) if answer else None, run_id))


def get_run(run_id):
    return q("select id, project_id, query, status, answer, events from runs where id = %s", (run_id,), one=True)
