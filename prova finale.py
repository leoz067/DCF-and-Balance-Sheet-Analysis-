import streamlit as st
import yfinance as yf
import pandas as pd
import re
import requests
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Balance Sheet Analyzer & Valuation", layout="wide")

# Initialize session state variables
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'ticker' not in st.session_state:
    st.session_state.ticker = ''
if 'annual_balance_sheet' not in st.session_state:
    st.session_state.annual_balance_sheet = None
if 'balance_mapping_user' not in st.session_state:
    st.session_state.balance_mapping_user = None
if 'df_balance_ts' not in st.session_state:
    st.session_state.df_balance_ts = None
if 'net_cash' not in st.session_state:
    st.session_state.net_cash = None
if 'annual_income_statement' not in st.session_state:
    st.session_state.annual_income_statement = None
if 'ttm_data' not in st.session_state:
    st.session_state.ttm_data = None
if 'forecast' not in st.session_state:
    st.session_state.forecast = None
if 'valuation_results' not in st.session_state:
    st.session_state.valuation_results = None
if 'ttm_series' not in st.session_state:
    st.session_state.ttm_series = None
if 'phase1_years' not in st.session_state:
    st.session_state.phase1_years = 5
if 'phase1_growth_rate' not in st.session_state:
    st.session_state.phase1_growth_rate = 0.10
if 'phase2_years' not in st.session_state:
    st.session_state.phase2_years = 5
if 'phase2_growth_rate' not in st.session_state:
    st.session_state.phase2_growth_rate = 0.05


st.title("💰 Balance Sheet Analyzer & DCF Valuation")
st.write("Analisi del Balance Sheet e DCF Valuation da Yahoo Finance")

###############################################
# DEMO DATA
###############################################

# Sample data for demo mode when API is rate limited
DEMO_COMPANY_INFO = {
    "AAPL": {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currentPrice": 174.79,
        "marketCap": 2740000000000,
        "logo_url": "https://logo.clearbit.com/apple.com"
    },
    "MSFT": {
        "longName": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software—Infrastructure",
        "currentPrice": 403.78,
        "marketCap": 3000000000000,
        "logo_url": "https://logo.clearbit.com/microsoft.com"
    },
    "GOOGL": {
        "longName": "Alphabet Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "currentPrice": 153.05,
        "marketCap": 1900000000000,
        "logo_url": "https://logo.clearbit.com/google.com"
    }
}

# Sample financial data structure for demo mode
DEMO_BALANCE_SHEET_DATA = {
    "AAPL": {
        "financials": {
            "Cash and Cash Equivalents": [35950000000, 27502000000, 34940000000, 38016000000],
            "Short Term Investments": [28735000000, 24658000000, 26670000000, 53927000000],
            "Cash Cash Equivalents And Short Term Investments": [64685000000, 52160000000, 61610000000, 91943000000],
            "Total Assets": [352755000000, 335024000000, 323888000000, 338516000000],
            "Accounts Payable": [47500000000, 55381000000, 54763000000, 42296000000],
            "Short Term Debt": [13494000000, 11128000000, 10000000000, 8773000000],
            "Long Term Debt": [95281000000, 110000000000, 109106000000, 98667000000],
            "Total Debt": [108775000000, 121128000000, 119106000000, 107440000000],
            "Total Liabilities Net Minority Interest": [267998000000, 261384000000, 250027000000, 258549000000],
            "Total Equity": [84757000000, 73640000000, 73861000000, 79967000000],
            "Total Equity Gross Minority Interest": [84757000000, 73640000000, 73861000000, 79967000000],
            "Total Capital": [193532000000, 194768000000, 192967000000, 187407000000],
            "Capital Lease Obligations": [11558000000, 12431000000, 11742000000, 9729000000],
            "Net Debt": [44090000000, 68968000000, 57496000000, 15497000000],
            "Inventory": [7018000000, 6296000000, 6580000000, 4061000000],
            "Prepaid Expenses": [13440000000, 15614000000, 14545000000, 11180000000],
            "Property Plant Equipment Net": [43715000000, 40335000000, 39440000000, 36766000000],
            "Goodwill": [0, 0, 0, 0],
            "Intangible Assets": [0, 0, 0, 0]
        },
        "dates": ["2023-09-30", "2022-09-30", "2021-09-30", "2020-09-30"]
    },
    "MSFT": {
        "financials": {
            "Cash and Cash Equivalents": [34704000000, 13931000000, 14224000000, 13576000000],
            "Short Term Investments": [81042000000, 90826000000, 116110000000, 122844000000],
            "Cash Cash Equivalents And Short Term Investments": [115746000000, 104757000000, 130334000000, 136527000000],
            "Total Assets": [409409000000, 364840000000, 333779000000, 301311000000],
            "Accounts Payable": [17515000000, 19000000000, 15163000000, 12530000000],
            "Short Term Debt": [3749000000, 2749000000, 8072000000, 3749000000],
            "Long Term Debt": [59931000000, 47032000000, 50074000000, 55071000000],
            "Total Debt": [63680000000, 49781000000, 58146000000, 58820000000],
            "Total Liabilities Net Minority Interest": [198291000000, 198860000000, 193694000000, 183007000000],
            "Total Equity": [211118000000, 166542000000, 141988000000, 118304000000],
            "Total Equity Gross Minority Interest": [211118000000, 166542000000, 141988000000, 118304000000],
            "Total Capital": [274798000000, 216323000000, 200134000000, 177124000000],
            "Capital Lease Obligations": [13351000000, 11489000000, 10092000000, 8575000000],
            "Net Debt": [-52066000000, -54976000000, -72188000000, -77707000000],
            "Inventory": [3360000000, 3742000000, 2636000000, 1895000000],
            "Prepaid Expenses": [16924000000, 16924000000, 13393000000, 12247000000],
            "Property Plant Equipment Net": [94823000000, 74398000000, 59715000000, 44151000000],
            "Goodwill": [67903000000, 69045000000, 49711000000, 43351000000],
            "Intangible Assets": [12451000000, 11297000000, 7800000000, 7038000000]
        },
        "dates": ["2023-06-30", "2022-06-30", "2021-06-30", "2020-06-30"]
    }
}

DEMO_INCOME_DATA = {
    "AAPL": {
        "financials": {
            "Total Revenue": [394328000000, 365817000000, 274515000000, 260174000000],
            "Cost Of Revenue": [226107000000, 208168000000, 152836000000, 161782000000],
            "Gross Profit": [168221000000, 157649000000, 121679000000, 98392000000],
            "Selling General And Administration": [26474000000, 25094000000, 21973000000, 19916000000],
            "Research And Development": [29915000000, 26251000000, 21914000000, 18752000000],
            "Operating Income": [111832000000, 109552000000, 94680000000, 66288000000],
            "Pretax Income": [113645000000, 109272000000, 94680000000, 67091000000],
            "Income Tax Expense": [18573000000, 14089000000, 14527000000, 9680000000],
            "Net Income": [95025000000, 99803000000, 94680000000, 57411000000],
            "Diluted EPS": [6.14, 6.11, 5.61, 3.28]
        },
        "dates": ["2023-09-30", "2022-09-30", "2021-09-30", "2020-09-30"],
        "quarterly": {
            "Total Revenue": [119575000000, 81797000000, 84310000000, 117154000000],
            "Cost Of Revenue": [70731000000, 45407000000, 46761000000, 63502000000],
            "Gross Profit": [48844000000, 36390000000, 37549000000, 53652000000],
            "Selling General And Administration": [6520000000, 6177000000, 6636000000, 6659000000],
            "Research And Development": [8146000000, 7308000000, 7442000000, 7489000000],
            "Operating Income": [34178000000, 22905000000, 23471000000, 39504000000],
            "Pretax Income": [34874000000, 23036000000, 23752000000, 40009000000],
            "Income Tax Expense": [5218000000, 4697000000, 3385000000, 6300000000],
            "Net Income": [29656000000, 18339000000, 20367000000, 33709000000],
            "Diluted EPS": [1.93, 1.18, 1.30, 2.15]
        },
        "ttm": {
            "Total Revenue": [394328000000],
            "Cost Of Revenue": [226107000000],
            "Gross Profit": [168221000000],
            "Selling General And Administration": [26474000000],
            "Research And Development": [29915000000],
            "Operating Income": [111832000000],
            "Pretax Income": [113645000000],
            "Income Tax Expense": [18573000000],
            "Net Income": [95025000000],
            "Diluted EPS": [6.14],
            "Shares": [15634710000]
        }
    },
    "MSFT": {
        "financials": {
            "Total Revenue": [211915000000, 198270000000, 168088000000, 143015000000],
            "Cost Of Revenue": [70950000000, 65812000000, 52232000000, 46078000000],
            "Gross Profit": [140965000000, 132458000000, 115856000000, 96937000000],
            "Selling General And Administration": [42513000000, 39585000000, 35327000000, 29539000000],
            "Research And Development": [27155000000, 24512000000, 20716000000, 19269000000],
            "Operating Income": [88389000000, 83383000000, 69916000000, 52959000000],
            "Pretax Income": [88092000000, 83386000000, 71102000000, 53036000000],
            "Income Tax Expense": [10605000000, 10978000000, 9831000000, 8755000000],
            "Net Income": [77487000000, 72738000000, 61271000000, 44281000000],
            "Diluted EPS": [10.31, 9.65, 8.05, 5.76]
        },
        "dates": ["2023-06-30", "2022-06-30", "2021-06-30", "2020-06-30"],
        "quarterly": {
            "Total Revenue": [56521000000, 56194000000, 57700000000, 53203000000],
            "Cost Of Revenue": [19376000000, 19114000000, 19914000000, 17483000000],
            "Gross Profit": [37145000000, 37080000000, 37786000000, 35720000000],
            "Selling General And Administration": [11623000000, 10927000000, 13010000000, 11430000000],
            "Research And Development": [7446000000, 7368000000, 6620000000, 6700000000],
            "Operating Income": [18076000000, 18785000000, 18156000000, 17590000000],
            "Pretax Income": [17961000000, 19108000000, 18294000000, 17756000000],
            "Income Tax Expense": [2149000000, 2528000000, 1644000000, 2293000000],
            "Net Income": [15812000000, 16580000000, 16650000000, 15463000000],
            "Diluted EPS": [2.11, 2.21, 2.22, 2.05]
        },
        "ttm": {
            "Total Revenue": [223618000000],
            "Cost Of Revenue": [75887000000],
            "Gross Profit": [147731000000],
            "Selling General And Administration": [46990000000],
            "Research And Development": [28134000000],
            "Operating Income": [72607000000],
            "Pretax Income": [73119000000],
            "Income Tax Expense": [8614000000],
            "Net Income": [64505000000],
            "Diluted EPS": [8.59],
            "Shares": [7512380000]
        }
    }
}

# Function to get demo financial data
def get_demo_financial_data(ticker, data_type="balance"):
    """Get demo financial data for a ticker"""
    if data_type == "balance":
        if ticker in DEMO_BALANCE_SHEET_DATA:
            return DEMO_BALANCE_SHEET_DATA[ticker]
        # Default to AAPL if ticker not in demo data
        return DEMO_BALANCE_SHEET_DATA["AAPL"]
    elif data_type == "income":
        if ticker in DEMO_INCOME_DATA:
            return DEMO_INCOME_DATA[ticker]
        # Default to AAPL if ticker not in demo data
        return DEMO_INCOME_DATA["AAPL"]

