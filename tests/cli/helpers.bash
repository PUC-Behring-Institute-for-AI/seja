setup_sandbox() {
  SEJA_SANDBOX=$(mktemp -d /tmp/seja-test.XXXXXX)
  export HOME="${SEJA_SANDBOX}/home"
  mkdir -p "${HOME}"

  export SEJA_SEJA_DIR="${HOME}/.seja"
  export SEJA_ENV_FILE="${SEJA_SEJA_DIR}/.env"
  export SEJA_VERSION_FILE="${SEJA_SEJA_DIR}/.version"
  export SEJA_COMPOSE_FILE="${SEJA_SEJA_DIR}/docker-compose.yml"
  export SEJA_COMPOSE_OVERRIDE="${SEJA_SEJA_DIR}/docker-compose.override.yml"

  export SEJA_IMAGE="${SEJA_IMAGE:-ghcr.io/puc-behring-institute-for-ai/seja:latest}"
  export SEJA_AUTO_PULL="${SEJA_AUTO_PULL:-true}"
  export SEJA_CONTAINER_NAME="${SEJA_CONTAINER_NAME:-seja}"

  export SEJA_MOCK_DIR="${SEJA_SANDBOX}/bin"
  mkdir -p "${SEJA_MOCK_DIR}"

  export ORIGINAL_PATH="${PATH}"
  export PATH="${SEJA_MOCK_DIR}:${PATH}"
}

teardown_sandbox() {
  rm -rf "${SEJA_SANDBOX}"
  export PATH="${ORIGINAL_PATH}"
}

create_env_file() {
  mkdir -p "${SEJA_SEJA_DIR}"
  cat > "${SEJA_ENV_FILE}" << ENVEOF
SEJA_IMAGE=${SEJA_IMAGE}
SEJA_CONTAINER_NAME=${SEJA_CONTAINER_NAME}
SEJA_OPENCODE_HOST_PORT=4096
SEJA_MCP_PORT=8765
SEJA_PROXY_PORT=4443
OMNITOOLS_HOST_PORT=7654
SEJA_TIER_REASON=anthropic/claude-opus-4-5
SEJA_TIER_CODE=anthropic/claude-sonnet-4-5
SEJA_TIER_FAST=anthropic/claude-haiku-4-5
OMNITOOLS_ENABLED=true
SEJA_WORKSPACE_DIR=${SEJA_SEJA_DIR}/workspace
ENVEOF
}

create_compose_file() {
  mkdir -p "${SEJA_SEJA_DIR}"
  generate_compose_file
}

create_version_file() {
  local previous="${1:-ghcr.io/puc-behring-institute-for-ai/seja:2.1.5}"
  mkdir -p "$(dirname "${SEJA_VERSION_FILE}")"
  echo "SEJA_PREVIOUS_IMAGE=${previous}" > "${SEJA_VERSION_FILE}"
}

mock_docker() {
  local mock_bin="${SEJA_MOCK_DIR}"
  cat > "${mock_bin}/docker" << 'DOCKEREOF'
#!/usr/bin/env bash
case "${1:-}" in
  pull)
    exit 0
    ;;
  images)
    echo "latest    730MB     2026-06-23 18:14:27 -0300 -03"
    echo "2.1.5     730MB     2026-06-23 17:50:43 -0300 -03"
    echo "2.1.0     729MB     2026-06-20 19:44:59 -0300 -03"
    exit 0
    ;;
  system)
    if [[ "${2:-}" == "info" ]]; then
      exit 0
    fi
    exit 0
    ;;
  inspect)
    if echo "${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "${*}" | grep -q "State.Health.Status"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  compose)
    exit 0
    ;;
  create)
    echo "mock-container-id"
    exit 0
    ;;
  cp)
    local dest="${@: -1}"
    mkdir -p "$(dirname "${dest}")"
    echo "#!/usr/bin/env bash" > "${dest}"
    echo "echo 'mock script'" >> "${dest}"
    chmod +x "${dest}"
    exit 0
    ;;
  rm)
    exit 0
    ;;
  login)
    exit 0
    ;;
  exec)
    exit 0
    ;;
  logs)
    echo "(mock logs)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${mock_bin}/docker"
}

mock_gh() {
  local mock_bin="${SEJA_MOCK_DIR}"
  cat > "${mock_bin}/gh" << 'GHEOF'
#!/usr/bin/env bash
case "${1:-}" in
  release)
    if [[ "${2:-}" == "list" ]]; then
      echo "v2.1.6  (2026-06-23)"
      echo "v2.1.5  (2026-06-23)"
      exit 0
    fi
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
GHEOF
  chmod +x "${mock_bin}/gh"
}

assert_env_value() {
  local key="$1"
  local expected="$2"
  local actual
  actual=$(grep "^${key}=" "${SEJA_ENV_FILE}" 2>/dev/null | cut -d= -f2-)
  if [[ "${actual}" != "${expected}" ]]; then
    echo "FAIL: expected ${key}=${expected}, got ${actual}"
    return 1
  fi
}

assert_version_file() {
  local expected="$1"
  if [[ ! -f "${SEJA_VERSION_FILE}" ]]; then
    echo "FAIL: version file not found at ${SEJA_VERSION_FILE}"
    return 1
  fi
  local actual
  actual=$(grep "^SEJA_PREVIOUS_IMAGE=" "${SEJA_VERSION_FILE}" 2>/dev/null | cut -d= -f2-)
  if [[ "${actual}" != "${expected}" ]]; then
    echo "FAIL: expected SEJA_PREVIOUS_IMAGE=${expected}, got ${actual}"
    return 1
  fi
}
