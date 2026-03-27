import os
import json
import datetime
import google.generativeai as genai

# Setup Gemini
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_best_available_model():
    """Finds the best model for this key (Self-Fixing)."""
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in priority:
            if p in available_models: return p
        return available_models[0] if available_models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_blog_post():
    """Generates a high-quality mental health blog post using Gemini."""
    model_name = get_best_available_model()
    model = genai.GenerativeModel(model_name)
    
    # Randomly select a topic area to keep it fresh
    topics = [
        "Coping with social anxiety in a digital world",
        "The power of gentle movement for depression",
        "How to build a mental health first-aid kit",
        "Understanding 'Brain Fog' and how to clear it",
        "The importance of setting boundaries for self-care",
        "Mindful eating for mental clarity",
        "How to support a friend who is struggling",
        "The science of gratitude and the brain"
    ]
    selected_topic = datetime.datetime.now().day % len(topics)
    topic = topics[selected_topic]

    prompt = f"""
    You are a compassionate mental health expert writing for Xorane 24 (a free support site).
    Write a blog post about: "{topic}"
    
    Requirements:
    - Tone: Gentle, non-judgmental, evidence-informed.
    - Format: JSON object only. No markdown around the JSON.
    
    JSON Fields:
    - "title": Compelling title
    - "tag": One word tag (e.g. Anxiety, Recovery, Self-Care)
    - "excerpt": 1-2 sentence summary
    - "content": Full article content in HTML (use <p>, <h2>, <ul>, <li>, and <strong> tags). Keep it concise but helpful.
    """

    response = model.generate_content(prompt)
    raw_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)

def update_blogs_json(file_path="blogs.json"):
    """Reads, updates, and writes the blogs.json file."""
    # Load existing blogs
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                blogs = json.load(f)
            except:
                blogs = []
    else:
        blogs = []

    # Generate new post
    new_post = generate_blog_post()
    new_post["date"] = datetime.datetime.now().strftime("%B %d, %Y")
    new_post["id"] = datetime.datetime.now().strftime("%Y%m%d%H%M")
    new_post["read"] = f"{max(3, len(new_post['content']) // 1000)} min"

    # Prepend new post
    blogs.insert(0, new_post)

    # Keep only the last 50 posts to keep the file small (around 100KB)
    blogs = blogs[:50]

    # Save
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(blogs, f, indent=2)
    
    print(f"Successfully added blog: {new_post['title']}")

if __name__ == "__main__":
    update_blogs_json()
