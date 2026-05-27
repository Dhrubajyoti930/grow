import os
import google.generativeai as genai

# Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Read the wishlist
if not os.path.exists('wishlist.txt'):
    exit("No wishlist found.")

with open('wishlist.txt', 'r') as f:
    lines = f.readlines()

if not lines:
    exit("Wishlist is empty.")

prompt = lines[0].strip()

# Determine next page number
files = [f for f in os.listdir('.') if f.startswith('page') and f.endswith('.html')]
next_num = len(files) + 1
filename = f"page{next_num}.html"

# Generate content
try:
    response = model.generate_content(
        f"Create a complete, single-file HTML game/page for: {prompt}. "
        "Include all CSS and JS within the file. Return ONLY the HTML code. "
        "No markdown code blocks (```html), just raw HTML."
    )
    html_code = response.text.replace("```html", "").replace("```", "")
    
    # Save the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_code)

    # Update index.html
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    anchor = ""
    link = f'<li><a href="{filename}">Page {next_num}</a></li>'
    new_content = content.replace(anchor, f"{link}\n    {anchor}")

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Update wishlist (remove the first line)
    with open('wishlist.txt', 'w', encoding='utf-8') as f:
        f.writelines(lines[1:])
        
    print(f"Successfully generated {filename}")

except Exception as e:
    print(f"Failed to generate: {e}")
    exit(1)
