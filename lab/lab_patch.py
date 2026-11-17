"""Lab harness. Product routers stay unmodified.

boto3.client is replaced on import. list_code_interpreters returns the
interpreter a harness named billing already owns. create_harness returns a
runtime id so delete_agent does not take the empty-runtime early return.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from fastapi import Request

logger = logging.getLogger("lab_patch")

VICTIM_CI_ID = "ci-billing-existing"
VICTIM_CI_NAME = "loom_ci_billing"
VICTIM_CI_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:123456789012:"
    "code-interpreter/ci-billing-existing"
)
ROLE_ARN = "arn:aws:iam::123456789012:role/loom-demo-exec"
BILLING_RUNTIME_ID = "rt-billing-existing"
BILLING_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/rt-billing-existing"
)
SEED_PATH = Path("/lab/seed.json")
CREATED_PATH = Path("/lab/capture/created.json")
DELETED_PATH = Path("/lab/capture/deleted.json")
DEMO_GROUPS = ["t-admin", "g-admins-demo"]
DEMO_TOKEN = "lab-demo"


@dataclass
class _State:
    hooked: bool = False
    seeded: bool = False
    seq: int = 0
    patched: set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)


_STATE = _State()


class _AwsError(Exception):
    """Stand-in so `except client.exceptions.SomeError` has a real class."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.response = {"Error": {"Code": "LabError", "Message": "lab"}}
        super().__init__("lab")
        del args, kwargs


class _Exceptions:
    def __getattr__(self, name: str) -> type[_AwsError]:
        del name
        return _AwsError


def _read_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, str)]


