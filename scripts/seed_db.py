"""(Re)create the vehicles table and load the seed catalog.

Run with the venv active, from the project root:
    python scripts/seed_db.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_cursor
from seed_data import SEED_VEHICLES

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schema.sql")

INSERT_SQL = """
    INSERT INTO vehicles
        (type, make, model, year, engine, horsepower, torque,
         zero_to_sixty, top_speed, weight, price, drivetrain,
         body_style, bike_style)
    VALUES
        (%(type)s, %(make)s, %(model)s, %(year)s, %(engine)s,
         %(horsepower)s, %(torque)s, %(zero_to_sixty)s, %(top_speed)s,
         %(weight)s, %(price)s, %(drivetrain)s, %(body_style)s, %(bike_style)s)
"""


def main():
    with open(SCHEMA_PATH) as f:
        schema_sql = f.read()

    with get_cursor() as cur:
        cur.execute(schema_sql)
        cur.execute("TRUNCATE vehicles RESTART IDENTITY")
        for vehicle in SEED_VEHICLES:
            row = {"drivetrain": None, "body_style": None, "bike_style": None, **vehicle}
            cur.execute(INSERT_SQL, row)

    print(f"Seeded {len(SEED_VEHICLES)} vehicles.")


if __name__ == "__main__":
    main()
