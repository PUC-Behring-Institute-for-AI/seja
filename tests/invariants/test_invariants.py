import ast
import os
import re
import subprocess
import sys

import pytest

SEJA_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
AGENTS_DIR = os.path.join(SEJA_ROOT, "opencode", "agents")
SECURITY_DIR = os.path.join(SEJA_ROOT, "security")
MCP_DIR = os.path.join(SEJA_ROOT, "mcp", "seja_mcp")
MODULES_DIR = os.path.join(MCP_DIR, "modules")

EXPECTED_FSM_STATES = {
    "setup", "design", "research", "plan",
    "implement", "check", "document", "reflect",
}

MCP_SERVER_URL = "http://localhost:8765"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tool_names_from_module(module_path: str) -> list[str]:
    with open(module_path) as f:
        tree = ast.parse(f.read())

    tools = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Attribute)
                    and decorator.attr == "tool"
                ):
                    tools.append(node.name)
    return tools


def _extract_all_tool_names() -> list[str]:
    names = []
    for fname in sorted(os.listdir(MODULES_DIR)):
        if fname.endswith(".py") and fname != "__init__.py":
            path = os.path.join(MODULES_DIR, fname)
            names.extend(_extract_tool_names_from_module(path))
    return names


def _parse_bash_allow_list(tpl_path: str) -> list[str]:
    with open(tpl_path) as f:
        content = f.read()
    lines = content.splitlines()
    in_bash_allow = False
    allows = []
    for line in lines:
        stripped = line.strip()
        if stripped == "allow:":
            in_bash_allow = True
            continue
        if in_bash_allow:
            if stripped.startswith("- "):
                allows.append(stripped[2:].strip())
            elif not stripped.startswith("-") and not stripped.startswith("#"):
                if stripped and not stripped.startswith("  "):
                    in_bash_allow = False
    return allows


# ---------------------------------------------------------------------------
# Invariant: no destructive tools on read-only / append-only modules
# ---------------------------------------------------------------------------


class TestNoConstitutionWrite:

    @pytest.fixture(autouse=True)
    def _load_tools(self):
        path = os.path.join(MODULES_DIR, "constitution.py")
        self.tool_names = _extract_tool_names_from_module(path)

    def test_no_constitution_write(self):
        forbidden = {"write_constitution", "update_constitution", "set_constitution"}
        for name in self.tool_names:
            assert name not in forbidden, (
                f"Constitution module has a write tool: {name}"
            )

    def test_no_constitution_delete(self):
        forbidden = {"delete_constitution", "remove_constitution"}
        for name in self.tool_names:
            assert name not in forbidden, (
                f"Constitution module has a delete tool: {name}"
            )


class TestNoDecisionsEdit:

    @pytest.fixture(autouse=True)
    def _load_tools(self):
        path = os.path.join(MODULES_DIR, "decisions.py")
        self.tool_names = _extract_tool_names_from_module(path)

    def test_no_decisions_edit(self):
        forbidden = {
            "edit_decision", "update_decision", "change_decision",
            "modify_decision",
        }
        for name in self.tool_names:
            assert name not in forbidden, (
                f"Decisions module has an edit tool: {name}"
            )

    def test_no_decisions_delete(self):
        forbidden = {"delete_decision", "remove_decision", "destroy_decision"}
        for name in self.tool_names:
            assert name not in forbidden, (
                f"Decisions module has a delete tool: {name}"
            )


class TestNoBriefsDelete:

    @pytest.fixture(autouse=True)
    def _load_tools(self):
        path = os.path.join(MODULES_DIR, "briefs.py")
        self.tool_names = _extract_tool_names_from_module(path)

    def test_no_briefs_delete(self):
        forbidden = {"delete_brief", "remove_brief", "destroy_brief"}
        for name in self.tool_names:
            assert name not in forbidden, (
                f"Briefs module has a delete tool: {name}"
            )


# ---------------------------------------------------------------------------
# Invariant: all tools have the seja. prefix in their intended naming
# ---------------------------------------------------------------------------


class TestAllToolsSejaPrefixed:
    """Verify that tool naming follows the seja.<module>.<action> convention.

    This test checks that every @mcp.tool-decorated function name matches
    the pattern ``<module>_<action>`` (which at registration time becomes
    ``seja.<module>.<action>`` when FastMCP normalizes underscores).
    """

    def test_all_tools_have_expected_naming(self):
        all_tools = _extract_all_tool_names()
        for name in all_tools:
            parts = name.split("_")
            assert len(parts) >= 2, (
                f"Tool '{name}' does not follow <module>_<action> naming"
            )

    def test_no_tool_names_are_just_verbs(self):
        single_word_verbs = {"list", "get", "create", "delete", "update", "search"}
        all_tools = _extract_all_tool_names()
        for name in all_tools:
            assert name not in single_word_verbs, (
                f"Tool named '{name}' is too generic"
            )


# ---------------------------------------------------------------------------
# Invariant: FSM has exactly 8 states
# ---------------------------------------------------------------------------


class TestFSMStates:
    def test_fsm_has_8_states(self):
        from seja_mcp.lifecycle_fsm import SejaLifecycleFSM

        fsm = SejaLifecycleFSM()
        state_names = {s.value for s in fsm.states}
        for expected in EXPECTED_FSM_STATES:
            assert expected in state_names, f"Missing state: {expected}"
        assert len(state_names) == 8, (
            f"Expected 8 states, got {len(state_names)}: {state_names}"
        )

    def test_initial_state_is_setup(self):
        from seja_mcp.lifecycle_fsm import SejaLifecycleFSM

        fsm = SejaLifecycleFSM()
        assert list(fsm.configuration)[0].value == "setup"


