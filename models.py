"""Database models for Gronksoft GamesTracker."""

from datetime import UTC, date, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Battle(db.Model):
    """A single tabletop wargame battle record."""

    __tablename__ = "battles"

    id = db.Column(db.Integer, primary_key=True)

    # --- core fields (DataEntry_Portrait1) ---
    date = db.Column(db.Date, nullable=False, default=date.today)
    my_army = db.Column(db.String(120), nullable=False, default="")
    opponent_army = db.Column(db.String(120), nullable=False, default="")
    result = db.Column(
        db.String(20), nullable=False, default="Draw"
    )  # Win / Loss / Draw
    scenario = db.Column(db.String(120), nullable=False, default="")
    army_size = db.Column(db.Integer, nullable=False, default=0)

    # --- additional / points (DataEntry_Portrait2) ---
    my_control_points = db.Column(db.Integer, nullable=False, default=0)
    opp_control_points = db.Column(db.Integer, nullable=False, default=0)
    my_army_points = db.Column(db.Integer, nullable=False, default=0)
    opp_army_points = db.Column(db.Integer, nullable=False, default=0)
    my_kill_points = db.Column(db.Integer, nullable=False, default=0)
    opp_kill_points = db.Column(db.Integer, nullable=False, default=0)

    event = db.Column(db.String(120), nullable=False, default="")
    initiative = db.Column(db.String(60), nullable=False, default="")
    comment = db.Column(db.Text, nullable=False, default="")

    # --- meta ---
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self):
        """Serialise to a plain dictionary (useful for JSON / export)."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else "",
            "my_army": self.my_army,
            "opponent_army": self.opponent_army,
            "result": self.result,
            "scenario": self.scenario,
            "army_size": self.army_size,
            "my_control_points": self.my_control_points,
            "opp_control_points": self.opp_control_points,
            "my_army_points": self.my_army_points,
            "opp_army_points": self.opp_army_points,
            "my_kill_points": self.my_kill_points,
            "opp_kill_points": self.opp_kill_points,
            "event": self.event,
            "initiative": self.initiative,
            "comment": self.comment,
        }

    def __repr__(self):
        return f"<Battle {self.id}: {self.my_army} vs {self.opponent_army} ({self.result})>"
