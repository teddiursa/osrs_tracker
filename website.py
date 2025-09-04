from flask import Flask, render_template_string
import requests
import json

app = Flask(__name__)

# Target XP for level 99 Runecrafting
XP_99 = 13034431
USERNAME = "gim_axolotl"
DEFAULT_XP_RATE = 14816  # XP per hour (from 8/28 1:39 PM PT → 9/2 12:01 AM PT, 92→94)

# XP table for OSRS levels 1–99 (+ level 100 to prevent index errors)
with open("level_xp.json", "r") as f:
    LEVEL_XP = json.load(f)

# Ensure LEVEL_XP has at least 100 levels
if len(LEVEL_XP) < 100:
    LEVEL_XP.append(14391160)  # XP for level 100 (virtual cap)

# Themed HTML template with commas and countdown
template = """[UNCHANGED HTML TEMPLATE YOU ALREADY HAVE]"""  # Keep your current template here

# Fetch XP from OSRS hiscores
def fetch_runecrafting_xp(username):
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={username}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    lines = response.text.split("\n")
    if len(lines) <= 21:
        return None
    rc_data = lines[21].split(",")
    return int(rc_data[2])

# Determine current level from XP
def get_current_level(xp):
    for level in range(1, len(LEVEL_XP)):
        if xp < LEVEL_XP[level]:
            return level
    return 99  # Cap at 99

# Format numbers with commas
def format_comma(value):
    if isinstance(value, int):
        return f"{value:,}"
    try:
        fval = float(value)
        return f"{fval:,.2f}"
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['format_comma'] = format_comma

# Main route
@app.route("/", methods=["GET"])
def index():
    xp = fetch_runecrafting_xp(USERNAME)
    remaining = percent = current_level = next_level = xp_to_next = next_percent = hours_left = days_left = None

    if xp is not None:
        remaining = max(0, XP_99 - xp)
        percent = min(100, round((xp / XP_99) * 100, 2))
        current_level = get_current_level(xp)
        next_level = min(99, current_level + 1)

        # Handle level progress bar correctly
        if current_level >= 99:
            xp_to_next = 0
            next_percent = 100.0
        else:
            current_index = current_level - 1
            next_index = next_level - 1
            xp_to_next = max(0, LEVEL_XP[next_index] - xp)
            level_start_xp = LEVEL_XP[current_index]
            level_end_xp = LEVEL_XP[next_index]
            if level_end_xp - level_start_xp > 0:
                next_percent = round(
                    ((xp - level_start_xp) / (level_end_xp - level_start_xp)) * 100, 2
                )
            else:
                next_percent = 100.0

        # Estimate time remaining
        if DEFAULT_XP_RATE > 0:
            hours_left = round(remaining / DEFAULT_XP_RATE, 2)
            days_left = round(hours_left / 24, 2)

    return render_template_string(template,
        username=USERNAME,
        xp=xp,
        remaining=remaining,
        percent=percent,
        current_level=current_level,
        next_level=next_level,
        xp_to_next=xp_to_next,
        next_percent=next_percent,
        xp_rate=DEFAULT_XP_RATE,
        hours_left=hours_left,
        days_left=days_left
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
