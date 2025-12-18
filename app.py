import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vaccine Cold Chain Dashboard",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* HIDE TOP BAR & FOOTER */
    header {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* --- REMOVE HOVER LINKS ON HEADERS --- */
    /* This targets the specific anchor link inside all headers */
    .anchor-link { display: none !important; }
    
    /* This targets any 'a' tag inside headers h1-h6 to be sure */
    h1 > a, h2 > a, h3 > a, h4 > a, h5 > a, h6 > a {
        display: none !important;
        opacity: 0 !important;
        pointer-events: none;
    }
    
    /* Additional target for Streamlit's markdown container links */
    [data-testid="stMarkdownContainer"] a.anchor-link {
        display: none !important;
    }
    
    /* STYLE BUTTONS */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        margin-bottom: 5px;
    }

    /* CUSTOM FOOTER STYLE */
    .footer {
        width: 100%;
        background-color: transparent;
        color: #808080;
        text-align: center;
        padding: 20px;
        font-size: 12px;
        margin-top: 50px;
        border-top: 1px solid #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. LOAD DATA
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('Vaccine_Cold_Chain_Dashboard_Data.csv')
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    return df.iloc[::10, :]

df = load_data()

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTION (KPI CARD)
# -----------------------------------------------------------------------------
def custom_metric_card(label, value, delta_text, status):
    if status == 'safe':
        color = "#00CC96" # Green
        arrow = "▼"
    else:
        color = "#EF553B" # Red
        arrow = "▲"
    
    return f"""
    <div style="border: 1px solid #e6e6e6; border-radius: 10px; padding: 15px; background-color: transparent;">
        <p style="margin: 0; font-size: 14px; color: gray;">{label}</p>
        <p style="margin: 0; font-size: 28px; font-weight: bold;">{value}</p>
        <p style="margin: 0; font-size: 14px; color: {color}; font-weight: 500;">
            {arrow} {delta_text}
        </p>
    </div>
    """

# -----------------------------------------------------------------------------
# 4. DASHBOARD LAYOUT
# -----------------------------------------------------------------------------
st.title("Vaccine Cold Chain Integrity Monitor")
st.markdown("**Topic:** Vaccine Cold Chain Integrity Dashboard: Visualizing temperature logs during vaccine transport.")

if 'selected_location' not in st.session_state:
    st.session_state.selected_location = 'All Locations'

# --- A. TOP CONTAINER (KPIs) ---
kpi_container = st.container()

st.divider()

# --- B. MAIN COLUMNS (Left: Buttons | Right: Map) ---
col_left, col_right = st.columns([1, 4], gap="medium")

# LEFT: BUTTONS
with col_left:
    st.subheader("📍 Select Stage")
    location_list = ['All Locations'] + list(df['Location_Name'].unique())
    for loc in location_list:
        is_active = (loc == st.session_state.selected_location)
        button_type = "primary" if is_active else "secondary"
        if st.button(loc, key=loc, type=button_type, use_container_width=True):
            st.session_state.selected_location = loc
            st.rerun() 

# FILTER DATA
df_filtered = df.copy()
if st.session_state.selected_location != 'All Locations':
    df_filtered = df_filtered[df_filtered['Location_Name'] == st.session_state.selected_location]

# RIGHT: MAP
with col_right:
    st.subheader("Transport Route Map")
    if not df_filtered.empty:
        fig_map = px.scatter_mapbox(
            df_filtered, 
            lat="Latitude", lon="Longitude",
            color="Status",
            hover_name="Location_Name",
            zoom=3,
            color_discrete_map={'OK': '#00CC96', 'WARNING': '#EF553B'},
            height=400
        )
        fig_map.update_traces(marker=dict(size=9)) 
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No location data available.")

# --- C. POPULATE KPIs ---
with kpi_container:
    if not df_filtered.empty:
        avg_temp = df_filtered['Pod20'].mean()
        max_temp = df_filtered['Pod20'].max()
        total_breaches = len(df_filtered[df_filtered['Status'] == 'WARNING'])
    else:
        avg_temp, max_temp, total_breaches = 0, 0, 0

    if avg_temp <= -60:
        kpi1_html = custom_metric_card("Avg Temperature", f"{avg_temp:.2f} °C", "Optimal Range", "safe")
    else:
        kpi1_html = custom_metric_card("Avg Temperature", f"{avg_temp:.2f} °C", f"Too Warm (+{avg_temp - (-60):.1f}°C)", "danger")

    if max_temp <= -60:
        kpi2_html = custom_metric_card("Max Temperature", f"{max_temp:.2f} °C", "Within Limit (< -60°C)", "safe")
    else:
        kpi2_html = custom_metric_card("Max Temperature", f"{max_temp:.2f} °C", "Exceeds Limit", "danger")

    if total_breaches == 0:
        kpi3_html = custom_metric_card("Breach Events", "0", "No Incidents", "safe")
    else:
        kpi3_html = custom_metric_card("Breach Events", f"{total_breaches}", "Alerts Detected", "danger")

    k1, k2, k3 = st.columns(3)
    k1.markdown(kpi1_html, unsafe_allow_html=True)
    k2.markdown(kpi2_html, unsafe_allow_html=True)
    k3.markdown(kpi3_html, unsafe_allow_html=True)

st.divider()

# --- D. MIDDLE SECTION: CHARTS (Line Graph | Bar Graph) ---
col_mid_left, col_mid_right = st.columns(2, gap="medium")

# 1. Line Graph (Time Trend)
with col_mid_left:
    st.subheader("Temperature Trends")
    if not df_filtered.empty:
        fig_temp = px.line(df_filtered, x='DateTime', y='Pod20', 
                           color_discrete_sequence=['#00CC96'])
        fig_temp.add_hline(y=-60, line_dash="dash", line_color="red", annotation_text="Limit (-60C)")
        fig_temp.update_traces(line=dict(width=2.5)) 
        fig_temp.update_layout(yaxis_title="Temp (°C)", xaxis_title="Time", height=350, margin=dict(l=20, r=20, t=10, b=20))
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.warning("No data.")

# 2. Bar Graph (Location Comparison)
with col_mid_right:
    st.subheader("Average Temperature by Location")
    if not df_filtered.empty:
        avg_loc_df = df_filtered.groupby('Location_Name')['Pod20'].mean().reset_index().sort_values('Pod20')
        
        fig_bar = px.bar(
            avg_loc_df, 
            x='Location_Name', 
            y='Pod20', 
            color='Pod20',
            color_continuous_scale='RdBu_r', 
            text_auto='.1f'
        )
        fig_bar.update_layout(
            yaxis_title="Avg Temp (°C)", 
            xaxis_title=None,
            coloraxis_showscale=False,
            height=350,
            margin=dict(l=20, r=20, t=10, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No data.")

st.divider()

# --- E. BOTTOM SECTION: TABLE (Full Width) ---
st.subheader("Detailed Shipment Log")
if not df_filtered.empty:
    table_df = df_filtered[['DateTime', 'Location_Name', 'Pod20', 'Status']].copy()
    table_df.columns = ['Timestamp', 'Location', 'Temperature (°C)', 'Status']
    
    def highlight_status(val):
        color = '#EF553B' if val == 'WARNING' else '#00CC96'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        table_df.style.map(highlight_status, subset=['Status']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No data to display.")

# -----------------------------------------------------------------------------
# 6. FOOTER
# -----------------------------------------------------------------------------
st.markdown("""
<div class="footer">
    <p>Data Source: Scientific Data (Nature.com) | ITE3 Final Project</p>
    <p>Sun, J., Zhang, M., Gehl, A. et al. Dataset of ultralow temperature refrigeration for COVID 19 vaccine distribution solution. Sci Data 9, 67 (2022). https://doi.org/10.1038/s41597-022-01167-y</p>
</div>
""", unsafe_allow_html=True)