# WhoGapsWho

Enter two vehicles (car or motorbike), fill in their specs, and see which one
is faster on paper.

## Structure

- `app.py` -- everything that thinks: field definitions, form parsing,
  validation, the speed-score calculation, and stat formatting. This is the
  only file with logic in it.
- `templates/index.html` -- layout only. It loops over field definitions
  passed in from `app.py` and renders whatever it's given; it has no
  knowledge of how a winner is picked.
- `static/style.css` -- styling.

There's no vehicle database yet -- you type in both vehicles' specs by hand.
Swapping in a real database later means adding a lookup step in `app.py`
before `parse_vehicle()`; the form and comparison logic won't need to change.

## Run it

```bash
pip install -r requirements.txt
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