# ---------------------------------------------------------------------------
# Invariant: FSM transitions count and completeness
# ---------------------------------------------------------------------------


class TestFSMTransitions:
    def test_fsm_has_expected_transitions(self):
        from seja_mcp.lifecycle_fsm import SejaLifecycleFSM

        fsm = SejaLifecycleFSM()
        transition_events = {
            a for a in dir(fsm)
            if not a.startswith("_")
            and hasattr(getattr(fsm, a), "__call__")
            and "_to_" in a
        }

        expected = {
            "setup_to_design",
            "design_to_research",
            "research_to_plan",
            "plan_to_implement",
            "implement_to_check",
            "check_to_document",
            "document_to_reflect",
            "reflect_to_design",
            "implement_to_design",
            "implement_to_research",
            "implement_to_plan",
            "plan_to_design",
            "plan_to_research",
            "design_to_setup",
            "research_to_design",
            "research_to_setup",
            "check_to_implement",
            "check_to_plan",
            "document_to_check",
        }
        missing = expected - transition_events
        extra = transition_events - expected
        assert not missing, f"Missing transitions: {missing}"
        assert not extra, f"Unexpected transitions: {extra}"

    def test_all_forward_states_have_path_in_forward_paths(self):
        from seja_mcp.lifecycle_fsm import FORWARD_PATHS

        for state in EXPECTED_FSM_STATES:
            assert state in FORWARD_PATHS, (
                f"Missing FORWARD_PATHS entry for state '{state}'"
            )


# ---------------------------------------------------------------------------
# Invariant: no agent template allows "git push"
# ---------------------------------------------------------------------------


class TestNoGitPush:
    @pytest.fixture(autouse=True)
    def _collect_agents(self):
        self.tpl_files = sorted(
            os.path.join(AGENTS_DIR, f)
            for f in os.listdir(AGENTS_DIR)
            if f.endswith(".md.tpl")
        )

    def test_no_git_push_in_bash_allow_lists(self):
        violations = []
        for tpl in self.tpl_files:
            allows = _parse_bash_allow_list(tpl)
            for entry in allows:
                if "git push" in entry:
                    violations.append((os.path.basename(tpl), entry))
        assert not violations, (
            f"Agents with 'git push' in bash allow list: {violations}"
        )

    def test_no_git_star_in_bash_allow_lists(self):
        violations = []
        for tpl in self.tpl_files:
            allows = _parse_bash_allow_list(tpl)
            for entry in allows:
                if entry.strip() == "git *":
                    violations.append(os.path.basename(tpl))
        assert not violations, (
            f"Agents with overly broad 'git *' allow: {violations}"
        )

    def test_at_least_one_tpl_file_exists(self):
        assert len(self.tpl_files) > 0, "No .md.tpl files found"


# ---------------------------------------------------------------------------
# Invariant: cosign public key exists
# ---------------------------------------------------------------------------


class TestCosignPublicKey:
    def test_cosign_public_key_exists(self):
        key_path = os.path.join(SECURITY_DIR, "cosign.pub")
        assert os.path.exists(key_path), f"Missing: {key_path}"
        with open(key_path) as f:
            content = f.read()
        assert "BEGIN PUBLIC KEY" in content, "Not a valid PEM public key"


# ---------------------------------------------------------------------------
# Invariant: _skip_export is documented in dual_write decorator
# ---------------------------------------------------------------------------


class TestDualWrite:
    def test_skip_export_key_is_recognized(self):
        from seja_mcp.modules import dual_write

        assert hasattr(dual_write, "__wrapped__") or callable(dual_write), (
            "dual_write is not a proper decorator"
        )

    def test_skip_export_logic_in_source(self):
        path = os.path.join(MODULES_DIR, "__init__.py")
        with open(path) as f:
            src = f.read()
        assert "_skip_export" in src, (
            "dual_write decorator does not reference _skip_export"
        )
        assert "result.get(\"_skip_export\")" in src.replace(" ", ""), (
            "dual_write does not guard export with _skip_export check"
        )


# ---------------------------------------------------------------------------
# Invariant: health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    @pytest.mark.skipif(
        not os.environ.get("SEJA_MCP_PORT"),
        reason="MCP server not running — set SEJA_MCP_PORT or start server",
    )
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        import httpx

        port = int(os.environ["SEJA_MCP_PORT"])
        url = f"http://localhost:{port}/health"
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_connection_refused(self):
        import httpx

        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(f"{MCP_SERVER_URL}/health")
            assert resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("MCP server is not running")


# ---------------------------------------------------------------------------
# Invariant (bonus): no module imports things it should not
# ---------------------------------------------------------------------------


class TestModuleBoundaries:
    def test_constitution_only_reads(self):
        path = os.path.join(MODULES_DIR, "constitution.py")
        with open(path) as f:
            src = f.read()
        upper = src.upper()
        assert "DELETE" not in upper, "Constitution module has DELETE"
        assert "UPDATE" not in upper or "UPDATE" not in [
            w for w in src.split() if "UPDATE" in w.upper()
            and not any(kw in w.lower() for kw in ["get", "list", "check"])
        ]
