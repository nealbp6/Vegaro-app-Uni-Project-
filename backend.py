# backend.py
import json
import os
import random
from supabase import create_client
from groq import Groq
from dotenv import load_dotenv

# -------------------- Load Environment --------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("GROQ_API_KEY")
USER_CODE = os.getenv("USER_CODE")  # optional: you can set this in .env

# If USER_CODE not provided, generate a stable random 4-digit runtime code
if not USER_CODE:
    USER_CODE = str(random.randint(1000, 9999))
    # store in os.environ for runtime access (won't persist to .env)
    os.environ["USER_CODE"] = USER_CODE

DATA_FILE = "local_data.json"

# -------------------- Supabase client --------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- Groq / AI client --------------------
client = Groq(api_key=API_KEY)

# -------------------- Local Storage --------------------
def load_local_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # corrupt file fallback
            return {"user_profile": {"diet": "", "allergies": ""}, "saved_recipes": []}
    return {"user_profile": {"diet": "", "allergies": ""}, "saved_recipes": []}

def save_local_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_recipe_local(title, content):
    data = load_local_data()
    if "saved_recipes" not in data:
        data["saved_recipes"] = []
    # Prevent duplicate by title (case-insensitive)
    title_clean = title.strip()
    if any(r["title"].strip().lower() == title_clean.lower() for r in data["saved_recipes"]):
        return False
    data["saved_recipes"].append({"title": title_clean, "content": content})
    save_local_data(data)
    return True

def get_saved_recipes():
    data = load_local_data()
    return data.get("saved_recipes", [])

def save_user_profile_local(diet, allergies):
    data = load_local_data()
    data["user_profile"] = {"diet": diet, "allergies": allergies}
    save_local_data(data)

def fetch_user_profile_local():
    data = load_local_data()
    return data.get("user_profile", {"diet": "", "allergies": ""})

# -------------------- Helpers: duplicate checks --------------------
def recipe_exists_local(title):
    recipes = get_saved_recipes()
    title_clean = title.strip().lower()
    return any(r["title"].strip().lower() == title_clean for r in recipes)

def recipe_exists_supabase(title):
    try:
        res = supabase.table("recipes").select("id").eq("user_code", USER_CODE).eq("title", title).execute()
        # supabase returns .data or .data attribute depending on client version
        data = getattr(res, "data", None)
        if data is None and isinstance(res, dict):
            data = res.get("data")
        return bool(data)
    except Exception:
        # If Supabase errors (RLS/policy), treat as not existing so local save still works
        return False

# -------------------- Supabase: User profile --------------------
def fetch_user_profile_supabase():
    try:
        res = supabase.table("users").select("*").eq("user_code", USER_CODE).execute()
        data = getattr(res, "data", None)
        if data is None and isinstance(res, dict):
            data = res.get("data")
        if data:
            # take first row
            row = data[0]
            # ensure keys exist
            return {"diet": row.get("diet", "") or "", "allergies": row.get("allergies", "") or ""}
        return None
    except Exception:
        return None

def save_user_profile(diet, allergies):
    payload = {"user_code": USER_CODE, "diet": diet, "allergies": allergies}
    try:
        # upsert on user_code
        res = supabase.table("users").upsert(payload, on_conflict="user_code").execute()
        return getattr(res, "data", None)
    except Exception as e:
        # may fail due to RLS; raise or return None
        # returning None for the caller to handle
        return None

# -------------------- Supabase: Recipes --------------------
def save_recipe_supabase(title, content):
    # ensure not duplicate
    if recipe_exists_supabase(title):
        return None
    payload = {"user_code": USER_CODE, "title": title, "content": content}
    try:
        res = supabase.table("recipes").insert(payload).execute()
        return getattr(res, "data", None)
    except Exception:
        return None

def fetch_recipes_supabase():
    try:
        res = supabase.table("recipes").select("*").eq("user_code", USER_CODE).order("created_at", {"ascending": False}).execute()
        return getattr(res, "data", []) or []
    except Exception:
        return []

# -------------------- AI Recipe Generation --------------------
def _sanitize_title(raw_title):
    # Keep only first line, trim, max 120 chars
    t = raw_title.strip().split("\n")[0].strip()
    return t[:120]

def generate_recipe_ai(query, diet="", avoid="", have=""):
    # Clean inputs
    diet = diet or "general"
    avoid = avoid or ""
    have = have or ""

    prompt = f"""
Create a recipe for "{query}".
The user follows a {diet} diet and must avoid: {avoid}.
They currently have: {have}.

Output in plain text ONLY. DO NOT include section headers like "Recipe Name" or "Short Description".
Format EXACTLY like this:

<Recipe Title>
<Short 1–2 sentence description>

Ingredients:
- ingredient 1
- ingredient 2

Instructions:
1. step 1
2. step 2

Estimated Time: X minutes
Difficulty: 1-10

Make the title concise (one line). Do not add extra labels or commentary.
"""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_completion_tokens=1024,
        top_p=1,
        reasoning_effort="medium",
    )
    response = completion.choices[0].message.content

    # Extract title and content
    title = _sanitize_title(response)
    content = response.strip()

    # Save locally (prevent duplicate)
    added = add_recipe_local(title, content)

    # Save to supabase only if not duplicate
    saved = None
    if not recipe_exists_supabase(title):
        saved = save_recipe_supabase(title, content)

    # return the generated text (full recipe)
    return content

# -------------------- Utility: sync local with supabase (optional) --------------------
def sync_from_supabase_to_local():
    # fetch user profile
    profile = fetch_user_profile_supabase()
    if profile:
        save_user_profile_local(profile.get("diet", ""), profile.get("allergies", ""))

    # fetch recipes
    remote = fetch_recipes_supabase()
    if not remote:
        return
    local = load_local_data()
    local_recipes = local.get("saved_recipes", [])
    titles_local = {r["title"].strip().lower() for r in local_recipes}
    added = False
    for r in remote:
        title = r.get("title", "").strip()
        content = r.get("content", "")
        if title and title.lower() not in titles_local:
            local_recipes.append({"title": title, "content": content})
            added = True
    if added:
        local["saved_recipes"] = local_recipes
        save_local_data(local)

