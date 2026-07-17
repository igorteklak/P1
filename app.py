"""
WhoGapsWho -- vehicle comparison MVP.

All comparison logic, field definitions, and validation live here in Python.
templates/index.html only renders whatever this module hands it -- it holds
no scoring or formatting logic of its own.
"""

import psycopg2
from flask import Flask, jsonify, render_template, request

from db import get_cursor

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Schema: this is the single source of truth for what a "vehicle" is.
# Add a field here and it shows up in the form automatically.
# ---------------------------------------------------------------------------

VEHICLE_TYPES = ["car", "motorbike"]

# Fields every vehicle type shares, used for both the form and the comparison.
COMMON_FIELDS = [
    {"key": "make", "label": "Make", "input": "text", "placeholder": "Toyota", "required": True},
    {"key": "model", "label": "Model", "input": "text", "placeholder": "GR86", "required": True},
    {"key": "year", "label": "Year", "input": "number", "placeholder": "2024",
     "required": True, "min": 1900, "max": 2100, "step": "1"},
    {"key": "engine", "label": "Engine", "input": "text", "placeholder": "2.4L Turbo I4", "required": True},
    {"key": "horsepower", "label": "Horsepower", "input": "number", "unit": "hp",
     "placeholder": "228", "required": True, "min": 0, "step": "1"},
    {"key": "torque", "label": "Torque", "input": "number", "unit": "lb-ft",
     "placeholder": "184", "required": True, "min": 0, "step": "1"},
    {"key": "zero_to_sixty", "label": "0-60 mph", "input": "number", "unit": "sec",
     "placeholder": "6.1", "required": True, "min": 0, "step": "0.1"},
    {"key": "top_speed", "label": "Top speed", "input": "number", "unit": "mph",
     "placeholder": "140", "required": True, "min": 0, "step": "1"},
    {"key": "weight", "label": "Weight", "input": "number", "unit": "lbs",
     "placeholder": "2811", "required": True, "min": 0, "step": "1"},
    {"key": "price", "label": "Price", "input": "number", "unit": "$",
     "placeholder": "28400", "required": False, "min": 0, "step": "1"},
]

# Fields specific to each vehicle type. Purely descriptive for now -- they
# show up on the vehicle card but don't feed the speed score yet.
TYPE_FIELDS = {
    "car": [
        {"key": "drivetrain", "label": "Drivetrain", "input": "select",
         "options": ["FWD", "RWD", "AWD", "4WD"]},
        {"key": "body_style", "label": "Body style", "input": "select",
         "options": ["Sedan", "Coupe", "Hatchback", "SUV", "Truck", "Convertible"]},
    ],
    "motorbike": [
        {"key": "drivetrain", "label": "Final drive", "input": "select",
         "options": ["Chain", "Belt", "Shaft"]},
        {"key": "bike_style", "label": "Bike style", "input": "select",
         "options": ["Sport", "Naked", "Cruiser", "Touring", "Adventure", "Cafe racer"]},
    ],
}

# Stats shown in the side-by-side comparison, and how to score/format each one.
STAT_FIELDS = [
    {"key": "horsepower", "label": "Horsepower", "higher_better": True, "fmt": "int"},
    {"key": "torque", "label": "Torque", "higher_better": True, "fmt": "int"},
    {"key": "zero_to_sixty", "label": "0-60 mph", "higher_better": False, "fmt": "float1"},
    {"key": "top_speed", "label": "Top speed", "higher_better": True, "fmt": "int"},
    {"key": "weight", "label": "Weight", "higher_better": False, "fmt": "int"},
    {"key": "price", "label": "Price", "higher_better": False, "fmt": "currency"},
]

# ---------------------------------------------------------------------------
# Parsing + validation
# ---------------------------------------------------------------------------

def parse_vehicle(form, slot):
    """Build a vehicle dict for slot 'a' or 'b' from posted form data.

    Returns (vehicle_dict, list_of_error_strings).
    """
    vtype = form.get(f"type_{slot}", "car")
    if vtype not in VEHICLE_TYPES:
        vtype = "car"

    vehicle = {"type": vtype}
    errors = []

    for field in COMMON_FIELDS:
        raw = (form.get(f"{slot}_{field['key']}") or "").strip()
        if field["input"] == "number":
            if raw == "":
                if field.get("required"):
                    errors.append(f"Vehicle {slot.upper()}: {field['label']} is required.")
                vehicle[field["key"]] = None
                continue
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"Vehicle {slot.upper()}: {field['label']} must be a number.")
                vehicle[field["key"]] = None
                continue
            if "min" in field and value < field["min"]:
                errors.append(f"Vehicle {slot.upper()}: {field['label']} can't be below {field['min']}.")
            vehicle[field["key"]] = value
        else:
            if not raw and field.get("required"):
                errors.append(f"Vehicle {slot.upper()}: {field['label']} is required.")
            vehicle[field["key"]] = raw

    for field in TYPE_FIELDS.get(vtype, []):
        vehicle[field["key"]] = (form.get(f"{slot}_{field['key']}") or "").strip()

    return vehicle, errors


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def format_value(fmt, value):
    if value is None or value == "":
        return "\u2014"  # em dash for "no data"
    if fmt == "currency":
        return f"${value:,.0f}"
    if fmt == "float1":
        return f"{value:.1f}"
    return f"{value:,.0f}"