def _append(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _STATE.lock:
        rows = _read_list(path)
        rows.append(value)
        path.write_text(json.dumps(rows), encoding="utf-8")


class _Client:
    """Control-plane stand-in. Unknown calls return an empty dict."""

    def __init__(self, service: str, region: str) -> None:
        self.service = service
        self.region = region
        self.exceptions = _Exceptions()

    def list_code_interpreters(self, *args: object, **kwargs: object) -> dict[str, object]:
        del args, kwargs
        return {
            "codeInterpreterSummaries": [
                {
                    "name": VICTIM_CI_NAME,
                    "codeInterpreterId": VICTIM_CI_ID,
                    "codeInterpreterArn": VICTIM_CI_ARN,
                }
            ]
        }

    def create_code_interpreter(self, *args: object, **kwargs: object) -> dict[str, str]:
        del args
        name = str(kwargs.get("name") or "")
        _append(CREATED_PATH, name)
        with _STATE.lock:
            _STATE.seq += 1
            seq = _STATE.seq
        created_id = f"ci-created-{seq}"
        logger.info("lab create_code_interpreter name=%s id=%s", name, created_id)
        return {
            "codeInterpreterId": created_id,
            "codeInterpreterArn": (
                "arn:aws:bedrock-agentcore:us-east-1:123456789012:"
                f"code-interpreter/{created_id}"
            ),
        }

    def delete_code_interpreter(self, *args: object, **kwargs: object) -> dict[str, str]:
        del args
        ci_id = str(kwargs.get("codeInterpreterId") or "")
        _append(DELETED_PATH, ci_id)
        logger.info("lab delete_code_interpreter id=%s", ci_id)
        return {}

    def create_harness(self, *args: object, **kwargs: object) -> dict[str, str]:
        """Non-empty harness id. An empty body would leave runtime_id blank."""
        del args
        name = str(kwargs.get("harnessName") or "harness")
        harness_id = f"harness-{name}"
        return {
            "harnessId": harness_id,
            "arn": (
                "arn:aws:bedrock-agentcore:us-east-1:123456789012:"
                f"harness/{harness_id}"
            ),
            "status": "READY",
        }

    def get_agent_runtime(self, *args: object, **kwargs: object) -> dict[str, str]:
        # Empty status makes the post-delete poll sleep 30 times.
        del args, kwargs
        return {"status": "FAILED"}

    def __getattr__(self, name: str) -> object:
        if name == "exceptions":
            return self.exceptions

        def _call(*args: object, **kwargs: object) -> dict[str, str]:
            del args, kwargs
            logger.info("lab boto %s.%s empty", self.service, name)
            return {}

        return _call


def _lab_boto_client(service_name: str, *args: object, **kwargs: object) -> _Client:
    del args
    region = str(kwargs.get("region_name") or "us-east-1")
    logger.info("lab boto3.client service=%s region=%s", service_name, region)
    return _Client(str(service_name), region)


def _mark(name: str) -> bool:
    if name in _STATE.patched:
        return False
    _STATE.patched.add(name)
    return True


def _patch_boto3(mod: object) -> None:
    # boto3.session imports boto3 while boto3/__init__.py is still running,
    # before client() exists. Marking that pass as done left the real client
    # in place after the package finished loading.
    if not hasattr(mod, "client") or getattr(mod, "client", None) is _lab_boto_client:
        return
    mod.client = _lab_boto_client
    logger.info("lab harness: boto3.client stubbed")


def _patch_auth(auth_mod: object) -> None:
    if not _mark("auth") or getattr(auth_mod, "_lab_ci_adopt_patched", False):
        return
    orig = auth_mod.get_current_user
    user_info = auth_mod.UserInfo
    derive_scopes = auth_mod.derive_scopes

    def lab_get_current_user(request: Request) -> object:
        header = request.headers.get("Authorization", "") or ""
        token = header[7:].strip() if header.startswith("Bearer ") else ""
        if token != DEMO_TOKEN:
            return orig(request)
        return user_info(
            sub=token,
            username=token,
            groups=list(DEMO_GROUPS),
            scopes=derive_scopes(list(DEMO_GROUPS)),
            idp_type="lab",
        )

    auth_mod.get_current_user = lab_get_current_user
    auth_mod._lab_ci_adopt_patched = True
    logger.info("lab harness: get_current_user wrapped")


def _write_seed(role_id: int, agent_id: int) -> None:
    payload = {
        "billing_agent_id": agent_id,
        "billing_name": "billing",
        "billing_group": "payments",
        "code_interpreter_id": VICTIM_CI_ID,
        "runtime_id": BILLING_RUNTIME_ID,
        "role_id": role_id,
        "role_arn": ROLE_ARN,
    }
    SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEED_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _seed() -> None:
    if _STATE.seeded:
        return
    from app.db import SessionLocal
    from app.models.agent import Agent
    from app.models.managed_role import ManagedRole

    db = SessionLocal()
    try:
        role = db.query(ManagedRole).filter(ManagedRole.role_arn == ROLE_ARN).first()
        if role is None:
            role = ManagedRole(
                role_name="loom-demo-exec",
                role_arn=ROLE_ARN,
                role_type="agent",
                description="lab execution role",
                policy_document="{}",
            )
            role.set_tags(
                {"loom:group": "demo", "loom:application": "lab", "loom:owner": "lab"}
            )
            db.add(role)
            db.flush()

        agent = db.query(Agent).filter(Agent.name == "billing", Agent.source == "harness").first()
        if agent is None:
            agent = Agent(
                arn=BILLING_ARN,
                runtime_id=BILLING_RUNTIME_ID,
                name="billing",
                status="READY",
                region="us-east-1",
                account_id="123456789012",
                source="harness",
                deployment_status="READY",
                protocol="HTTP",
                network_mode="PUBLIC",
                registered_at=datetime.utcnow(),
                code_interpreter_id=VICTIM_CI_ID,
            )
            agent.set_tags(
                {"loom:group": "payments", "loom:application": "lab", "loom:owner": "lab"}
            )
            agent.set_available_qualifiers(["DEFAULT"])
            db.add(agent)
        db.commit()
        db.refresh(role)
        db.refresh(agent)
        if role.id is None or agent.id is None:
            raise RuntimeError("seed-missing-id")
        if agent.code_interpreter_id != VICTIM_CI_ID or not agent.runtime_id:
            raise RuntimeError("seed-billing-mismatch")
        _write_seed(int(role.id), int(agent.id))
        _STATE.seeded = True
        logger.info(
            "lab harness: seeded role_id=%s billing_agent_id=%s", role.id, agent.id
        )
    except Exception:
        db.rollback()
        logger.exception("lab harness: seed failed")
        raise
    finally:
        db.close()


def _patch_db(db_mod: object) -> None:
    if not _mark("db") or getattr(db_mod, "_lab_ci_adopt_patched", False):
        return
    orig = db_mod.init_db

    def init_db() -> None:
        orig()
        _seed()

    db_mod.init_db = init_db
    db_mod._lab_ci_adopt_patched = True
    logger.info("lab harness: init_db wrapped")


def install_import_hook() -> None:
    """Patch product modules the first time they import."""
    if _STATE.hooked:
        return
    import builtins

    orig_import = builtins.__import__

    def hooked(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        mod = orig_import(name, globals, locals, fromlist, level)
        mod_name = getattr(mod, "__name__", "")
        if name == "boto3" or mod_name == "boto3":
            _patch_boto3(mod)
        if name == "app.dependencies.auth" or mod_name == "app.dependencies.auth":
            _patch_auth(mod)
        if name == "app.db" or mod_name == "app.db":
            _patch_db(mod)
        return mod

    builtins.__import__ = hooked
    _STATE.hooked = True
