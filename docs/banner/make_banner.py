"""Draw the banner of the technical-writing skill: an AI teacher explains a lesson on a blackboard to a lecture hall of
students who take notes. Run this script to write banner.svg beside it. The drawing is self-contained, because it embeds
the two fonts from fonts/. Then run render_png.py to make banner.png, the picture that the README shows.

The drawing is deterministic: the same code always writes the same bytes. Every random choice (the students' looks, the
chalk dust, the sparks) comes from a seeded generator."""
import base64
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
W, H = 1280, 640
rng = random.Random(11)


def font_face(name, file):
    data = base64.b64encode((HERE / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data}) format('truetype');}}"


def shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    clamp = lambda v: max(0, min(255, int(v)))
    return f"#{clamp(r * f):02x}{clamp(g * f):02x}{clamp(b * f):02x}"


def star(cx, cy, s, fill="#ffe27a", opacity=1.0, glow=True):
    pts = [(0, -1), (0.26, -0.26), (1, 0), (0.26, 0.26), (0, 1), (-0.26, 0.26), (-1, 0), (-0.26, -0.26)]
    d = "M" + " L".join(f"{cx + s * px:.1f},{cy + s * py:.1f}" for px, py in pts) + " Z"
    glow_attribute = ' filter="url(#glow)"' if glow else ""      # outside the f-string: Python 3.9 forbids a backslash inside one
    return f'<path d="{d}" fill="{fill}" opacity="{opacity}"{glow_attribute}/>'


# ---------------------------------------------------------------- students
SKINS = ["#f6d3b3", "#e8b48c", "#cf9569", "#b27a52", "#8a5a3a", "#6b4129"]
HAIRS = ["#2a2018", "#40281a", "#6b3f22", "#a85d1f", "#d8b26a", "#1e2233", "#c2456f", "#3d6fd6", "#8d8d96"]
SHIRTS = ["#ff7a7a", "#ffb04a", "#ffd24d", "#6fd18a", "#5ac2ff", "#7d8cff", "#c58bff", "#ff8cc6", "#4fd0d9", "#f29b5b",
          "#9ad9ae", "#ff9f80"]
STYLES = ["short", "long", "bun", "pony", "curly", "short", "long", "curly"]
HEADS = []                                  # (x, head y, radius, pose) of every student, filled by student(); place_sparks() reads it


def desk(x, y, r):
    pts = f"{x - 2.7 * r:.1f},{y - 1.6 * r:.1f} {x + 2.7 * r:.1f},{y - 1.6 * r:.1f} {x + 3.1 * r:.1f},{y + 1.45 * r:.1f} {x - 3.1 * r:.1f},{y + 1.45 * r:.1f}"
    return (f'<polygon points="{pts}" fill="url(#desk)" stroke="#c9a06a" stroke-width="{0.05 * r:.2f}"/>'
            f'<line x1="{x - 2.7 * r:.1f}" y1="{y - 1.6 * r:.1f}" x2="{x + 2.7 * r:.1f}" y2="{y - 1.6 * r:.1f}" stroke="#fff3dd" stroke-width="{0.08 * r:.2f}" opacity=".7"/>')


def notebook(cx, cy, r, tilt, scribble):
    w, h = 2.0 * r, 1.35 * r
    g = [f'<g transform="rotate({tilt:.1f} {cx:.1f} {cy:.1f})">',
         f'<rect x="{cx - w / 2 + 0.07 * r:.1f}" y="{cy - h / 2 + 0.09 * r:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{0.08 * r:.1f}" fill="#000" opacity=".12"/>',
         f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{0.08 * r:.1f}" fill="#fffdf7" stroke="#ddd6c8" stroke-width="{0.04 * r:.2f}"/>',
         f'<line x1="{cx - w / 2 + 0.28 * r:.1f}" y1="{cy - h / 2:.1f}" x2="{cx - w / 2 + 0.28 * r:.1f}" y2="{cy + h / 2:.1f}" stroke="#f0a0a0" stroke-width="{0.04 * r:.2f}"/>']
    for k in range(1, 5):
        yy = cy - h / 2 + k * h / 5
        g.append(f'<line x1="{cx - w / 2 + 0.12 * r:.1f}" y1="{yy:.1f}" x2="{cx + w / 2 - 0.12 * r:.1f}" y2="{yy:.1f}" stroke="#bcd3f2" stroke-width="{0.035 * r:.2f}"/>')
    if scribble:
        for k in range(1, 4):
            yy = cy - h / 2 + k * h / 5 - 0.07 * r
            n = rng.randint(5, 9)
            path = f"M{cx - w / 2 + 0.38 * r:.1f},{yy:.1f}"
            for j in range(n):
                path += f" q{0.09 * r:.1f},{-0.14 * r:.1f} {0.18 * r:.1f},0"
            g.append(f'<path d="{path}" fill="none" stroke="#4c5d86" stroke-width="{0.05 * r:.2f}" stroke-linecap="round" opacity=".85"/>')
    g.append("</g>")
    return "".join(g)


