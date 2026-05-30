import os
import json
import random
import datetime
import google.generativeai as genai

# ── Setup Gemini ──────────────────────────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY secret is not set in GitHub Actions.")
genai.configure(api_key=api_key)

# ── 50+ Long-tail SEO topics ──────────────────────────────────────────────────
# These are phrased the way people actually search on Google
TOPICS = [
    # Anxiety
    "how to stop a panic attack at night",
    "why do I wake up with anxiety every morning",
    "how to calm anxiety without medication",
    "social anxiety vs shyness: what's the difference",
    "how to cope with health anxiety and stop googling symptoms",
    "what does high-functioning anxiety feel like",
    "how to stop anxious thoughts spiralling",
    "can anxiety cause physical symptoms",
    "how to help someone having a panic attack",
    "anxiety in relationships: how it affects you and your partner",
    # Depression
    "how to get out of bed when you are depressed",
    "signs of high-functioning depression people miss",
    "what is the difference between sadness and depression",
    "how to support a depressed partner without burning out",
    "small daily habits that help lift depression",
    "why does depression make you so tired",
    "how to explain depression to someone who has never had it",
    "depression and loss of identity: finding yourself again",
    "seasonal depression: why winter feels unbearable",
    "exercise and depression: what the science actually says",
    # Sleep & Fatigue
    "why anxiety keeps you awake at night and what to do",
    "sleep deprivation and mental health: the hidden link",
    "how to fix your sleep schedule when you have depression",
    "what is revenge bedtime procrastination and how to stop it",
    "why do I feel more anxious at night",
    # Stress & Burnout
    "signs you are heading for burnout before it happens",
    "how to recover from burnout when you cannot take time off",
    "work stress vs burnout: how to tell the difference",
    "how to set boundaries at work without feeling guilty",
    "why saying no is a mental health skill",
    "compassion fatigue: when caring for others drains you",
    # Relationships & Loneliness
    "how to cope with loneliness when you live alone",
    "why do I feel lonely even around people",
    "how to rebuild trust after it has been broken",
    "toxic relationship patterns to watch out for",
    "how to make friends as an adult: what actually works",
    "what is emotional unavailability and how to deal with it",
    "how to stop people pleasing and set healthy limits",
    # Grief & Loss
    "stages of grief: what they really feel like day to day",
    "how long does grief last and is there a normal timeline",
    "how to support a grieving friend without saying the wrong thing",
    "grief and depression: how to tell them apart",
    "what is ambiguous grief and why it is so hard",
    # Self-esteem & Identity
    "how to build self-esteem when you have none",
    "what is imposter syndrome and how to overcome it",
    "how to stop comparing yourself to others on social media",
    "negative self-talk: how to recognise and challenge it",
    "how to be kinder to yourself: a practical guide",
    # Mindfulness & Coping Tools
    "grounding techniques for anxiety that actually work",
    "how to start meditating when your mind will not stop",
    "what is the 5-4-3-2-1 technique and does it work",
    "box breathing: how to use it for instant calm",
    "journaling for mental health: how to start today",
    "how to build a daily mental health routine",
    # Therapy & Help-seeking
    "what happens in your first therapy session",
    "how to find a therapist you can actually afford",
    "types of therapy explained: which one is right for you",
    "how to talk to your doctor about mental health",
    "online therapy vs in-person: pros and cons",
    # Specific Groups
    "mental health tips for students during exam stress",
    "parenting with anxiety: how to manage and model calm",
    "men and mental health: why it is hard to ask for help",
    "how social media affects teenage mental health",
    "mental health in the workplace: your rights and options",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_best_available_model():
    """Find the best available Gemini model for this API key."""
    try:
        available = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        priority = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-2.0-flash',
            'models/gemini-pro',
        ]
        for p in priority:
            if p in available:
                return p
        return available[0] if available else 'models/gemini-pro'
    except Exception:
        return 'models/gemini-pro'


def pick_topic(existing_blogs: list) -> str:
    """Pick a topic that hasn't been used recently (last 60 posts)."""
    recent_titles = {b.get('topic', '') for b in existing_blogs[:60]}
    available = [t for t in TOPICS if t not in recent_titles]
    # If somehow all topics are used, reset and pick from full list
    if not available:
        available = TOPICS
    return random.choice(available)


def generate_blog_post(topic: str) -> dict:
    """Call Gemini to write a full SEO-optimised mental health article."""
    model_name = get_best_available_model()
    model = genai.GenerativeModel(model_name)

    prompt = f"""
You are an expert mental health writer for Xorane 24, a free global mental health support website.

Write a complete, SEO-optimised blog post about this topic:
"{topic}"

STRICT REQUIREMENTS:
1. Target length: 900-1200 words of actual content.
2. Tone: warm, evidence-informed, non-judgmental, accessible to a global audience.
3. Structure the article with at least 4 H2 subheadings. Each H2 should naturally include related search keywords.
4. Include a practical, actionable section (tips, steps, or techniques people can use today).
5. Never be preachy or overly clinical. Write like a knowledgeable friend.
6. Always end with a short encouraging closing paragraph.

RESPOND WITH A SINGLE JSON OBJECT ONLY.
No markdown. No code fences. No explanation. Just the raw JSON.

JSON fields:
{{
  "title": "SEO-friendly article title (50-65 characters ideally)",
  "tag": "Single category word, one of: Anxiety, Depression, Stress, Sleep, Relationships, Grief, Self-Care, Mindfulness, Recovery, Burnout, Loneliness, Therapy",
  "meta_description": "SEO meta description, 140-160 characters, includes the main keyword naturally",
  "excerpt": "2-sentence preview shown on the blog card. Hook the reader.",
  "content": "Full article HTML using <p>, <h2>, <ul>, <li>, <strong> tags only. No inline styles. 900-1200 words."
}}
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown fences if Gemini adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def update_blogs_json(file_path: str = "blogs.json"):
    """Load existing blogs, generate a new one, prepend, save."""

    # Load existing
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                blogs = json.load(f)
            except Exception:
                blogs = []
    else:
        blogs = []

    # Pick a fresh topic
    topic = pick_topic(blogs)
    print(f"📝 Generating article for topic: {topic}")

    # Generate
    new_post = generate_blog_post(topic)

    # Add metadata
    now = datetime.datetime.utcnow()
    new_post["topic"]  = topic                              # store for duplicate check
    new_post["date"]   = now.strftime("%B %d, %Y")
    new_post["id"]     = now.strftime("%Y%m%d%H%M")
    new_post["read"]   = f"{max(4, len(new_post.get('content', '')) // 900)} min"

    # Prepend and cap at 60 posts (~keep ~2 months of daily posts)
    blogs.insert(0, new_post)
    blogs = blogs[:60]

    # Save
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(blogs, f, indent=2, ensure_ascii=False)

    print(f"✅ Blog added: {new_post['title']}")
    print(f"   Tag: {new_post['tag']}")
    print(f"   Meta: {new_post.get('meta_description', 'N/A')}")


if __name__ == "__main__":
    update_blogs_json()
