import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_manager import get_expenses, get_budget, set_budget
from utils.helpers import format_currency, CATEGORIES

def show_budget_planner():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">💰 Budget Planner</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Set and track your spending budgets</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id
    current_month = datetime.now().strftime("%Y-%m")
    month_label = datetime.now().strftime("%B %Y")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown(f"<div class='section-header'>Set Budget — {month_label}</div>", unsafe_allow_html=True)

        # Overall monthly budget
        with st.expander("💼 Overall Monthly Budget", expanded=True):
            overall_budget = st.number_input(
                "Total Monthly Budget (₹)", min_value=0.0, step=1000.0, key="overall_budget"
            )
            if st.button("Set Overall Budget"):
                set_budget(user_id, current_month, "Overall", overall_budget)
                st.success("✅ Overall budget set!")
                st.rerun()

        # Category budgets
        with st.expander("🏷️ Category Budgets", expanded=True):
            selected_cat = st.selectbox("Category", CATEGORIES, key="budget_cat_select")
            cat_budget = st.number_input(f"Budget for {selected_cat} (₹)", min_value=0.0, step=100.0, key="cat_budget")
            if st.button("Set Category Budget"):
                set_budget(user_id, current_month, selected_cat, cat_budget)
                st.success(f"✅ Budget set for {selected_cat}!")
                st.rerun()

    with col_right:
        st.markdown(f"<div class='section-header'>Budget Utilization — {month_label}</div>", unsafe_allow_html=True)

        # Get this month's expenses
        month_start = datetime.now().replace(day=1).date()
        df = get_expenses(user_id, start_date=month_start)
        budgets_df = get_budget(user_id, current_month)

        if budgets_df.empty:
            st.markdown("""
            <div class="insight-card">
                <div class="insight-title">No budgets set</div>
                <div class="insight-value">Use the panel on the left to set your monthly budgets.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Overall budget check
            overall_row = budgets_df[budgets_df['category'] == 'Overall']
            if not overall_row.empty:
                overall_limit = float(overall_row.iloc[0]['budget_amount'])
                total_spent = df['amount'].sum() if not df.empty else 0
                pct = min((total_spent / overall_limit * 100), 100) if overall_limit > 0 else 0
                color = "#3fb950" if pct < 70 else "#e3b341" if pct < 90 else "#f85149"

                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 16px; text-align: left;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #e6edf3; font-weight: 600; font-size: 15px;">💼 Overall Monthly Budget</div>
                            <div style="color: #8b949e; font-size: 12px;">
                                {format_currency(total_spent)} spent of {format_currency(overall_limit)}
                            </div>
                        </div>
                        <div style="font-size: 22px; font-weight: 700; color: {color};">{pct:.1f}%</div>
                    </div>
                    <div class="budget-progress" style="margin-top: 10px;">
                        <div class="budget-bar" style="width: {pct}%; background: {color};"></div>
                    </div>
                    <div style="color: {'#f85149' if pct >= 100 else '#3fb950'}; font-size: 12px; margin-top: 6px;">
                        {'⚠️ OVER BUDGET by ' + format_currency(total_spent - overall_limit) if pct >= 100
                         else '✅ ' + format_currency(overall_limit - total_spent) + ' remaining'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Category budgets
            cat_budgets = budgets_df[budgets_df['category'] != 'Overall']
            if not cat_budgets.empty:
                st.markdown("<div style='color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin: 12px 0 8px;'>Category Budgets</div>", unsafe_allow_html=True)
                for _, budget_row in cat_budgets.iterrows():
                    cat = budget_row['category']
                    limit = float(budget_row['budget_amount'])
                    spent = float(df[df['category'] == cat]['amount'].sum()) if not df.empty else 0
                    pct = min((spent / limit * 100), 100) if limit > 0 else 0
                    color = "#3fb950" if pct < 70 else "#e3b341" if pct < 90 else "#f85149"
                    remaining = limit - spent

                    st.markdown(f"""
                    <div style="background: #161b22; border: 1px solid #21262d; border-radius: 8px;
                                padding: 12px 14px; margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #e6edf3; font-size: 13px; font-weight: 500;">{cat}</span>
                            <span style="color: {color}; font-size: 13px; font-weight: 600;">{pct:.0f}%</span>
                        </div>
                        <div style="color: #8b949e; font-size: 11px; margin: 3px 0 6px;">
                            ₹{spent:,.0f} / ₹{limit:,.0f}
                        </div>
                        <div class="budget-progress">
                            <div class="budget-bar" style="width: {pct}%; background: {color};"></div>
                        </div>
                        <div style="color: {'#f85149' if remaining < 0 else '#6e7681'}; font-size: 11px; margin-top: 5px;">
                            {'⚠️ Over by ₹' + f'{abs(remaining):,.0f}' if remaining < 0 else f'₹{remaining:,.0f} left'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Overspending Alerts
    if not df.empty and not budgets_df.empty:
        alerts = []
        for _, br in budgets_df.iterrows():
            cat = br['category']
            limit = float(br['budget_amount'])
            if cat == 'Overall':
                spent = df['amount'].sum()
            else:
                spent = float(df[df['category'] == cat]['amount'].sum())
            if spent > limit * 0.9:
                alerts.append((cat, spent, limit))

        if alerts:
            st.markdown("<div class='section-header'>⚠️ Alerts</div>", unsafe_allow_html=True)
            for cat, spent, limit in alerts:
                pct = spent / limit * 100
                st.markdown(f"""
                <div class="alert-card">
                    <div style="color: #e6edf3; font-weight: 600;">
                        {'🚨 Over Budget' if pct >= 100 else '⚠️ Approaching Limit'} — {cat}
                    </div>
                    <div style="color: #8b949e; font-size: 13px; margin-top: 4px;">
                        Spent {format_currency(spent)} of {format_currency(limit)} budget ({pct:.1f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)