def compute_speed_score(vehicle):
    """Higher top speed and lower 0-60 both push this up."""
    zts = vehicle.get("zero_to_sixty") or 0
    top = vehicle.get("top_speed") or 0
    if zts <= 0:
        return 0
    return top / zts


def build_comparison(a, b):
    score_a = compute_speed_score(a)
    score_b = compute_speed_score(b)
    a_is_faster = score_a >= score_b
    winner, loser = (a, b) if a_is_faster else (b, a)

    smaller = min(score_a, score_b)
    diff_pct = round(abs(score_a - score_b) / smaller * 100) if smaller > 0 else 0

    rows = []
    for field in STAT_FIELDS:
        key = field["key"]
        va, vb = a.get(key), b.get(key)

        a_wins = b_wins = False
        if va is not None and vb is not None and va != vb:
            if field["higher_better"]:
                a_wins, b_wins = va > vb, vb > va
            else:
                a_wins, b_wins = va < vb, vb < va

        max_val = max(va or 0, vb or 0) or 1
        rows.append({
            "label": field["label"],
            "a_value": format_value(field["fmt"], va),
            "b_value": format_value(field["fmt"], vb),
            "a_pct": max(6, round((va or 0) / max_val * 100)),
            "b_pct": max(6, round((vb or 0) / max_val * 100)),
            "a_wins": a_wins,
            "b_wins": b_wins,
        })

    return {
        "winner_name": f"{winner.get('make', '')} {winner.get('model', '')}".strip(),
        "loser_name": f"{loser.get('make', '')} {loser.get('model', '')}".strip(),
        "winner_top_speed": format_value("int", winner.get("top_speed")),
        "winner_zero_to_sixty": format_value("float1", winner.get("zero_to_sixty")),
        "diff_pct": diff_pct,
        "rows": rows,
    }


def vehicle_subtitle(vehicle):
    """Small descriptive line under the vehicle name, e.g. '2024 - 2.4L Turbo I4 - RWD'."""
    parts = []
    if vehicle.get("year"):
        parts.append(str(int(vehicle["year"])))
    if vehicle.get("engine"):
        parts.append(vehicle["engine"])
    if vehicle.get("drivetrain"):
        parts.append(vehicle["drivetrain"])
    return " \u00b7 ".join(parts)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def base_context(values=None, errors=None, result=None, vehicle_a=None, vehicle_b=None):
    return {
        "vehicle_types": VEHICLE_TYPES,
        "common_fields": COMMON_FIELDS,
        "type_fields": TYPE_FIELDS,
        "values": values or {},
        "errors": errors or [],
        "result": result,
        "vehicle_a": vehicle_a,
        "vehicle_b": vehicle_b,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", **base_context())


@app.route("/compare", methods=["POST"])
def compare():
    vehicle_a, errors_a = parse_vehicle(request.form, "a")
    vehicle_b, errors_b = parse_vehicle(request.form, "b")
    errors = errors_a + errors_b

    result = None
    if not errors:
        result = build_comparison(vehicle_a, vehicle_b)

    return render_template(
        "index.html",
        **base_context(
            values=request.form,
            errors=errors,
            result=result,
            vehicle_a=vehicle_a if not errors else None,
            vehicle_b=vehicle_b if not errors else None,
        ),
        vehicle_a_subtitle=vehicle_subtitle(vehicle_a) if not errors else "",
        vehicle_b_subtitle=vehicle_subtitle(vehicle_b) if not errors else "",
    )


@app.route("/api/vehicles")
def search_vehicles():
    """Backs the "search for your vehicle" box -- returns up to 8 matches."""
    vtype = request.args.get("type", "car")
    if vtype not in VEHICLE_TYPES:
        vtype = "car"

    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify([])

    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT type, make, model, year, engine,
                       horsepower::float AS horsepower,
                       torque::float AS torque,
                       zero_to_sixty::float AS zero_to_sixty,
                       top_speed::float AS top_speed,
                       weight::float AS weight,
                       price::float AS price,
                       drivetrain, body_style, bike_style
                FROM vehicles
                WHERE type = %s
                  AND (make || ' ' || model || ' ' || year::text) ILIKE %s
                ORDER BY make, model
                LIMIT 8
                """,
                (vtype, f"%{query}%"),
            )
            columns = [col.name for col in cur.description]
            matches = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error:
        app.logger.exception("Vehicle search query failed")
        return jsonify([]), 503

    return jsonify(matches)


if __name__ == "__main__":
    app.run(debug=True)
