import streamlit as st
import pandas as pd
import utils
from datetime import datetime
import time
import matplotlib.pyplot as plt

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Onyx Capital",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INITIALIZATION ---
if "db_initialized" not in st.session_state:
    utils.init_db()
    st.session_state["db_initialized"] = True

if "page" not in st.session_state: st.session_state.page = "landing"
if "auth_status" not in st.session_state: st.session_state.auth_status = False
if "username" not in st.session_state: st.session_state.username = ""
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Dashboard"

# Initialize Document Queue
if "pending_docs" not in st.session_state: st.session_state.pending_docs = []
if "review_mode" not in st.session_state: st.session_state.review_mode = False
if "current_review_doc" not in st.session_state: st.session_state.current_review_doc = None
if "extracted_data" not in st.session_state: st.session_state.extracted_data = {}

# --- 3. GLOBAL PROFESSIONAL CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; -webkit-user-select: none; user-select: none; }
    input, textarea { user-select: text !important; -webkit-user-select: text !important; }

    /* HIDE 'PRESS ENTER TO APPLY' */
    div[data-testid="InputInstructions"] { display: none !important; }

    /* LOCK CURSOR ON DROPDOWNS (CURRENCY) */
    div[data-testid="stSelectbox"] input {
        cursor: pointer !important;
        caret-color: transparent !important; /* Hides blinking text cursor */
    }
    div[data-testid="stSelectbox"] {
        cursor: pointer !important;
    }

    [data-testid="stAppViewContainer"] { background-color: #050505 !important; color: #E0E0E0; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    div[data-testid="stDecoration"] { display: none; }
    section[data-testid="stSidebar"] { background-color: #0B0C10; border-right: 1px solid #1F1F1F; }
    
    .sidebar-label { color: #666; font-size: 0.85rem; font-weight: 700; letter-spacing: 1.5px; margin-top: 40px; margin-bottom: 15px; padding-left: 14px; text-transform: uppercase; }
    
    div[role="radiogroup"] label { padding: 14px 16px; margin-bottom: 6px; border-radius: 8px; transition: all 0.2s ease; cursor: pointer !important; color: #999; border: 1px solid transparent; font-size: 16px; font-weight: 500; }
    div[role="radiogroup"] label:hover { background-color: #151515; color: #FFF !important; }
    div[role="radiogroup"] label[data-checked="true"] { background-color: #1A1A1A; color: #FFF !important; border-left: 4px solid #6366F1; font-weight: 700; }
    
    /* DOC CARDS & PROFILE CARDS */
    .doc-card { background-color: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }
    .doc-icon-container { background-color: #1A1A1A; width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-right: 20px; }
    .doc-status-bar { background-color: #3A2E15; color: #F59E0B; padding: 6px 10px; border-radius: 6px; font-size: 0.75rem; margin-top: 8px; display: inline-flex; align-items: center; }
    .mini-stat-card { background-color: #111; border: 1px solid #222; border-radius: 12px; padding: 16px 24px; display: flex; align-items: center; }
    
    /* PROFILE SPECIFIC */
    .profile-header { background-color: #111; border: 1px solid #222; border-radius: 12px; padding: 30px; margin-bottom: 24px; display: flex; align-items: center; }
    .profile-avatar { width: 80px; height: 80px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 36px; color: white; margin-right: 24px; font-weight: 700;}
    
    /* ANIMATION CONTAINER */
    .onyx-bg-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; overflow: hidden; pointer-events: none; background: #050505; }
    .stock-graph-svg { position: absolute; top: 40%; left: 0; width: 200%; height: 60%; animation: slideGraph 20s linear infinite; opacity: 0.6; }
    .graph-line { fill: none; stroke: #3f3f46; stroke-width: 2; vector-effect: non-scaling-stroke; }
    .graph-glow { filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.2)); }
    @keyframes slideGraph { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    
    .hero-container { position: relative; z-index: 10; text-align: center; padding-top: 15vh; }
    .hero-title { font-size: 6rem; font-weight: 900; color: #ffffff; letter-spacing: -3px; margin-bottom: 0; text-shadow: 0 10px 30px rgba(0,0,0,0.8); }
    .hero-subtitle { font-size: 1.6rem; color: #a1a1aa; font-weight: 400; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def hide_sidebar():
    st.markdown("""<style>section[data-testid="stSidebar"] {display: none !important;}</style>""", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.write("") 
        c_logo, c_text = st.columns([1, 4])
        with c_logo: st.markdown("<div style='font-size: 32px; line-height: 1;'>💎</div>", unsafe_allow_html=True)
        with c_text: st.markdown("<h2 style='margin:0; padding-top: 5px; font-size:24px; font-weight:800; color:white; letter-spacing: -0.5px; line-height: 1;'>ONYX</h2>", unsafe_allow_html=True)
        st.write(""); st.write("")
        st.markdown('<p class="sidebar-label">PLATFORM</p>', unsafe_allow_html=True)
        # Added "Profile" to the list below
        nav = st.radio("Main Navigation", ["Dashboard", "Transactions", "Documents", "AI Advisor", "Goals", "Reports", "Profile"], label_visibility="collapsed", key="navigation_radio")
        st.write(""); st.write(""); st.write(""); st.divider()
        st.caption(f"User: **{st.session_state.username}**")
        if st.button("Log Out", use_container_width=True):
            st.session_state.auth_status = False; st.session_state.username = ""; st.session_state.page = "landing"; st.rerun()
        return nav

def render_custom_metric(label, value, extra_html=""):
    html = f"""<div style="background-color: #111; border: 1px solid #222; border-radius: 12px; padding: 24px; height: 100%; box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: space-between;">
        <div style="color: #888; font-size: 14px; font-weight: 500; margin-bottom: 8px;">{label}</div>
        <div style="color: #FFF; font-size: 28px; font-weight: 700;">{value}</div>
        <div style="margin-top: 12px; display: flex; align-items: center;">{extra_html}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)

def load_data():
    df = utils.get_expenses_from_db()
    total_spend = df["amount"].sum() if not df.empty else 0.0
    return df, total_spend

# =========================================================
# VIEWS
# =========================================================
def show_landing():
    hide_sidebar()
    st.markdown("""
        <div class="onyx-bg-container"><svg class="stock-graph-svg" viewBox="0 0 2000 400" preserveAspectRatio="none"><path class="graph-line graph-glow" d="M0,200 L50,150 L100,220 L100,350 M100,220 L150,180 L200,250 L250,150 L250,380 M250,150 L300,100 L350,160 L400,120 L400,300 M400,120 L450,180 L500,140 L550,220 L600,160 L600,350 M600,160 L650,100 L700,200 L750,150 L800,220 L800,380 M800,220 L850,180 L900,250 L950,200 L1000,200 L1050,150 L1100,220 L1100,350 M1100,220 L1150,180 L1200,250 L1250,150 L1250,380 M1250,150 L1300,100 L1350,160 L1400,120 L1400,300 M1400,120 L1450,180 L1500,140 L1550,220 L1600,160 L1600,350 M1600,160 L1650,100 L1700,200 L1750,150 L1800,220 L1800,380 M1800,220 L1850,180 L1900,250 L1950,200 L2000,200" /></svg></div>
        <div class="hero-container"><h1 class="hero-title">ONYX CAPITAL.</h1><p class="hero-subtitle">The Enterprise Operating System for Personal Wealth.<br>AI-Driven. Private. Secure.</p></div>
    """, unsafe_allow_html=True)
    
    st.write(""); st.write(""); c1, c2, c3 = st.columns([1, 0.5, 1])
    with c2: 
        if st.button("Access Dashboard", use_container_width=True): st.session_state.page = "auth"; st.rerun()

def show_auth():
    hide_sidebar()
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>Welcome Back</h2>", unsafe_allow_html=True)
        st.write("")
        auth_mode = st.tabs(["Sign In", "Register"])
        with auth_mode[0]:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            st.write("")
            if st.button("Sign In", use_container_width=True):
                if utils.verify_user(u, p): st.session_state.auth_status = True; st.session_state.username = u; st.session_state.page = "app"; st.rerun()
                else: st.error("Invalid credentials.")
        with auth_mode[1]:
            new_u = st.text_input("Choose Username", key="signup_u"); new_p = st.text_input("Choose Password", type="password", key="signup_p"); st.write("")
            if st.button("Create Account", use_container_width=True):
                if utils.create_user(new_u, new_p): st.success("Account created.")
                else: st.error("Username taken.")
        st.markdown("---"); 
        if st.button("← Back"): st.session_state.page = "landing"; st.rerun()

def show_app():
    nav = render_sidebar()
    df, total_spend = load_data()
    # LOAD SETTINGS DYNAMICALLY
    budget = utils.get_budget()
    currency = utils.get_currency()
    
    # --- DASHBOARD ---
    if nav == "Dashboard":
        st.title("Financial Overview")
        
        # EDIT BUDGET BUTTON
        with st.expander(f"⚙️ Adjust Monthly Budget"):
            new_budget = st.number_input(f"Set Budget Amount ({currency})", value=float(budget))
            if st.button("Update Budget"):
                utils.set_budget(new_budget)
                st.success("Budget Updated!")
                time.sleep(0.5)
                st.rerun()

        st.caption(f"Real-time Data • {datetime.now().strftime('%B %Y')}")
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1: render_custom_metric("Monthly Budget", f"{currency}{budget:,.0f}", "<span style='color:#666; font-size:12px;'>Fixed Allocation</span>")
        with c2: render_custom_metric("Total Spent", f"{currency}{total_spend:,.2f}", """<svg width="100" height="25" viewBox="0 0 100 25" style="margin-right:10px;"><path d="M0 20 L10 15 L20 18 L30 10 L40 12 L50 5 L60 15 L70 8 L80 18 L90 10 L100 15" fill="none" stroke="#4ADE80" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg><span style='color:#4ADE80; font-weight:bold; font-size:12px;'>+ Volatility</span>""")
        with c3: render_custom_metric("Remaining Capital", f"{currency}{budget - total_spend:,.2f}", "<span style='color:#6366F1; font-weight:bold; font-size:12px;'>90% Liquid</span>")
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Capital Allocation")
            if not df.empty:
                cat_data = df.groupby("category")["amount"].sum()
                fig, ax = plt.subplots(figsize=(5, 3))
                fig.patch.set_facecolor('#050505'); fig.patch.set_alpha(0.0); ax.set_facecolor('#050505')
                colors = ['#6366F1', '#10B981', '#F59E0B', '#EF4444']
                wedges, texts, autotexts = ax.pie(cat_data, autopct='%1.1f%%', startangle=90, pctdistance=0.85, colors=colors[:len(cat_data)], textprops={'color':"white", 'fontsize': 9, 'weight':'bold'}, wedgeprops={'edgecolor': '#050505', 'linewidth': 3, 'width': 0.6})
                ax.legend(wedges, cat_data.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False, labelcolor="#E0E0E0")
                st.pyplot(fig, use_container_width=True)
            else: st.info("No data available.")
        with c2:
            st.subheader("Recent Activity")
            if not df.empty: st.dataframe(df.sort_values("date", ascending=False).head(5), hide_index=True, use_container_width=True, column_config={"date": "Date", "amount": st.column_config.NumberColumn(f"{currency}", format=f"{currency}%.0f")})
            else: st.caption("No recent transactions.")

    # --- TRANSACTIONS ---
    elif nav == "Transactions":
        st.title("Transaction Ledger")
        t1, t2 = st.tabs(["New Entry", "History Log"])
        with t1:
            c1, c2 = st.columns(2)
            with c1:
                st.info("📸 **AI Scan**")
                up = st.file_uploader("Upload Receipt", type=["jpg", "png"], label_visibility="collapsed")
                if up and st.button("Scan Receipt"):
                    with st.spinner("Processing..."):
                        d = utils.analyze_image_direct(up)
                        st.session_state['ai_data'] = d
                        if "warning" in d:
                            st.warning(d['warning']) 
                        else:
                            st.success("Scanned!")
                        st.rerun()
            with c2:
                st.info("✏️ **Details**")
                val = st.session_state.get('ai_data', {})
                date = st.date_input("Date", datetime.today())
                cat = st.selectbox("Category", ["Food", "Transport", "Utilities", "Other"])
                amt = st.number_input(f"Amount ({currency})", value=float(val.get('amount', 0.0)))
                desc = st.text_input("Note", value=val.get('description', ''))
                if st.button("Save Entry", type="primary"):
                    utils.add_expense_to_db(str(date), cat, amt, desc)
                    if 'ai_data' in st.session_state: del st.session_state['ai_data']
                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
        with t2:
            st.dataframe(df, use_container_width=True, column_config={"amount": st.column_config.NumberColumn(f"Amount ({currency})", format=f"{currency}%.2f")})
            
    # --- DOCUMENTS ---
    elif nav == "Documents":
        if st.session_state.review_mode and st.session_state.current_review_doc:
            doc_file = st.session_state.current_review_doc
            data = st.session_state.extracted_data
            
            st.markdown(f"### Reviewing: {doc_file.name}")
            
            if "warning" in data:
                st.warning(f"⚠️ {data['warning']} - Please enter details manually.")
            else:
                st.info("AI Analysis Complete. Verify & Correct Details.")
            
            with st.container():
                c_date = st.text_input("Date", value=data.get('date', datetime.today().strftime('%Y-%m-%d')))
                c_cat = st.selectbox("Category", ["Food", "Transport", "Utilities", "Entertainment", "Investment", "Other"], 
                                     index=["Food", "Transport", "Utilities", "Entertainment", "Investment", "Other"].index(data.get('category', 'Food')) if data.get('category') in ["Food", "Transport", "Utilities", "Entertainment", "Investment", "Other"] else 0)
                c_amt = st.number_input(f"Amount ({currency})", value=float(data.get('amount', 0.0)))
                c_desc = st.text_input("Description", value=data.get('description', ''))
                
                st.write("")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Approve & Save", type="primary", use_container_width=True):
                        utils.add_expense_to_db(c_date, c_cat, c_amt, c_desc)
                        st.session_state.pending_docs.remove(doc_file)
                        st.session_state.review_mode = False
                        st.success("Saved!")
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.review_mode = False
                        st.rerun()
        else:
            st.title("Document Management")
            st.write("Upload and review your financial documents.")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
                    <div class="mini-stat-card">
                        <div style="font-size: 24px; margin-right: 16px;">📄</div>
                        <div>
                            <div style="color: #888; font-size: 14px; font-weight: 500;">Pending Review</div>
                            <div style="color: #FFF; font-size: 24px; font-weight: 700;">{len(st.session_state.pending_docs)}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                with st.expander("📤 Upload Document", expanded=True):
                     uploaded_file = st.file_uploader("Choose file", label_visibility="collapsed")
                     if uploaded_file and st.button("Upload Queue", type="primary", use_container_width=True):
                         st.session_state.pending_docs.append(uploaded_file)
                         st.success("Added to queue")
                         st.rerun()

            st.divider()
            st.subheader("Pending Review")
            st.write("")

            if not st.session_state.pending_docs:
                st.info("No documents pending.")
            else:
                for idx, doc in enumerate(st.session_state.pending_docs):
                    st.markdown(f"""
                        <div class="doc-card">
                            <div style="display: flex; align-items: flex-start;">
                                <div class="doc-icon-container">📄</div>
                                <div>
                                    <div style="font-weight: 600; color: white; font-size: 1rem;">{doc.name}</div>
                                    <div style="color: #888; font-size: 0.8rem; margin-top: 4px;">Size: {doc.size / 1024:.1f} KB</div>
                                     <div class="doc-status-bar">
                                        <span style="margin-right: 8px;">⏳</span> Awaiting AI Analysis
                                    </div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_spacer, col_btn = st.columns([5, 1])
                    with col_btn:
                         st.markdown('<div style="margin-top: -75px; margin-bottom: 38px;">', unsafe_allow_html=True)
                         if st.button("Review", key=f"rev_{idx}", use_container_width=True):
                             with st.spinner("AI is analyzing image..."):
                                 extracted = utils.analyze_image_direct(doc)
                                 st.session_state.extracted_data = extracted
                                 st.session_state.current_review_doc = doc
                                 st.session_state.review_mode = True
                                 st.rerun()
                         st.markdown('</div>', unsafe_allow_html=True)

    # --- AI ADVISOR ---
    elif nav == "AI Advisor":
        st.title("Onyx AI Advisory")
        c1, c2 = st.columns([3, 1])
        with c1:
            personas = ["The Wealth Architect 🏛️ (Long-term Strategy)", "The Strategic Investor 📈 (Aggressive Growth)", "The Frugal Sage 🧘 (Smart Budgeting)", "The Tax Tactician 💼 (Tax Optimization)"]
            guru = st.selectbox("Select Advisor Model", personas)
        with c2: st.write(""); active = st.toggle("Activate AI", value=True)
        st.divider()
        chat_box = st.container(height=500)
        with chat_box:
            if "messages" not in st.session_state: st.session_state.messages = []
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])
        if q := st.chat_input("Ask about your finances..."):
            st.session_state.messages.append({"role": "user", "content": q})
            with chat_box:
                st.chat_message("user").markdown(q)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        ans = utils.get_chat_response(q, persona=guru, enable_guru=active)
                        st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- GOALS ---
    elif nav == "Goals":
        st.title("Financial Targets")
        with st.expander("➕ Create Target"):
            g_name = st.text_input("Goal Name"); g_target = st.number_input(f"Target Amount ({currency})", min_value=1.0)
            if st.button("Create"): utils.add_goal(g_name, g_target); st.success("Created!"); st.rerun()
        st.divider(); goals_df = utils.get_goals()
        if not goals_df.empty:
            for i, row in goals_df.iterrows():
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1: st.subheader(row['name']); prog = min(row['current_amount'] / row['target_amount'], 1.0); st.progress(prog); st.caption(f"{currency}{row['current_amount']:,.0f} / {currency}{row['target_amount']:,.0f}")
                    with c2:
                        add_val = st.number_input("Add", key=f"add_{row['id']}", min_value=0.0, label_visibility="collapsed")
                        if st.button("Fund", key=f"btn_{row['id']}"): utils.update_goal_progress(row['id'], add_val); st.rerun()
                    st.markdown("---")
        else: st.info("No active targets.")

    # --- REPORTS ---
    elif nav == "Reports":
        st.title("Executive Reports")
        if not df.empty:
            st.download_button("📥 Download CSV Ledger", df.to_csv(index=False).encode('utf-8'), "onyx_ledger.csv", "text/csv", type="primary")
            st.dataframe(df, use_container_width=True, column_config={"amount": st.column_config.NumberColumn(f"Amount ({currency})", format=f"{currency}%.2f")})
        else: st.warning("No data found.")

    # --- PROFILE (UPDATED WITH SETTINGS TAB) ---
    elif nav == "Profile":
        st.title("User Profile")
        
        # Profile Header Card (Common to both tabs)
        st.markdown(f"""
        <div class="profile-header">
            <div class="profile-avatar">{st.session_state.username[0].upper()}</div>
            <div class="profile-info">
                <h2 style="margin:0; color:white;">{st.session_state.username}</h2>
                <p style="margin:0; color:#888;">Onyx Premium Member</p>
                <div style="margin-top:8px;">
                    <span style="background:#10B981; color:#050505; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;">ACTIVE</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # TABBED INTERFACE FOR SETTINGS
        tab1, tab2 = st.tabs(["My Profile", "Settings"])
        
        # TAB 1: OVERVIEW & BUDGET
        with tab1:
            st.subheader("Financial Configuration")
            st.markdown("""
            <div class="doc-card">
                <div style="display: flex; align-items: center;">
                    <div class="doc-icon-container" style="font-size: 20px;">💰</div>
                    <div>
                        <div style="font-weight: 600; color: white;">Monthly Budget</div>
                        <div style="color: #666; font-size: 12px;">Base allocation limit</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            new_budget_profile = st.number_input(f"Update Budget ({currency})", value=float(budget), key="profile_budget")
            if st.button("Save New Budget", key="save_profile_budget", type="primary"):
                utils.set_budget(new_budget_profile)
                st.success("Budget Saved")
                time.sleep(0.5)
                st.rerun()

        # TAB 2: SETTINGS (NOTIFICATIONS + CURRENCY + SECURITY)
        with tab2:
            # 1. NOTIFICATION SECTION (TOP FULL WIDTH)
            st.subheader("Notification Preferences")
            st.markdown("""
            <div class="doc-card">
                <div style="display: flex; align-items: center;">
                    <div class="doc-icon-container" style="font-size: 20px;">🔔</div>
                    <div>
                        <div style="font-weight: 600; color: white;">Alerts & Updates</div>
                        <div style="color: #666; font-size: 12px;">Email & Push notifications</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.toggle("Enable All Notifications", value=True)
            
            st.write(""); st.divider(); st.write("")

            # 2. GLOBAL PREFS & SECURITY (BELOW, SIDE BY SIDE)
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Global Preferences")
                st.info("Changing currency will update all dashboards.")
                
                currency_options = ["₹", "$", "€", "£", "¥", "Rp"]
                current_curr_index = 0
                if currency in currency_options:
                    current_curr_index = currency_options.index(currency)
                
                new_currency = st.selectbox("Select Currency Symbol", currency_options, index=current_curr_index)
                if new_currency != currency:
                    utils.set_currency(new_currency)
                    st.success(f"Currency updated to {new_currency}")
                    time.sleep(0.5)
                    st.rerun()

            with c2:
                st.subheader("Security Settings")
                
                with st.expander("Change Password"):
                    p_new = st.text_input("New Password", type="password")
                    p_confirm = st.text_input("Confirm New Password", type="password")
                    if st.button("Update Password"):
                        if p_new and p_new == p_confirm:
                            if utils.update_credentials(st.session_state.username, p_new):
                                st.success("Password Updated Successfully.")
                            else:
                                st.error("Update failed.")
                        else:
                            st.error("Passwords do not match.")
                            
                # ADDED: Change Username Section BELOW Password
                st.write("") 
                with st.expander("Change Username"):
                    new_user_input = st.text_input("New Username")
                    if st.button("Update Username"):
                        if new_user_input:
                            if utils.update_username(st.session_state.username, new_user_input):
                                st.session_state.username = new_user_input
                                st.success(f"Username updated to {new_user_input}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Username already taken.")


# =========================================================
# APP ROUTER
# =========================================================
if st.session_state.page == "landing": show_landing()
elif st.session_state.page == "auth": show_auth()
elif st.session_state.page == "app":
    if st.session_state.auth_status: show_app()
    else: st.session_state.page = "auth"; st.rerun()