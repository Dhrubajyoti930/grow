"""
scripts/generate_game.py
───────────────────────
Asks Gemini to generate a self-contained HTML game / page,
saves it under games/ (or tools/ / art/ / stories/),
then injects a new entry into the PAGES array inside index.html.
"""

import os, re, json, textwrap
from datetime import date
import google.generativeai as genai

# ── Config ─────────────────────────────────────────────────────────
WISHLIST_PATH = "wishlist.txt"
INDEX_PATH    = "index.html"
INJECT_START  = "// GENERATED_PAGES_START"
INJECT_END    = "// GENERATED_PAGES_END"
TAG_DIRS      = {"game": "games", "tool": "tools", "art": "art", "story": "stories"}

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ── Pick next wishlist item ────────────────────────────────────────
def pick_idea():
    """Return the first un-generated idea from wishlist.txt."""
    if not os.path.exists(WISHLIST_PATH):
        return None

    with open(WISHLIST_PATH, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and not stripped.startswith("#") and "✅" not in line:
            return i, lines, stripped
    return None

def mark_done(lines, idx):
    lines[idx] = lines[idx].rstrip() + "  ✅\n"
    with open(WISHLIST_PATH, "w") as f:
        f.writelines(lines)

def parse_idea(raw):
    """Parse '[tag]  Title — desc' into parts."""
    m = re.match(r'\[(\w+)\]\s+(.+?)\s+—\s+(.+)', raw)
    if not m:
        return None
    tag, title, desc = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return {"tag": tag, "title": title, "desc": desc, "slug": slug}

# ── Generate HTML via Gemini ───────────────────────────────────────
def generate_html(idea):
    prompt = textwrap.dedent(f"""
        Create a beautiful, self-contained single HTML file for the following:

        Title: {idea['title']}
        Type:  {idea['tag']}
        Brief: {idea['desc']}

        Requirements:
        - Entirely self-contained (no external dependencies except Google Fonts via <link>).
        - Dark theme with a distinctive, polished aesthetic. No generic purple gradients.
        - Fully functional and playable / usable right away.
        - Mobile-friendly.
        - Include a subtle back link: <a href="../index.html">← /grow</a> in the top-left corner.
        - Return ONLY the raw HTML, starting with <!DOCTYPE html>. No markdown, no explanation.
    """)

    response = model.generate_content(prompt)
    return response.text.strip()

# ── Update index.html ──────────────────────────────────────────────
def inject_into_index(idea, file_path, icon="🎮"):
    today = date.today().isoformat()
    new_entry = textwrap.dedent(f"""
      {{
        title: "{idea['title']}",
        file:  "{file_path}",
        desc:  "{idea['desc']}",
        tag:   "{idea['tag']}",
        date:  "{today}",
        icon:  "{icon}"
      }},""")

    with open(INDEX_PATH, "r") as f:
        content = f.read()

    # Insert after INJECT_START marker
    if INJECT_START not in content:
        print("⚠️  Marker not found in index.html — skipping injection.")
        return

    content = content.replace(
        INJECT_START,
        INJECT_START + new_entry
    )

    with open(INDEX_PATH, "w") as f:
        f.write(content)

    print(f"✅  Injected '{idea['title']}' into index.html")

# ── Icon picker ───────────────────────────────────────────────────
TAG_ICONS = {
    "game":  ["🎮","🕹️","🧩","⚡","🏆"],
    "tool":  ["🔧","🛠️","⚙️","📐","🎛️"],
    "art":   ["🎨","✨","🌀","🖼️","💫"],
    "story": ["📖","🌱","✍️","🗺️","💬"],
}

def pick_icon(tag, slug):
    icons = TAG_ICONS.get(tag, ["🌐"])
    # deterministic but varied
    idx = sum(ord(c) for c in slug) % len(icons)
    return icons[idx]

# ── Main ───────────────────────────────────────────────────────────
def main():
    result = pick_idea()
    if not result:
        print("📋  Wishlist exhausted or not found. Nothing to generate.")
        return

    idx, lines, raw = result
    idea = parse_idea(raw)
    if not idea:
        print(f"⚠️  Could not parse line: {raw}")
        return

    print(f"🚀  Generating: [{idea['tag']}] {idea['title']}")

    html = generate_html(idea)

    # Ensure output directory exists
    out_dir = TAG_DIRS.get(idea["tag"], "pages")
    os.makedirs(out_dir, exist_ok=True)
    out_file = f"{out_dir}/{idea['slug']}.html"

    with open(out_file, "w") as f:
        f.write(html)
    print(f"💾  Saved: {out_file}")

    icon = pick_icon(idea["tag"], idea["slug"])
    inject_into_index(idea, out_file, icon)
    mark_done(lines, idx)

if __name__ == "__main__":
    main()
