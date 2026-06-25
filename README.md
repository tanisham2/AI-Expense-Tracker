# AI Expense Tracker & Forecasting System

An AI-powered expense analysis tool that helps users track spending, understand financial habits, and predict future expenses using machine learning.

## Features

Stores user profiles, expense records, budgets, and forecasting data in PostgreSQL via Supabase.
Supports secure cloud-based data management and retrieval using Supabase.
Categorizes expenses into Food, Travel, Health, Entertainment, Utilities, Education, Rent, Subscriptions, and Investments using machine learning classification.
Forecasts future spending for the next 15 days, 30 mdays, and 1 month months using XGBoost and Prophet.
Utilizes lag features, rolling averages, and recursive forecasting for improved prediction accuracy.
Generates monthly and yearly spending analytics with category-wise breakdowns.
Detects budget overruns, recurring expenses, and seasonal spending patterns.
Provides interactive dashboards and visualizations through Streamlit.

## Tech Stack

* Python
* Pandas
* PostgresSQL
* NumPy
* Scikit-Learn
* XGBoost
* Prophet
* Matplotlib
* Supabase
* Streamlit

## Workflow

1. Upload expense transactions or enter expenses manually.
2. Store and manage financial data using PostgreSQL (Supabase).
3. Clean and preprocess transaction records.
4. Categorize expenses using machine learning models.
5. Generate spending insights and visualizations.
6. Forecast future expenses using XGBoost and Prophet.
7. Monitor budgets and spending trends through interactive dashboards.

## Future Improvements

* Bank account integration
* Personalized saving recommendations
* Real-time expense tracking
* Mobile application support
  

## Live Demo

Frontend:
https://fintrack-ai-app.streamlit.app/

Backend API:
https://fintrack-ai-api.onrender.com

API Documentation:
https://fintrack-ai-api.onrender.com/docs
