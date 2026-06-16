import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.authentication import show_login_page, show_register_page, is_authenticated, logout
from views.dashboard import show_dashboard
from views.expense_manager import show_expense_manager
from views.ai_forecasting import show_ai_forecasting
from views.analytics import show_analytics
from views.budget_planner import show_budget_planner
from views.profile_settings import show_profile_settings
from database.db_manager import init_database

st.set_page_config(
    page_title="FinTrack AI",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * { font-family: 'Inter', sans-serif; }

        .stApp {
            background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a0e1a 100%);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
            border-right: 1px solid #21262d !important;
        }

        section[data-testid="stSidebar"] .stRadio > div {
            gap: 4px;
        }

        section[data-testid="stSidebar"] .stRadio label {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 10px 14px;
            color: #8b949e;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        section[data-testid="stSidebar"] .stRadio label:hover {
            background: #21262d;
            color: #e6edf3;
            border-color: #30363d;
        }

        .metric-card {
            background: linear-gradient(145deg, #161b22, #1c2128);
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #388bfd;
        }

        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: #e6edf3;
            margin: 8px 0 4px;
        }

        .metric-label {
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-icon {
            font-size: 24px;
            margin-bottom: 4px;
        }

        .metric-delta {
            font-size: 12px;
            margin-top: 4px;
        }

        .metric-delta.positive { color: #3fb950; }
        .metric-delta.negative { color: #f85149; }

        .section-header {
            color: #e6edf3;
            font-size: 20px;
            font-weight: 600;
            margin: 24px 0 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #21262d;
        }

        .insight-card {
            background: linear-gradient(145deg, #161b22, #1c2128);
            border: 1px solid #21262d;
            border-radius: 10px;
            padding: 16px;
            margin: 8px 0;
            border-left: 3px solid #388bfd;
        }

        .insight-title {
            color: #8b949e;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .insight-value {
            color: #e6edf3;
            font-size: 16px;
            font-weight: 600;
        }

        .alert-card {
            background: linear-gradient(145deg, #1f1117, #1c1118);
            border: 1px solid #6e3050;
            border-radius: 10px;
            padding: 14px 16px;
            border-left: 3px solid #f85149;
        }

        .success-card {
            background: linear-gradient(145deg, #0f1f0f, #111d11);
            border: 1px solid #1a4520;
            border-radius: 10px;
            padding: 14px 16px;
            border-left: 3px solid #3fb950;
        }

        .stButton > button {
            background: linear-gradient(135deg, #238636, #2ea043);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #2ea043, #3fb950);
            transform: translateY(-1px);
        }

        .stDataFrame {
            border: 1px solid #21262d !important;
            border-radius: 8px !important;
        }

        .budget-progress {
            background: #21262d;
            border-radius: 4px;
            height: 8px;
            margin: 6px 0;
            overflow: hidden;
        }

        .budget-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #161b22, #1c2128);
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 16px 20px;
        }

        div[data-testid="stMetric"] label {
            color: #8b949e !important;
            font-size: 12px !important;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #e6edf3 !important;
        }

        .stSelectbox > div > div {
            background: #161b22 !important;
            border: 1px solid #21262d !important;
            color: #e6edf3 !important;
        }

        .stTextInput > div > div > input {
            background: #161b22 !important;
            border: 1px solid #21262d !important;
            color: #e6edf3 !important;
        }

        .stNumberInput > div > div > input {
            background: #161b22 !important;
            border: 1px solid #21262d !important;
            color: #e6edf3 !important;
        }

        .stDateInput > div > div > input {
            background: #161b22 !important;
            border: 1px solid #21262d !important;
            color: #e6edf3 !important;
        }

        .login-container {
            max-width: 420px;
            margin: 60px auto;
            background: linear-gradient(145deg, #161b22, #1c2128);
            border: 1px solid #21262d;
            border-radius: 16px;
            padding: 40px;
        }

        .logo-text {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #388bfd, #58a6ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 8px;
        }

        .logo-sub {
            color: #8b949e;
            text-align: center;
            font-size: 13px;
            margin-bottom: 32px;
        }

        h1, h2, h3 { color: #e6edf3 !important; }
        p { color: #8b949e; }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #8b949e;
            border-bottom: 2px solid transparent;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #58a6ff;
            border-bottom: 2px solid #58a6ff;
        }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #484f58; }
    </style>
    """, unsafe_allow_html=True)


def main():
    init_database()
    load_css()

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if not is_authenticated():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            tabs = st.tabs(["🔐 Login", "📝 Register"])
            with tabs[0]:
                show_login_page()
            with tabs[1]:
                show_register_page()
        return

    with st.sidebar:
        st.markdown("""
        <div style="padding: 16px 0 24px; text-align: center;">
            <div style="font-size: 26px; font-weight: 700; background: linear-gradient(135deg, #388bfd, #58a6ff);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                💹 FinTrack AI
            </div>
            <div style="color: #8b949e; font-size: 11px; margin-top: 2px;">Intelligent Expense Management</div>
        </div>
        """, unsafe_allow_html=True)

        user = st.session_state.get("user", {})
        st.markdown(f"""
        <div style="background: #21262d; border-radius: 10px; padding: 12px; margin-bottom: 20px; text-align:center;">
            <div style="font-size: 28px;">👤</div>
            <div style="color: #e6edf3; font-weight: 600; font-size: 14px;">{user.get('name', 'User')}</div>
            <div style="color: #8b949e; font-size: 11px;">{user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 0 4px; margin-bottom: 8px;'>Navigation</div>", unsafe_allow_html=True)

        nav_options = {
            "📊 Dashboard": "dashboard",
            "💳 Expense Manager": "expenses",
            "🤖 AI Forecasting": "forecasting",
            "📈 Analytics": "analytics",
            "💰 Budget Planner": "budget",
            "⚙️ Profile & Settings": "profile"
        }

        current = st.session_state.get("current_page", "dashboard")
        selected = st.radio(
            "Navigate",
            list(nav_options.keys()),
            label_visibility="collapsed",
            index=list(nav_options.values()).index(current) if current in nav_options.values() else 0
        )

        st.session_state.current_page = nav_options[selected]

        st.markdown("<hr style='border-color: #21262d; margin: 20px 0;'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    page = st.session_state.get("current_page", "dashboard")

    if page == "dashboard":
        show_dashboard()
    elif page == "expenses":
        show_expense_manager()
    elif page == "forecasting":
        show_ai_forecasting()
    elif page == "analytics":
        show_analytics()
    elif page == "budget":
        show_budget_planner()
    elif page == "profile":
        show_profile_settings()


if __name__ == "__main__":
    main()