def student(x, y, r, pose):
    skin, hair, shirt, style = rng.choice(SKINS), rng.choice(HAIRS), rng.choice(SHIRTS), rng.choice(STYLES)
    side = rng.choice([-1, 1])
    dy = {"write": 0.12 * r, "look": -0.12 * r, "hand": -0.05 * r}[pose]
    tilt = {"write": rng.uniform(3, 7) * side, "look": rng.uniform(-4, 4), "hand": rng.uniform(-3, 3)}[pose]
    hy = y + dy
    g = [desk(x, y, r)]
    ncx, ncy = x + side * 1.75 * r, y - 0.35 * r                      # notebook centre
    g.append(notebook(ncx, ncy, r, rng.uniform(-7, 7), pose == "write"))
    sh = shade(shirt, 0.86)
    # arms: one rests or writes at the notebook, the other rests on the desk or is raised
    hand_w = (ncx + side * 0.15 * r, ncy + 0.3 * r)
    hand_o = (x - side * 1.45 * r, y + 0.05 * r)
    arm = lambda p, q, col=shirt: (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{col}" '
                                   f'stroke-width="{0.95 * r:.1f}" stroke-linecap="round"/>')
    handc = lambda q: f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{0.38 * r:.1f}" fill="{skin}"/>'
    g.append(arm((x + side * 2.2 * r, y + 1.9 * r), hand_w))
    if pose == "hand":
        top = (x - side * 2.7 * r, y - 2.3 * r)
        g.append(arm((x - side * 2.2 * r, y + 1.9 * r), top))
        g.append(f'<ellipse cx="{top[0]:.1f}" cy="{top[1] - 0.2 * r:.1f}" rx="{0.46 * r:.1f}" ry="{0.58 * r:.1f}" fill="{skin}"/>')
    else:
        g.append(arm((x - side * 2.2 * r, y + 1.9 * r), hand_o))
        g.append(handc(hand_o))
    g.append(handc(hand_w))
    if pose == "write":                                                # the pencil
        tip = (ncx - side * 0.35 * r, ncy - 0.05 * r)
        g.append(f'<line x1="{hand_w[0]:.1f}" y1="{hand_w[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" stroke="#ffd23f" stroke-width="{0.2 * r:.1f}" stroke-linecap="round"/>'
                 f'<circle cx="{tip[0]:.1f}" cy="{tip[1]:.1f}" r="{0.09 * r:.1f}" fill="#4a3a2a"/>')
    # torso: shoulders and back
    t = (f"M{x - 2.7 * r:.1f},{y + 5.5 * r:.1f} L{x - 2.7 * r:.1f},{y + 2.7 * r:.1f} Q{x - 2.7 * r:.1f},{y + 1.75 * r:.1f} {x - 1.6 * r:.1f},{y + 1.55 * r:.1f} "
         f"L{x + 1.6 * r:.1f},{y + 1.55 * r:.1f} Q{x + 2.7 * r:.1f},{y + 1.75 * r:.1f} {x + 2.7 * r:.1f},{y + 2.7 * r:.1f} L{x + 2.7 * r:.1f},{y + 5.5 * r:.1f} Z")
    g.append(f'<path d="{t}" fill="{shirt}"/>')
    g.append(f'<path d="M{x:.1f},{y + 1.7 * r:.1f} L{x:.1f},{y + 5.5 * r:.1f}" stroke="{sh}" stroke-width="{0.1 * r:.1f}" opacity=".35"/>')
    g.append(f'<path d="M{x - 1.0 * r:.1f},{y + 1.55 * r:.1f} Q{x:.1f},{y + 2.15 * r:.1f} {x + 1.0 * r:.1f},{y + 1.55 * r:.1f}" fill="none" stroke="{sh}" stroke-width="{0.14 * r:.1f}" stroke-linecap="round"/>')
    # neck, head, hair (rotated together)
    g.append(f'<g transform="rotate({tilt:.1f} {x:.1f} {y + 1.2 * r:.1f})">')
    g.append(f'<rect x="{x - 0.5 * r:.1f}" y="{hy + 0.6 * r:.1f}" width="{1.0 * r:.1f}" height="{1.2 * r:.1f}" fill="{shade(skin, 0.9)}"/>')
    g.append(f'<ellipse cx="{x - 1.0 * r:.1f}" cy="{hy + 0.1 * r:.1f}" rx="{0.24 * r:.1f}" ry="{0.34 * r:.1f}" fill="{skin}"/>')
    g.append(f'<ellipse cx="{x + 1.0 * r:.1f}" cy="{hy + 0.1 * r:.1f}" rx="{0.24 * r:.1f}" ry="{0.34 * r:.1f}" fill="{skin}"/>')
    g.append(f'<ellipse cx="{x:.1f}" cy="{hy:.1f}" rx="{1.02 * r:.1f}" ry="{1.1 * r:.1f}" fill="{skin}"/>')
    hc = hair
    if style == "long":
        g.append(f'<path d="M{x - 1.12 * r:.1f},{hy - 0.1 * r:.1f} Q{x - 1.5 * r:.1f},{hy + 2.0 * r:.1f} {x - 1.2 * r:.1f},{hy + 2.4 * r:.1f} L{x + 1.2 * r:.1f},{hy + 2.4 * r:.1f} Q{x + 1.5 * r:.1f},{hy + 2.0 * r:.1f} {x + 1.12 * r:.1f},{hy - 0.1 * r:.1f} Z" fill="{hc}"/>')
    if style == "pony":
        g.append(f'<ellipse cx="{x + 0.1 * r:.1f}" cy="{hy + 1.25 * r:.1f}" rx="{0.34 * r:.1f}" ry="{0.95 * r:.1f}" fill="{hc}"/>'
                 f'<circle cx="{x + 0.1 * r:.1f}" cy="{hy + 0.45 * r:.1f}" r="{0.2 * r:.1f}" fill="#ff6b8b"/>')
    g.append(f'<ellipse cx="{x:.1f}" cy="{hy - 0.14 * r:.1f}" rx="{1.08 * r:.1f}" ry="{1.03 * r:.1f}" fill="{hc}"/>')
    if style == "bun":
        g.append(f'<circle cx="{x:.1f}" cy="{hy - 1.25 * r:.1f}" r="{0.55 * r:.1f}" fill="{hc}"/>')
    if style == "curly":
        for k in range(9):
            a = math.pi * (1.05 + 0.9 * k / 8)
            g.append(f'<circle cx="{x + 1.08 * r * math.cos(a):.1f}" cy="{hy - 0.1 * r + 1.08 * r * math.sin(a):.1f}" r="{0.46 * r:.1f}" fill="{hc}"/>')
    g.append(f'<path d="M{x - 0.6 * r:.1f},{hy - 0.55 * r:.1f} Q{x:.1f},{hy - 1.0 * r:.1f} {x + 0.6 * r:.1f},{hy - 0.55 * r:.1f}" fill="none" stroke="{shade(hc, 1.25)}" stroke-width="{0.12 * r:.1f}" stroke-linecap="round" opacity=".5"/>')
    g.append("</g>")
    if pose == "look":
        rng.random()                       # the value is unused; the call keeps the random stream, and so every student's look, as it was
    HEADS.append((x, hy, r, pose))
    return "".join(g)


