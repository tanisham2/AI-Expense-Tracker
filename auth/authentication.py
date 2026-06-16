import streamlit as st
from utils.api_client import login, register

def is_authenticated():
    return st.session_state.get("authenticated", False)

def logout():
    for key in ["authenticated", "user", "user_id", "access_token", "refresh_token", "current_page"]:
        st.session_state.pop(key, None)

def show_login_page():
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <div style="font-size:40px;">💹</div>
        <div style="font-size:24px; font-weight:700; color:#58a6ff;">Welcome Back</div>
        <div style="color:#8b949e; font-size:13px;">Sign in to your FinTrack AI account</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
            return
        data, status = login(email, password)
        if status == 200:
            st.session_state.authenticated = True
            st.session_state.user = data["user"]
            st.session_state.user_id = data["user"]["id"]
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            st.session_state.current_page = "dashboard"
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error(f"❌ {data.get('detail', 'Login failed')}")

def show_register_page():
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <div style="font-size:40px;">🚀</div>
        <div style="font-size:24px; font-weight:700; color:#58a6ff;">Create Account</div>
        <div style="color:#8b949e; font-size:13px;">Start tracking finances intelligently</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        name = st.text_input("👤 Full Name", placeholder="John Doe")
        email = st.text_input("📧 Email", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password")
        confirm = st.text_input("🔒 Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not all([name, email, password, confirm]):
            st.error("Please fill all fields.")
            return
        if password != confirm:
            st.error("Passwords don't match.")
            return
        if len(password) < 8:
            st.error("Password must be 8+ characters.")
            return
        data, status = register(name, email, password)
        if status == 201:
            st.success("✅ Account created! Please sign in.")
        else:
            st.error(f"❌ {data.get('detail', 'Registration failed')}")