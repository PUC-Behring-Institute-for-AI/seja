setup() {
  load helpers
  setup_sandbox
  mock_docker
}

teardown() {
  teardown_sandbox
}

@test "start without compose file shows error" {
  run ./scripts/seja start
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "no docker-compose.yml"
}

@test "start with auto-pull calls docker pull" {
  create_env_file
  mkdir -p "${SEJA_SEJA_DIR}"
  cat > "${SEJA_COMPOSE_FILE}" << 'EOF'
services:
  seja:
    image: ${SEJA_IMAGE}
    container_name: seja
    ports:
      - "4096:4096"
    healthcheck:
      test: ["CMD", "echo", "ok"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
EOF

  local pull_log="${SEJA_SANDBOX}/pull.log"
  cat > "${SEJA_MOCK_DIR}/docker" << 'DOCKEREOF'
#!/usr/bin/env bash
case "${1:-}" in
  pull)
    echo "pulled: $2" >> "${2}"
    exit 0
    ;;
  compose)
    exit 0
    ;;
  inspect)
    if echo "${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "${*}" | grep -q "State.Health"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  system|info)
    exit 0
    ;;
  logs)
    echo "(mock)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"
  # Fix: pull log path inside heredoc was wrong, write correctly
  cat > "${SEJA_MOCK_DIR}/docker" << DOCKEREOF
#!/usr/bin/env bash
case "\${1:-}" in
  pull)
    echo "pulled: \$2" >> "${pull_log}"
    exit 0
    ;;
  compose)
    exit 0
    ;;
  inspect)
    if echo "\${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "\${*}" | grep -q "State.Health"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  system|info)
    exit 0
    ;;
  logs)
    echo "(mock)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"

  export SEJA_AUTO_PULL=true
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja start
  grep -q "pulled:" "${pull_log}"
}

@test "start with auto-pull=false skips docker pull" {
  create_env_file
  mkdir -p "${SEJA_SEJA_DIR}"
  cat > "${SEJA_COMPOSE_FILE}" << 'EOF'
services:
  seja:
    image: ${SEJA_IMAGE}
    container_name: seja
    ports:
      - "4096:4096"
    healthcheck:
      test: ["CMD", "echo", "ok"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
EOF

  local pull_log="${SEJA_SANDBOX}/pull.log"
  cat > "${SEJA_MOCK_DIR}/docker" << DOCKEREOF
#!/usr/bin/env bash
case "\${1:-}" in
  pull)
    echo "pulled: \$2" >> "${pull_log}"
    exit 0
    ;;
  compose)
    exit 0
    ;;
  inspect)
    if echo "\${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "\${*}" | grep -q "State.Health"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  system|info)
    exit 0
    ;;
  logs)
    echo "(mock)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"

  export SEJA_AUTO_PULL=false
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja start
  if [[ -f "${pull_log}" ]]; then
    echo "FAIL: docker pull was called when AUTO_PULL=false"
    cat "${pull_log}"
    return 1
  fi
}

@test "start with pinned version skips docker pull" {
  export SEJA_AUTO_PULL=true
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:2.1.5"
  create_env_file
  mkdir -p "${SEJA_SEJA_DIR}"
  cat > "${SEJA_COMPOSE_FILE}" << 'EOF'
services:
  seja:
    image: ${SEJA_IMAGE}
    container_name: seja
    ports:
      - "4096:4096"
    healthcheck:
      test: ["CMD", "echo", "ok"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
EOF

  local pull_log="${SEJA_SANDBOX}/pull.log"
  cat > "${SEJA_MOCK_DIR}/docker" << DOCKEREOF
#!/usr/bin/env bash
case "\${1:-}" in
  pull)
    echo "pulled: \$2" >> "${pull_log}"
    exit 0
    ;;
  compose)
    exit 0
    ;;
  inspect)
    if echo "\${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "\${*}" | grep -q "State.Health"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  system|info)
    exit 0
    ;;
  logs)
    echo "(mock)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"

  export SEJA_AUTO_PULL=true
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:2.1.5"

  run ./scripts/seja start
  if [[ -f "${pull_log}" ]]; then
    echo "FAIL: docker pull was called when image is pinned"
    cat "${pull_log}"
    return 1
  fi
}

@test "start with pull failure continues with warning" {
  create_env_file
  mkdir -p "${SEJA_SEJA_DIR}"
  cat > "${SEJA_COMPOSE_FILE}" << 'EOF'
services:
  seja:
    image: ${SEJA_IMAGE}
    container_name: seja
    ports:
      - "4096:4096"
    healthcheck:
      test: ["CMD", "echo", "ok"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
EOF

  cat > "${SEJA_MOCK_DIR}/docker" << DOCKEREOF
#!/usr/bin/env bash
case "\${1:-}" in
  pull)
    exit 1
    ;;
  compose)
    exit 0
    ;;
  inspect)
    if echo "\${*}" | grep -q "State.Running"; then
      echo "true"
    elif echo "\${*}" | grep -q "State.Health"; then
      echo "healthy"
    else
      echo "{}"
    fi
    exit 0
    ;;
  system|info)
    exit 0
    ;;
  logs)
    echo "(mock)"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"

  export SEJA_AUTO_PULL=true
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja start
  echo "$output" | grep -qi "could not pull"
}
