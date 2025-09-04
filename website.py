from flask import Flask, render_template_string
import requests
import json

app = Flask(__name__)

# Target XP for level 99 Runecrafting
XP_99 = 13034431
USERNAME = "gim_axolotl"
DEFAULT_XP_RATE = 14816  # XP per hour (estimated from 8/28 1:39 PM PT → 9/2 12:01 AM PT, 92→94)

# XP table for OSRS levels 1–99
with open("level_xp.json", "r") as f:
    LEVEL_XP = json.load(f)

# Themed HTML template with commas and countdown
template = """
<!DOCTYPE html>
<html>
<head>
    <title>How Close GIM_Axolotl is to Maxing Runecrafting</title>
    <style>
        body { background: #121212 url('https://oldschool.runescape.wiki/images/thumb/Astral_altar.png/640px-Astral_altar.png') no-repeat center top fixed; background-size: cover; color: #f5f5f5; font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; }
        .overlay { background: rgba(0, 0, 0, 0.7); min-height: 100vh; padding: 40px; }
        h1 { font-size: 3.5em; margin-bottom: 10px; color: #ffd700; text-shadow: 2px 2px 5px black; }
        h2 { font-size: 2.2em; margin-top: 30px; color: #87cefa; text-shadow: 1px 1px 3px black; }
        p { font-size: 1.5em; margin: 10px 0; }
        .progress-container { width: 80%; margin: 30px auto; background: #333; border-radius: 15px; overflow: hidden; height: 55px; box-shadow: 0 0 10px #000; }
        .progress-bar { height: 55px; background: linear-gradient(to right, #00ff99, #4caf50); text-align: center; color: black; font-size: 1.5em; font-weight: bold; line-height: 55px; }
        img.skill-icon { width: 72px; height: 72px; vertical-align: middle; margin-right: 10px; }
        img.cape-icon { width: 100px; height: 100px; margin-top: 20px; }
        .highlight { color: #00ffcc; font-weight: bold; }
    </style>
</head>
<body>
<div class="overlay">
    <h1>How Close Vinny is to Maxing Runecrafting</h1>
    <h2><img src="https://oldschool.runescape.wiki/images/Runecraft_icon.png" class="skill-icon"> Tracking {{ username }}</h2>

    {% if xp is not none %}
        <p>Vinny currently has <span class="highlight">{{ xp | format_comma }}</span> Runecrafting XP.</p>
        <p>He needs <span class="highlight">{{ remaining | format_comma }}</span> XP to reach <span class="highlight">99 Runecrafting</span>.</p>

        <div class="progress-container">
            <div class="progress-bar" style="width: {{ percent }}%">{{ percent }}%</div>
        </div>

        <h2>Next Level Progress</h2>
        <p>Current Level: <span class="highlight">{{ current_level }}</span></p>
        <p>XP to Next Level ({{ next_level }}): <span class="highlight">{{ xp_to_next | format_comma }}</span></p>

        <div class="progress-container">
            <div class="progress-bar" style="width: {{ next_percent }}%">{{ next_percent }}%</div>
        </div>

        <h2>Countdown Estimate</h2>
        <p>Based on recent gains (<span class="highlight">92 → 94</span> from <span class="highlight">Aug 28, 2025 1:39 PM PT</span> to <span class="highlight">Sep 2, 2025 12:01 AM PT</span>), Vinny averaged <span class="highlight">{{ xp_rate | format_comma }}</span> XP/hour.</p>
        <p>At that pace, maxing 99 Runecrafting will take about <span class="highlight">{{ hours_left | format_comma }}</span> hours (~<span class="highlight">{{ days_left | format_comma }}</span> days).</p>

        {% if current_level == 99 %}
            <h2>🎉 Congratulations, Vinny! 🎉</h2>
            <img src="https://oldschool.runescape.wiki/images/Runecraft_cape_(t)_icon.png" class="cape-icon">
            <p>You’ve achieved the <span class="highlight">99 Runecrafting</span> milestone!</p>
        {% endif %}
    {% else %}
        <p>Could not fetch data for {{ username }}.</p>
    {% endif %}
</div>
</body>
</html>
"""
# Fetch XP from OSRS hiscores
def fetch_runecrafting_xp(username):
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={username}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    lines = response.text.split("\n")
    if len(lines) < 21:
        return None
    rc_data = lines[21].split(",") 
    return int(rc_data[2])

# Determine current level
def get_current_level(xp):
    if xp < LEVEL_XP[1]:
        return 1
    for level in range(1, len(LEVEL_XP)):
        if xp < LEVEL_XP[level]:
            return level
    return 99

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
        if next_level >= len(LEVEL_XP):
            xp_to_next = 0
            next_percent = 100.0
        else:
            xp_to_next = max(0, LEVEL_XP[next_level] - xp)
            next_percent = round(((xp - LEVEL_XP[current_level]) / (LEVEL_XP[next_level] - LEVEL_XP[current_level])) * 100, 2)
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
