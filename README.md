# WhoGapsWho

Enter two vehicles (car or motorbike), fill in their specs, and see which one
is faster on paper.

## Structure

- `app.py` -- everything that thinks: field definitions, form parsing,
  validation, the speed-score calculation, stat formatting, and the vehicle
  search API. This is the only file with logic in it.
- `templates/index.html` -- layout only. It loops over field definitions
  passed in from `app.py` and renders whatever it's given; it has no
  knowledge of how a winner is picked.
- `static/style.css` -- styling.
- `db.py` -- Postgres connection pooling (lazy: importing this module doesn't
  require the database to be reachable yet).
- `schema.sql` -- the `vehicles` table + trigram index used for search.
- `seed_data.py` / `scripts/seed_db.py` -- the starting vehicle catalog and
  the script that loads it into Postgres.

You can still type in both vehicles' specs by hand. The "search for your
vehicle" box additionally autofills those same fields from a Postgres-backed
catalog, which you're then free to edit before comparing.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env   # adjust DATABASE_URL if needed
python scripts/seed_db.py   # creates the vehicles table and loads seed data
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## How the comparison works

Each vehicle needs: make, model, year, engine, horsepower, torque, 0-60 time,
top speed, and weight. Price is optional. Car and motorbike each also get a
couple of type-specific fields (drivetrain style, body/bike style) that show
up on the result cards but don't yet factor into scoring.

The "faster on paper" verdict is a simple speed score:

```
score = top_speed / zero_to_sixty
```

Whichever vehicle scores higher wins the verdict. Every other stat
(horsepower, torque, weight, price) is compared independently and the better
value on each row is highlighted -- winning that stat doesn't have to mean
winning the overall verdict.
