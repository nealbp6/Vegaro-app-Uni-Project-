<h1 align="center">
  <br>
  <a href="#"><img src="logo.jpg" alt="Vegaro Logo" width="350"></a>
  <br>
</h1>

<h4 align="center">An AI-powered dietary assistant that creates personalized recipes based on your allergies, diet, and available ingredients — built with Python, CustomTkinter, and Supabase.</h4>

> ⚠️ **Note:** Vegaro is currently an MVP for a university project. It is not yet a finished product, and additional features and improvements are required for a launch.

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/UI-CustomTkinter-9cf" alt="UI Framework"></a>
  <a href="#"><img src="https://img.shields.io/badge/backend-Supabase-00A37A" alt="Backend"></a>
  
</p>

<p align="center">
<a href="#Core-Components">Core Components</a> •
<a href="#Installation">Installation</a> •
<a href="#Environment-Setup">Environment Setup</a> •
<a href="#Database-Setup">Database Setup</a> •
<a href="#AI-Disclosure">AI disclosure</a> •
<a href="#Credits">Credits</a> •
<a href="#License">License</a>
</p>

---

## Core Components

- **Home**
  - View your saved recipes.
  - Create new AI-powered recipes using your *diet*, *allergies*, *ingredients you have*, and *what you feel like eating*.

- **Profile**
  - Set and update your **diet** and **allergies**.
  - These preferences are saved locally and synced to Supabase.

- **Recipe Creator**
  - Input:
    - Ingredients you have  
    - What you want to eat  
  - Output:
    - AI-generated recipe name  
    - Description  
    - Ingredients list  
    - Instructions  
    - Time estimate  
    - Difficulty  
  - Saved **locally** and **in Supabase** (protected from double-save issues).

---

## Installation

To run Vegaro locally:

```bash
# 1️⃣ Clone the repository
git clone https://github.com/<your-username>/vegaro.git
cd vegaro

# 2️⃣ Install dependencies
pip install -r requirements.txt

# 3️⃣ Run the app
python main.py
```

## Environment Setup

Before running the app, create a `.env` file in the project root:

```bash
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-service-role-or-anon-key
GROQ_API_KEY=your-groq-api-key
USER_ID=your-user-id
```

⚠️ These values must **not** be committed to GitHub.


---

## Database Setup

Vegaro uses **two tables** in Supabase.

---

### 1️⃣ user_profiles

**SQL:**

```sql
create table user_profiles (
  id uuid primary key,
  diet text,
  allergies text,
  updated_at timestamptz default now()
); 
```

### 2️⃣ recipes

**SQL:**

```sql
create table recipes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references user_profiles(id) on delete cascade,
  name text,
  description text,
  ingredients text,
  instructions text,
  difficulty text,
  time text,
  created_at timestamptz default now()
);
```
 
## AI Disclosure

During the development of **Vegaro**, AI-powered tools played a major role in building, structuring, and refining the application. The project was primarily developed with the assistance of AI.

- **ChatGPT and related models:** Helped generate code, improve structure, create documentation, and optimize UI logic.

> ⚠️ Important: While AI contributed heavily to development, all final decisions, testing, and validations were performed by the human developer. AI was used as a development tool, not as an autonomous decision-maker.


## Credits
- **Developer:** Neal
- **AI Tools Used:** ChatGPT, Leonardo AI
- **Open-Source Libraries / Frameworks:**
  - Python
  - CustomTkinter
  - JSON (native)
  - Supabase (Python client)
- **APIs Used:**  Supabase API
- **Design Assets / Icons:** Leonardo AI
- **Inspiration / References:** https://chatgpt.com

## License

This project is licensed under the MIT License.

> © **2025 Neal**  

> *Feel free to modify, improve, and share — just include credit to the original author.*