def rows():
    HEADS.clear()
    out = []
    spec = [(462, 15, 12, 62, 104), (528, 21, 9, 100, 140), (600, 29, 6, 86, 196)]    # head y, radius, count, first x, step
    for yb, r, n, x0, step in spec:
        for i in range(n):
            x = x0 + i * step + rng.uniform(-6, 6)
            if abs(x - 1040) < 40 and yb == 462:                        # keep the teacher's feet in view
                x += 70
            p = rng.random()
            pose = "write" if p < 0.58 else "look" if p < 0.86 else "hand"
            out.append(student(x, yb + rng.uniform(-3, 3), r, pose))
    return "".join(out)


def spark(cx, cy, s):
    """A bright four-point sparkle with a dark amber outline, so it shows on the cream wall and on the wooden floor."""
    def burst(px, py, k, w):
        pts = [(0, -1), (0.36, -0.36), (1, 0), (0.36, 0.36), (0, 1), (-0.36, 0.36), (-1, 0), (-0.36, -0.36)]
        d = "M" + " L".join(f"{px + k * a:.1f},{py + k * b:.1f}" for a, b in pts) + " Z"
        return f'<path d="{d}" fill="#ffd21f" stroke="#c46a00" stroke-width="{w:.1f}" stroke-linejoin="round"/>'
    g = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{1.9 * s:.1f}" fill="url(#sparkhalo)"/>']
    for a in (-135, -45, 45, 135):                                       # short rays between the four points
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        g.append(f'<line x1="{cx + 1.15 * s * ca:.1f}" y1="{cy + 1.15 * s * sa:.1f}" x2="{cx + 1.6 * s * ca:.1f}" y2="{cy + 1.6 * s * sa:.1f}" '
                 f'stroke="#ff9a1f" stroke-width="{max(2.0, 0.13 * s):.1f}" stroke-linecap="round"/>')
    g.append(burst(cx, cy, s, max(1.6, 0.1 * s)))
    g.append(burst(cx + 1.5 * s, cy + 0.9 * s, 0.4 * s, max(1.2, 0.07 * s)))
    g.append(burst(cx - 1.4 * s, cy + 0.8 * s, 0.28 * s, max(1.0, 0.06 * s)))
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{0.17 * s:.1f}" fill="#fffbe0"/>')
    return "".join(g)


def place_sparks():
    """Choose where the sparks of understanding go: above some students' heads, spread along each row.
    Row radius -> the x positions where a spark is wanted; the nearest student whose spot is free gets it."""
    srng = random.Random(23)                # its own random stream: the students keep the look they had
    slots = {15: (150, 400, 650, 900), 21: (220, 520, 820), 29: (290, 680, 1060)}
    size = {15: 16, 21: 19, 29: 23}         # a spark's radius per row: farther rows are smaller
    placed = []
    for r, xs in slots.items():
        s = size[r]
        for tx in xs:
            near = sorted((h for h in HEADS if h[2] == r and h[3] != "hand"), key=lambda h: abs(h[0] - tx))
            done = False
            for x, hy, rr, _pose in near[:4]:
                for side in srng.sample((-1, 1), 2):
                    cx, cy = x + side * 0.7 * rr, hy - 1.8 * rr - s - 0.2 * rr
                    clear_of_heads = all(math.hypot(cx - hx, cy - hy2) > 0.8 * s + 0.85 * r2 for hx, hy2, r2, _ in HEADS)
                    clear_of_sparks = all(math.hypot(cx - px, cy - py) > 1.5 * (s + ps) for px, py, ps in placed)
                    in_the_way = (abs(cx - 1040) < 90 and cy < 470) or (cx > 1170 and cy < 480)       # the teacher's legs, the plant
                    if clear_of_heads and clear_of_sparks and not in_the_way:
                        placed.append((cx, cy, s))
                        done = True
                        break
                if done:
                    break
    if not placed:                          # fail loudly: a picture without its sparks is a silent miss
        raise RuntimeError("No spark could be placed. Draw the students with rows() first, or leave room above their heads.")
    return placed


def sparks():
    """The sparks, drawn after every student so that no head or desk covers one."""
    return "".join(spark(cx, cy, s) for cx, cy, s in place_sparks())


# ---------------------------------------------------------------- board
def board():
    g = []
    g.append('<rect x="124" y="40" width="742" height="302" rx="12" fill="url(#wood)"/>')
    g.append('<rect x="124" y="40" width="742" height="302" rx="12" fill="none" stroke="#e7c598" stroke-width="2" opacity=".5"/>')
    g.append('<rect x="142" y="58" width="706" height="266" rx="6" fill="url(#board)" stroke="#143430" stroke-width="3"/>')
    for cx, cy, rx, ry, o in [(300, 150, 150, 36, .05), (640, 230, 190, 44, .045), (470, 270, 230, 30, .04), (760, 110, 90, 24, .05)]:
        g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#fff" opacity="{o}" transform="rotate(-8 {cx} {cy})"/>')
    g.append('<rect x="134" y="334" width="722" height="13" rx="5" fill="#7e532c"/><rect x="134" y="334" width="722" height="4" rx="2" fill="#a97a46"/>')
    for x, c, rot in [(200, "#ffffff", -8), (226, "#ffe08a", 4), (252, "#ffb3c7", -3)]:
        g.append(f'<rect x="{x}" y="326" width="22" height="9" rx="3" fill="{c}" transform="rotate({rot} {x + 11} 330)"/>')
    g.append('<rect x="760" y="324" width="56" height="12" rx="3" fill="#6b4a2b"/><rect x="760" y="324" width="56" height="5" rx="2" fill="#e8d9b0"/>')
    chalk = ['<g filter="url(#chalk)" stroke-linecap="round" stroke-linejoin="round">']
    chalk.append('<text x="168" y="112" font-family="Caveat Brush" font-size="45" fill="#fffbe9">Explain in simple language</text>')
    chalk.append('<path d="M170,124 q22,-9 44,0' + ' t44,0' * 8 + '" fill="none" stroke="#ffe08a" stroke-width="3.5"/>')    # the underline: nine waves
    items = [("1", "Use plain English", "#a8d8ff"), ("2", "Give one example", "#ffe08a"),
             ("3", "Explain every technical term", "#ffb3c7"), ("4", "Show next steps one at a time", "#b6f0c2")]
    for k, (n, label, col) in enumerate(items):
        y = 172 + k * 41
        chalk.append(f'<circle cx="190" cy="{y - 9}" r="15" fill="none" stroke="{col}" stroke-width="3"/>')
        chalk.append(f'<text x="190" y="{y - 1}" text-anchor="middle" font-family="Patrick Hand" font-size="23" fill="{col}">{n}</text>')
        chalk.append(f'<text x="219" y="{y}" font-family="Patrick Hand" font-size="31" fill="#fffbe9">{label}</text>')
    # a light bulb
    bx, by = 668, 146
    chalk.append(f'<circle cx="{bx}" cy="{by}" r="34" fill="#ffe08a" opacity=".16"/>')
    chalk.append(f'<path d="M{bx - 20},{by + 22} Q{bx - 38},{by - 4} {bx - 30},{by - 22} Q{bx},{by - 52} {bx + 30},{by - 22} Q{bx + 38},{by - 4} {bx + 20},{by + 22} Z" fill="none" stroke="#ffe08a" stroke-width="4"/>')
    chalk.append(f'<path d="M{bx - 15},{by + 34} h30 M{bx - 11},{by + 45} h22" stroke="#fffbe9" stroke-width="4"/>')
    chalk.append(f'<path d="M{bx - 9},{by + 22} q-6,-14 4,-18 t10,-6 t-2,10 t4,14" fill="none" stroke="#ffe08a" stroke-width="2.5"/>')
    for a in range(-150, 31, 30):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        chalk.append(f'<line x1="{bx + 48 * ca:.1f}" y1="{by - 6 + 48 * sa:.1f}" x2="{bx + 62 * ca:.1f}" y2="{by - 6 + 62 * sa:.1f}" stroke="#ffe08a" stroke-width="3.5"/>')
    # a before-and-after bar chart: the vertical axis says what the bars measure, the numbers say how much
    chalk.append('<path d="M602,282 H826 M602,282 V164 M602,164 l-5,10 M602,164 l5,10" stroke="#fffbe9" stroke-width="3.5" fill="none"/>')
    chalk.append('<text transform="translate(588,223) rotate(-90)" text-anchor="middle" font-family="Patrick Hand" font-size="24" fill="#fffbe9">GROK index</text>')
    chalk.append('<rect x="622" y="236" width="56" height="46" fill="#a8d8ff" fill-opacity=".28" stroke="#a8d8ff" stroke-width="3"/>')
    chalk.append('<rect x="742" y="198" width="56" height="84" fill="#ffe08a" fill-opacity=".28" stroke="#ffe08a" stroke-width="3"/>')
    chalk.append('<text x="650" y="226" text-anchor="middle" font-family="Patrick Hand" font-size="27" fill="#a8d8ff">0.41</text>')
    chalk.append('<text x="770" y="188" text-anchor="middle" font-family="Patrick Hand" font-size="27" fill="#ffe08a">0.50</text>')
    chalk.append('<path d="M686,222 q26,-30 48,-24 M734,198 l-12,-3 M734,198 l-4,12" fill="none" stroke="#fffbe9" stroke-width="3"/>')
    chalk.append('<text x="650" y="308" text-anchor="middle" font-family="Patrick Hand" font-size="22" fill="#fffbe9">before</text>')
    chalk.append('<text x="770" y="308" text-anchor="middle" font-family="Patrick Hand" font-size="22" fill="#fffbe9">after</text>')
    chalk.append("</g>")
    g.extend(chalk)
    return "".join(g)


# ---------------------------------------------------------------- the AI teacher
def hair_back():
    """The hair behind the head: a wavy mass that falls to the shoulders."""
    mass = ("M1040,97 C1086,97 1126,122 1130,168 C1133,204 1124,224 1132,248 C1136,262 1116,266 1102,256 "
            "C1094,250 1086,240 1070,236 L1010,236 C994,240 986,250 978,256 C964,266 944,262 948,248 "
            "C956,224 946,204 950,168 C954,122 994,97 1040,97 Z")
    return (f'<path d="{mass}" fill="url(#hairBack)"/>'
            '<path d="M1121,150 C1127,188 1117,212 1124,242" fill="none" stroke="#b5562b" stroke-width="3" stroke-linecap="round" opacity=".45"/>'
            '<path d="M959,150 C953,188 963,212 956,242" fill="none" stroke="#b5562b" stroke-width="3" stroke-linecap="round" opacity=".45"/>')


def hair_front():
    """A side-parted fringe and two locks that frame the face, with strand lines and a glossy highlight."""
    # Both shapes start at the part, (1010,102). The right one carries the fringe: its lower edge runs from the part down to
    # a tip at the right temple, (1094,166). It averages about 35 degrees from horizontal and steepens toward the tip,
    # so it stays well above the right eye (which tops out near y=150).
    left = ("M1010,102 C988,102 966,118 966,150 C966,178 972,204 962,230 C958,246 966,258 980,256 "
            "C990,248 992,230 990,206 C988,184 986,160 992,144 C996,134 998,128 1000,124 C1002,116 1006,108 1010,102 Z")
    right = ("M1010,102 C1040,90 1096,94 1112,140 C1118,166 1112,196 1120,226 C1124,244 1116,256 1100,254 "
             "C1090,246 1090,228 1090,206 C1090,186 1092,178 1094,166 "
             "C1070,128 1036,114 1010,106 Z")
    g = [f'<path d="{right}" transform="translate(0,3)" fill="#000" opacity=".18" filter="url(#soft)"/>',      # the fringe's shadow on the face
         f'<path d="{left}" fill="url(#hairFront)"/>', f'<path d="{right}" fill="url(#hairFront)"/>']
    strands = [("M984,150 C984,180 988,206 978,238", "#f2a86b", .5), ("M975,160 C975,186 979,208 971,232", "#3d170d", .35),
               ("M1104,150 C1106,180 1102,206 1110,236", "#f2a86b", .5), ("M1112,160 C1112,188 1108,210 1114,232", "#3d170d", .35),
               ("M1016,104 C1040,106 1064,118 1084,146", "#f2a86b", .55), ("M1018,108 C1040,102 1074,104 1100,142", "#3d170d", .32),
               ("M1022,106 C1038,110 1058,121 1076,138", "#f2a86b", .4)]                                    # the last three follow the sweep
    for d, col, o in strands:
        g.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2" stroke-linecap="round" opacity="{o}"/>')
    g.append('<path d="M1018,106 C1044,108 1068,120 1088,148" fill="none" stroke="#ffd9ae" stroke-width="5" stroke-linecap="round" opacity=".5" filter="url(#soft)"/>')
    g.append('<path d="M1004,114 C1034,98 1078,100 1102,126" fill="none" stroke="#ffd9ae" stroke-width="5" stroke-linecap="round" opacity=".5" filter="url(#soft)"/>')
    for d in ("M979,162 C977,188 981,208 973,230", "M1111,164 C1113,190 1109,212 1115,232"):                # gloss on the side locks
        g.append(f'<path d="{d}" fill="none" stroke="#ffd9ae" stroke-width="4" stroke-linecap="round" opacity=".38" filter="url(#soft)"/>')
    return "".join(g)


def scarf():
    """A coral silk scarf knotted at the neck, with two short tails and white dots. It replaces the bow tie."""
    g = ['<path d="M1010,241 Q1040,228 1070,241 Q1075,255 1061,259 Q1040,251 1019,259 Q1005,255 1010,241 Z" fill="url(#scarf)"/>',
         '<path d="M1038,262 C1046,274 1053,287 1059,300 Q1051,308 1042,301 C1040,289 1036,277 1033,266 Z" fill="#e9567f"/>',      # the tail underneath
         '<path d="M1029,262 C1023,276 1019,291 1017,307 Q1027,314 1035,305 C1035,292 1037,278 1041,265 Z" fill="url(#scarf)"/>',
         '<ellipse cx="1034" cy="257" rx="9.5" ry="8" fill="#f0648f"/>',
         '<path d="M1028,254 Q1034,249 1041,253" fill="none" stroke="#ffd0dd" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>',
         '<path d="M1024,262 C1021,278 1021,292 1022,304" fill="none" stroke="#d94577" stroke-width="1.6" stroke-linecap="round" opacity=".35"/>']
    for x, y in [(1022, 247), (1032, 243), (1048, 243), (1058, 247), (1027, 285), (1024, 298), (1045, 284), (1050, 294)]:
        g.append(f'<circle cx="{x}" cy="{y}" r="1.7" fill="#fff" opacity=".85"/>')
    return "".join(g)


def antenna():
    """A short antenna with a glowing bulb that rises from the crown of the hair."""
    g = ['<line x1="1040" y1="97" x2="1040" y2="88" stroke="#4aa3ff" stroke-width="4" stroke-linecap="round"/>',
         '<circle cx="1040" cy="83" r="11" fill="#ffd166" opacity=".5" filter="url(#glow)"/><circle cx="1040" cy="83" r="6.5" fill="#ffd166"/>']
    for a in range(0, 360, 60):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        g.append(f'<line x1="{1040 + 10 * ca:.1f}" y1="{83 + 10 * sa:.1f}" x2="{1040 + 14 * ca:.1f}" y2="{83 + 14 * sa:.1f}" stroke="#ffd166" stroke-width="2.2" stroke-linecap="round"/>')
    return "".join(g)


def agent():
    g = ['<ellipse cx="1040" cy="270" rx="190" ry="230" fill="url(#aura)"/>', '<ellipse cx="1040" cy="458" rx="78" ry="9" fill="#000" opacity=".2"/>']
    g.append('<rect x="1008" y="404" width="25" height="46" rx="11" fill="#2b3a55"/><rect x="1048" y="404" width="25" height="46" rx="11" fill="#2b3a55"/>')
    g.append('<ellipse cx="1017" cy="454" rx="22" ry="10" fill="#1c2638"/><ellipse cx="1063" cy="454" rx="22" ry="10" fill="#1c2638"/>')
    g.append('<ellipse cx="1011" cy="450" rx="9" ry="3" fill="#fff" opacity=".18"/><ellipse cx="1057" cy="450" rx="9" ry="3" fill="#fff" opacity=".18"/>')
    # relaxed arm holding a little book
    g.append('<line x1="1090" y1="262" x2="1113" y2="332" stroke="url(#cardigan)" stroke-width="25" stroke-linecap="round"/>')
    g.append('<line x1="1113" y1="332" x2="1100" y2="378" stroke="#1580f0" stroke-width="19" stroke-linecap="round"/>')
    g.append('<rect x="1084" y="366" width="34" height="44" rx="5" fill="#ff9f43" transform="rotate(-8 1101 388)"/><rect x="1088" y="370" width="6" height="36" fill="#e17f1e" transform="rotate(-8 1101 388)"/>')
    g.append('<circle cx="1099" cy="380" r="11" fill="#1580f0"/>')
    # torso: cardigan, shirt, bow tie
    g.append('<path d="M986,262 Q986,242 1006,240 L1074,240 Q1094,242 1094,262 L1102,396 Q1103,410 1089,410 L991,410 Q977,410 978,396 Z" fill="url(#cardigan)"/>')
    g.append('<path d="M1018,240 L1062,240 L1040,300 Z" fill="#ffffff"/>')
    g.append('<path d="M1040,300 L1040,410" stroke="#17756c" stroke-width="2.5"/>')
    for yy in (330, 356, 382):
        g.append(f'<circle cx="1040" cy="{yy}" r="3.6" fill="#17756c"/>')
    g.append('<rect x="1060" y="356" width="26" height="22" rx="5" fill="none" stroke="#17756c" stroke-width="2.5"/>')
    # back hair, neck, scarf and head
    g.append(hair_back())
    g.append('<rect x="1030" y="212" width="20" height="30" fill="#0a63c8"/>')
    g.append(scarf())
    g.append('<rect x="976" y="112" width="128" height="106" rx="44" fill="url(#skin)" stroke="#0a50a8" stroke-width="2"/>')
    g.append('<ellipse cx="1004" cy="128" rx="22" ry="8" fill="#cfe6ff" opacity=".55" transform="rotate(-20 1004 128)"/>')
    g.append('<rect x="988" y="124" width="104" height="82" rx="33" fill="url(#skin)"/>')
    g.append('<rect x="988" y="124" width="104" height="82" rx="33" fill="none" stroke="#0a50a8" stroke-width="2" opacity=".25"/>')
    g.append('<path d="M1003,164 Q1015,145 1027,164 M1053,164 Q1065,145 1077,164" fill="none" stroke="#f4fcff" stroke-width="7" stroke-linecap="round" filter="url(#glow)"/>')
    g.append('<path d="M1023,181 Q1040,198 1057,181" fill="none" stroke="#f4fcff" stroke-width="6" stroke-linecap="round" filter="url(#glow)"/>')
    g.append('<circle cx="1002" cy="184" r="7.5" fill="#ff9fbd" opacity=".92"/><circle cx="1078" cy="184" r="7.5" fill="#ff9fbd" opacity=".92"/>')
    g.append('<polygon points="1000,128 1034,128 1004,204 988,204 988,160" fill="#fff" opacity=".1"/>')
    g.append(hair_front())
    g.append(antenna())
    # pointing arm and pointer
    g.append('<line x1="992" y1="262" x2="944" y2="290" stroke="url(#cardigan)" stroke-width="25" stroke-linecap="round"/>')
    g.append('<line x1="944" y1="290" x2="900" y2="262" stroke="#1580f0" stroke-width="19" stroke-linecap="round"/>')
    g.append('<line x1="898" y1="260" x2="772" y2="208" stroke="#b9803f" stroke-width="5.5" stroke-linecap="round"/>')
    g.append('<circle cx="772" cy="208" r="4.5" fill="#ff6b6b"/><circle cx="898" cy="260" r="11.5" fill="#1580f0"/>')
    return "".join(g)


def room():
    g = ['<rect width="1280" height="640" fill="url(#wall)"/>',
         '<rect width="1280" height="640" fill="url(#glowwall)"/>',
         '<rect y="400" width="1280" height="60" fill="#ecd0ad"/><rect y="396" width="1280" height="8" fill="#d9b78e"/>']
    # floor with perspective planks
    g.append('<polygon points="0,440 1280,440 1280,640 0,640" fill="url(#floor)"/>')
    for k in range(-14, 15):
        x = 640 + k * 90
        g.append(f'<line x1="{x}" y1="440" x2="{640 + (x - 640) * 2.1:.0f}" y2="640" stroke="#9a6638" stroke-width="2" opacity=".35"/>')
    for y in (470, 505, 548, 600):
        g.append(f'<line x1="0" y1="{y}" x2="1280" y2="{y}" stroke="#9a6638" stroke-width="2" opacity=".25"/>')
    # ceiling lights
    for cx in (330, 960):
        g.append(f'<ellipse cx="{cx}" cy="-6" rx="210" ry="40" fill="url(#lamp)"/>')
    # bulletin board on the left
    g.append('<rect x="24" y="84" width="82" height="104" rx="5" fill="#b98a55"/><rect x="30" y="90" width="70" height="92" rx="3" fill="#d8a96b"/>')
    for x, y, c, rot in [(36, 98, "#ffd166", -6), (66, 100, "#8de0c7", 5), (40, 134, "#ff9fb2", 4), (70, 138, "#a8d8ff", -5), (52, 160, "#ffe9a6", 2)]:
        g.append(f'<rect x="{x}" y="{y}" width="26" height="26" fill="{c}" transform="rotate({rot} {x + 13} {y + 13})"/><circle cx="{x + 13}" cy="{y + 4}" r="2.5" fill="#d64545"/>')
    # a plant by the teacher
    g.append('<path d="M1196,420 h46 l-6,40 h-34 z" fill="#c8693f"/><rect x="1192" y="414" width="54" height="9" rx="3" fill="#dd7e52"/>')
    for a, h_ in [(-40, 62), (-12, 74), (14, 70), (40, 56), (0, 50)]:
        g.append(f'<ellipse cx="{1219 + a * 0.9}" cy="{402 - h_ / 2}" rx="11" ry="{h_ / 2}" fill="#4caf6a" transform="rotate({a} {1219 + a * 0.5} 414)"/>')
    return "".join(g)


def dust():
    g = []
    for _ in range(26):
        x, y = rng.uniform(150, 840), rng.uniform(66, 316)
        g.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(0.8, 1.8):.1f}" fill="#fff" opacity="{rng.uniform(.2, .5):.2f}"/>')
    return "".join(g)


