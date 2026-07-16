"""
WhoGapsWho -- vehicle comparison MVP.

All comparison logic, field definitions, and validation live here in Python.
templates/index.html only renders whatever this module hands it -- it holds
no scoring or formatting logic of its own.
"""

from flask import Flask, render_template, request

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

# Seed catalog used by the "search for your vehicle" box. Selecting an entry
# autofills the form fields above (which the user can still edit by hand).
VEHICLE_DATABASE = [
    {"type": "car", "make": "Toyota", "model": "GR86", "year": 2024, "engine": "2.4L Flat-4",
     "horsepower": 228, "torque": 184, "zero_to_sixty": 6.1, "top_speed": 140, "weight": 2811,
     "price": 28400, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Mazda", "model": "MX-5 Miata", "year": 2024, "engine": "2.0L I4",
     "horsepower": 181, "torque": 151, "zero_to_sixty": 6.5, "top_speed": 135, "weight": 2341,
     "price": 29050, "drivetrain": "RWD", "body_style": "Convertible"},
    {"type": "car", "make": "Honda", "model": "Civic Type R", "year": 2024, "engine": "2.0L Turbo I4",
     "horsepower": 315, "torque": 310, "zero_to_sixty": 5.0, "top_speed": 170, "weight": 3188,
     "price": 44890, "drivetrain": "FWD", "body_style": "Hatchback"},
    {"type": "car", "make": "Ford", "model": "Mustang GT", "year": 2024, "engine": "5.0L V8",
     "horsepower": 480, "torque": 415, "zero_to_sixty": 4.3, "top_speed": 155, "weight": 3705,
     "price": 44090, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Chevrolet", "model": "Camaro SS", "year": 2024, "engine": "6.2L V8",
     "horsepower": 455, "torque": 455, "zero_to_sixty": 4.0, "top_speed": 165, "weight": 3685,
     "price": 42395, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Subaru", "model": "WRX", "year": 2024, "engine": "2.4L Turbo Flat-4",
     "horsepower": 271, "torque": 258, "zero_to_sixty": 5.7, "top_speed": 155, "weight": 3300,
     "price": 33825, "drivetrain": "AWD", "body_style": "Sedan"},
    {"type": "car", "make": "Volkswagen", "model": "Golf GTI", "year": 2024, "engine": "2.0L Turbo I4",
     "horsepower": 241, "torque": 273, "zero_to_sixty": 5.8, "top_speed": 155, "weight": 3131,
     "price": 31215, "drivetrain": "FWD", "body_style": "Hatchback"},
    {"type": "car", "make": "BMW", "model": "M3", "year": 2024, "engine": "3.0L Twin-Turbo I6",
     "horsepower": 473, "torque": 406, "zero_to_sixty": 3.8, "top_speed": 180, "weight": 3880,
     "price": 76395, "drivetrain": "AWD", "body_style": "Sedan"},
    {"type": "car", "make": "Porsche", "model": "911 Carrera", "year": 2024, "engine": "3.0L Twin-Turbo Flat-6",
     "horsepower": 379, "torque": 331, "zero_to_sixty": 4.0, "top_speed": 182, "weight": 3354,
     "price": 106100, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Tesla", "model": "Model 3 Performance", "year": 2024, "engine": "Dual Motor Electric",
     "horsepower": 510, "torque": 546, "zero_to_sixty": 2.9, "top_speed": 163, "weight": 4054,
     "price": 52990, "drivetrain": "AWD", "body_style": "Sedan"},
    {"type": "car", "make": "Nissan", "model": "Z", "year": 2024, "engine": "3.0L Twin-Turbo V6",
     "horsepower": 400, "torque": 350, "zero_to_sixty": 4.5, "top_speed": 155, "weight": 3486,
     "price": 42990, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Dodge", "model": "Challenger R/T", "year": 2023, "engine": "5.7L V8",
     "horsepower": 375, "torque": 410, "zero_to_sixty": 5.1, "top_speed": 155, "weight": 4185,
     "price": 39590, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Toyota", "model": "GR Supra", "year": 2024, "engine": "3.0L Turbo I6",
     "horsepower": 382, "torque": 368, "zero_to_sixty": 3.9, "top_speed": 155, "weight": 3400,
     "price": 55250, "drivetrain": "RWD", "body_style": "Coupe"},
    {"type": "car", "make": "Hyundai", "model": "Elantra N", "year": 2024, "engine": "2.0L Turbo I4",
     "horsepower": 276, "torque": 289, "zero_to_sixty": 5.3, "top_speed": 155, "weight": 3163,
     "price": 34000, "drivetrain": "FWD", "body_style": "Sedan"},
    {"type": "car", "make": "Kia", "model": "Stinger GT", "year": 2023, "engine": "3.3L Twin-Turbo V6",
     "horsepower": 368, "torque": 376, "zero_to_sixty": 4.7, "top_speed": 167, "weight": 3958,
     "price": 44785, "drivetrain": "AWD", "body_style": "Hatchback"},
    {"type": "motorbike", "make": "Yamaha", "model": "YZF-R6", "year": 2020, "engine": "599cc I4",
     "horsepower": 118, "torque": 46, "zero_to_sixty": 3.3, "top_speed": 160, "weight": 419,
     "price": 12299, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Kawasaki", "model": "Ninja ZX-6R", "year": 2024, "engine": "636cc I4",
     "horsepower": 127, "torque": 52, "zero_to_sixty": 3.2, "top_speed": 165, "weight": 431,
     "price": 11299, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Honda", "model": "CBR600RR", "year": 2024, "engine": "599cc I4",
     "horsepower": 121, "torque": 48, "zero_to_sixty": 3.4, "top_speed": 160, "weight": 410,
     "price": 12599, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Suzuki", "model": "GSX-R750", "year": 2023, "engine": "750cc I4",
     "horsepower": 148, "torque": 63, "zero_to_sixty": 3.0, "top_speed": 165, "weight": 419,
     "price": 12849, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Ducati", "model": "Panigale V4", "year": 2024, "engine": "1103cc V4",
     "horsepower": 214, "torque": 91, "zero_to_sixty": 2.6, "top_speed": 186, "weight": 439,
     "price": 23495, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Harley-Davidson", "model": "Iron 883", "year": 2022, "engine": "883cc V-Twin",
     "horsepower": 50, "torque": 54, "zero_to_sixty": 4.5, "top_speed": 100, "weight": 564,
     "price": 9499, "drivetrain": "Belt", "bike_style": "Cruiser"},
    {"type": "motorbike", "make": "Triumph", "model": "Street Triple RS", "year": 2024, "engine": "765cc I3",
     "horsepower": 128, "torque": 59, "zero_to_sixty": 3.1, "top_speed": 165, "weight": 417,
     "price": 12595, "drivetrain": "Chain", "bike_style": "Naked"},
    {"type": "motorbike", "make": "KTM", "model": "390 Duke", "year": 2024, "engine": "399cc Single",
     "horsepower": 44, "torque": 29, "zero_to_sixty": 5.5, "top_speed": 107, "weight": 348,
     "price": 5999, "drivetrain": "Chain", "bike_style": "Naked"},
    {"type": "motorbike", "make": "BMW", "model": "S1000RR", "year": 2024, "engine": "999cc I4",
     "horsepower": 205, "torque": 83, "zero_to_sixty": 2.7, "top_speed": 188, "weight": 434,
     "price": 18545, "drivetrain": "Chain", "bike_style": "Sport"},
    {"type": "motorbike", "make": "Yamaha", "model": "MT-07", "year": 2024, "engine": "689cc Twin",
     "horsepower": 73, "torque": 50, "zero_to_sixty": 3.7, "top_speed": 130, "weight": 406,
     "price": 8199, "drivetrain": "Chain", "bike_style": "Naked"},
    {"type": "motorbike", "make": "Honda", "model": "Africa Twin", "year": 2024, "engine": "1084cc Twin",
     "horsepower": 101, "torque": 77, "zero_to_sixty": 3.8, "top_speed": 130, "weight": 502,
     "price": 14899, "drivetrain": "Chain", "bike_style": "Adventure"},
    {"type": "motorbike", "make": "Kawasaki", "model": "Z900", "year": 2024, "engine": "948cc I4",
     "horsepower": 125, "torque": 72, "zero_to_sixty": 3.2, "top_speed": 155, "weight": 467,
     "price": 9199, "drivetrain": "Chain", "bike_style": "Naked"},
    {"type": "motorbike", "make": "Ducati", "model": "Monster", "year": 2024, "engine": "937cc Twin",
     "horsepower": 111, "torque": 69, "zero_to_sixty": 3.3, "top_speed": 150, "weight": 414,
     "price": 12995, "drivetrain": "Chain", "bike_style": "Naked"},
    {"type": "motorbike", "make": "Royal Enfield", "model": "Interceptor 650", "year": 2024, "engine": "648cc Twin",
     "horsepower": 47, "torque": 38, "zero_to_sixty": 6.5, "top_speed": 115, "weight": 445,
     "price": 6799, "drivetrain": "Chain", "bike_style": "Cafe racer"},
    {"type": "motorbike", "make": "Suzuki", "model": "Hayabusa", "year": 2024, "engine": "1340cc I4",
     "horsepower": 190, "torque": 111, "zero_to_sixty": 2.6, "top_speed": 186, "weight": 582,
     "price": 18799, "drivetrain": "Chain", "bike_style": "Sport"},
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
        "vehicle_database": VEHICLE_DATABASE,
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


if __name__ == "__main__":
    app.run(debug=True)
