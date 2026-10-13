# Overall score (0–100). Number parts are min–max scaled across the hotels being compared
# (best hotel gets full points, worst gets 0). Yes/no parts give full points or none.
WEIGHTS = {"reviews": 25, "price": 20, "travel": 20, "room": 15, "heat": 10, "food": 5, "bath": 5}
LOWER_IS_BETTER = {"price", "travel"}
YES_NO = {"heat", "bath"}

def _scale(vals, higher_better):
    known = [v for v in vals if v is not None]
    lo, hi = (min(known), max(known)) if known else (0, 0)
    out = []
    for v in vals:
        if v is None or hi == lo: out.append(0.5)   # unknown (e.g. no price) or no spread → half points
        else: out.append((v - lo) / (hi - lo) if higher_better else (hi - v) / (hi - lo))
    return out

def overall_scores(hotels, g):
    """g(h, part) returns the raw value for a part, or None if unknown. For YES_NO parts return 1/0."""
    parts = {}
    for p in WEIGHTS:
        vals = [g(h, p) for h in hotels]
        parts[p] = [0.5 if v is None else float(v) for v in vals] if p in YES_NO else _scale(vals, p not in LOWER_IS_BETTER)
    for i, h in enumerate(hotels):
        h["score_parts"] = {p: round(parts[p][i] * w, 1) for p, w in WEIGHTS.items()}
        h["overall"] = round(sum(h["score_parts"].values()), 1)
