#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-loom1103ciadopt}"
export LOOM_URL="${LOOM_URL:-http://127.0.0.1:18810}"

LABEL="LOOM-1103-CI-ADOPT"
WITNESS="LOOM-1103-CI-ADOPT-WITNESS"
PIN_TAG="v1.10.3"
PIN_SHA="cc10ab08573087fa12154f7c8181ffcd985fea88"
SRC_DEST="src-v1.10.3"

down() {
  echo "== docker compose down -v =="
  docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans || true
}

fail() {
  echo "FAIL ${LABEL} $* ${WITNESS}" | tee poc-last-run.txt
  exit 1
}


write_result() {
  local raw="$1"
  local rc="$2"
  local verdict=""
  verdict="$(grep -E "^(SUCCESS|FAIL) ${LABEL} " "${raw}" | tail -n 1 || true)"
  if [[ -z "${verdict}" ]]; then
    verdict="FAIL ${LABEL} poc-no-verdict exit=${rc} ${WITNESS}"
  fi
  {
    echo "${verdict}"
    grep -vE "^(SUCCESS|FAIL) ${LABEL} " "${raw}" || true
  } > poc-last-run.txt
  rm -f "${raw}"
  echo "== poc-last-run.txt =="
  cat poc-last-run.txt
  if [[ "${verdict}" == SUCCESS\ ${LABEL}\ * ]]; then
    exit 0
  fi
  exit 1
}

trap down EXIT

copy_pin() {
  local tmp got
  tmp="$(mktemp -d)"
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "${PIN_TAG}" --filter=blob:none --sparse \
    https://github.com/awslabs/loom.git "${tmp}"
  git -C "${tmp}" sparse-checkout set backend
  got="$(git -C "${tmp}" rev-parse HEAD)"
  echo "checkout tag=${PIN_TAG} sha=${got} expect=${PIN_SHA}"
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    GIT_TERMINAL_PROMPT=0 git -C "${tmp}" fetch --depth 1 origin "${PIN_SHA}"
    git -C "${tmp}" checkout -f "${PIN_SHA}"
    got="$(git -C "${tmp}" rev-parse HEAD)"
    echo "checkout-forced sha=${got}"
  fi
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    rm -rf "${tmp}"
    echo "FAIL ${LABEL} unexpected-commit got=${got} expect=${PIN_SHA}" | tee poc-last-run.txt
    exit 1
  fi
  rm -rf "src-v1.10.3"
  mkdir -p "src-v1.10.3/backend"
  cp -a "${tmp}/backend/app" "src-v1.10.3/backend/"
  cp -a "${tmp}/backend/etc" "src-v1.10.3/backend/"
  cp "${tmp}/backend/requirements.txt" "src-v1.10.3/backend/"
  rm -rf "${tmp}"
  find "src-v1.10.3" -type d -name '__pycache__' -exec rm -rf {} + || true
  echo "checkout-ok tag=${PIN_TAG} sha=${got} source=public-tag"
}

echo "== pin ${PIN_TAG} ${PIN_SHA} =="
copy_pin
if [[ ! -f "${SRC_DEST}/backend/app/routers/agents.py" ]]; then
  fail "missing-app-tree"
fi

python3 -m py_compile lab_patch.py poc.py sitecustomize.py || fail "py-compile"

echo "== docker compose down (clean) =="
down

echo "== docker compose up --build =="
up_ok=0
for attempt in $(seq 1 4); do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" up --build -d; then
    up_ok=1
    break
  fi
  echo "compose-up-retry attempt=${attempt}"
  sleep 20
  down
done
if [[ "${up_ok}" != 1 ]]; then
  fail "compose-up-failed"
fi

echo "== wait /health =="
ready=0
code=""
for i in $(seq 1 90); do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "${LOOM_URL}/health" || true)"
  if [[ "${code}" == "200" ]]; then
    ready=1
    echo "health-ready attempt=${i} http=${code} url=${LOOM_URL}/health"
    break
  fi
  echo "health-wait attempt=${i} http=${code}"
  sleep 2
done
if [[ "${ready}" != 1 ]]; then
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --tail=160 || true
  fail "loom-not-ready http=${code}"
fi

echo "== poc.py =="
raw="poc-raw.txt"
rm -f "${raw}"
set +e
docker compose -p "${COMPOSE_PROJECT_NAME}" exec -T \
  -e LOOM_URL=http://127.0.0.1:8000 \
  -e LAB_SEED=/lab/seed.json \
  -e LAB_CREATED=/lab/capture/created.json \
  -e LAB_DELETED=/lab/capture/deleted.json \
  loom python /lab/poc.py | tee "${raw}"
rc=${PIPESTATUS[0]}
set -e
write_result "${raw}" "${rc}"
