import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px

# 📌 Custom variables for each river
custom_variables = {
    "KualaSG": {
        "raw": ["time", "PH_Sensor", "ORP_Sensor", "TR_Sensor", "CT_Sensor", "TDS_Sensor", "NH_SEnsor", "DO_Sensor", "COD_Sensor", "BOD_Sensor"],
        "cleaned": ["Timestamp", "PH_Sensor", "ORP_Sensor", "TR_Sensor", "CT_Sensor", "DO_Sensor"]
    },
    "Bilut": {
        "raw": ["time", "PH_Sensor", "ORP_Sensor", "CT_Sensor", "TDS_Sensor", "NH_sensor", "COD_Sensor", "DO_Sensor", "BOD_Sensor", "TR_Sensor"],
        "cleaned": ["Timestamp", "PH_Sensor", "ORP_Sensor", "CT_Sensor", "TDS_Sensor", "NH_sensor", "TR_Sensor"]
    },
    "Kechau": {
        "raw": ["time", "Ph_Sensor", "ORP_Sensor", "CT_Sensor", "TDS_Sensor", "NH_Sensor", "DO_Sensor", "TR_Sensor", "BOD_Sensor", "COD_Sensor"],
        "cleaned": ["Timestamp", "ORP_Sensor", "CT_Sensor", "TDS_Sensor", "NH_Sensor"]
    }
}

# 📌 Load CSV files based on selected river
def load_data(river):
    raw_file_path = f"{river}_Raw.csv"
    cleaned_file_path = f"{river}_Cleaned.csv"

    try:
        df_raw = pd.read_csv(raw_file_path, usecols=custom_variables[river]["raw"])
        df_cleaned = pd.read_csv(cleaned_file_path, usecols=custom_variables[river]["cleaned"])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure CSV files are available in the correct directory!")
        return None, None

    # 📌 Detect and rename time column
    df_raw.rename(columns={col: "Timestamp" for col in df_raw.columns if 'time' in col.lower()}, inplace=True)

    df_raw["Timestamp"] = pd.to_datetime(df_raw["Timestamp"], errors='coerce')
    df_cleaned["Timestamp"] = pd.to_datetime(df_cleaned["Timestamp"], errors='coerce')

    # 📌 Convert all columns to numeric
    for df in [df_raw, df_cleaned]:
        for col in df.columns:
            if col != "Timestamp":
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # 📌 Create resampled datasets
    df_raw.set_index("Timestamp", inplace=True)
    df_cleaned.set_index("Timestamp", inplace=True)

    df_raw_daily = df_raw.resample('D').mean(numeric_only=True)
    df_raw_weekly = df_raw.resample('W').mean(numeric_only=True)
    df_raw_monthly = df_raw.resample('ME').mean(numeric_only=True)  # Fixed warning

    df_cleaned_daily = df_cleaned.resample('D').mean(numeric_only=True)
    df_cleaned_weekly = df_cleaned.resample('W').mean(numeric_only=True)
    df_cleaned_monthly = df_cleaned.resample('ME').mean(numeric_only=True)

    return df_raw, df_cleaned, df_raw_daily, df_raw_weekly, df_raw_monthly, df_cleaned_daily, df_cleaned_weekly, df_cleaned_monthly

# Load default dataset
selected_river = "KualaSG"
df_raw, df_cleaned, df_raw_daily, df_raw_weekly, df_raw_monthly, df_cleaned_daily, df_cleaned_weekly, df_cleaned_monthly = load_data(selected_river)

# 📌 Initialize Dash App
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🌊 River Water Quality Dashboard", style={'textAlign': 'center', 'color': '#007bff', 'padding': '10px'}),

    # Select River
    html.Div([
        html.Label("🌍 Select River:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id="sungai_selector",
            options=[{"label": river, "value": river} for river in custom_variables.keys()],
            value=selected_river,
            clearable=False
        )
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

    # Select Dataset
    html.Div([
        html.Label("📂 Select Dataset:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id="dataset_selector",
            options=[
                {"label": "Raw Data", "value": "raw"},
                {"label": "Cleaned Data", "value": "cleaned"}
            ],
            value="raw",
            clearable=False
        )
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

    # Select Visualization
    html.Div([
        html.Label("📊 Select Visualization:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id="visualization_selector",
            options=[
                {"label": "Show Data Table", "value": "table"},
                {"label": "Variable Distribution (Histogram)", "value": "histogram"},
                {"label": "Trend Analysis (Daily/Weekly/Monthly)", "value": "trend"}
            ],
            value="table",
            clearable=False
        )
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

    # Select Parameter & Time Range
    html.Div([
        dcc.Dropdown(id="parameter_selector", clearable=False, style={'width': '45%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id="time_range_selector",
            options=[
                {"label": "Daily", "value": "daily"},
                {"label": "Weekly", "value": "weekly"},
                {"label": "Monthly", "value": "monthly"}
            ],
            value="daily",
            clearable=False,
            style={'width': '45%', 'display': 'inline-block', 'marginLeft': '10px'}
        ),
    ], style={'padding': '10px'}),

    # Display Button
    html.Button("Display Data", id="display_button", n_clicks=0, style={'marginTop': '10px'}),

    # Output
    html.Div(id="output_content", style={'marginTop': '20px'})
])

# 📌 CALLBACK: Update parameter options dynamically based on river and dataset selection
@app.callback(
    Output("parameter_selector", "options"),
    [Input("sungai_selector", "value"), Input("dataset_selector", "value")]
)
def update_parameter_options(selected_river, selected_dataset):
    parameters = custom_variables[selected_river][selected_dataset][1:]  # Exclude 'Timestamp'
    return [{"label": param, "value": param} for param in parameters]

# 📌 CALLBACK: Update content only when "Display Data" is clicked
@app.callback(
    Output("output_content", "children"),
    [Input("display_button", "n_clicks")],
    [State("sungai_selector", "value"), State("dataset_selector", "value"),
     State("visualization_selector", "value"), State("time_range_selector", "value"),
     State("parameter_selector", "value")]
)
def update_content(n_clicks, selected_river, selected_dataset, selected_visualization, selected_time_range, selected_parameter):
    if n_clicks == 0:
        return html.Div("Click 'Display Data' to show the results.")

    df_raw, df_cleaned, df_raw_daily, df_raw_weekly, df_raw_monthly, df_cleaned_daily, df_cleaned_weekly, df_cleaned_monthly = load_data(selected_river)
    df = df_raw if selected_dataset == "raw" else df_cleaned
    df_trend = {"daily": df_raw_daily, "weekly": df_raw_weekly, "monthly": df_raw_monthly}[selected_time_range]

    if selected_visualization == "table":
        return dash_table.DataTable(data=df.reset_index().to_dict("records"), columns=[{"name": i, "id": i} for i in df.columns])

    elif selected_visualization == "histogram":
        return dcc.Graph(figure=px.histogram(df, x=selected_parameter))

    elif selected_visualization == "trend":
        return dcc.Graph(figure=px.line(df_trend, x=df_trend.index, y=selected_parameter))

if __name__ == '__main__':
    app.run_server(debug=True)
