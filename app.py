"""Gronksoft GamesTracker – Flask application.

Spiritual successor to Iron Grudge.
"""

import csv
import io
import os
from datetime import date

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from models import Battle, db


def create_app(testing: bool = False):
    """Application factory."""
    app = Flask(__name__)

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gamestracker.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gronksoft-dev-key")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    # --- Games List (home) -------------------------------------------
    @app.route("/")
    def battle_list():
        """Home screen – list of all battles with optional filtering."""
        query = Battle.query

        # Filter parameters
        result_filter = request.args.get("result", "").strip()
        army_filter = request.args.get("army", "").strip()
        opponent_filter = request.args.get("opponent", "").strip()
        scenario_filter = request.args.get("scenario", "").strip()
        event_filter = request.args.get("event", "").strip()
        search_query = request.args.get("q", "").strip()
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        if result_filter:
            query = query.filter(Battle.result == result_filter)
        if army_filter:
            query = query.filter(Battle.my_army.ilike(f"%{army_filter}%"))
        if opponent_filter:
            query = query.filter(Battle.opponent_army.ilike(f"%{opponent_filter}%"))
        if scenario_filter:
            query = query.filter(Battle.scenario.ilike(f"%{scenario_filter}%"))
        if event_filter:
            query = query.filter(Battle.event.ilike(f"%{event_filter}%"))
        if date_from:
            try:
                query = query.filter(Battle.date >= date.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                query = query.filter(Battle.date <= date.fromisoformat(date_to))
            except ValueError:
                pass
        if search_query:
            like = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Battle.my_army.ilike(like),
                    Battle.opponent_army.ilike(like),
                    Battle.scenario.ilike(like),
                    Battle.event.ilike(like),
                    Battle.comment.ilike(like),
                )
            )

        battles = query.order_by(Battle.date.desc()).all()

        # Collect unique values for filter dropdowns
        all_armies = sorted(
            {b.my_army for b in Battle.query.all() if b.my_army}
        )
        all_opponents = sorted(
            {b.opponent_army for b in Battle.query.all() if b.opponent_army}
        )
        all_scenarios = sorted(
            {b.scenario for b in Battle.query.all() if b.scenario}
        )
        all_events = sorted(
            {b.event for b in Battle.query.all() if b.event}
        )

        return render_template(
            "battle_list.html",
            battles=battles,
            filters={
                "result": result_filter,
                "army": army_filter,
                "opponent": opponent_filter,
                "scenario": scenario_filter,
                "event": event_filter,
                "q": search_query,
                "date_from": date_from,
                "date_to": date_to,
            },
            all_armies=all_armies,
            all_opponents=all_opponents,
            all_scenarios=all_scenarios,
            all_events=all_events,
        )

    # --- Add Battle --------------------------------------------------
    @app.route("/battles/new", methods=["GET", "POST"])
    def battle_add():
        """Add battle form (two-section layout)."""
        if request.method == "POST":
            battle = _battle_from_form(request.form)
            db.session.add(battle)
            db.session.commit()
            return redirect(url_for("battle_detail", battle_id=battle.id))

        return render_template("battle_form.html", battle=None)

    # --- Edit Battle -------------------------------------------------
    @app.route("/battles/<int:battle_id>/edit", methods=["GET", "POST"])
    def battle_edit(battle_id):
        """Edit an existing battle."""
        battle = db.get_or_404(Battle, battle_id)
        if request.method == "POST":
            _update_battle_from_form(battle, request.form)
            db.session.commit()
            return redirect(url_for("battle_detail", battle_id=battle.id))

        return render_template("battle_form.html", battle=battle)

    # --- Battle Detail -----------------------------------------------
    @app.route("/battles/<int:battle_id>")
    def battle_detail(battle_id):
        """Game result / detail view."""
        battle = db.get_or_404(Battle, battle_id)
        return render_template("battle_detail.html", battle=battle)

    # --- Delete Battle -----------------------------------------------
    @app.route("/battles/<int:battle_id>/delete", methods=["POST"])
    def battle_delete(battle_id):
        """Delete a battle (from long-press context menu)."""
        battle = db.get_or_404(Battle, battle_id)
        db.session.delete(battle)
        db.session.commit()
        return redirect(url_for("battle_list"))

    # --- Statistics --------------------------------------------------
    @app.route("/statistics")
    def statistics():
        """Statistics screen – summary views."""
        query = Battle.query

        # Apply same filters as list for scoped statistics
        result_filter = request.args.get("result", "").strip()
        army_filter = request.args.get("army", "").strip()
        event_filter = request.args.get("event", "").strip()

        if result_filter:
            query = query.filter(Battle.result == result_filter)
        if army_filter:
            query = query.filter(Battle.my_army.ilike(f"%{army_filter}%"))
        if event_filter:
            query = query.filter(Battle.event.ilike(f"%{event_filter}%"))

        battles = query.all()
        total = len(battles)
        wins = sum(1 for b in battles if b.result == "Win")
        losses = sum(1 for b in battles if b.result == "Loss")
        draws = sum(1 for b in battles if b.result == "Draw")
        win_pct = round(wins / total * 100, 1) if total else 0

        # Per-army breakdown
        army_stats = {}
        for b in battles:
            name = b.my_army or "(unknown)"
            entry = army_stats.setdefault(
                name, {"wins": 0, "losses": 0, "draws": 0, "total": 0}
            )
            entry["total"] += 1
            if b.result == "Win":
                entry["wins"] += 1
            elif b.result == "Loss":
                entry["losses"] += 1
            else:
                entry["draws"] += 1
        for entry in army_stats.values():
            entry["win_pct"] = (
                round(entry["wins"] / entry["total"] * 100, 1)
                if entry["total"]
                else 0
            )

        # Points totals
        total_my_cp = sum(b.my_control_points for b in battles)
        total_opp_cp = sum(b.opp_control_points for b in battles)
        total_my_ap = sum(b.my_army_points for b in battles)
        total_opp_ap = sum(b.opp_army_points for b in battles)
        total_my_kp = sum(b.my_kill_points for b in battles)
        total_opp_kp = sum(b.opp_kill_points for b in battles)

        return render_template(
            "statistics.html",
            total=total,
            wins=wins,
            losses=losses,
            draws=draws,
            win_pct=win_pct,
            army_stats=army_stats,
            total_my_cp=total_my_cp,
            total_opp_cp=total_opp_cp,
            total_my_ap=total_my_ap,
            total_opp_ap=total_opp_ap,
            total_my_kp=total_my_kp,
            total_opp_kp=total_opp_kp,
            filters={
                "result": result_filter,
                "army": army_filter,
                "event": event_filter,
            },
        )

    # --- Options / Export -------------------------------------------
    @app.route("/options")
    def options():
        """Options / settings screen."""
        return render_template("options.html")

    @app.route("/export/csv")
    def export_csv():
        """Export all battles as CSV."""
        battles = Battle.query.order_by(Battle.date.desc()).all()
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "date",
                "my_army",
                "opponent_army",
                "result",
                "scenario",
                "army_size",
                "my_control_points",
                "opp_control_points",
                "my_army_points",
                "opp_army_points",
                "my_kill_points",
                "opp_kill_points",
                "event",
                "initiative",
                "comment",
            ],
        )
        writer.writeheader()
        for b in battles:
            writer.writerow(b.to_dict())
        csv_data = output.getvalue()
        return (
            csv_data,
            200,
            {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=battles_export.csv",
            },
        )

    # --- JSON API (for potential future mobile client) ---------------
    @app.route("/api/battles")
    def api_battles():
        """Return all battles as JSON."""
        battles = Battle.query.order_by(Battle.date.desc()).all()
        return jsonify([b.to_dict() for b in battles])

    return app


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_int(value, default=0):
    """Safely parse an integer from form input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _battle_from_form(form):
    """Create a new Battle instance from form data."""
    battle = Battle()
    _update_battle_from_form(battle, form)
    return battle


def _update_battle_from_form(battle, form):
    """Update a Battle instance from submitted form data."""
    date_str = form.get("date", "")
    try:
        battle.date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        battle.date = date.today()

    battle.my_army = form.get("my_army", "").strip()
    battle.opponent_army = form.get("opponent_army", "").strip()
    battle.result = form.get("result", "Draw").strip()
    battle.scenario = form.get("scenario", "").strip()
    battle.army_size = _parse_int(form.get("army_size"))

    battle.my_control_points = _parse_int(form.get("my_control_points"))
    battle.opp_control_points = _parse_int(form.get("opp_control_points"))
    battle.my_army_points = _parse_int(form.get("my_army_points"))
    battle.opp_army_points = _parse_int(form.get("opp_army_points"))
    battle.my_kill_points = _parse_int(form.get("my_kill_points"))
    battle.opp_kill_points = _parse_int(form.get("opp_kill_points"))

    battle.event = form.get("event", "").strip()
    battle.initiative = form.get("initiative", "").strip()
    battle.comment = form.get("comment", "").strip()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    application = create_app()
    application.run()
