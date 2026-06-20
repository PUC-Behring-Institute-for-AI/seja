import pytest
import pytest_asyncio
import aiosqlite

from seja_mcp.db.schema import SCHEMA_SQL


@pytest_asyncio.fixture
async def db():
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()
    yield conn
    await conn.close()


@pytest.mark.asyncio
class TestSchemaTables:
    EXPECTED_TABLES = [
        "projects",
        "constitution_principles",
        "decisions",
        "design_features",
        "lifecycle_history",
        "pending_actions",
        "briefs",
        "telemetry",
        "telemetry_config",
        "plans",
        "plan_steps",
        "research_reports",
        "journey_maps",
        "test_runs",
        "experiments",
        "_migrations",
        "export_log",
    ]

    async def test_all_tables_exist(self, db):
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        for t in self.EXPECTED_TABLES:
            assert t in tables, f"Missing table: {t}"

    async def test_fts5_table_exists(self, db):
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions_fts'"
        )
        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
class TestSchemaPragmas:
    @pytest.mark.skipif(True, reason="In-memory DB cannot have WAL mode; run against file DB")
    async def test_wal_mode(self, db):
        cursor = await db.execute("PRAGMA journal_mode")
        mode = await cursor.fetchone()
        assert mode[0] == "wal"

    async def test_foreign_keys_enabled(self, db):
        cursor = await db.execute("PRAGMA foreign_keys")
        fk = await cursor.fetchone()
        assert fk[0] == 1


@pytest.mark.asyncio
class TestSchemaRoundtrips:
    async def test_project_roundtrip(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("test-id", "Test Project", "/test", "setup"),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM projects WHERE id=?", ("test-id",))
        row = await cursor.fetchone()
        assert row["name"] == "Test Project"
        assert row["phase"] == "setup"

    async def test_constitution_principle_roundtrip(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("p1", "Test", "/test", "setup"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO constitution_principles (id, project_id, rank, principle, description) "
            "VALUES (?, ?, ?, ?, ?)",
            ("c1", "p1", 1, "Be clear", "Always write clearly"),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM constitution_principles WHERE id=?", ("c1",)
        )
        row = await cursor.fetchone()
        assert row["principle"] == "Be clear"
        assert row["project_id"] == "p1"

    async def test_decision_fts_sync(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("p1", "Test", "/test", "setup"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO decisions (id, project_id, title, context, decision, rationale) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("d1", "p1", "Use Python", "Language choice", "Python 3.11", "Best ecosystem"),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM decisions_fts WHERE id=?", ("d1",)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert "Python" in row["title"]

    async def test_lifecycle_history_roundtrip(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("p1", "Test", "/test", "setup"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO lifecycle_history (id, project_id, from_phase, to_phase, reason, transition_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("h1", "p1", "setup", "design", "Constitution ready", "forward"),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM lifecycle_history WHERE id=?", ("h1",)
        )
        row = await cursor.fetchone()
        assert row["from_phase"] == "setup"
        assert row["to_phase"] == "design"

    async def test_brief_roundtrip(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("p1", "Test", "/test", "design"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO briefs (id, project_id, phase, content, session_id, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("b1", "p1", "design", "Working on feature X", "sess-1", "started"),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM briefs WHERE id=?", ("b1",))
        row = await cursor.fetchone()
        assert row["status"] == "started"
        assert row["session_id"] == "sess-1"

    async def test_unique_constraint_on_feature(self, db):
        await db.execute(
            "INSERT INTO projects (id, name, workspace_path, phase) VALUES (?, ?, ?, ?)",
            ("p1", "Test", "/test", "design"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO design_features (id, project_id, feature_id, as_intended) "
            "VALUES (?, ?, ?, ?)",
            ("f1", "p1", "feat-1", "Do something"),
        )
        await db.commit()
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO design_features (id, project_id, feature_id, as_intended) "
                "VALUES (?, ?, ?, ?)",
                ("f2", "p1", "feat-1", "Duplicate"),
            )
            await db.commit()
