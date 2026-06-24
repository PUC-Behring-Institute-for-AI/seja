setup() {
  load helpers
  setup_sandbox
}

teardown() {
  teardown_sandbox
}

@test "help shows all command sections" {
  run ./scripts/seja help
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Core Commands:"
  echo "$output" | grep -q "Workspace Commands:"
  echo "$output" | grep -q "Config Commands:"
  echo "$output" | grep -q "Admin Commands:"
  echo "$output" | grep -q "Experiment Commands:"
  echo "$output" | grep -q "Special Commands:"
}

@test "help shows use, rollback, versions in Core Commands" {
  run ./scripts/seja help
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "use <ver>"
  echo "$output" | grep -q "rollback"
  echo "$output" | grep -q "versions"
}

@test "help use shows specific documentation" {
  run ./scripts/seja help use
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Switch SEJA to a specific version"
}

@test "help rollback shows specific documentation" {
  run ./scripts/seja help rollback
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Revert to the version"
}

@test "help versions shows specific documentation" {
  run ./scripts/seja help versions
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "List locally cached images"
}

@test "version shows version string" {
  run ./scripts/seja version
  [ "$status" -eq 0 ]
  [[ "$output" == "seja v"* ]]
}

@test "version works with --version flag" {
  run ./scripts/seja --version
  [ "$status" -eq 0 ]
  [[ "$output" == "seja v"* ]]
}

@test "version works with -v flag" {
  run ./scripts/seja -v
  [ "$status" -eq 0 ]
  [[ "$output" == "seja v"* ]]
}

@test "unknown command exits with error" {
  run ./scripts/seja nonexistent-command-xyz
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "unknown command"
}