# Function to get demo company info
def get_demo_company_info(ticker):
    """Get demo company info for a ticker"""
    if ticker in DEMO_COMPANY_INFO:
        return DEMO_COMPANY_INFO[ticker]
    # Default to AAPL if ticker not in demo data
    return DEMO_COMPANY_INFO["AAPL"]

###############################################
# CONFIGURAZIONE – Balance Sheet Mapping
###############################################

config = {
    "balance_mapping": {
        "Cash": [
            "Cash and Cash Equivalents",
            "Cash Cash Equivalents And Short Term Investments",
            "Short Term Investments",
            "Long Term Investments"
        ],
        "A/P": ["Accounts Payable"],
        "Short Term Debt": ["Short Term Debt", "Short Long Term Debt"],
        "Long Term Debt": ["Long Term Debt"],
        "Total Debt": ["Total Debt"],
        "D/R": ["Deferred Revenue"],
        "OL": ["Other Liabilities"],
        "S/E": ["Total Equity", "Total Equity Gross Minority Interest"],
        "L+S/E": ["Total Liabilities Net Minority Interest"],
        "Net Debt": ["Net Debt"],
        "Capital Lease Obligations": ["Capital Lease Obligations"],
        "Inventories": ["Inventory"],
        "Prepaids": ["Prepaid Expenses"],
        "PP&E NET": ["Property Plant Equipment Net"],
        "Goodwill": ["Goodwill"],
        "Intangibles": ["Intangible Assets"]
    }
}

###############################################
# FUNZIONE DI CREAZIONE GRAFICI CON PLOTLY
###############################################

