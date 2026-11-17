#!/usr/bin/env python3
"""
Hellenistic chart calculator (Swiss Ephemeris).

Calculates, from exact birth data:
  1 Sect (day/night chart, sect of each planet, above/below horizon)
  2 Condition (domicile/exaltation/detriment/fall, triplicity and bound rulers, phase with the Sun, beams, retrograde)
  3 Aspects (whole-sign aspects and aversion, plus exact-angle orbs)
  4 Houses (whole-sign)
  5 Lots (Fortune, Spirit; day/night formulas)
  6 Timing (annual + monthly profections, zodiacal releasing from Spirit and Fortune, current transits)

Usage:
  python chart_calc.py --name Jane --date 1985-03-14 --time 14:07 --lat 39.0997 --lon -94.5786 --out jane
  python chart_calc.py --name Jane --date 1985-03-14 --time 14:07 --place "Kansas City, Missouri, USA" --out jane

Time is LOCAL civil time at the birthplace. The timezone (with historical DST) is looked up from the coordinates
unless you pass --tz (an IANA name like America/Chicago). Output: <out>.json and <out>.md
Zodiac: tropical. Ephemeris: built-in Moshier (no data files needed), accurate to about 1 arc second for these planets.
"""
import argparse, json, math, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import swisseph as swe

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
PLANETS = [("Sun", swe.SUN), ("Moon", swe.MOON), ("Mercury", swe.MERCURY), ("Venus", swe.VENUS),
           ("Mars", swe.MARS), ("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN)]
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

DOMICILE = {"Sun": [4], "Moon": [3], "Mercury": [2, 5], "Venus": [1, 6], "Mars": [0, 7], "Jupiter": [8, 11], "Saturn": [9, 10]}
SIGN_RULER = {0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"}
EXALT = {"Sun": (0, 19), "Moon": (1, 3), "Mercury": (5, 15), "Venus": (11, 27), "Mars": (9, 28), "Jupiter": (3, 15), "Saturn": (6, 21)}
# Dorothean triplicity rulers by element (day, night, participating)
TRIP = {"fire": ("Sun", "Jupiter", "Saturn"), "earth": ("Venus", "Moon", "Mars"),
        "air": ("Saturn", "Mercury", "Jupiter"), "water": ("Venus", "Mars", "Moon")}
ELEMENT = ["fire", "earth", "air", "water"] * 3
# Egyptian bounds (terms): (ruler, upper degree)
BOUNDS = [
    [("Jupiter", 6), ("Venus", 12), ("Mercury", 20), ("Mars", 25), ("Saturn", 30)],
    [("Venus", 8), ("Mercury", 14), ("Jupiter", 22), ("Saturn", 27), ("Mars", 30)],
    [("Mercury", 6), ("Jupiter", 12), ("Venus", 17), ("Mars", 24), ("Saturn", 30)],
    [("Mars", 7), ("Venus", 13), ("Mercury", 19), ("Jupiter", 26), ("Saturn", 30)],
    [("Jupiter", 6), ("Venus", 11), ("Saturn", 18), ("Mercury", 24), ("Mars", 30)],
    [("Mercury", 7), ("Venus", 17), ("Jupiter", 21), ("Mars", 28), ("Saturn", 30)],
    [("Saturn", 6), ("Mercury", 14), ("Jupiter", 21), ("Venus", 28), ("Mars", 30)],
    [("Mars", 7), ("Venus", 11), ("Mercury", 19), ("Jupiter", 24), ("Saturn", 30)],
    [("Jupiter", 12), ("Venus", 17), ("Mercury", 21), ("Saturn", 26), ("Mars", 30)],
    [("Mercury", 7), ("Jupiter", 14), ("Venus", 22), ("Saturn", 26), ("Mars", 30)],
    [("Mercury", 7), ("Venus", 13), ("Jupiter", 20), ("Mars", 25), ("Saturn", 30)],
    [("Venus", 12), ("Jupiter", 16), ("Mercury", 19), ("Mars", 28), ("Saturn", 30)],
]
# Zodiacal releasing: planetary years of each sign's ruler
ZR_YEARS = {0: 15, 1: 8, 2: 20, 3: 25, 4: 19, 5: 20, 6: 8, 7: 15, 8: 12, 9: 27, 10: 30, 11: 12}
DIURNAL = {"Sun", "Jupiter", "Saturn"}
NOCTURNAL = {"Moon", "Venus", "Mars"}
ASPECT_NAMES = {0: "conjunction (same sign)", 2: "sextile", 3: "square", 4: "trine", 6: "opposition"}
AVERSION = {1, 5, 7, 11}
EXACT = [(0, "conjunction", 8), (60, "sextile", 5), (90, "square", 7), (120, "trine", 7), (180, "opposition", 8)]


def sign_of(lon): return int(lon // 30) % 12
def deg_in_sign(lon): return lon % 30
def fmt(lon):
    d = deg_in_sign(lon); m = int(round((d - int(d)) * 60))
    di = int(d)
    if m == 60: di += 1; m = 0
    return f"{di}°{m:02d}' {SIGNS[sign_of(lon)]}"
def norm(x): return x % 360.0
def bound_ruler(lon):
    d = deg_in_sign(lon)
    for r, up in BOUNDS[sign_of(lon)]:
        if d < up: return r
    return BOUNDS[sign_of(lon)][-1][0]


def dignity(name, lon):
    s = sign_of(lon); out = []
    if s in DOMICILE[name]: out.append("domicile")
    if EXALT[name][0] == s: out.append("exaltation")
    if (s + 6) % 12 in DOMICILE[name]: out.append("detriment")
    if (EXALT[name][0] + 6) % 12 == s: out.append("fall")
    return out or ["peregrine (no major dignity or debility by sign)"]


def locate(place):
    from geopy.geocoders import Nominatim
    try: g = Nominatim(user_agent="emc-chart-calc").geocode(place, timeout=10)
    except Exception as e: sys.exit(f"Place lookup failed ({type(e).__name__}). Pass --lat and --lon instead.")
    if not g: sys.exit(f"Could not find '{place}'. Pass --lat and --lon instead.")
    return g.latitude, g.longitude, g.address


def to_utc(date, time, lat, lon, tzname):
    if not tzname:
        from timezonefinder import TimezoneFinder
        tzname = TimezoneFinder().timezone_at(lat=lat, lng=lon)
        if not tzname: sys.exit("Could not determine the timezone. Pass --tz.")
    tz = ZoneInfo(tzname)
    y, mo, d = map(int, date.split("-")); hh, mm = map(int, time.split(":"))
    naive = datetime(y, mo, d, hh, mm)
    a = naive.replace(tzinfo=tz, fold=0); b = naive.replace(tzinfo=tz, fold=1)
    warn = []
    rt = a.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None)
    if rt == naive and a.utcoffset() != b.utcoffset():
        warn.append("This local time is AMBIGUOUS (daylight saving 'fall back' hour). Confirm whether it was before or after the change. Fold=0 (first occurrence) was used.")
    if rt != naive:
        warn.append("This local time did NOT EXIST (daylight saving 'spring forward' gap). Check the birth time.")
    if y < 1970:
        warn.append("Birth year before 1970: historical timezone/DST rules for this place are less reliable. Confirm the offset from the birth record if you can.")
    return a.astimezone(timezone.utc), tzname, a.utcoffset(), warn


def planet_pos(jd, pid):
    xx, _ = swe.calc_ut(jd, pid, FLAGS)
    return {"lon": xx[0], "lat": xx[1], "dist": xx[2], "speed": xx[3]}


def chart(args):
    if args.place and (args.lat is None or args.lon is None):
        lat, lon, addr = locate(args.place)
    else:
        lat, lon, addr = args.lat, args.lon, args.place or ""
    if lat is None or lon is None: sys.exit("Need --place or both --lat and --lon.")
    utc, tzname, off, warns = to_utc(args.date, args.time, lat, lon, args.tz)
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60 + utc.second / 3600)

    pos = {n: planet_pos(jd, pid) for n, pid in PLANETS}
    nn = planet_pos(jd, swe.MEAN_NODE)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_MOSEPH)
    asc, mc = ascmc[0], ascmc[1]
    asc_sign = sign_of(asc)

    def alt(lon_, lat_, dist_):
        _, ta, _ = swe.azalt(jd, swe.ECL2HOR, (lon, lat, 0), 1013.25, 15, (lon_, lat_, dist_))
        return ta
    for n in pos: pos[n]["alt"] = alt(pos[n]["lon"], pos[n]["lat"], pos[n]["dist"])

    sun_alt = pos["Sun"]["alt"]
    is_day = sun_alt > -0.833  # upper limb on the horizon
    if abs(sun_alt + 0.833) < 1.0:
        warns.append(f"The Sun is within 1° of the horizon (altitude {sun_alt:.2f}°). Sect depends on the exact birth minute here; verify the birth time.")
    house = lambda l: (sign_of(l) - asc_sign) % 12 + 1

    sun_lon = pos["Sun"]["lon"]
    planets = {}
    for n, _ in PLANETS:
        p = pos[n]; l = p["lon"]
        elong = norm(l - sun_lon)
        d = {"longitude": round(l, 4), "position": fmt(l), "sign": SIGNS[sign_of(l)], "house": house(l),
             "retrograde": p["speed"] < 0, "speed_deg_per_day": round(p["speed"], 4), "altitude": round(p["alt"], 2),
             "above_horizon": p["alt"] > -0.833, "dignity_by_sign": dignity(n, l),
             "sign_ruler": SIGN_RULER[sign_of(l)], "bound_ruler": bound_ruler(l)}
        el = ELEMENT[sign_of(l)]; t = TRIP[el]
        d["triplicity_rulers"] = {"day": t[0], "night": t[1], "participating": t[2], "in_charge_now": t[0] if is_day else t[1]}
        if n == "Sun":
            d["phase_with_sun"] = "the Sun"
        else:
            sep = min(elong, 360 - elong)
            oriental = elong > 180  # rises before the Sun
            d["elongation_from_sun"] = round(sep, 3)
            d["side_of_sun"] = "oriental (morning, rises before the Sun)" if oriental else "occidental (evening, sets after the Sun)"
            if sep < 17 / 60: ph = "cazimi (in the heart of the Sun)"
            elif sep < 8.5: ph = "combust"
            elif sep < 15: ph = "under the Sun's beams"
            else: ph = "free of the Sun's beams"
            d["beams"] = ph
            if n == "Moon":
                names = [(45, "new / waxing crescent start"), (90, "waxing crescent"), (135, "waxing gibbous"), (180, "waxing gibbous to full"),
                         (225, "full / waning"), (270, "waning gibbous"), (315, "waning crescent"), (360, "waning crescent to new")]
                d["moon_phase"] = f"{elong:.1f}° ahead of the Sun; " + ("waxing" if elong < 180 else "waning")
        # sect
        if n == "Mercury":
            sect = "diurnal" if elong > 180 else "nocturnal"
            d["sect_group"] = sect + " (Mercury follows the Sun: oriental = diurnal, occidental = nocturnal)"
            insect = (sect == "diurnal") == is_day
        else:
            sect = "diurnal" if n in DIURNAL else "nocturnal"; d["sect_group"] = sect
            insect = (n in DIURNAL) == is_day
        d["in_sect"] = insect
        planets[n] = d

    if is_day: bene, male_in, male_out = "Jupiter", "Saturn", "Mars"
    else: bene, male_in, male_out = "Venus", "Mars", "Saturn"
    sect_info = {"chart": "day" if is_day else "night", "sun_altitude": round(sun_alt, 2),
                 "benefic_of_sect": bene, "other_benefic": "Venus" if is_day else "Jupiter",
                 "malefic_of_sect": male_in, "malefic_contrary_to_sect": male_out,
                 "luminary_of_sect": "Sun" if is_day else "Moon"}

    # aspects (whole-sign) and exact angles
    names = [n for n, _ in PLANETS]; aspects = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            la, lb = planets[a]["longitude"], planets[b]["longitude"]
            diff = (sign_of(lb) - sign_of(la)) % 12
            rel = {0: "conjunction (same sign)", 2: "sextile", 10: "sextile", 3: "square", 9: "square", 4: "trine", 8: "trine", 6: "opposition"}.get(diff, "aversion (cannot see each other)")
            sep = abs(la - lb); sep = min(sep, 360 - sep); exact = None
            for ang, nm, orb in EXACT:
                if abs(sep - ang) <= orb: exact = f"{nm}, orb {abs(sep - ang):.2f}°"
            aspects.append({"a": a, "b": b, "sign_relation": rel, "sees_each_other": diff not in AVERSION,
                            "exact_angle": round(sep, 2), "within_orb": exact})

    # lots
    sun_l, moon_l = planets["Sun"]["longitude"], planets["Moon"]["longitude"]
    if is_day: fortune = norm(asc + moon_l - sun_l); spirit = norm(asc + sun_l - moon_l)
    else: fortune = norm(asc + sun_l - moon_l); spirit = norm(asc + moon_l - sun_l)
    lots = {}
    for nm, l in (("Fortune", fortune), ("Spirit", spirit)):
        lots[nm] = {"longitude": round(l, 4), "position": fmt(l), "house": house(l), "ruler": SIGN_RULER[sign_of(l)],
                    "formula": ("day: " if is_day else "night: ") + ("Asc + Moon - Sun" if (nm == "Fortune") == is_day else "Asc + Sun - Moon")}

    # profections
    asof = datetime.fromisoformat(args.asof).replace(tzinfo=timezone.utc) if args.asof else datetime.now(timezone.utc)
    bday = utc
    age = asof.year - bday.year - ((asof.month, asof.day, asof.hour, asof.minute) < (bday.month, bday.day, bday.hour, bday.minute))
    try: last_bd = bday.replace(year=bday.year + age)
    except ValueError: last_bd = bday.replace(year=bday.year + age, day=28)
    days_in = (asof - last_bd).total_seconds() / 86400
    month_idx = int(days_in // (365.2422 / 12))
    prof_sign = (asc_sign + age) % 12
    mprof_sign = (prof_sign + month_idx) % 12
    profections = {"as_of": asof.date().isoformat(), "age": age,
                   "annual": {"house": age % 12 + 1, "sign": SIGNS[prof_sign], "lord_of_the_year": SIGN_RULER[prof_sign],
                              "planets_in_that_sign": [n for n in names if sign_of(planets[n]["longitude"]) == prof_sign]},
                   "monthly": {"month_of_year": month_idx + 1, "house": (age + month_idx) % 12 + 1, "sign": SIGNS[mprof_sign],
                               "lord_of_the_month": SIGN_RULER[mprof_sign]},
                   "next_years": [{"age": a, "house": a % 12 + 1, "sign": SIGNS[(asc_sign + a) % 12], "lord": SIGN_RULER[(asc_sign + a) % 12]} for a in range(age, age + 6)]}

    # zodiacal releasing (360-day years, 30-day months per Valens)
    def zr(lot_lon, horizon_years=100):
        s0 = sign_of(lot_lon); start = utc
        def seq(S, total_days, unit_days):
            out, t, cnt, s = [], 0.0, 0, S
            while t < total_days - 1e-9:
                L = ZR_YEARS[s] * unit_days
                L2 = min(L, total_days - t)
                out.append((s, t, t + L2)); t += L2; cnt += 1
                s = (S + 6) % 12 if cnt == 12 else (s + 1) % 12   # loosing of the bond after a full circuit
            return out
        l1 = []; t = 0.0; s = s0
        while t / 360 < horizon_years:
            L = ZR_YEARS[s] * 360; l1.append((s, t, t + L)); t += L; s = (s + 1) % 12
        date = lambda days: (start + timedelta(days=days)).date().isoformat()
        asof_days = (asof - start).total_seconds() / 86400
        def angular(s): return ["Angular (peak)", None, None, "Angular (peak)", None, None, "Angular (peak)", None, None, "Angular (peak)", None, None][(s - s0) % 12]
        res = {"start_sign": SIGNS[s0], "level1": [], "current": {}}
        for s, a, b in l1:
            res["level1"].append({"sign": SIGNS[s], "ruler": SIGN_RULER[s], "from": date(a), "to": date(b), "years": ZR_YEARS[s],
                                  "age_from": round(a / 360, 1), "angular_from_lot": angular(s)})
        for s, a, b in l1:
            if a <= asof_days < b:
                cur = {"sign": SIGNS[s], "ruler": SIGN_RULER[s], "from": date(a), "to": date(b), "level2": []}
                for s2, a2, b2 in seq(s, b - a, 30):
                    row = {"sign": SIGNS[s2], "ruler": SIGN_RULER[s2], "from": date(a + a2), "to": date(a + b2), "angular_from_lot": angular(s2)}
                    if a + a2 <= asof_days < a + b2:
                        row["current"] = True
                        l3 = []
                        for s3, a3, b3 in seq(s2, b2 - a2, 2.5):
                            r3 = {"sign": SIGNS[s3], "ruler": SIGN_RULER[s3], "from": date(a + a2 + a3), "to": date(a + a2 + b3)}
                            if a + a2 + a3 <= asof_days < a + a2 + b3: r3["current"] = True
                            l3.append(r3)
                        row["level3"] = l3
                    cur["level2"].append(row)
                res["current"] = cur
                break
        return res

    zrel = {"from_Spirit": zr(spirit), "from_Fortune": zr(fortune),
            "note": "360-day years and 30-day months (Valens). Level 3 units are 2.5 days. After a full circuit of 12 signs, level 2 jumps to the sign opposite its start (loosing of the bond)."}

    # transits as of date
    jd_now = swe.julday(asof.year, asof.month, asof.day, asof.hour + asof.minute / 60)
    transits = {}
    for n, pid in PLANETS:
        p = planet_pos(jd_now, pid); l = p["lon"]
        conj = [m for m in names if abs((l - planets[m]["longitude"] + 180) % 360 - 180) <= 3]
        transits[n] = {"position": fmt(l), "natal_house": house(l), "retrograde": p["speed"] < 0, "conjunct_natal_within_3deg": conj}

    return {"name": args.name, "input": {"date": args.date, "time_local": args.time, "place": addr, "lat": lat, "lon": lon,
            "timezone": tzname, "utc_offset": (lambda m: f"{'+' if m >= 0 else '-'}{abs(m)//60:02d}:{abs(m)%60:02d}")(int(off.total_seconds() // 60)), "utc": utc.isoformat()},
            "warnings": warns,
            "angles": {"Ascendant": fmt(asc), "Midheaven": fmt(mc), "rising_sign": SIGNS[asc_sign]},
            "sect": sect_info, "planets": planets,
            "north_node_mean": fmt(nn["lon"]),
            "houses_whole_sign": [{"house": i + 1, "sign": SIGNS[(asc_sign + i) % 12], "ruler": SIGN_RULER[(asc_sign + i) % 12],
                                   "planets": [n for n in names if house(planets[n]["longitude"]) == i + 1]} for i in range(12)],
            "aspects": aspects, "lots": lots, "profections": profections, "zodiacal_releasing": zrel, "transits": transits}


def md(c):
    L = []; a = L.append
    i = c["input"]
    a(f"# Chart data: {c['name']}\n")
    a(f"Born {i['date']} {i['time_local']} local ({i['timezone']}, UTC{i['utc_offset']}), UTC {i['utc']}. {i['place']} ({i['lat']:.4f}, {i['lon']:.4f}).\n")
    for w in c["warnings"]: a(f"> **CHECK:** {w}\n")
    s = c["sect"]
    a(f"## 1. Sect\n**{s['chart'].title()} chart** (Sun altitude {s['sun_altitude']}°). Luminary of sect: {s['luminary_of_sect']}. Benefic of sect: {s['benefic_of_sect']}; other benefic: {s['other_benefic']}. Malefic of sect: {s['malefic_of_sect']}; malefic contrary to sect: {s['malefic_contrary_to_sect']}.\n")
    a(f"Ascendant {c['angles']['Ascendant']}; Midheaven {c['angles']['Midheaven']}; mean North Node {c['north_node_mean']}.\n")
    a("## 2. Condition\n| Planet | Position | House | Dignity | Bound | Sect | Beams / side of Sun | Motion |\n|---|---|---|---|---|---|---|---|")
    for n, p in c["planets"].items():
        beams = p.get("beams", "-"); side = p.get("side_of_sun", "")
        a(f"| {n} | {p['position']} | {p['house']} | {', '.join(p['dignity_by_sign'])} | {p['bound_ruler']} | {'in' if p['in_sect'] else 'out of'} sect ({p['sect_group'].split(' ')[0]}), {'above' if p['above_horizon'] else 'below'} horizon | {beams}; {side} | {'Rx' if p['retrograde'] else 'direct'} |")
    a("\n## 3. Aspects (whole-sign) \n| Pair | Relation | Exact angle |\n|---|---|---|")
    for x in c["aspects"]: a(f"| {x['a']} - {x['b']} | {x['sign_relation']} | {x['exact_angle']}° {('(' + x['within_orb'] + ')') if x['within_orb'] else ''} |")
    a("\n## 4. Houses (whole-sign)\n| House | Sign | Ruler | Planets |\n|---|---|---|---|")
    for h in c["houses_whole_sign"]: a(f"| {h['house']} | {h['sign']} | {h['ruler']} | {', '.join(h['planets']) or '-'} |")
    a("\n## 5. Lots")
    for n, l in c["lots"].items(): a(f"- **{n}**: {l['position']}, house {l['house']}, ruler {l['ruler']} ({l['formula']})")
    p = c["profections"]
    a(f"\n## 6. Timing (as of {p['as_of']})\n**Annual profection**, age {p['age']}: house {p['annual']['house']}, {p['annual']['sign']}; Lord of the Year **{p['annual']['lord_of_the_year']}**; planets there: {', '.join(p['annual']['planets_in_that_sign']) or 'none'}. **Monthly**: month {p['monthly']['month_of_year']}, house {p['monthly']['house']}, {p['monthly']['sign']}, lord {p['monthly']['lord_of_the_month']}.\n")
    a("| Age | House | Sign | Lord |\n|---|---|---|---|")
    for r in p["next_years"]: a(f"| {r['age']} | {r['house']} | {r['sign']} | {r['lord']} |")
    for key in ("from_Spirit", "from_Fortune"):
        z = c["zodiacal_releasing"][key]; cur = z["current"]
        a(f"\n### Zodiacal releasing {key.replace('_', ' ')} (starts {z['start_sign']})")
        a("| Level 1 sign | Ruler | From | To | Age from | Peak? |\n|---|---|---|---|---|---|")
        for r in z["level1"][:8]: a(f"| {r['sign']} | {r['ruler']} | {r['from']} | {r['to']} | {r['age_from']} | {r['angular_from_lot'] or ''} |")
        if cur:
            a(f"\nCurrent L1: **{cur['sign']}** ({cur['ruler']}) {cur['from']} to {cur['to']}.")
            a("| L2 sign | Ruler | From | To | Peak? | Now |\n|---|---|---|---|---|---|")
            for r in cur["level2"]: a(f"| {r['sign']} | {r['ruler']} | {r['from']} | {r['to']} | {r['angular_from_lot'] or ''} | {'<<' if r.get('current') else ''} |")
            for r in cur["level2"]:
                if r.get("current"):
                    a("\nCurrent L3 within the current L2: " + "; ".join(f"{x['sign']} {x['from']} to {x['to']}{' <<' if x.get('current') else ''}" for x in r["level3"]))
    a("\n### Transits (as of date), read inside the periods above\n| Planet | Position | Natal house | Motion | Conjunct natal (3°) |\n|---|---|---|---|---|")
    for n, t in c["transits"].items(): a(f"| {n} | {t['position']} | {t['natal_house']} | {'Rx' if t['retrograde'] else 'direct'} | {', '.join(t['conjunct_natal_within_3deg']) or '-'} |")
    a("\n_Zodiacal releasing uses 360-day years. Tropical zodiac, Moshier ephemeris._")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="Client"); ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM local, 24-hour, to the minute")
    ap.add_argument("--place"); ap.add_argument("--lat", type=float); ap.add_argument("--lon", type=float)
    ap.add_argument("--tz", help="IANA timezone override, e.g. America/Chicago")
    ap.add_argument("--asof", help="YYYY-MM-DD for timing/transits (default: today UTC)")
    ap.add_argument("--out", default="chart")
    args = ap.parse_args()
    c = chart(args)
    json.dump(c, open(args.out + ".json", "w"), indent=2, default=str)
    open(args.out + ".md", "w").write(md(c))
    print(f"Wrote {args.out}.json and {args.out}.md")
    for w in c["warnings"]: print("CHECK:", w)
