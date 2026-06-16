import streamlit as st
from database.db_manager import authenticate_user, create_user

def is_authenticated():
    return st.session_state.get("authenticated", False)

def logout():
    for key in ["authenticated", "user", "user_id", "current_page"]:
        if key in st.session_state:
            del st.session_state[key]

def show_login_page():
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <div style="font-size:40px;">💹</div>
        <div style="font-size:24px; font-weight:700; color:#58a6ff; margin-top:8px;">Welcome Back</div>
        <div style="color:#8b949e; font-size:13px; margin-top:4px;">Sign in to your FinTrack AI account</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("📧 Email Address", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
            return
        user = authenticate_user(email, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.user_id = user['id']
            st.session_state.current_page = "dashboard"
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid email or password.")

    st.markdown("""
    <div style="text-align:center; margin-top:16px; color:#8b949e; font-size:12px;">
        Don't have an account? Switch to the Register tab above.
    </div>
    """, unsafe_allow_html=True)

def show_register_page():
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px;">
        <div style="font-size:40px;">🚀</div>
        <div style="font-size:24px; font-weight:700; color:#58a6ff; margin-top:8px;">Create Account</div>
        <div style="color:#8b949e; font-size:13px; margin-top:4px;">Start tracking your finances intelligently</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        name = st.text_input("👤 Full Name", placeholder="John Doe")
        email = st.text_input("📧 Email Address", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Min 8 characters")
        confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not all([name, email, password, confirm]):
            st.error("Please fill in all fields.")
            return
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return
        if "@" not in email:
            st.error("Please enter a valid email address.")
            return

        success, user_id = create_user(name, email, password)
        if success:
            st.success("✅ Account created! Please sign in.")
        else:
            st.error("❌ Email already registered. Please login.")