import sqlite3
import pandas as pd
from PIL import Image
import google.generativeai as genai
import os
import json
import re
import hashlib
import io
from datetime import datetime
import streamlit as st

# --- 1. CONFIGURATION ---
# 🔒 SECURE LOADING: This looks for the key in Streamlit Secrets
# It will NO LONGER crash if you upload this to GitHub.
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # This is just a fallback for local testing if you don't have secrets set up
    # DO NOT paste your actual key here before uploading to GitHub
    st.error("Google API Key not found. Please add it to Streamlit Secrets.")
    GOOGLE_API_KEY = "" 

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

DB_NAME = "expenses.db"

# --- 2. DATABASE MANAGEMENT ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, date TEXT, category TEXT, amount REAL, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY, name TEXT, target_amount REAL, current_amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

# --- USER AUTHENTICATION & SETTINGS ---
def create_user(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, pwd_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, pwd_hash))
    user = c.fetchone()
    conn.close()
    return user is not None

def update_credentials(old_username, new_password):
    pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE username = ?", (pwd_hash, old_username))
    conn.commit()
    conn.close()
    return True

def update_username(current_username, new_username):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, current_username))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# --- SETTINGS (BUDGET & CURRENCY) ---
def get_setting(key, default_value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_value

def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_budget():
    return float(get_setting('budget', 25000.0))

def set_budget(amount):
    set_setting('budget', amount)

def get_currency():
    return get_setting('currency', '₹')

def set_currency(symbol):
    set_setting('currency', symbol)

# --- EXPENSE FUNCTIONS ---
def add_expense_to_db(date, category, amount, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)",
              (date, category, amount, description))
    conn.commit()
    conn.close()

def get_expenses_from_db():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    return df

# --- GOALS FUNCTIONS ---
def add_goal(name, target):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO goals (name, target_amount, current_amount) VALUES (?, ?, 0)", (name, target))
    conn.commit()
    conn.close()

def get_goals():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM goals", conn)
    conn.close()
    return df

def update_goal_progress(goal_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE goals SET current_amount = current_amount + ? WHERE id = ?", (amount, goal_id))
    conn.commit()
    conn.close()

# --- SHARED AI HELPER ---
def get_working_model_name():
    valid_model = "gemini-1.5-flash"
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    valid_model = m.name
                    break
    except:
        pass
    return valid_model

# --- AI LOGIC ---
def analyze_image_direct(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        model_name = get_working_model_name()
        # print(f"Onyx Vision: Using model {model_name}") # Removed print for clean logs
        model = genai.GenerativeModel(model_name)
        
        prompt = """
        Extract receipt data. Return ONLY JSON.
        Format: {"date": "YYYY-MM-DD", "amount": 0.00, "category": "Food", "description": "Brief desc"}
        """
        response = model.generate_content([prompt, image])
        
        if response.text:
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(clean_text)
            
    except Exception as e:
        return {
            "date": datetime.today().strftime('%Y-%m-%d'),
            "amount": 0.0,
            "category": "Other",
            "description": "Manual Entry (AI Failed)",
            "warning": f"AI Error: {str(e)[:50]}..."
        }
    return {}

def get_chat_response(query, persona="Generic", enable_guru=True):
    try:
        model_name = get_working_model_name()
        model = genai.GenerativeModel(model_name)
        chat = model.start_chat(history=[])
        sys_msg = f"You are {persona}. Keep it short." if enable_guru else "You are a helpful assistant."
        response = chat.send_message(f"{sys_msg}\nUser: {query}")
        return response.text
    except Exception as e:
        return f"System Error: {str(e)[:100]}. Please try again later."

