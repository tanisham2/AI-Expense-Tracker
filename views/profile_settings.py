import streamlit as st
import pandas as pd
import io
from datetime import datetime
from database.db_manager import get_expenses, get_user_by_id, update_user_password
from utils.helpers import format_currency

def show_profile_settings():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">⚙️ Profile & Settings</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Manage your account and preferences</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id
    user = get_user_by_id(user_id)
    df = get_expenses(user_id)

    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🔒 Security", "📤 Export Data"])

    # ─── TAB 1: Profile ───
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center; padding: 30px;">
                <div style="font-size: 56px; margin-bottom: 12px;">👤</div>
                <div style="font-size: 20px; font-weight: 700; color: #e6edf3;">{user.get('name','')}</div>
                <div style="color: #8b949e; font-size: 13px; margin-top: 4px;">{user.get('email','')}</div>
                <div style="color: #3fb950; font-size: 11px; margin-top: 8px; background: #0f1f0f;
                            border-radius: 20px; padding: 4px 12px; display: inline-block;">
                    ✓ Active Account
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='section-header'>Account Statistics</div>", unsafe_allow_html=True)
            if not df.empty:
                stats = [
                    ("💸", "Total Spent", format_currency(df['amount'].sum())),
                    ("🔢", "Total Transactions", str(len(df))),
                    ("📅", "First Expense", str(df['date'].min())),
                    ("🗓️", "Last Expense", str(df['date'].max())),
                    ("📊", "Avg Transaction", format_currency(df['amount'].mean())),
                    ("🏷️", "Categories Used", str(df['category'].nunique())),
                ]
                c1, c2 = st.columns(2)
                for i, (icon, label, val) in enumerate(stats):
                    with (c1 if i % 2 == 0 else c2):
                        st.markdown(f"""
                        <div class="insight-card">
                            <div class="insight-title">{icon} {label}</div>
                            <div class="insight-value">{val}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No expenses recorded yet.")

        st.markdown("<div class='section-header'>Membership Info</div>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Member Since</div>
                <div class="insight-value">{str(user.get('created_at',''))[:10]}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Default Currency</div>
                <div class="insight-value">{user.get('currency','INR')} ₹</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Theme</div>
                <div class="insight-value">Dark Mode 🌙</div>
            </div>
            """, unsafe_allow_html=True)

    # ─── TAB 2: Security ───
    with tab2:
        st.markdown("<div class='section-header'>Change Password</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.form("change_password"):
                current_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                submitted = st.form_submit_button("🔐 Update Password", use_container_width=True)

            if submitted:
                from database.db_manager import hash_password, get_connection
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT password_hash FROM users WHERE id=?", (user_id,))
                row = c.fetchone()
                conn.close()
                if row and row['password_hash'] == hash_password(current_pw):
                    if len(new_pw) < 8:
                        st.error("New password must be at least 8 characters.")
                    elif new_pw != confirm_pw:
                        st.error("Passwords do not match.")
                    else:
                        update_user_password(user_id, new_pw)
                        st.success("✅ Password updated successfully!")
                else:
                    st.error("❌ Current password is incorrect.")

    # ─── TAB 3: Export ───
    with tab3:
        st.markdown("<div class='section-header'>Export Your Data</div>", unsafe_allow_html=True)

        if df.empty:
            st.info("No data to export.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div class="insight-card">
                    <div class="insight-title">📊 CSV Export</div>
                    <div class="insight-value">Download all expenses as CSV</div>
                </div>
                """, unsafe_allow_html=True)

                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"fintrack_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col2:
                st.markdown("""
                <div class="insight-card">
                    <div class="insight-title">📑 Summary Report</div>
                    <div class="insight-value">Download monthly summary as CSV</div>
                </div>
                """, unsafe_allow_html=True)

                if not df.empty:
                    df_copy = df.copy()
                    df_copy['date'] = pd.to_datetime(df_copy['date'])
                    df_copy['month'] = df_copy['date'].dt.to_period('M').astype(str)
                    summary = df_copy.groupby(['month', 'category']).agg(
                        Total=('amount', 'sum'),
                        Count=('amount', 'count'),
                        Average=('amount', 'mean')
                    ).round(2).reset_index()

                    summary_csv = summary.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Summary",
                        data=summary_csv,
                        file_name=f"fintrack_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        # Danger zone
        st.markdown("<div class='section-header' style='color: #f85149;'>⚠️ Danger Zone</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="alert-card">
            <div style="color: #e6edf3; font-weight: 600;">Delete All Expenses</div>
            <div style="color: #8b949e; font-size: 13px; margin-top: 4px;">
                This action is irreversible. All your expense data will be permanently deleted.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_d1, col_d2 = st.columns([1, 3])
        with col_d1:
            confirm_delete = st.checkbox("I understand this is permanent")
        if confirm_delete:
            if st.button("🗑️ Delete All My Expenses", type="primary"):
                from database.db_manager import get_connection
                conn = get_connection()
                conn.execute("DELETE FROM expenses WHERE user_id=?", (user_id,))
                conn.commit()
                conn.close()
                st.success("All expenses deleted.")
                st.rerun()