import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import (get_expenses, add_expense, update_expense,
                                  delete_expense, import_csv_expenses)
from utils.helpers import CATEGORIES, PAYMENT_MODES, format_currency
import joblib
import os

def load_category_model():
    model_path = "expense_category_model.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception:
            return None
    return None

def show_expense_manager():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">💳 Expense Manager</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Track, manage and organize your expenses</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id
    cat_model = load_category_model()

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📋 Expense History", "✏️ Edit / Delete", "📥 Import CSV"])

    # ─── TAB 1: Add Expense ───
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("<div class='section-header'>New Expense</div>", unsafe_allow_html=True)

            exp_date = st.date_input("📅 Date", value=date.today())
            notes = st.text_input("📝 Description / Notes", placeholder="e.g., Lunch at restaurant")

            # Auto-categorize if model available
            suggested_cat = CATEGORIES[0]
            if cat_model and notes:
                try:
                    pred = cat_model.predict([notes])
                    if pred[0] in CATEGORIES:
                        suggested_cat = pred[0]
                        st.info(f"🤖 AI suggests: **{suggested_cat}**")
                except Exception:
                    pass

            category = st.selectbox("🏷️ Category", CATEGORIES,
                                    index=CATEGORIES.index(suggested_cat) if suggested_cat in CATEGORIES else 0)
            amount = st.number_input("💰 Amount (₹)", min_value=0.01, step=0.01, format="%.2f")
            payment_mode = st.selectbox("💳 Payment Mode", PAYMENT_MODES)

            if st.button("➕ Add Expense", use_container_width=True):
                if amount > 0:
                    add_expense(user_id, exp_date, category, amount, payment_mode, notes)
                    st.success(f"✅ Expense of ₹{amount:,.2f} added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid amount.")

        with col2:
            st.markdown("<div class='section-header'>Recent Transactions</div>", unsafe_allow_html=True)
            recent = get_expenses(user_id).head(8)
            if not recent.empty:
                for _, row in recent.iterrows():
                    st.markdown(f"""
                    <div style="background: #161b22; border: 1px solid #21262d; border-radius: 8px;
                                padding: 10px 14px; margin: 6px 0; display: flex; justify-content: space-between;">
                        <div>
                            <div style="color: #e6edf3; font-size: 13px; font-weight: 500;">{row.get('category','')}</div>
                            <div style="color: #8b949e; font-size: 11px;">{row.get('date','')} · {row.get('payment_mode','')}</div>
                            <div style="color: #6e7681; font-size: 11px;">{str(row.get('notes',''))[:40]}</div>
                        </div>
                        <div style="color: #f85149; font-size: 15px; font-weight: 700; align-self: center;">
                            ₹{float(row.get('amount',0)):,.0f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ─── TAB 2: Expense History ───
    with tab2:
        st.markdown("<div class='section-header'>All Expenses</div>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("🔍 Search notes", placeholder="Type to search...")
        with col2:
            filter_cat = st.selectbox("Category", ["All"] + CATEGORIES, key="hist_cat")
        with col3:
            filter_pay = st.selectbox("Payment", ["All"] + PAYMENT_MODES, key="hist_pay")
        with col4:
            sort_by = st.selectbox("Sort by", ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"])

        df = get_expenses(user_id, category=filter_cat, payment_mode=filter_pay)

        if search:
            df = df[df['notes'].str.contains(search, case=False, na=False)]

        sort_map = {
            "Date ↓": ("date", False), "Date ↑": ("date", True),
            "Amount ↓": ("amount", False), "Amount ↑": ("amount", True)
        }
        sort_col, sort_asc = sort_map[sort_by]
        if not df.empty:
            df = df.sort_values(sort_col, ascending=sort_asc)

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Total", format_currency(df['amount'].sum()) if not df.empty else "₹0")
        with col_s2:
            st.metric("Transactions", len(df))
        with col_s3:
            st.metric("Avg Amount", format_currency(df['amount'].mean()) if not df.empty else "₹0")

        if not df.empty:
            display_df = df[['date', 'category', 'amount', 'payment_mode', 'notes']].copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
            display_df.columns = ['Date', 'Category', 'Amount', 'Payment Mode', 'Notes']
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info("No expenses found matching your filters.")

    # ─── TAB 3: Edit/Delete ───
    with tab3:
        st.markdown("<div class='section-header'>Edit or Delete Expense</div>", unsafe_allow_html=True)

        df_all = get_expenses(user_id)
        if df_all.empty:
            st.info("No expenses to edit.")
        else:
            df_all['label'] = df_all.apply(
                lambda r: f"[{r['date']}] {r['category']} — ₹{r['amount']:,.0f} ({r['notes'][:20] if r['notes'] else ''})",
                axis=1
            )
            selected_label = st.selectbox("Select expense to edit/delete", df_all['label'].tolist())
            selected_row = df_all[df_all['label'] == selected_label].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                e_date = st.date_input("Date", value=pd.to_datetime(selected_row['date']).date(), key="edit_date")
                e_cat = st.selectbox("Category", CATEGORIES,
                                     index=CATEGORIES.index(selected_row['category']) if selected_row['category'] in CATEGORIES else 0,
                                     key="edit_cat")
                e_amount = st.number_input("Amount", value=float(selected_row['amount']), min_value=0.01, key="edit_amt")
            with col2:
                e_pay = st.selectbox("Payment Mode", PAYMENT_MODES,
                                     index=PAYMENT_MODES.index(selected_row['payment_mode']) if selected_row['payment_mode'] in PAYMENT_MODES else 0,
                                     key="edit_pay")
                e_notes = st.text_input("Notes", value=str(selected_row['notes'] or ""), key="edit_notes")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("💾 Save Changes", use_container_width=True):
                    update_expense(int(selected_row['id']), e_date, e_cat, e_amount, e_pay, e_notes)
                    st.success("✅ Expense updated!")
                    st.rerun()
            with col_b2:
                if st.button("🗑️ Delete Expense", use_container_width=True):
                    delete_expense(int(selected_row['id']))
                    st.success("🗑️ Expense deleted!")
                    st.rerun()

    # ─── TAB 4: Import CSV ───
    with tab4:
        st.markdown("<div class='section-header'>Import Expenses from CSV</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="insight-card">
            <div class="insight-title">Expected CSV Format</div>
            <div class="insight-value">Date, Category, Amount, Payment_Mode, Notes</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file:
            try:
                df_import = pd.read_csv(uploaded_file)
                st.dataframe(df_import.head(), use_container_width=True)
                if st.button("📥 Import All Records"):
                    count = import_csv_expenses(user_id, df_import)
                    st.success(f"✅ Successfully imported {count} expense records!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")