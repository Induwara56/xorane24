import os
import re
import google.generativeai as genai

# Setup Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_seo_tags(content_snippet):
    prompt = f"""
    You are an SEO expert. Analyze the following website content and generate optimized SEO meta tags.
    Website Content:
    {content_snippet}

    Please provide the following tags in HTML format:
    1. Optimized <title> tag.
    2. <meta name="description" content="..."> (max 160 chars)
    3. <meta name="keywords" content="...">
    4. OpenGraph tags (og:title, og:description, og:type=website, og:url=https://xorane24.org)
    5. Twitter Card tags (twitter:card=summary_large_image, twitter:title, twitter:description)
    6. A <script type="application/ld+json"> tag containing Schema.org markup (Organization, WebSite) for AI models to understand the site's purpose.

    Format the output as a clean block of HTML tags. Do not include any other text or markdown formatting.
    """
    
    response = model.generate_content(prompt)
    return response.text.replace("```html", "").replace("```", "").strip()

def update_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract a snippet of content for context (first 2000 chars)
    # Removing style and script tags first to get clean text
    clean_text = re.sub(r'<(style|script).*?>.*?</\1>', '', html_content, flags=re.DOTALL)
    content_snippet = clean_text[:2000]

    print("Generating SEO tags with Gemini...")
    new_tags = generate_seo_tags(content_snippet)
    
    print("New tags generated:")
    print(new_tags)

    # Simple logic to find the <head> section and insert/replace tags
    # We'll look for the existing meta tags and replace them, or just insert at the start of head
    
    # Remove existing common meta tags to avoid duplicates
    patterns_to_remove = [
        r'<title>.*?</title>',
        r'<meta name="description" content=".*?">',
        r'<meta name="keywords" content=".*?">',
        r'<meta property="og:.*?" content=".*?">',
        r'<meta name="twitter:.*?" content=".*?">'
    ]
    
    updated_content = html_content
    for pattern in patterns_to_remove:
        updated_content = re.sub(pattern, '', updated_content, flags=re.IGNORECASE)

    # Insert new tags after <head> or at the top
    if '<head>' in updated_content:
        updated_content = updated_content.replace('<head>', f'<head>\n{new_tags}\n', 1)
    else:
        # If no <head> tag found (unlikely), prepend to top
        updated_content = f"{new_tags}\n" + updated_content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Successfully updated {file_path}")

if __name__ == "__main__":
    target_file = "index.html"
    if os.path.exists(target_file):
        update_html_file(target_file)
    else:
        print(f"Error: {target_file} not found.")