def build():
    rng.seed(11)                            # start every build from the same state, so that two builds give the same drawing
    defs = f"""
<style>{font_face('Patrick Hand', 'fonts/PatrickHand-Regular.ttf')}{font_face('Caveat Brush', 'fonts/CaveatBrush-Regular.ttf')}</style>
<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff4e4"/><stop offset="1" stop-color="#f6d9bc"/></linearGradient>
<radialGradient id="glowwall" cx="0.45" cy="0.28" r="0.6"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9a56b"/><stop offset="1" stop-color="#a86f3e"/></linearGradient>
<linearGradient id="board" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2a5c55"/><stop offset="1" stop-color="#1a3f3a"/></linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b98450"/><stop offset="1" stop-color="#8a5a2b"/></linearGradient>
<linearGradient id="skin" gradientUnits="userSpaceOnUse" x1="980" y1="112" x2="1100" y2="218"><stop offset="0" stop-color="#4aa3ff"/><stop offset=".5" stop-color="#1580f0"/><stop offset="1" stop-color="#0062cc"/></linearGradient>
<linearGradient id="cardigan" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3bd1c2"/><stop offset="1" stop-color="#1f9a8e"/></linearGradient>
<linearGradient id="hairBack" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6e2f19"/><stop offset="1" stop-color="#4a1d10"/></linearGradient>
<linearGradient id="hairFront" gradientUnits="userSpaceOnUse" x1="1040" y1="94" x2="1040" y2="258"><stop offset="0" stop-color="#c8683a"/><stop offset=".5" stop-color="#9a4622"/><stop offset="1" stop-color="#63290f"/></linearGradient>
<radialGradient id="sparkhalo"><stop offset="0" stop-color="#fff6c0" stop-opacity=".9"/><stop offset=".5" stop-color="#ffe680" stop-opacity=".4"/><stop offset="1" stop-color="#ffe680" stop-opacity="0"/></radialGradient>
<linearGradient id="scarf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffa3bc"/><stop offset="1" stop-color="#f0648f"/></linearGradient>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.6"/></filter>
<linearGradient id="desk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4d9b4"/><stop offset="1" stop-color="#e2ba88"/></linearGradient>
<radialGradient id="aura" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#7ff3e4" stop-opacity=".30"/><stop offset="1" stop-color="#7ff3e4" stop-opacity="0"/></radialGradient>
<radialGradient id="lamp" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<radialGradient id="vignette" cx="0.5" cy="0.5" r="0.75"><stop offset="0.6" stop-color="#2a1a0a" stop-opacity="0"/><stop offset="1" stop-color="#2a1a0a" stop-opacity=".32"/></radialGradient>
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="chalk" x="-2%" y="-2%" width="104%" height="104%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.4"/></filter>
"""
    body = [room(), board(), dust(), agent()]
    # a few sparkles drifting from the board towards the class
    for x, y, s in [(880, 252, 9), (905, 330, 6), (860, 392, 7), (790, 372, 5)]:
        body.append(star(x, y, s))
    body.append(rows())
    body.append(sparks())
    body.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f"<defs>{defs}</defs>{''.join(body)}</svg>")


if __name__ == "__main__":
    out = HERE / "banner.svg"
    with open(out, "w", encoding="utf-8", newline="") as handle:      # newline="": the same bytes on every platform
        handle.write(build())
    print("wrote", out, f"({out.stat().st_size // 1024} KB)")
