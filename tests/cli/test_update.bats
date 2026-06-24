setup() {
  load helpers
  setup_sandbox
  mock_docker
  create_env_file
  mkdir -p "${SEJA_SEJA_DIR}/tmp" "${SEJA_SEJA_DIR}/backups" "${SEJA_SEJA_DIR}/logs"
  cat > "${SEJA_COMPOSE_FILE}" << 'EOF'
services:
  seja:
    image: ${SEJA_IMAGE}
    container_name: seja
    ports:
      - "4096:4096"
EOF
}

teardown() {
  teardown_sandbox
}

@test "update --check without setup fails" {
  rm -f "${SEJA_COMPOSE_FILE}"
  run ./scripts/seja update --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "no setup found"
}

@test "update --check passes with setup" {
  run ./scripts/seja update --check
  [ "$status" -eq 0 ]
}

@test "update with failing pull exits with error" {
  cat > "${SEJA_MOCK_DIR}/docker" << 'DOCKEREOF'
#!/usr/bin/env bash
case "${1:-}" in
  pull) exit 1 ;;
  *) exit 0 ;;
esac
DOCKEREOF
  chmod +x "${SEJA_MOCK_DIR}/docker"

  run ./scripts/seja update
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "failed to pull"
}