def create_balance_charts(df, income_data=None):
    """Create charts from the balance sheet data and income data"""
    # Create a copy for chart formatting
    chart_df = df.copy()
    
    # 1. Cash & Debt Chart
    fig1 = go.Figure()
    
    if "Cash" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Cash"],
            name="Cash",
            marker_color='rgb(53, 201, 132)'  # Green
        ))
    
    if "Total Debt" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Total Debt"] * -1,  # Negative to show below x-axis
            name="Total Debt",
            marker_color='rgb(235, 83, 83)'  # Red
        ))
    
    if "Net Cash" in chart_df.columns:
        fig1.add_trace(go.Scatter(
            x=chart_df.index,
            y=chart_df["Net Cash"],
            mode='lines+markers',
            name="Net Cash",
            marker_color='rgb(55, 126, 184)'  # Blue
        ))
    
    fig1.update_layout(
        title="Cash & Debt (in millions)",
        xaxis_title="Year",
        yaxis_title="Amount (in millions)",
        barmode='relative',
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 2. Assets Composition Chart
    fig2 = go.Figure()
    
    asset_columns = ["Cash", "Inventories", "PP&E NET", "Goodwill", "Intangibles"]
    asset_colors = ['rgb(53, 201, 132)', 'rgb(254, 204, 92)', 'rgb(55, 126, 184)', 'rgb(141, 85, 173)', 'rgb(235, 83, 83)']
    
    for i, col in enumerate([c for c in asset_columns if c in chart_df.columns]):
        fig2.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df[col],
            name=col,
            marker_color=asset_colors[i % len(asset_colors)]
        ))
    
    fig2.update_layout(
        title="Assets Composition (in millions)",
        xaxis_title="Year",
        yaxis_title="Amount (in millions)",
        barmode='stack',
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 3. Tax Percentage Chart (New)
    fig3 = None
    if income_data is not None and not income_data.empty:
        # Create tax percentage chart if income data is available
        fig3 = go.Figure()
        
        # Check if necessary columns exist
        if "Taxes" in income_data.columns and "Pretax Income" in income_data.columns:
            # Calculate tax percentage
            income_data_copy = income_data.copy()
            income_data_copy['Tax Percentage'] = (income_data_copy['Taxes'] / income_data_copy['Pretax Income']) * 100
            
            # Add tax percentage line
            fig3.add_trace(go.Scatter(
                x=income_data_copy.index,
                y=income_data_copy['Tax Percentage'],
                mode='lines+markers',
                name="Tax Percentage",
                marker_color='rgb(255, 127, 14)'  # Orange
            ))
            
            # Check if gross margin exists
            if "Gross Margin" in income_data_copy.columns:
                fig3.add_trace(go.Scatter(
                    x=income_data_copy.index,
                    y=income_data_copy['Gross Margin'],
                    mode='lines+markers',
                    name="Gross Margin",
                    marker_color='rgb(44, 160, 44)'  # Green
                ))
            
            # Check if net margin exists or can be calculated
            if "Net Income" in income_data_copy.columns and "Revenue" in income_data_copy.columns:
                income_data_copy['Net Margin'] = (income_data_copy['Net Income'] / income_data_copy['Revenue']) * 100
                fig3.add_trace(go.Scatter(
                    x=income_data_copy.index,
                    y=income_data_copy['Net Margin'],
                    mode='lines+markers',
                    name="Net Margin",
                    marker_color='rgb(31, 119, 180)'  # Blue
                ))
            
            fig3.update_layout(
                title="Margin & Tax Percentage Analysis",
                xaxis_title="Year",
                yaxis_title="Percentage (%)",
                legend=dict(x=0, y=1.0),
                template="plotly_white"
            )
    
    if fig3 is not None:
        return fig1, fig2, fig3
    else:
        return fig1, fig2

def create_forecast_charts(df):
    """Create charts from the forecast data"""
    # Create a copy for chart formatting
    chart_df = df.copy()
    
    # 1. Revenue & Net Income Forecast
    fig1 = go.Figure()
    
    if "Revenue" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Revenue"] / 1e6,  # Convert to millions
            name="Revenue",
            marker_color='rgb(55, 83, 109)'
        ))
    
    if "Net Income" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Net Income"] / 1e6,  # Convert to millions
            name="Net Income",
            marker_color='rgb(26, 118, 255)'
        ))
    
    fig1.update_layout(
        title="Revenue & Net Income Forecast (in millions)",
        xaxis_title="Year",
        yaxis_title="Amount (in millions)",
        barmode='group',
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 2. Operating Expenses Forecast
    fig2 = go.Figure()
    
    expense_columns = ["SG&A", "R&D", "S&M"]
    expense_colors = ['rgb(235, 83, 83)', 'rgb(254, 204, 92)', 'rgb(55, 126, 184)']
    
    for i, col in enumerate([c for c in expense_columns if c in chart_df.columns]):
        fig2.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df[col] / 1e6,  # Convert to millions
            name=col,
            marker_color=expense_colors[i % len(expense_colors)]
        ))
    
    fig2.update_layout(
        title="Operating Expenses Forecast (in millions)",
        xaxis_title="Year",
        yaxis_title="Amount (in millions)",
        barmode='stack',
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 3. NPV Cumulative Chart
    cumulative_npv = []
    discount_rate = 0.05  # Default value, should match user input
    current_npv = 0
    
    for year in chart_df.index:
        current_npv += chart_df.loc[year, "Net Income"] / ((1 + discount_rate) ** year)
        cumulative_npv.append(current_npv / 1e6)  # Convert to millions
    
    fig3 = go.Figure()
    
    fig3.add_trace(go.Scatter(
        x=chart_df.index,
        y=cumulative_npv,
        mode='lines+markers',
        name="Cumulative NPV",
        fill='tozeroy',
        marker_color='rgb(53, 201, 132)'
    ))
    
    fig3.update_layout(
        title="Cumulative NPV of Forecast (in millions)",
        xaxis_title="Year",
        yaxis_title="NPV (in millions)",
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    return fig1, fig2, fig3

###############################################
# FUNZIONE DI NAVIGAZIONE
###############################################

def render_navigation_bar():
    """Render navigation buttons to move back and forth between steps"""
    st.markdown("---")
    
    # Define steps in order
    steps = [
        'input', 
        'load_balance_sheet', 
        'balance_mapping', 
        'balance_mapping_config', 
        'process_balance_sheet', 
        'load_income_statement', 
        'forecast_setup', 
        'show_results'
    ]
    
    # Define visible steps (steps shown in the navigation bar)
    visible_steps = [
        'input',
        'balance_mapping',
        'balance_mapping_config',
        'process_balance_sheet',
        'load_income_statement',  # Add this to visible steps
        'forecast_setup',
        'show_results'
    ]
    
    # Get current step index
    current_step_index = steps.index(st.session_state.step)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    
    # Previous button
    with col1:
        if current_step_index > 0:
            if st.button("⬅️ Indietro"):
                # Some steps require data loading, so we skip back to the previous user input step
                if current_step_index > 1:  # Skip data loading steps
                    if steps[current_step_index-1] == 'load_balance_sheet':
                        st.session_state.step = 'input'
                    elif steps[current_step_index-1] == 'load_income_statement':
                        st.session_state.step = 'process_balance_sheet'
                    else:
                        st.session_state.step = steps[current_step_index-1]
                else:
                    st.session_state.step = steps[current_step_index-1]
                st.rerun()
    
    # Step indicator
    with col2:
        # Generate step names for display
        step_names = {
            'input': 'Selezione Ticker',
            'load_balance_sheet': 'Caricamento Balance Sheet',
            'balance_mapping': 'Mapping Balance Sheet',
            'balance_mapping_config': 'Configurazione Mapping',
            'process_balance_sheet': 'Analisi Balance Sheet',
            'load_income_statement': 'Caricamento Income Statement',
            'forecast_setup': 'Configurazione Forecast',
            'show_results': 'Risultati Valutazione'
        }
        
        # Show progress and current step
        progress_text = " → ".join([
            f"**{step_names[step]}**" if step == st.session_state.step else step_names[step] 
            for step in visible_steps  # Use visible_steps instead of filtering steps
        ])
        st.markdown(f"<div style='text-align: center'>{progress_text}</div>", unsafe_allow_html=True)
        
        # Show progress bar
        if st.session_state.step in visible_steps:
            current_visible_index = visible_steps.index(st.session_state.step)
            st.progress(current_visible_index / (len(visible_steps) - 1))
        else:
            # Fallback for steps not in visible_steps
            st.progress(0)
    
    # Next button (only for specific steps where it makes sense)
    with col3:
        if st.session_state.step in ['balance_mapping', 'process_balance_sheet', 'forecast_setup']:
            next_step_map = {
                'balance_mapping': 'balance_mapping_config',
                'process_balance_sheet': 'load_income_statement',
                'forecast_setup': 'show_results'
            }
            
            if st.button("Avanti ➡️"):
                st.session_state.step = next_step_map[st.session_state.step]
                st.rerun()

###############################################
# FUNZIONI DI MAPPING E VALUTAZIONE
###############################################

def transform_expr(user_input, available):
    """
    Sostituisce ogni numero (indice) nell'input con il nome della colonna corrispondente
    (racchiuso tra backtick), basandosi sulla lista available.
    """
    # Check if the input is just a single number
    if user_input.strip().isdigit():
        idx = int(user_input.strip())
        if 1 <= idx <= len(available):
            return available[idx-1]
        else:
            # Return the input as is if the index is out of range
            return user_input
    
    # For more complex expressions, replace each number with the corresponding column name
    def repl(match):
        idx = int(match.group(0))
        if 1 <= idx <= len(available):
            return f"`{available[idx-1]}`"
        else:
            return match.group(0)
    
    # Use regex to find all standalone digits in the expression
    return re.sub(r'\b\d+\b', repl, user_input)

def display_candidates_with_values(df, candidate_list, quarterly_df=None):
    """
    Visualizza le colonne candidate con i loro valori per l'ultimo trimestre disponibile.
    Se i dati trimestrali non sono disponibili, usa l'ultimo anno.
    
    Args:
        df: DataFrame con i dati annuali
        candidate_list: Lista di colonne candidate
        quarterly_df: DataFrame con i dati trimestrali (opzionale)
    """
    if df.empty:
        return {}
    
    # Determina quale DataFrame usare per i valori
    display_df = quarterly_df if quarterly_df is not None else df
    latest = display_df.iloc[0]  # Prima riga (più recente)
    
    # Indica la fonte dei dati per migliore comprensione
    source = "trimestre" if quarterly_df is not None else "anno"
    st.info(f"I valori mostrati sono dell'ultimo {source} disponibile")
    
    results = {}
    for i, col in enumerate(candidate_list, start=1):
        try:
            # Verifica se la colonna esiste
            if col in display_df.columns:
                # Accedi al valore
                raw_value = latest[col]
                
                # Formatta il valore in base al tipo
                if pd.notna(raw_value):
                    if isinstance(raw_value, (int, float)):
                        formatted_value = f"${raw_value/1e6:.2f}M"
                    else:
                        # Tenta conversione a float se è una stringa
                        try:
                            num_value = float(raw_value)
                            formatted_value = f"${num_value/1e6:.2f}M"
                        except (ValueError, TypeError):
                            formatted_value = str(raw_value)
                else:
                    formatted_value = "N/A"
            else:
                # Ricerca flessibile
                found = False
                for df_col in display_df.columns:
                    if col.lower() == df_col.lower():
                        raw_value = latest[df_col]
                        if pd.notna(raw_value):
                            if isinstance(raw_value, (int, float)):
                                formatted_value = f"${raw_value/1e6:.2f}M"
                            else:
                                try:
                                    num_value = float(raw_value)
                                    formatted_value = f"${num_value/1e6:.2f}M"
                                except (ValueError, TypeError):
                                    formatted_value = str(raw_value)
                        else:
                            formatted_value = "N/A"
                        found = True
                        break
                
                if not found:
                    formatted_value = "N/A"
        except Exception as e:
            formatted_value = "N/A"
        
        results[i] = {"col": col, "value": formatted_value}
    
    return results

def streamlit_mapping_complex(df, mapping_config):
    """
    Versione migliorata che usa i dati trimestrali per visualizzare i valori
    e per calcolare le espressioni personalizzate.
    """
    new_mapping = {}
    
    st.subheader("Mapping Interattivo (Balance Sheet)")
    
    # Ottieni i dati trimestrali, se disponibili
    quarterly_df = st.session_state.quarterly_data if 'quarterly_data' in st.session_state else None
    
    with st.expander("Colonne disponibili nel bilancio", expanded=True):
        # Determina quale DataFrame usare per visualizzare i valori
        display_df = quarterly_df if quarterly_df is not None else df
        latest_values = display_df.iloc[0] if not display_df.empty else pd.Series()
        
        # Crea una tabella per visualizzare tutte le colonne con i loro valori
        cols_data = []
        for i, col in enumerate(df.columns, start=1):
            try:
                # Verifica se la colonna esiste anche nei dati trimestrali
                if quarterly_df is not None and col in quarterly_df.columns:
                    raw_value = latest_values[col]
                else:
                    # Fallback ai dati annuali se la colonna non esiste nei trimestrali
                    raw_value = df.iloc[0][col] if col in df.columns else None
                
                # Formatta il valore
                if pd.isna(raw_value):
                    formatted_value = "N/A"
                elif isinstance(raw_value, (int, float)):
                    formatted_value = f"${raw_value/1e6:.2f}M"
                else:
                    try:
                        num_value = float(raw_value)
                        formatted_value = f"${num_value/1e6:.2f}M"
                    except (ValueError, TypeError):
                        formatted_value = str(raw_value)
            except Exception:
                formatted_value = "N/A"
            
            cols_data.append({
                "Indice": i,
                "Colonna": col,
                "Valore Ultimo Periodo": formatted_value
            })
        
        cols_df = pd.DataFrame(cols_data)
        st.dataframe(cols_df, hide_index=True)
    
    for target, candidates in mapping_config.items():
        available = [cand for cand in candidates if cand in df.columns]
        
        st.write(f"### Mapping per '{target}'")
        
        if not available:
            st.warning(f"Nessuna delle candidate predefinite è stata trovata. Verrà usato l'intero elenco disponibile.")
            available = list(df.columns)
            candidates_info = display_candidates_with_values(df, available, quarterly_df)
            default_value = available[0] if available else None
        else:
            st.success(f"Candidate trovate: {', '.join(available)}")
            candidates_info = display_candidates_with_values(df, available, quarterly_df)
            default_value = available[0] if available else None
        
        # Chiavi univoche per ogni input
        target_key = f"mapping_{target}"
        method_key = f"method_{target}"
        select_key = f"select_{target}"
        expr_key = f"expr_{target}"
        
        if method_key not in st.session_state:
            st.session_state[method_key] = "Usa prima opzione disponibile"
        if select_key not in st.session_state:
            st.session_state[select_key] = default_value
        if expr_key not in st.session_state:
            st.session_state[expr_key] = ""
        
        mapping_method = st.radio(
            f"Scegli il metodo di mapping per '{target}':",
            ["Usa prima opzione disponibile", "Seleziona da lista", "Espressione personalizzata"],
            key=method_key
        )
        
        if mapping_method == "Usa prima opzione disponibile":
            if default_value:
                new_mapping[target] = default_value
                default_value_idx = available.index(default_value) + 1
                st.info(f"Verrà usato: {default_value} ({candidates_info[default_value_idx]['value']})")
            else:
                st.error("Nessuna opzione disponibile")
                new_mapping[target] = None
        
        elif mapping_method == "Seleziona da lista":
            if available:
                # Crea una lista di opzioni con i valori inclusi
                options_with_values = [f"{col} ({candidates_info[i+1]['value']})" for i, col in enumerate(available)]
                selected_index = 0
                
                if select_key in st.session_state and st.session_state[select_key] in available:
                    selected_index = available.index(st.session_state[select_key])
                
                selected_option_with_value = st.selectbox(
                    f"Seleziona l'opzione per '{target}':",
                    options_with_values,
                    index=selected_index,
                    key=f"{select_key}_with_value"
                )
                
                # Estrai il nome della colonna dal testo selezionato
                selected_option = selected_option_with_value.split(" (")[0]
                st.session_state[select_key] = selected_option
                new_mapping[target] = selected_option
            else:
                st.error("Nessuna opzione disponibile")
                new_mapping[target] = None
        
        elif mapping_method == "Espressione personalizzata":
            st.write("Opzioni disponibili per l'espressione:")
            
            # Crea la tabella delle opzioni con i valori
            options_data = []
            for i, col in enumerate(available, start=1):
                options_data.append({
                    "Indice": i,
                    "Colonna": col,
                    "Valore Ultimo Periodo": candidates_info[i]["value"]
                })
            
            options_df = pd.DataFrame(options_data)
            st.dataframe(options_df, hide_index=True)
            
            st.info("Puoi inserire un singolo numero (es. '1') per selezionare direttamente una colonna, oppure un'espressione matematica usando gli indici (es. '1+2-3').")
            
            expr_input = st.text_input(
                f"Inserisci un'espressione per '{target}':",
                key=expr_key
            )
            
            if expr_input:
                # Se l'input è un singolo numero, seleziona la colonna corrispondente
                if expr_input.strip().isdigit():
                    idx = int(expr_input.strip())
                    if 1 <= idx <= len(available):
                        new_mapping[target] = available[idx-1]
                        st.info(f"Colonna selezionata: {available[idx-1]} ({candidates_info[idx]['value']})")
                    else:
                        st.error(f"Indice fuori range. Inserisci un numero tra 1 e {len(available)}.")
                        if default_value:
                            new_mapping[target] = default_value
                            default_value_idx = available.index(default_value) + 1
                            st.info(f"Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                        else:
                            new_mapping[target] = None
                # Se è un'espressione aritmetica
                elif any(op in expr_input for op in ['+', '-', '*', '/']):
                    transformed = transform_expr(expr_input, available)
                    new_mapping[target] = transformed
                    st.info(f"Espressione trasformata: {transformed}")
                    
                    # Calcola il valore dell'espressione utilizzando i dati trimestrali se disponibili
                    try:
                        # Scegli quale DataFrame usare per calcolare l'anteprima
                        calc_df = quarterly_df if quarterly_df is not None else df
                        latest_row = {col: float(calc_df.iloc[0][col]) if col in calc_df.iloc[0] and pd.notna(calc_df.iloc[0][col]) else 0 
                                     for col in calc_df.columns}
                        
                        # Sostituisci i nomi di colonna con i valori
                        expr_with_values = transformed
                        for col in calc_df.columns:
                            if f"`{col}`" in expr_with_values:
                                value = latest_row.get(col, 0)
                                expr_with_values = expr_with_values.replace(f"`{col}`", str(value))
                        
                        # Valuta l'espressione
                        result = eval(expr_with_values)
                        period_type = "trimestre" if quarterly_df is not None else "anno"
                        st.success(f"Valore calcolato (ultimo {period_type}): ${result/1e6:.2f}M")
                    except Exception as e:
                        st.warning(f"Non è possibile calcolare il valore dell'espressione: {e}")
                else:
                    # Potrebbe essere un nome di colonna diretto
                    if expr_input in df.columns:
                        new_mapping[target] = expr_input
                        
                        # Ottieni il valore dai dati trimestrali se disponibili
                        if quarterly_df is not None and expr_input in quarterly_df.columns:
                            value = float(quarterly_df.iloc[0][expr_input]) if pd.notna(quarterly_df.iloc[0][expr_input]) else None
                        else:
                            value = float(df.iloc[0][expr_input]) if pd.notna(df.iloc[0][expr_input]) else None
                            
                        formatted_value = f"${value/1e6:.2f}M" if value is not None else "N/A"
                        period_type = "trimestre" if quarterly_df is not None and expr_input in quarterly_df.columns else "anno"
                        st.info(f"Colonna selezionata direttamente: {expr_input} ({formatted_value}, ultimo {period_type})")
                    else:
                        st.error(f"Input non valido. Inserisci un indice, un'espressione aritmetica o un nome di colonna valido.")
                        if default_value:
                            new_mapping[target] = default_value
                            default_value_idx = available.index(default_value) + 1
                            st.info(f"Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                        else:
                            new_mapping[target] = None
            else:
                if default_value:
                    new_mapping[target] = default_value
                    default_value_idx = available.index(default_value) + 1
                    st.info(f"Nessuna espressione inserita. Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                else:
                    new_mapping[target] = None
        
        st.markdown("---")
    
    return new_mapping


def evaluate_mapping_row(row_dict, expr, columns_list, debug=False):
    """
    Valuta una singola espressione su una singola riga.

    Args:
        row_dict: Dizionario con i valori della riga (es. {"Cash": 100000, "Debt": 50000, ...})
        expr: Espressione da valutare (es. "Cash", "1", "Cash+Debt", "1+2", "1+2-3", ecc.)
        columns_list: Lista di tutte le colonne disponibili (es. ["Cash", "Debt", "Inventory", ...])
        debug: Se True, stampa informazioni di debug

    Returns:
        Il risultato della valutazione dell'espressione (float), oppure 0 in caso di errore o se expr è None.
    """
    if expr is None:
        return 0

    if debug:
        st.write(f"DEBUG - Evaluating expression: {expr}")
        st.write(f"DEBUG - Available columns: {columns_list[:5]}...")
        st.write(f"DEBUG - Row keys: {list(row_dict.keys())[:5]}...")

    # 1) Se l'espressione corrisponde esattamente al nome di una colonna
    if expr in row_dict:
        try:
            return float(row_dict[expr]) if pd.notna(row_dict[expr]) else 0
        except (ValueError, TypeError):
            return 0

    # 2) Se l'espressione contiene operatori aritmetici (+, -, *, /)
    if any(op in expr for op in ['+', '-', '*', '/']):
        try:
            # Se l'espressione non contiene backtick, trasformala (sostituisce "1" con "`NomeColonna`")
            if '`' not in expr:
                expr = transform_expr(expr, columns_list)

            # Sostituisci i nomi di colonna racchiusi in backtick con i rispettivi valori numerici
            def replace_col(match):
                colname = match.group(0).strip('`')
                if colname in row_dict:
                    val = row_dict[colname]
                    return str(float(val) if pd.notna(val) else 0)
                return "0"

            transformed_expr = re.sub(r'`[^`]+`', replace_col, expr)

            # Verifica che l'espressione trasformata contenga solo caratteri sicuri
            if all(c.isdigit() or c in '+-*/.() ' for c in transformed_expr):
                return eval(transformed_expr)
            else:
                st.warning(f"Espressione potenzialmente non sicura: {transformed_expr}")
                return 0

        except Exception as e:
            st.error(f"Errore nell'eval dell'espressione '{expr}': {e}")
            return 0

    # 3) Se l'espressione è un indice numerico (es. "1"), che fa riferimento a columns_list
    if expr.strip().isdigit():
        try:
            idx = int(expr.strip()) - 1  # Converte in indice 0-based
            if 0 <= idx < len(columns_list):
                colname = columns_list[idx]
                val = row_dict.get(colname, 0)
                return float(val) if pd.notna(val) else 0
            return 0
        except (ValueError, IndexError):
            return 0

    # 4) Se nessun caso corrisponde, ritorna 0
    return 0



def compute_balance_mapping_timeseries(df, mapping_dict, debug_mode=False):
    """
    Applica il mapping a tutte le righe del dataframe.

    Args:
        df: DataFrame contenente i dati del bilancio.
        mapping_dict: Dizionario contenente il mapping target -> espressione.
        debug_mode: Se True, attiva il debug per ogni espressione

    Returns:
        DataFrame con il mapping applicato.
    """
    rows_as_dicts = df.to_dict('records')
    columns_list = list(df.columns)
    
    results = pd.DataFrame(index=df.index)
    
    # Debug info if needed
    if debug_mode:
        st.write("DEBUG - Mapping dictionary:", mapping_dict)
        st.write("DEBUG - DataFrame shape:", df.shape)
        st.write("DEBUG - DataFrame index:", list(df.index))
        st.write("DEBUG - DataFrame columns:", list(df.columns)[:10])  # First 10 columns
    
    for target, expr in mapping_dict.items():
        if debug_mode:
            st.write(f"DEBUG - Processing target: {target} with expression: {expr}")
        
        target_values = []
        for i, row_dict in enumerate(rows_as_dicts):
            # Enable debug for TTM row only to avoid clutter
            row_debug = debug_mode and (i == 0 and 'TTM' in df.index)
            
            if row_debug:
                st.write(f"DEBUG - Evaluating {target} for row: {df.index[i]}")
            
            value = evaluate_mapping_row(row_dict, expr, columns_list, debug=row_debug)
            target_values.append(value)
        
        results[target] = target_values
    
    return results



def fetch_shares_from_polygon_v3(ticker, api_key):
    """
    Fetch shares outstanding from Polygon API v3.

    Args:
        ticker: Ticker della società.
        api_key: API key per l'accesso a Polygon.

    Returns:
        Il numero delle azioni outstanding oppure None.
    """
    url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        st.write("Polygon v3 API Response:", data)
        results = data.get("results", {})
        if "weighted_shares_outstanding" in results and results["weighted_shares_outstanding"]:
            return float(results["weighted_shares_outstanding"])
        elif "share_class_shares_outstanding" in results and results["share_class_shares_outstanding"]:
            return float(results["share_class_shares_outstanding"])
        else:
            st.warning("Il numero delle azioni non è disponibile nella risposta di Polygon (v3).")
            return None
    except Exception as e:
        st.error(f"Errore durante il fetch delle azioni da Polygon (v3): {e}")
        return None


def format_dataframe(df, is_forecast=False):
    """
    Format dataframe for display.

    Args:
        df: DataFrame da formattare.
        is_forecast: Booleano che indica se il DataFrame rappresenta dati di forecast.

    Returns:
        DataFrame formattato.
    """
    if df is None or df.empty:
        return df
    
    formatted_df = df.copy()
    
    if not is_forecast:
        amount_columns = [
            "Cash", "A/P", "Short Term Debt", "Long Term Debt", "Total Debt",
            "D/R", "OL", "S/E", "L+S/E", "Net Cash", "Inventories", "PP&E NET",
            "Goodwill", "Intangibles"
        ]
    else:
        amount_columns = [
            "Revenue", "Gross Profit", "SG&A", "R&D", "S&M", "Operating Expenses",
            "Operating Income", "Other Income", "Pretax Income", "Taxes", "Net Income"
        ]
    
    for col in amount_columns:
        if col in formatted_df.columns:
            if is_forecast:
                formatted_df[col] = formatted_df[col] / 1e6
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
    
    return formatted_df

# Add caching for API calls with longer TTL
@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_company_info(ticker):
    """Fetch company info with caching"""
    if st.session_state.demo_mode:
        return get_demo_company_info(ticker)
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        info = company.info
        
        # Check if we got a valid response
        if not info or len(info) < 5:  # Basic validity check
            st.warning(f"Risposta limitata da Yahoo Finance per {ticker}. Alcuni dati potrebbero mancare.")
            
        return info
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_demo_company_info(ticker)
        else:
            st.error(f"Errore nel recupero delle informazioni aziendali: {str(e)}")
            return None

@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_balance_sheet_data(ticker):
    """Fetch balance sheet con miglioramenti per la trasposizione e debug"""
    if st.session_state.demo_mode:
        demo_data = get_demo_financial_data(ticker, "balance")
        
        # Debug per capire la struttura dei dati demo
        st.write("DEBUG - Struttura dati demo:")
        st.write("Keys:", list(demo_data.keys()))
        st.write("Colonne finanziarie:", list(demo_data["financials"].keys()))
        st.write("Date:", demo_data["dates"])
        
        # Convert demo data to pandas DataFrame format in modo più esplicito
        # Prima creiamo il dataframe così com'è (date come colonne)
        fin_data_initial = pd.DataFrame(demo_data["financials"])
        st.write("DEBUG - DataFrame iniziale (pre-trasposizione):")
        st.write("Shape:", fin_data_initial.shape)
        st.write("Colonne (date):", list(fin_data_initial.columns))
        st.write("Righe (voci bilancio):", list(fin_data_initial.index))
        
        # Usiamo le date come indice
        fin_data = fin_data_initial.copy()
        fin_data.columns = pd.to_datetime(demo_data["dates"])
        
        # Debug post-indice
        st.write("DEBUG - DataFrame post-indice:")
        st.write("Shape:", fin_data.shape)
        st.write("Colonne (date):", list(fin_data.columns))
        
        # Transponiamo per avere il formato atteso da yfinance (date come righe, voci come colonne)
        fin_data_transposed = fin_data.T
        
        st.write("DEBUG - DataFrame dopo trasposizione:")
        st.write("Shape:", fin_data_transposed.shape)
        st.write("Colonne (voci bilancio):", list(fin_data_transposed.columns))
        st.write("Indice (date):", list(fin_data_transposed.index))
        
        # Esempio di valori nel dataframe trasposto
        st.write("DEBUG - Esempio di valori (prime 3 colonne, prime 2 righe):")
        for col in list(fin_data_transposed.columns)[:3]:
            for idx in list(fin_data_transposed.index)[:2]:
                st.write(f"  {idx} - {col}: {fin_data_transposed.loc[idx, col]}")
        
        return fin_data_transposed
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        balance_sheet = company.balance_sheet
        
        # Debug per la struttura da yfinance
        st.write("DEBUG - Balance sheet da yfinance:")
        if balance_sheet is not None:
            st.write("Shape:", balance_sheet.shape)
            st.write("Colonne (date):", list(balance_sheet.columns))
            st.write("Indice (voci bilancio):", list(balance_sheet.index))
            
            # Esempio di valori nel dataframe
            st.write("DEBUG - Esempio di valori (pre-trasposizione):")
            for idx in list(balance_sheet.index)[:3]:
                for col in list(balance_sheet.columns)[:2]:
                    st.write(f"  {idx} - {col}: {balance_sheet.loc[idx, col]}")
        else:
            st.write("Il balance sheet è None")
        
        if balance_sheet is None or balance_sheet.empty:
            st.warning(f"Nessun dato di bilancio disponibile per {ticker}. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_balance_sheet_data(ticker)  # Recursively call with demo mode activated
        
        return balance_sheet
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_balance_sheet_data(ticker)  # Recursively call with demo mode activated
        else:
            st.error(f"Errore nel recupero dei dati di bilancio: {str(e)}")
            st.exception(e)  # Mostra lo stack trace completo
            return None

@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_income_statement_data(ticker):
    """
    Restituisce un tuple (income_stmt, ttm_series).
    Se st.session_state.demo_mode è True, usa i dati demo; 
    altrimenti, usa i dati reali da yfinance.
    """

    # 1. Se siamo in DEMO MODE, costruiamo fin_data e ttm_series dai dati demo
    if st.session_state.demo_mode:
        demo_data = get_demo_financial_data(ticker, "income")

        # Convert demo data to pandas DataFrame format
        fin_data = pd.DataFrame(demo_data["financials"])
        fin_data.columns = pd.to_datetime(demo_data["dates"])
        fin_data = fin_data.T  # Transpose to match yfinance format

        # Create ttm series from demo data
        ttm_series = None
        if "ttm" in demo_data:
            ttm_dict = {}
            for key, value in demo_data["ttm"].items():
                if isinstance(value, list) and len(value) > 0:
                    ttm_dict[key] = value[0]
                else:
                    ttm_dict[key] = value
            ttm_series = pd.Series(ttm_dict)

        # Restituiamo i dati demo
        return fin_data, ttm_series

    # 2. Altrimenti, usiamo i dati REALI da yfinance
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        income_stmt = company.financials

        # Se non ci sono dati, forziamo la demo mode e richiamiamo la funzione
        if income_stmt is None or income_stmt.empty:
            st.warning(f"Nessun dato di conto economico disponibile per {ticker}. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_income_statement_data(ticker)  # Recursively call in demo mode

        # Otteniamo i dati trimestrali
        q_financials = company.quarterly_financials

        # Calcoliamo il TTM
        if q_financials is not None and not q_financials.empty:
            ttm_series = q_financials.sum(axis=1)
        else:
            # Se non ci sono dati trimestrali, usiamo la colonna più recente dell'annuale
            ttm_series = income_stmt.iloc[:, 0]

        # Restituiamo i dati reali
        return income_stmt, ttm_series

    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_income_statement_data(ticker)  # Riprova in demo mode
        else:
            st.error(f"Errore nel recupero dei dati di conto economico: {str(e)}")
            return None, None

def get_quarterly_data(ticker):
    """
    Ottiene i dati dell'ultimo trimestre per un ticker.
    Restituisce un DataFrame formattato per essere compatibile con le funzioni di mapping.
    """
    try:
        company = yf.Ticker(ticker)
        quarterly_balance_sheet = company.quarterly_balance_sheet
        
        if quarterly_balance_sheet is None or quarterly_balance_sheet.empty:
            st.warning(f"Nessun dato trimestrale disponibile per {ticker}")
            return None
        
        # Estrai solo l'ultimo trimestre (la prima colonna)
        latest_quarter_date = quarterly_balance_sheet.columns[0]
        latest_quarter_data = quarterly_balance_sheet[latest_quarter_date]
        
        # Crea un DataFrame formattato come se fosse un balance sheet annuale
        # ma con solo i dati del trimestre più recente
        quarter_df = pd.DataFrame(
            {col: [latest_quarter_data[col]] for col in latest_quarter_data.index},
            index=[latest_quarter_date]
        )
        
        return quarter_df
    except Exception as e:
        st.error(f"Errore nel recupero dei dati trimestrali: {e}")
        return None


def load_balance_sheet_data():
    ticker = st.session_state.ticker
    try:
        with st.spinner(f"Caricamento dati di bilancio per {ticker}..."):
            # Ottiene i dati del bilancio annuale
            balance_sheet = get_balance_sheet_data(ticker)
            
            if balance_sheet is None:
                st.error(f"Nessun dato di bilancio disponibile per {ticker}")
                return None
            
            # Trasforma per ottenere il formato desiderato
            annual_balance_sheet = balance_sheet.T.sort_index(ascending=False)
            
            # Ottiene anche i dati trimestrali
            quarterly_data = get_quarterly_data(ticker)
            if quarterly_data is not None:
                st.session_state.quarterly_data = quarterly_data
                st.success("Dati trimestrali caricati con successo")
            else:
                st.warning("Dati trimestrali non disponibili, verranno usati solo dati annuali")
                st.session_state.quarterly_data = None
            
            if annual_balance_sheet.empty:
                st.error(f"Nessun dato di bilancio trovato per {ticker}")
                return None
            
            st.success(f"Dati di bilancio caricati con successo per {ticker}")
            return annual_balance_sheet
    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati di bilancio: {e}")
        return None


@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_balance_sheet_data(ticker):
    """Fetch balance sheet with caching - versione migliorata"""
    if st.session_state.demo_mode:
        demo_data = get_demo_financial_data(ticker, "balance")
        
        # Convert demo data to pandas DataFrame format
        fin_data = pd.DataFrame(demo_data["financials"])
        fin_data.index = pd.to_datetime(demo_data["dates"])
        
        # Transpose to match yfinance format
        fin_data = fin_data.T
        
        # Debug dei dati demo
        st.write("Debug - Dati demo caricati:")
        st.write(f"Shape: {fin_data.shape}")
        st.write(f"Colonne demo: {list(fin_data.columns)[:5]}")  # Prime 5 colonne
        st.write(f"Righe demo: {list(fin_data.index)[:5]}")  # Prime 5 righe
        
        # Debug dei valori
        st.write("Debug - Esempio di valori demo (primi 3):")
        sample_values = {}
        for col in list(fin_data.columns)[:3]:
            for row in list(fin_data.index)[:3]:
                sample_values[f"{row}-{col}"] = fin_data.loc[row, col]
        st.write(sample_values)
        
        return fin_data
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        balance_sheet = company.balance_sheet
        
        # Debug dei dati reali
        st.write("Debug - Dati reali caricati:")
        if balance_sheet is not None:
            st.write(f"Shape: {balance_sheet.shape}")
            st.write(f"Colonne reali: {list(balance_sheet.columns)[:5]}")
            st.write(f"Righe reali: {list(balance_sheet.index)[:5]}")
        else:
            st.write("Il balance sheet è None")
        
        if balance_sheet is None or balance_sheet.empty:
            st.warning(f"Nessun dato di bilancio disponibile per {ticker}. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_balance_sheet_data(ticker)  # Recursively call with demo mode activated
            
        return balance_sheet
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_balance_sheet_data(ticker)  # Recursively call with demo mode activated
        else:
            st.error(f"Errore nel recupero dei dati di bilancio: {str(e)}")
            return None


def get_quarterly_balance_sheet(ticker):
    """
    Funzione dedicata per ottenere i dati trimestrali del balance sheet.
    Fornisce più debug e gestione degli errori.
    """
    try:
        company = yf.Ticker(ticker)
        quarterly_balance_sheet = company.quarterly_balance_sheet
        
        if quarterly_balance_sheet is None or quarterly_balance_sheet.empty:
            st.warning(f"Nessun dato trimestrale di bilancio disponibile per {ticker}.")
            return None
        
        # Debug dei dati originali
        st.write("Debug - Dati trimestrali (originali):")
        st.write(f"Shape: {quarterly_balance_sheet.shape}")
        st.write(f"Colonne: {list(quarterly_balance_sheet.columns)}")
        
        # Prendi i valori più recenti
        latest_quarter = quarterly_balance_sheet.iloc[:, 0]
        
        # Crea un nuovo DataFrame con una sola data (TTM)
        ttm_data = pd.DataFrame(
            {col: [latest_quarter[col]] for col in latest_quarter.index},
            index=["TTM"]
        )
        
        # Debug dei dati TTM
        st.write("Debug - Dati TTM creati:")
        st.write(f"Shape: {ttm_data.shape}")
        st.write(f"Index: {ttm_data.index}")
        st.write(f"Colonne: {list(ttm_data.columns)[:5]}")
        
        return ttm_data
    except Exception as e:
        st.error(f"Errore durante il recupero dei dati trimestrali: {e}")
        st.exception(e)
        return None


def get_quarterly_balance_sheet(ticker):
    """
    Funzione dedicata per ottenere i dati trimestrali del balance sheet.
    Fornisce più debug e gestione degli errori.
    """
    try:
        company = yf.Ticker(ticker)
        quarterly_balance_sheet = company.quarterly_balance_sheet
        
        if quarterly_balance_sheet is None or quarterly_balance_sheet.empty:
            st.warning(f"Nessun dato trimestrale di bilancio disponibile per {ticker}.")
            return None
        
        # Debug dei dati originali
        st.write("Debug - Dati trimestrali (originali):")
        st.write(f"Shape: {quarterly_balance_sheet.shape}")
        st.write(f"Colonne: {list(quarterly_balance_sheet.columns)}")
        
        # Prendi i valori più recenti
        latest_quarter = quarterly_balance_sheet.iloc[:, 0]
        
        # Crea un nuovo DataFrame con una sola data (TTM)
        ttm_data = pd.DataFrame(
            {col: [latest_quarter[col]] for col in latest_quarter.index},
            index=["TTM"]
        )
        
        # Debug dei dati TTM
        st.write("Debug - Dati TTM creati:")
        st.write(f"Shape: {ttm_data.shape}")
        st.write(f"Index: {ttm_data.index}")
        st.write(f"Colonne: {list(ttm_data.columns)[:5]}")
        
        return ttm_data
    except Exception as e:
        st.error(f"Errore durante il recupero dei dati trimestrali: {e}")
        st.exception(e)
        return None

def process_balance_sheet():
    """Process the balance sheet data and compute net cash"""
    annual_balance_sheet = st.session_state.annual_balance_sheet
    balance_mapping_user = st.session_state.balance_mapping_user
    
    # Debug dei dati di mapping
    st.write("DEBUG - Mapping configurato:")
    for target, expr in balance_mapping_user.items():
        st.write(f"{target}: {expr}")
    
    # Process balance sheet con mapping per i dati annuali
    df_balance_ts = compute_balance_mapping_timeseries(annual_balance_sheet, balance_mapping_user)
    
    # Calculate Net Cash
    if "Cash" in df_balance_ts.columns and "Total Debt" in df_balance_ts.columns:
        df_balance_ts["Net Cash"] = df_balance_ts["Cash"] - df_balance_ts["Total Debt"]
    else:
        df_balance_ts["Net Cash"] = None
    
    # Aggiungi dati TTM basati sui dati trimestrali
    if not st.session_state.demo_mode and 'quarterly_data' in st.session_state and st.session_state.quarterly_data is not None:
        quarterly_df = st.session_state.quarterly_data
        
        # Mostra l'ordine delle colonne nei dati trimestrali per confronto
        st.expander("Visualizza l'ordine delle colonne nei dati trimestrali", expanded=False).write({
            'annual_columns': list(annual_balance_sheet.columns),
            'quarterly_columns': list(quarterly_df.columns)
        })
        
        # Approccio: creiamo manualmente il TTM per ogni target con attenzione all'ordine delle colonne
        ttm_values = {}
        
        for target, expr in balance_mapping_user.items():
            # Se l'espressione non contiene operatori aritmetici, è un riferimento diretto a una colonna
            if not any(op in expr for op in ['+', '-', '*', '/']):
                if expr in quarterly_df.columns:
                    ttm_values[target] = quarterly_df.iloc[0][expr]
                    st.write(f"DEBUG - Valore diretto per {target}: {ttm_values[target]}")
                else:
                    # Colonna non trovata nei dati trimestrali
                    st.write(f"DEBUG - Colonna '{expr}' per {target} non trovata nei dati trimestrali")
                    ttm_values[target] = None
            else:
                # Per espressioni con operatori, dobbiamo gestire l'ordine delle colonne
                try:
                    # Estrai i riferimenti alle colonne dall'espressione
                    cols = re.findall(r'`([^`]+)`', expr)
                    
                    # Se non ci sono backtick, potrebbe trattarsi di indici (1+2-3)
                    if not cols:
                        # Otteniamo le colonne annuali per avere l'ordine corretto
                        annual_cols_list = list(annual_balance_sheet.columns)
                        quarterly_cols_list = list(quarterly_df.columns)
                        
                        # Verifica se si tratta di un'espressione con indici numerici
                        if all(c.isdigit() or c in '+-*/() ' for c in expr):
                            # Trasforma gli indici in nomi di colonne usando l'ordine ANNUALE
                            st.write(f"DEBUG - Trasformo espressione con indici: {expr}")
                            transformed_expr = expr
                            
                            # Estrai tutti i numeri dall'espressione
                            numbers = re.findall(r'\d+', expr)
                            for num in numbers:
                                idx = int(num) - 1  # Assumiamo che gli indici inizino da 1
                                if 0 <= idx < len(annual_cols_list):
                                    col_name_annual = annual_cols_list[idx]
                                    # Ora cercala nel dataframe trimestrale
                                    if col_name_annual in quarterly_cols_list:
                                        transformed_expr = transformed_expr.replace(
                                            num, f"`{col_name_annual}`"
                                        )
                                    else:
                                        st.write(f"DEBUG - Colonna {col_name_annual} (indice {num}) non trovata nei dati trimestrali")
                                        transformed_expr = transformed_expr.replace(num, "0")
                            
                            st.write(f"DEBUG - Espressione trasformata: {transformed_expr}")
                            expr = transformed_expr
                            cols = re.findall(r'`([^`]+)`', expr)
                        else:
                            # Se non è un'espressione con indici e non ha backtick, non possiamo fare molto
                            st.write(f"DEBUG - Espressione non riconosciuta: {expr}")
                            ttm_values[target] = None
                            continue
                    
                    # Ora sostituiamo ogni colonna con il suo valore
                    expr_with_values = expr
                    for col in cols:
                        if col in quarterly_df.columns:
                            value = quarterly_df.iloc[0][col]
                            if pd.isna(value):
                                value = 0
                            expr_with_values = expr_with_values.replace(f"`{col}`", str(float(value)))
                            st.write(f"DEBUG - Sostituito `{col}` con {value}")
                        else:
                            st.write(f"DEBUG - Colonna '{col}' non trovata nei dati trimestrali per l'espressione")
                            expr_with_values = expr_with_values.replace(f"`{col}`", "0")
                    
                    # Valuta l'espressione
                    st.write(f"DEBUG - Espressione da valutare: {expr_with_values}")
                    if all(c.isdigit() or c in '+-*/.() ' for c in expr_with_values):
                        ttm_values[target] = eval(expr_with_values)
                        st.write(f"DEBUG - Valore calcolato per {target}: {ttm_values[target]}")
                    else:
                        st.write(f"DEBUG - Espressione non sicura: {expr_with_values}")
                        ttm_values[target] = None
                except Exception as e:
                    st.write(f"DEBUG - Errore nel calcolo di {target}: {e}")
                    ttm_values[target] = None
        
        # Aggiungi Net Cash se Cash e Total Debt sono disponibili
        if "Cash" in ttm_values and "Total Debt" in ttm_values:
            cash_value = ttm_values["Cash"] if pd.notna(ttm_values["Cash"]) else 0
            debt_value = ttm_values["Total Debt"] if pd.notna(ttm_values["Total Debt"]) else 0
            ttm_values["Net Cash"] = cash_value - debt_value
            st.write(f"DEBUG - Net Cash calcolato manualmente: {ttm_values['Net Cash']}")
            st.write(f"DEBUG - Componenti: Cash={cash_value}, Total Debt={debt_value}")
        else:
            ttm_values["Net Cash"] = None
        
        # Crea DataFrame TTM con i valori calcolati manualmente
        ttm_df = pd.DataFrame([ttm_values], index=["TTM"])
        st.write("DEBUG - DataFrame TTM creato manualmente:")
        st.write(ttm_df)
        
        # Concatena con i dati annuali
        df_balance_ts = pd.concat([ttm_df, df_balance_ts])
        
        st.success("Dati TTM basati sul trimestre più recente (calcolo manuale)")
    else:
        # Se non ci sono dati trimestrali, usa i dati dell'ultimo anno come TTM
        st.warning("Dati TTM basati sull'ultimo anno (dati trimestrali non disponibili)")
        ttm_row = df_balance_ts.iloc[[0]].copy()
        ttm_row.index = ['TTM']
        df_balance_ts = pd.concat([ttm_row, df_balance_ts])
    
    # Extract net cash from the most recent record
    try:
        net_cash = df_balance_ts.loc["TTM", "Net Cash"]
        if pd.isna(net_cash):
            st.write("DEBUG - Net Cash è NaN, utilizzo 0")
            net_cash = 0
    except (KeyError, TypeError) as e:
        st.write(f"DEBUG - Errore nell'estrazione di Net Cash: {e}")
        try:
            net_cash = df_balance_ts.iloc[0]["Net Cash"] if "Net Cash" in df_balance_ts.columns else 0
            if pd.isna(net_cash):
                net_cash = 0
        except Exception as e2:
            st.write(f"DEBUG - Secondo errore nell'estrazione di Net Cash: {e2}")
            net_cash = 0
    
    st.write(f"DEBUG - Net Cash finale: {net_cash}")
    return df_balance_ts, net_cash
def process_income_statement():
    """Process income statement data and prepare TTM data"""
    ticker = st.session_state.ticker
    
    try:
        with st.spinner(f"Caricamento dati di conto economico per {ticker}..."):
            # Get income statement data
            income_stmt, q_financials, ttm_series = get_income_statement_data(ticker)
            
            if income_stmt is None:
                st.error(f"Nessun dato di conto economico disponibile per {ticker}")
                return None, None
            
            # Apply numeric conversion
            df_income = income_stmt.T.apply(pd.to_numeric, errors='coerce')
            
            # Process TTM data
            ttm_data = {}
            income_map = {
                "Revenue": ["Total Revenue", "Operating Revenue"],
                "Total COGS": ["Cost Of Revenue"],
                "Gross Profit": ["Gross Profit"],
                "SG&A": ["Selling General And Administration"],
                "R&D": ["Research And Development"],
                "S&M": ["Sales And Marketing"],
                "Operating Income": ["Operating Income"],
                "Pretax Income": ["Pretax Income"],
                "Taxes": ["Income Tax Expense", "Taxes"],
                "Net Income": ["Net Income"],
                "EPS": ["Diluted EPS"]
            }
            
            # Extract TTM data based on mapping
            for target, candidates in income_map.items():
                for candidate in candidates:
                    if isinstance(ttm_series, pd.Series) and candidate in ttm_series.index:
                        ttm_data[target] = ttm_series[candidate]
                        break
            
            # Additional calculations
            if "Gross Profit" not in ttm_data and "Revenue" in ttm_data and "Total COGS" in ttm_data:
                ttm_data["Gross Profit"] = ttm_data["Revenue"] - ttm_data["Total COGS"]
            
            sg_a = ttm_data.get("SG&A", 0)
            r_and_d = ttm_data.get("R&D", 0)
            s_and_m = ttm_data.get("S&M", 0)
            ttm_data["Operating Expenses"] = sg_a + r_and_d + s_and_m
            
            if "Operating Income" not in ttm_data and "Gross Profit" in ttm_data:
                ttm_data["Operating Income"] = ttm_data["Gross Profit"] - ttm_data["Operating Expenses"]
            if "Taxes" not in ttm_data and "Pretax Income" in ttm_data and "Net Income" in ttm_data:
                ttm_data["Taxes"] = ttm_data["Pretax Income"] - ttm_data["Net Income"]
            
            # Get shares data if available
            if "Shares" in df_income.index:
                ttm_data["Shares"] = df_income.loc["Shares"].iloc[0]
            else:
                ttm_data["Shares"] = None
            
            # Calculate margins
            if "Revenue" in ttm_data and "Gross Profit" in ttm_data and ttm_data["Revenue"] != 0:
                ttm_data["Gross Margin"] = (ttm_data["Gross Profit"] / ttm_data["Revenue"]) * 100
            else:
                ttm_data["Gross Margin"] = None
            
            ttm_data["Net Income Y/Y"] = None
            ttm_data["Revenue Y/Y"] = None
            
            # Create TTM dataframe and combine with annual data
            ttm_df = pd.DataFrame(ttm_data, index=["TTM"])
            df_income = pd.concat([ttm_df, df_income])
            
            st.success(f"Dati di conto economico caricati con successo per {ticker}")
            return df_income, ttm_data
    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati di conto economico: {e}")
        return None, None

def get_income_statement_data(ticker):
    """Fetch income statement with caching"""
    if st.session_state.demo_mode:
        demo_data = get_demo_financial_data(ticker, "income")
        
        # Convert demo data to pandas DataFrame format
        fin_data = pd.DataFrame(demo_data["financials"])
        fin_data.index = pd.to_datetime(demo_data["dates"])
        
        # Transpose to match yfinance format
        fin_data = fin_data.T
        
        return fin_data, pd.DataFrame(demo_data["quarterly"]), pd.DataFrame(demo_data["ttm"]).iloc[0]
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        income_stmt = company.financials
        
        if income_stmt is None or income_stmt.empty:
            st.warning(f"Nessun dato di conto economico disponibile per {ticker}. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_income_statement_data(ticker)  # Recursively call with demo mode activated
            
        # Get quarterly data
        q_financials = company.quarterly_financials
        
        # Calculate TTM from quarterly data
        if q_financials is not None and not q_financials.empty:
            ttm_series = q_financials.sum(axis=1)
        else:
            # Use most recent annual data if quarterly not available
            ttm_series = income_stmt.iloc[:, 0]
        
        return income_stmt, q_financials, ttm_series
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_income_statement_data(ticker)  # Recursively call with demo mode activated
        else:
            st.error(f"Errore nel recupero dei dati di conto economico: {str(e)}")
            return None, None, None


def generate_forecast(ttm_data, phase1_years, phase1_growth_rate, 
                      phase2_years, phase2_growth_rate,
                      sg_a_pct, r_and_d_pct, s_and_m_pct, other_income, 
                      tax_rate, avg_gross_margin, cost_method):
    """Generate forecast based on user parameters with two phases of growth"""
    try:
        # Debug output of TTM data
        st.write("TTM data available for forecast:", list(ttm_data.keys()))
        
        # Get base revenue
        if "Revenue" not in ttm_data or pd.isna(ttm_data["Revenue"]):
            st.error("Revenue data not available in TTM data")
            return None
        
        revenue_base = ttm_data["Revenue"]
        
        # Total forecast years
        total_forecast_years = phase1_years + phase2_years
        
        # Create forecast DataFrame
        forecast = pd.DataFrame(index=range(1, total_forecast_years + 1))
        forecast.index.name = 'Year'
        
        # Project revenue growth with two phases
        for year in forecast.index:
            if year <= phase1_years:
                # Phase 1 growth
                forecast.loc[year, "Revenue"] = revenue_base * ((1 + phase1_growth_rate) ** year)
            else:
                # Phase 2 growth - continue from where phase 1 ended
                years_in_phase2 = year - phase1_years
                phase1_end_revenue = revenue_base * ((1 + phase1_growth_rate) ** phase1_years)
                forecast.loc[year, "Revenue"] = phase1_end_revenue * ((1 + phase2_growth_rate) ** years_in_phase2)
        
        # Calculate gross profit
        forecast["Gross Profit"] = forecast["Revenue"] * avg_gross_margin
        
        # Calculate operating expenses
        if cost_method == 2:  # Growth based on historical data
            sg_a_base = ttm_data.get("SG&A", 0) if pd.notna(ttm_data.get("SG&A", 0)) else 0
            r_and_d_base = ttm_data.get("R&D", 0) if pd.notna(ttm_data.get("R&D", 0)) else 0
            s_and_m_base = ttm_data.get("S&M", 0) if pd.notna(ttm_data.get("S&M", 0)) else 0
            
            # Apply the appropriate growth rate based on which phase the year is in
            for year in forecast.index:
                if year <= phase1_years:
                    # Phase 1 growth
                    growth_factor = (1 + phase1_growth_rate) ** year
                else:
                    # Phase 2 growth - continuing from phase 1
                    years_in_phase1 = phase1_years
                    years_in_phase2 = year - phase1_years
                    phase1_growth = (1 + phase1_growth_rate) ** years_in_phase1
                    phase2_growth = (1 + phase2_growth_rate) ** years_in_phase2
                    growth_factor = phase1_growth * phase2_growth
                
                forecast.loc[year, "SG&A"] = sg_a_base * growth_factor
                forecast.loc[year, "R&D"] = r_and_d_base * growth_factor
                forecast.loc[year, "S&M"] = s_and_m_base * growth_factor
        else:  # Fixed percentages
            forecast["SG&A"] = forecast["Revenue"] * sg_a_pct
            forecast["R&D"] = forecast["Revenue"] * r_and_d_pct
            forecast["S&M"] = forecast["Revenue"] * s_and_m_pct
        
        # Calculate operating expenses total
        forecast["Operating Expenses"] = forecast["SG&A"] + forecast["R&D"] + forecast["S&M"]
        
        # Calculate operating income
        forecast["Operating Income"] = forecast["Gross Profit"] - forecast["Operating Expenses"]
        
        # Add other income and calculate pretax income
        if not isinstance(other_income, (int, float)):
            other_income = 0
            
        forecast["Other Income"] = other_income
        forecast["Pretax Income"] = forecast["Operating Income"] + forecast["Other Income"]
        
        # Calculate taxes and net income
        forecast["Taxes"] = forecast["Pretax Income"] * tax_rate
        forecast["Net Income"] = forecast["Pretax Income"] - forecast["Taxes"]
        
        # Add growth phase indicator column
        forecast["Growth Phase"] = forecast.index.map(lambda x: "Phase 1" if x <= phase1_years else "Phase 2")
        
        return forecast
        
    except Exception as e:
        st.error(f"Errore durante la generazione del forecast: {e}")
        st.exception(e)
        return None

def calculate_valuation(forecast, net_cash, discount_rate, maturity_decline_rate, shares):
    """Calculate DCF valuation based on forecast"""
    try:
        # Calcola la somma dei flussi di cassa non scontati durante il periodo di previsione
        sum_forecast_cash_flows = 0
        for year in forecast.index:
            if "Net Income" in forecast.columns and year > 0:
                sum_forecast_cash_flows += forecast.loc[year, "Net Income"]
        
        # Calculate NPV of forecast period
        NPV_forecast = 0
        for year in forecast.index:
            if "Net Income" in forecast.columns and year > 0:
                NPV_forecast += forecast.loc[year, "Net Income"] / ((1 + discount_rate) ** year)
        
        # Calculate terminal value
        if forecast.empty or "Net Income" not in forecast.columns:
            terminal_value = 0
        else:
            terminal_value = (forecast.loc[forecast.index[-1], "Net Income"] * (1 - maturity_decline_rate)) / (discount_rate + maturity_decline_rate)
        
        # Calculate Total Enterprise Value (non-discounted) - somma dei flussi previsionali + valore terminale
        total_value_nondiscounted = sum_forecast_cash_flows + terminal_value
        
        # Calculate NPV of terminal value
        if forecast.empty:
            NPV_perpetuo = 0
        else:
            NPV_perpetuo = terminal_value / ((1 + discount_rate) ** forecast.index[-1])
        
        # Calculate total NPV
        NPV_total = NPV_forecast + NPV_perpetuo
        
        # Calculate final enterprise value
        if net_cash is None:
            net_cash = 0
        final_net_value = NPV_total + net_cash
        
        # Calculate per share value
        if shares is None or shares == 0 or pd.isna(shares):
            theoretical_share_value = None
        else:
            theoretical_share_value = final_net_value / shares
        
        return {
            "sum_forecast_cash_flows": sum_forecast_cash_flows,
            "total_value_nondiscounted": total_value_nondiscounted,
            "NPV_forecast": NPV_forecast,
            "terminal_value": terminal_value,
            "NPV_perpetuo": NPV_perpetuo,
            "NPV_total": NPV_total,
            "final_net_value": final_net_value,
            "theoretical_share_value": theoretical_share_value
        }
    except Exception as e:
        st.error(f"Errore durante il calcolo della valutazione: {e}")
        st.exception(e)  # Show full stack trace
        return {
            "sum_forecast_cash_flows": 0,
            "total_value_nondiscounted": 0,
            "NPV_forecast": 0,
            "terminal_value": 0,
            "NPV_perpetuo": 0,
            "NPV_total": 0,
            "final_net_value": 0,
            "theoretical_share_value": None
        }

def save_ticker_input():
    st.session_state.ticker = st.session_state.ticker_input.strip().upper()
    st.session_state.step = 'load_balance_sheet'
    st.session_state.annual_balance_sheet = None
    st.session_state.balance_mapping_user = None
    st.session_state.df_balance_ts = None
    st.session_state.net_cash = None
    st.session_state.annual_income_statement = None
    st.session_state.ttm_data = None
    st.session_state.forecast = None
    st.session_state.valuation_results = None

# Questa funzione non è più necessaria dato che stiamo gestendo il mapping direttamente nella fase balance_mapping_config
def save_balance_mapping():
    pass

def save_forecast_params():
    # Save forecast parameters for both phases
    st.session_state.phase1_years = st.session_state.phase1_years_input
    st.session_state.phase1_growth_rate = st.session_state.phase1_growth_rate_input / 100
    
    st.session_state.phase2_years = st.session_state.phase2_years_input
    st.session_state.phase2_growth_rate = st.session_state.phase2_growth_rate_input / 100
    
    # Total forecast years
    st.session_state.forecast_years = st.session_state.phase1_years + st.session_state.phase2_years
    
    # Save other forecast parameters
    st.session_state.sg_a_pct = st.session_state.sg_a_pct_input / 100
    st.session_state.r_and_d_pct = st.session_state.r_and_d_pct_input / 100
    st.session_state.s_and_m_pct = st.session_state.s_and_m_pct_input / 100
    
    if st.session_state.other_income_input.strip() == "":
        st.session_state.other_income = 0
    else:
        st.session_state.other_income = float(st.session_state.other_income_input) * 1e6
    
    st.session_state.tax_rate = st.session_state.tax_rate_input / 100
    st.session_state.maturity_decline_rate = st.session_state.maturity_decline_rate_input / 100
    st.session_state.discount_rate = st.session_state.discount_rate_input / 100
    
    if st.session_state.manual_gross_margin_input == "":
        if "Gross Margin" in st.session_state.ttm_data and st.session_state.ttm_data["Gross Margin"] is not None:
            st.session_state.avg_gross_margin = st.session_state.ttm_data["Gross Margin"] / 100
        else:
            st.session_state.avg_gross_margin = 0.5  # Default value
    else:
        st.session_state.avg_gross_margin = float(st.session_state.manual_gross_margin_input) / 100
    
    st.session_state.cost_method = st.session_state.cost_method_input
    
    # Generate forecast with two phases
    forecast = generate_forecast(
        st.session_state.ttm_data,
        st.session_state.phase1_years,
        st.session_state.phase1_growth_rate,
        st.session_state.phase2_years,
        st.session_state.phase2_growth_rate,
        st.session_state.sg_a_pct,
        st.session_state.r_and_d_pct,
        st.session_state.s_and_m_pct,
        st.session_state.other_income,
        st.session_state.tax_rate,
        st.session_state.avg_gross_margin,
        st.session_state.cost_method
    )
    
    if forecast is not None:
        st.session_state.forecast = forecast
        
        # Calculate valuation
        shares = st.session_state.ttm_data.get("Shares")
        
        # If shares not available, try to get them from Polygon API
        if shares in [None, 0] and "polygon_api_key" in st.session_state and st.session_state.polygon_api_key.strip() != "":
            shares = fetch_shares_from_polygon_v3(st.session_state.ticker, st.session_state.polygon_api_key)
        
        valuation_results = calculate_valuation(
            forecast, 
            st.session_state.net_cash, 
            st.session_state.discount_rate, 
            st.session_state.maturity_decline_rate, 
            shares
        )
        
        st.session_state.valuation_results = valuation_results
        st.session_state.step = 'show_results'
    else:
        st.error("Errore nella generazione del forecast. Riprova.")

###############################################
# INTERFACCIA UTENTE CON SIDEBAR
###############################################

# Add demo mode toggle in sidebar
with st.sidebar:
    st.title("Impostazioni")
    demo_toggle = st.checkbox("Usa modalità demo", value=st.session_state.demo_mode, 
                             help="Utilizza dati di esempio invece di dati live. Utile quando l'API è limitata.")
    
    if demo_toggle != st.session_state.demo_mode:
        st.session_state.demo_mode = demo_toggle
        st.rerun()
    
    if st.session_state.demo_mode:
        st.success("Modalità demo attiva! I dati visualizzati sono di esempio.")
    
    st.markdown("---")
    st.markdown("""
    ### Informazioni
    Questo strumento analizza il Balance Sheet e genera una valutazione DCF di aziende quotate.
    Se ricevi errori di rate limiting, attiva la modalità demo.
    """)
    
    if st.session_state.step not in ['input', 'load_balance_sheet']:
        if st.button("Ricomincia da capo"):
            st.session_state.step = 'input'
            st.rerun()

# STEP 1: Input iniziale
if st.session_state.step == 'input':
    st.header("Inserisci il ticker azionario")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Ticker (es. AAPL):", value="AAPL", key="ticker_input")
    with col2:
        st.button("Analizza", on_click=save_ticker_input)

# STEP 2: Caricamento dati Balance Sheet
elif st.session_state.step == 'load_balance_sheet':
    annual_balance_sheet = load_balance_sheet_data()
    
    if annual_balance_sheet is not None:
        st.session_state.annual_balance_sheet = annual_balance_sheet
        st.session_state.step = 'balance_mapping'
        st.rerun()

# STEP 3: Configurazione del mapping del Balance Sheet
elif st.session_state.step == 'balance_mapping':
    st.header(f"Configurazione del mapping del Balance Sheet per {st.session_state.ticker}")
    
    # Display company info
    info = get_company_info(st.session_state.ticker)
    if info:
        col1, col2 = st.columns([1, 3])
        with col1:
            if "logo_url" in info and info["logo_url"]:
                st.image(info["logo_url"], width=100)
            else:
                st.markdown("🏢")
        with col2:
            st.subheader(info.get("longName", st.session_state.ticker))
            st.markdown(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Prezzo attuale:** ${info.get('currentPrice', 'N/A')} | **Market Cap:** ${info.get('marketCap', 0)/1e9:.2f}B")
    
    st.subheader("Record più recente del Balance Sheet Annuale")
    st.dataframe(pd.DataFrame(st.session_state.annual_balance_sheet.iloc[0]).T)
    
    if st.button("Configura mapping del Balance Sheet"):
        st.session_state.step = 'balance_mapping_config'
        st.rerun()

# STEP 4: Configurazione dettagliata del mapping del Balance Sheet
elif st.session_state.step == 'balance_mapping_config':
    st.header(f"Mappatura dettagliata del Balance Sheet per {st.session_state.ticker}")
    
    # Prima esegui la mappatura e visualizza i campi di input
    mapping_result = streamlit_mapping_complex(
        st.session_state.annual_balance_sheet, 
        config["balance_mapping"]
    )
    
    # Solo dopo visualizzare gli input, mostra il pulsante per procedere
    if st.button("Applica mapping e procedi con l'analisi"):
        st.session_state.balance_mapping_user = mapping_result
        st.session_state.step = 'process_balance_sheet'
        st.rerun()

# Questa è la parte corretta nel STEP 5: Elaborazione del Balance Sheet

# STEP 5: Elaborazione del Balance Sheet
elif st.session_state.step == 'process_balance_sheet':
    st.header(f"Analisi del Balance Sheet per {st.session_state.ticker}")
    
    with st.spinner("Elaborazione del Balance Sheet in corso..."):
        df_balance_ts, net_cash = process_balance_sheet()
        st.session_state.df_balance_ts = df_balance_ts
        st.session_state.net_cash = net_cash
    
    st.success("Balance Sheet elaborato con successo!")
    
    # Display the processed balance sheet
    st.subheader("Balance Sheet elaborato (valori in milioni)")
    display_df = format_dataframe(df_balance_ts)
    st.dataframe(display_df, use_container_width=True)
    
    # Show charts - VERSIONE MODIFICATA per rimuovere riferimenti all'income statement
    st.subheader("Analisi Grafica del Balance Sheet")
    
    # Crea solo i grafici del balance sheet senza riferimenti al tax percentage
    fig1, fig2 = create_balance_charts(df_balance_ts / 1e6)
    
    tab1, tab2 = st.tabs(["Cash & Debt", "Composizione Assets"])
    with tab1:
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        st.plotly_chart(fig2, use_container_width=True)
    
    # Show Net Cash calculation
    st.subheader("Risultati Chiave")
    st.metric("Net Cash", f"${net_cash/1e6:.2f}M")
    
    # Load Income Statement Data
    st.subheader("Caricamento dati di Conto Economico")
    
    if st.button("Procedi alla Valutazione DCF"):
        st.session_state.step = 'load_income_statement'
        st.rerun()

# STEP 6: Caricamento dati Income Statement
elif st.session_state.step == 'load_income_statement':
    st.header(f"Caricamento dati di Conto Economico per {st.session_state.ticker}")
    
    df_income, ttm_data = process_income_statement()
    
    if df_income is not None and ttm_data is not None:
        st.session_state.annual_income_statement = df_income
        st.session_state.ttm_data = ttm_data
        st.session_state.step = 'forecast_setup'
        st.rerun()

# STEP 7: Impostazione dei parametri di Forecast
elif st.session_state.step == 'forecast_setup':
    st.header(f"Impostazione dei parametri di Forecast per {st.session_state.ticker}")
    
    # Display company info
    info = get_company_info(st.session_state.ticker)
    if info:
        col1, col2 = st.columns([1, 3])
        with col1:
            if "logo_url" in info and info["logo_url"]:
                st.image(info["logo_url"], width=100)
            else:
                st.markdown("🏢")
        with col2:
            st.subheader(info.get("longName", st.session_state.ticker))
            st.markdown(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Prezzo attuale:** ${info.get('currentPrice', 'N/A')} | **Market Cap:** ${info.get('marketCap', 0)/1e9:.2f}B")
    
    # Display TTM Data
    st.subheader("Dati TTM (Trailing Twelve Months)")
    
    # Convert TTM data to DataFrame for display
    ttm_df = pd.DataFrame({k: [v] for k, v in st.session_state.ttm_data.items() if k != "Shares"}, 
                         index=["Valore"])
    ttm_display = ttm_df.copy()
    
    # Format TTM data (convert to millions for monetary values)
    monetary_cols = ["Revenue", "Total COGS", "Gross Profit", "SG&A", "R&D", "S&M", 
                     "Operating Expenses", "Operating Income", "Pretax Income", "Taxes", "Net Income"]
    for col in monetary_cols:
        if col in ttm_display.columns:
            ttm_display[col] = ttm_display[col] / 1e6
            ttm_display[col] = ttm_display[col].apply(lambda x: f"${x:,.2f}M" if pd.notna(x) else "N/A")
    
    # Format percentage values
    pct_cols = ["Gross Margin"]
    for col in pct_cols:
        if col in ttm_display.columns:
            ttm_display[col] = ttm_display[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
    
    st.dataframe(ttm_display.T, use_container_width=True)
    
    # Input form for forecast parameters
    st.subheader("Parametri di Forecast")
    
    col1, col2 = st.columns(2)
    
    # Sezione Phase 1
    st.write("### Fase 1 di Forecast")
    col1_phase1, col2_phase1 = st.columns(2)

    with col1_phase1:
        st.number_input("Numero di anni (Fase 1):", 
                        min_value=1, max_value=20, value=5, step=1, key="phase1_years_input")
        
        st.number_input("Tasso di crescita annuale delle Revenues (%) - Fase 1:", 
                        min_value=-50.0, max_value=100.0, value=10.0, step=0.5, key="phase1_growth_rate_input")

    # Sezione Phase 2
    st.write("### Fase 2 di Forecast")
    col1_phase2, col2_phase2 = st.columns(2)

    with col1_phase2:
        st.number_input("Numero di anni (Fase 2):", 
                        min_value=0, max_value=20, value=5, step=1, key="phase2_years_input")
        
        st.number_input("Tasso di crescita annuale delle Revenues (%) - Fase 2:", 
                        min_value=-50.0, max_value=100.0, value=5.0, step=0.5, key="phase2_growth_rate_input")

        
        st.number_input("Percentuale di SG&A sulle Revenues (%):", 
                        min_value=0.0, max_value=100.0, value=15.0, step=0.5, key="sg_a_pct_input")
        
        st.number_input("Percentuale di R&D sulle Revenues (%):", 
                        min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="r_and_d_pct_input")
        
        st.number_input("Percentuale di S&M sulle Revenues (%):", 
                        min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="s_and_m_pct_input")
    
    with col2:
        st.text_input("Valore assoluto per Other Income (in milioni):", 
                    value="0", key="other_income_input")
        
        st.number_input("Tax rate (%):", 
                        min_value=0.0, max_value=100.0, value=20.0, step=0.5, key="tax_rate_input")
        
        st.number_input("Tasso di decrescita annuale del Net Income in perpetuo (%):", 
                        min_value=0.0, max_value=100.0, value=3.0, step=0.5, key="maturity_decline_rate_input")
        
        st.number_input("Tasso di sconto (%):", 
                        min_value=0.1, max_value=100.0, value=5.0, step=0.5, key="discount_rate_input")
        
        # Gross margin input
        gross_margin_placeholder = ""
        if "Gross Margin" in st.session_state.ttm_data and st.session_state.ttm_data["Gross Margin"] is not None:
            gross_margin_placeholder = f"{st.session_state.ttm_data['Gross Margin']:.2f}"
        
        st.text_input(f"Gross margin (%) [TTM: {gross_margin_placeholder}%]:", 
                     help="Lascia vuoto per usare il valore TTM", 
                     value="", key="manual_gross_margin_input")
    
    # Cost method selection
    st.radio("Metodo per il calcolo dei costi operativi:", 
             [1, 2], 
             format_func=lambda x: "Percentuali fisse" if x == 1 else "Crescita storica", 
             horizontal=True,
             key="cost_method_input")
    
    # Check for shares data
    shares = st.session_state.ttm_data.get("Shares")
    if shares in [None, 0]:
        st.warning("Il numero delle azioni non è disponibile. Inserisci una Polygon API key per recuperare il dato.")
        st.text_input("Polygon API key:", key="polygon_api_key")
    
    # Generate forecast button
    if st.button("Genera Forecast e Valutazione"):
        save_forecast_params()

# STEP 8: Visualizza risultati finali
elif st.session_state.step == 'show_results':
    st.header(f"Risultati di Valutazione per {st.session_state.ticker}")
    
    # Display company info
    info = get_company_info(st.session_state.ticker)
    if info:
        col1, col2 = st.columns([1, 3])
        with col1:
            if "logo_url" in info and info["logo_url"]:
                st.image(info["logo_url"], width=100)
            else:
                st.markdown("🏢")
        with col2:
            st.subheader(info.get("longName", st.session_state.ticker))
            st.markdown(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Prezzo attuale:** ${info.get('currentPrice', 'N/A')} | **Market Cap:** ${info.get('marketCap', 0)/1e9:.2f}B")
    
    # Display forecast table
    st.subheader("Forecast Financials (valori in milioni)")
    forecast_display = format_dataframe(st.session_state.forecast, is_forecast=True)
    st.dataframe(forecast_display, use_container_width=True)
    
    # Display forecast charts
    st.subheader("Analisi Grafica del Forecast")
    fig1, fig2, fig3 = create_forecast_charts(st.session_state.forecast)
    
    tab1, tab2, tab3 = st.tabs(["Revenue & Net Income", "Operating Expenses", "NPV Cumulativo"])
    with tab1:
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        st.plotly_chart(fig3, use_container_width=True)
    
    # Display valuation results
    st.subheader("Risultati di Valutazione")
    
    valuation = st.session_state.valuation_results
    
    # Rearranged to include Terminal Value (non-discounted)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("NPV Forecast", f"${valuation['NPV_forecast']/1e9:.2f}B")
        st.metric("Terminal Value (non-discounted)", f"${valuation['terminal_value']/1e9:.2f}B")
        st.metric("NPV Terminal Value", f"${valuation['NPV_perpetuo']/1e9:.2f}B")
    
    with col2:
        st.metric("NPV Totale", f"${valuation['NPV_total']/1e9:.2f}B")
        st.metric("Net Cash", f"${st.session_state.net_cash/1e9:.2f}B")
    
    with col3:
        st.metric("Enterprise Value", f"${valuation['final_net_value']/1e9:.2f}B")
        
        if valuation['theoretical_share_value'] is not None:
            current_price = info.get('currentPrice') if info else None
            
            if current_price:
                upside = ((valuation['theoretical_share_value'] / current_price) - 1) * 100
                delta = f"{upside:.2f}% vs current"
            else:
                delta = None
                
            st.metric(
                "Valore teorico per azione", 
                f"${valuation['theoretical_share_value']:.2f}", 
                delta=delta
            )
        else:
            st.warning("Il numero delle azioni non è disponibile. Non è possibile calcolare il valore teorico per azione.")
    
    # Display valuation parameters
    st.subheader("Parametri utilizzati per la valutazione")
    
    params_df = pd.DataFrame({
        "Parametro": [
            "Anni di forecast",
            "Crescita revenue annuale",
            "Gross margin",
            "SG&A % sulle revenue",
            "R&D % sulle revenue",
            "S&M % sulle revenue",
            "Tax rate",
            "Tasso di sconto",
            "Tasso di decrescita perpetua"
        ],
        "Valore": [
            f"{st.session_state.forecast_years} anni",
            f"{st.session_state.phase1_growth_rate*100:.2f}%",
            f"{st.session_state.avg_gross_margin*100:.2f}%",
            f"{st.session_state.sg_a_pct*100:.2f}%",
            f"{st.session_state.r_and_d_pct*100:.2f}%",
            f"{st.session_state.s_and_m_pct*100:.2f}%",
            f"{st.session_state.tax_rate*100:.2f}%",
            f"{st.session_state.discount_rate*100:.2f}%",
            f"{st.session_state.maturity_decline_rate*100:.2f}%"
        ]
    })
    
    st.dataframe(params_df, use_container_width=True, hide_index=True)
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_csv = st.session_state.forecast.to_csv().encode('utf-8')
        st.download_button(
            label="Download Forecast CSV",
            data=forecast_csv,
            file_name=f'{st.session_state.ticker}_forecast.csv',
            mime='text/csv',
        )
    
    with col2:
        balance_csv = st.session_state.df_balance_ts.to_csv().encode('utf-8')
        st.download_button(
            label="Download Balance Sheet CSV",
            data=balance_csv,
            file_name=f'{st.session_state.ticker}_balance_sheet.csv',
            mime='text/csv',
        )
    
    if st.button("Modifica parametri di forecast"):
        st.session_state.step = 'forecast_setup'
        st.rerun()

# Footer
st.markdown("---")
st.markdown("Creato con ❤️ usando Streamlit e yfinance")

# Render navigation bar at the end of each step
render_navigation_bar()