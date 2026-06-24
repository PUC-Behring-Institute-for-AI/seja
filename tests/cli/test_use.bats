setup() {
  load helpers
  setup_sandbox
  mock_docker
  create_env_file
}

teardown() {
  teardown_sandbox
}

@test "use without arguments shows usage" {
  run ./scripts/seja use
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "usage"
}

@test "use 2.1.5 updates env and saves previous" {
  run ./scripts/seja use 2.1.5
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/puc-behring-institute-for-ai/seja:2.1.5"
  assert_version_file "ghcr.io/puc-behring-institute-for-ai/seja:latest"
}

@test "use latest switches back to latest" {
  export SEJA_IMAGE="ghcr.io/puc-behring-institute-for-ai/seja:2.1.5"
  export SEJA_AUTO_PULL=false
  create_env_file
  create_version_file "ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja use latest
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/puc-behring-institute-for-ai/seja:latest"
}

@test "use with full image reference" {
  export SEJA_AUTO_PULL=false
  create_env_file

  run ./scripts/seja use ghcr.io/org/seja:custom
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/org/seja:custom"
}

@test "rollback without version file shows error" {
  rm -f "${SEJA_VERSION_FILE}"
  run ./scripts/seja rollback
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "no previous version"
}

@test "rollback restores previous image" {
  export SEJA_AUTO_PULL=false
  create_env_file
  create_version_file "ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja rollback
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/puc-behring-institute-for-ai/seja:latest"
}

@test "use and rollback create chain" {
  export SEJA_AUTO_PULL=false
  create_env_file

  run ./scripts/seja use 2.1.0
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/puc-behring-institute-for-ai/seja:2.1.0"
  assert_version_file "ghcr.io/puc-behring-institute-for-ai/seja:latest"

  run ./scripts/seja rollback
  [ "$status" -eq 0 ]
  assert_env_value "SEJA_IMAGE" "ghcr.io/puc-behring-institute-for-ai/seja:latest"
  assert_version_file "ghcr.io/puc-behring-institute-for-ai/seja:2.1.0"
}

@test "versions shows current image" {
  run ./scripts/seja versions
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Current image"
}
