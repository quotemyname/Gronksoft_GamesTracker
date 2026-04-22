"""Tests for Gronksoft GamesTracker."""

import csv
import io

import pytest

from app import create_app
from models import Battle, db


@pytest.fixture
def app():
    """Create a test application with an in-memory database."""
    application = create_app(testing=True)
    with application.app_context():
        db.create_all()
    yield application


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_battle(app):
    """Insert a sample battle and return it."""
    with app.app_context():
        battle = Battle(
            my_army="Space Marines",
            opponent_army="Orks",
            result="Win",
            scenario="Take and Hold",
            army_size=2000,
            my_control_points=12,
            opp_control_points=8,
            my_army_points=1800,
            opp_army_points=1500,
            my_kill_points=900,
            opp_kill_points=700,
            event="Summer League",
            initiative="First",
            comment="Great game!",
        )
        db.session.add(battle)
        db.session.commit()
        battle_id = battle.id
    return battle_id


# ------------------------------------------------------------------
# Home / Battle List
# ------------------------------------------------------------------

class TestBattleList:
    def test_empty_list(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"No battles recorded yet" in resp.data

    def test_list_with_battle(self, client, sample_battle):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Space Marines" in resp.data
        assert b"Orks" in resp.data

    def test_filter_by_result(self, client, sample_battle):
        resp = client.get("/?result=Win")
        assert b"battle-card" in resp.data

        resp = client.get("/?result=Loss")
        # No battle cards should render, only the empty state
        assert b"battle-card" not in resp.data

    def test_search(self, client, sample_battle):
        resp = client.get("/?q=marines")
        assert b"battle-card" in resp.data

        resp = client.get("/?q=nonexistent")
        assert b"battle-card" not in resp.data

    def test_filter_by_army(self, client, sample_battle):
        resp = client.get("/?army=Space")
        assert b"Space Marines" in resp.data

    def test_filter_by_date_range(self, client, sample_battle):
        resp = client.get("/?date_from=2020-01-01&date_to=2099-12-31")
        assert b"Space Marines" in resp.data


# ------------------------------------------------------------------
# Add Battle
# ------------------------------------------------------------------

class TestAddBattle:
    def test_add_form_renders(self, client):
        resp = client.get("/battles/new")
        assert resp.status_code == 200
        assert b"Add Battle" in resp.data

    def test_add_battle_post(self, client, app):
        resp = client.post("/battles/new", data={
            "date": "2025-06-15",
            "my_army": "Eldar",
            "opponent_army": "Tyranids",
            "result": "Loss",
            "scenario": "Cleanse",
            "army_size": "1500",
            "my_control_points": "5",
            "opp_control_points": "10",
            "my_army_points": "1200",
            "opp_army_points": "1400",
            "my_kill_points": "600",
            "opp_kill_points": "800",
            "event": "Weekend Brawl",
            "initiative": "Second",
            "comment": "Tough match",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Eldar" in resp.data

        with app.app_context():
            battle = Battle.query.first()
            assert battle.my_army == "Eldar"
            assert battle.result == "Loss"
            assert battle.army_size == 1500

    def test_add_battle_missing_date_defaults(self, client, app):
        """Submitting without a date should default to today."""
        resp = client.post("/battles/new", data={
            "my_army": "Necrons",
            "opponent_army": "Tau",
            "result": "Draw",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            battle = Battle.query.first()
            assert battle.date is not None


# ------------------------------------------------------------------
# Edit Battle
# ------------------------------------------------------------------

class TestEditBattle:
    def test_edit_form_renders(self, client, sample_battle):
        resp = client.get(f"/battles/{sample_battle}/edit")
        assert resp.status_code == 200
        assert b"Space Marines" in resp.data

    def test_edit_battle_post(self, client, app, sample_battle):
        resp = client.post(f"/battles/{sample_battle}/edit", data={
            "date": "2025-07-01",
            "my_army": "Dark Angels",
            "opponent_army": "Orks",
            "result": "Loss",
            "scenario": "Take and Hold",
            "army_size": "2000",
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            battle = db.session.get(Battle, sample_battle)
            assert battle.my_army == "Dark Angels"
            assert battle.result == "Loss"

    def test_edit_nonexistent(self, client):
        resp = client.get("/battles/9999/edit")
        assert resp.status_code == 404


# ------------------------------------------------------------------
# Battle Detail
# ------------------------------------------------------------------

class TestBattleDetail:
    def test_detail_renders(self, client, sample_battle):
        resp = client.get(f"/battles/{sample_battle}")
        assert resp.status_code == 200
        assert b"Space Marines" in resp.data
        assert b"Great game!" in resp.data

    def test_detail_nonexistent(self, client):
        resp = client.get("/battles/9999")
        assert resp.status_code == 404


# ------------------------------------------------------------------
# Delete Battle
# ------------------------------------------------------------------

class TestDeleteBattle:
    def test_delete_battle(self, client, app, sample_battle):
        resp = client.post(f"/battles/{sample_battle}/delete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(Battle, sample_battle) is None

    def test_delete_nonexistent(self, client):
        resp = client.post("/battles/9999/delete")
        assert resp.status_code == 404


# ------------------------------------------------------------------
# Statistics
# ------------------------------------------------------------------

class TestStatistics:
    def test_empty_statistics(self, client):
        resp = client.get("/statistics")
        assert resp.status_code == 200
        assert b"No battle data" in resp.data

    def test_statistics_with_data(self, client, sample_battle):
        resp = client.get("/statistics")
        assert resp.status_code == 200
        assert b"Win Rate" in resp.data
        assert b"Space Marines" in resp.data

    def test_statistics_filter(self, client, sample_battle):
        resp = client.get("/statistics?result=Win")
        assert resp.status_code == 200
        assert b"100.0%" in resp.data


# ------------------------------------------------------------------
# Options
# ------------------------------------------------------------------

class TestOptions:
    def test_options_page(self, client):
        resp = client.get("/options")
        assert resp.status_code == 200
        assert b"Export to CSV" in resp.data
        assert b"Gronksoft GamesTracker" in resp.data


# ------------------------------------------------------------------
# Export CSV
# ------------------------------------------------------------------

class TestExportCSV:
    def test_export_empty(self, client):
        resp = client.get("/export/csv")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv"

    def test_export_with_data(self, client, sample_battle):
        resp = client.get("/export/csv")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.data.decode()))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["my_army"] == "Space Marines"
        assert rows[0]["result"] == "Win"


# ------------------------------------------------------------------
# JSON API
# ------------------------------------------------------------------

class TestAPI:
    def test_api_empty(self, client):
        resp = client.get("/api/battles")
        assert resp.status_code == 200
        assert resp.json == []

    def test_api_with_data(self, client, sample_battle):
        resp = client.get("/api/battles")
        data = resp.json
        assert len(data) == 1
        assert data[0]["my_army"] == "Space Marines"


# ------------------------------------------------------------------
# Model
# ------------------------------------------------------------------

class TestModel:
    def test_to_dict(self, app, sample_battle):
        with app.app_context():
            battle = db.session.get(Battle, sample_battle)
            d = battle.to_dict()
            assert d["my_army"] == "Space Marines"
            assert d["result"] == "Win"
            assert "id" in d

    def test_repr(self, app, sample_battle):
        with app.app_context():
            battle = db.session.get(Battle, sample_battle)
            assert "Space Marines" in repr(battle)
