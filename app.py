import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests
import plotly.graph_objects as go
import base64

OPENWEATHER_API_KEY = "0d5e6c3a66d3d41adac3ddf935534d8d"

st.set_page_config(page_title="SahelCropCast", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

bg = get_base64_image("background.jpg")
bg_css = f"""<style>
.stApp {{
    background-image: linear-gradient(rgba(0,0,0,0.78), rgba(0,0,0,0.78)),
                      url("data:image/jpeg;base64,{bg}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
</style>""" if bg else ""

st.markdown(bg_css + """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #e8f5e9; }
[data-testid="stSidebar"] { background: rgba(8,25,8,0.95) !important; border-right: 1px solid #2e7d32; }
[data-testid="stSidebar"] * { color: #e8f5e9 !important; }
.main-title { font-family:'Playfair Display',serif; font-size:3.2rem; font-weight:700;
    background:linear-gradient(90deg,#69f0ae,#b9f6ca,#fff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; }
.subtitle { text-align:center; color:#a5d6a7; font-size:1rem; letter-spacing:3px;
    text-transform:uppercase; margin-bottom:2rem; }
.metric-card { background:rgba(27,58,43,0.88); border:1px solid #2e7d32; border-radius:16px;
    padding:1.2rem; margin:0.4rem 0; backdrop-filter:blur(8px); }
.metric-card h4 { color:#81c784; font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; margin:0 0 4px; }
.metric-card h2 { color:#69f0ae; font-size:1.8rem; font-family:'Playfair Display',serif; margin:0; }
.weather-card { background:rgba(20,45,65,0.88); border:1px solid #0288d1; border-radius:16px;
    padding:1.2rem; margin:0.4rem 0; text-align:center; backdrop-filter:blur(8px); }
.weather-card h4 { color:#81d4fa; font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; margin:0 0 4px; }
.weather-card h2 { color:#40c4ff; font-size:1.8rem; font-family:'Playfair Display',serif; margin:0; }
.result-box { background:rgba(20,60,35,0.92); border:2px solid #69f0ae; border-radius:20px;
    padding:2rem; text-align:center; box-shadow:0 0 40px rgba(105,240,174,0.2);
    margin:1rem 0; backdrop-filter:blur(10px); }
.result-box h1 { font-family:'Playfair Display',serif; font-size:3rem; color:#69f0ae; margin:0; }
.result-box p { color:#b9f6ca; margin-top:0.3rem; }
.info-box { background:rgba(27,58,43,0.85); border-left:4px solid #69f0ae;
    border-radius:0 12px 12px 0; padding:0.8rem 1rem; margin:0.4rem 0; color:#e8f5e9; }
.section-header { font-family:'Playfair Display',serif; color:#69f0ae; font-size:1.4rem;
    margin-bottom:1rem; border-bottom:1px solid #2e7d32; padding-bottom:0.5rem; }
.stButton > button { background:linear-gradient(135deg,#2e7d32,#43a047) !important;
    color:white !important; border:none !important; border-radius:12px !important;
    padding:0.7rem 2rem !important; font-weight:500 !important; width:100% !important; }
.stTabs [data-baseweb="tab-list"] { background:rgba(10,30,15,0.88); border-radius:12px; padding:4px; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#81c784 !important; border-radius:8px; }
.stTabs [aria-selected="true"] { background:#2e7d32 !important; color:white !important; }
.stSelectbox > div > div { background:rgba(27,58,43,0.92) !important; border:1px solid #2e7d32 !important; color:#e8f5e9 !important; border-radius:10px !important; }
.stTextInput > div > div > input { background:rgba(27,58,43,0.92) !important; border:1px solid #2e7d32 !important; color:#e8f5e9 !important; border-radius:10px !important; }
</style>""", unsafe_allow_html=True)

@st.cache_resource
def load_models():
    with open('rf_model.pkl','rb') as f: rf=pickle.load(f)
    with open('le_area.pkl','rb') as f: le_area=pickle.load(f)
    with open('le_item.pkl','rb') as f: le_item=pickle.load(f)
    return rf, le_area, le_item

@st.cache_data
def load_data():
    return pd.read_csv('final_dataset.csv')

try:
    rf_model, le_area, le_item = load_models()
    df = load_data()
    countries = sorted(df['Area'].unique().tolist())
    crops = sorted(df['Item'].unique().tolist())
except Exception as e:
    st.error(f"Error loading models: {e}")
    st.stop()

RAINFALL_EST = {
    "Cameroon":1604,"Nigeria":1150,"Ghana":1187,"Senegal":686,
    "Mali":282,"Burkina Faso":748,"Niger":151,"Guinea":1651,
    "Benin":1039,"Togo":1168,"Sierra Leone":2526,"Liberia":2391,
    "Central African Republic":1343,"Congo":1646,"Gabon":1831,
}

def get_weather(city, country):
    try:
        r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={OPENWEATHER_API_KEY}&units=metric", timeout=10)
        d = r.json()
        if r.status_code == 200:
            return {"temp":round(d["main"]["temp"],1),"humidity":d["main"]["humidity"],
                    "description":d["weather"][0]["description"].title(),"city":d["name"]}
    except: pass
    return None

# HEADER
st.markdown("<div class='main-title'>🌾 SahelCropCast</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI-Powered · Crop Yield Prediction · West & Central Africa · NASA + FAO Data</div>", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("""<div style='text-align:center; padding:1rem 0;'>
        <div style='font-size:2.5rem;'>🌾</div>
        <div style='font-family:Playfair Display,serif; font-size:1.2rem; color:#69f0ae; font-weight:700;'>SahelCropCast</div>
        <div style='font-size:0.7rem; color:#81c784; letter-spacing:2px;'>AGRICULTURAL AI SYSTEM</div>
    </div><hr style='border-color:#2e7d32; opacity:0.4;'>""", unsafe_allow_html=True)

    st.markdown("### 🌍 Location")
    selected_country = st.selectbox("Select Country", countries,
        index=countries.index("Cameroon") if "Cameroon" in countries else 0)
    city_input = st.text_input("Enter City/Region", placeholder="e.g. Yaoundé, Bamenda...")

    st.markdown("### 🌾 Crop & Year")
    country_crops = sorted(df[df['Area']==selected_country]['Item'].unique().tolist())
    selected_crop = st.selectbox("Select Crop", country_crops)
    selected_year = st.slider("Select Year", 1990, 2030, 2024)

    st.markdown("### 🌱 Soil Type")
    soil_type = st.selectbox("Soil Type", ["Loamy Soil","Clay Soil","Sandy Soil","Silt Soil","Peaty Soil","Chalky Soil"])

    st.markdown("<hr style='border-color:#2e7d32; opacity:0.4;'>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: fetch_weather_btn = st.button("🌤️ Weather")
    with c2: predict_btn = st.button("🔍 Predict")

    st.markdown("<hr style='border-color:#2e7d32; opacity:0.4;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='info-box'>🌍 <b>{df['Area'].nunique()}</b> Countries</div>
    <div class='info-box'>🌾 <b>{df['Item'].nunique()}</b> Crop Types</div>
    <div class='info-box'>📋 <b>{len(df):,}</b> Records</div>
    <div class='info-box'>📅 <b>1990 – 2024</b></div>
    <div class='info-box'>🛰️ <b>NASA POWER + FAO</b></div>
    <div class='info-box'>🤖 <b>Random Forest Model</b></div>
    """, unsafe_allow_html=True)

if 'weather_data' not in st.session_state: st.session_state.weather_data = None
if 'rainfall' not in st.session_state: st.session_state.rainfall = float(RAINFALL_EST.get(selected_country, 1000))
if 'temperature' not in st.session_state: st.session_state.temperature = 25.0

country_data = df[df['Area']==selected_country]
soil_moisture = country_data['soil_moisture'].mean() if len(country_data)>0 else 0.5
temp_range = country_data['temp_range_c'].mean() if len(country_data)>0 else 10.0

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌤️ Weather", "🔮 Predictor", "📈 Analytics", "🧠 About", "👤 About Me"])

# ── TAB 1 WEATHER ──
with tab1:
    st.markdown("<div class='section-header'>🌤️ Real-Time Weather & NASA Climate Data</div>", unsafe_allow_html=True)
    if fetch_weather_btn and city_input:
        with st.spinner("Fetching weather..."):
            weather = get_weather(city_input, selected_country)
            if weather:
                st.session_state.weather_data = weather
                st.session_state.temperature = weather['temp']
                st.success(f"✅ Weather fetched for {weather['city']}")
            else:
                st.warning("Could not fetch. Using estimated values.")

    w = st.session_state.weather_data
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f"<div class='weather-card'><h4>🌡️ Temperature</h4><h2>{st.session_state.temperature}°C</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='weather-card'><h4>💧 Humidity</h4><h2>{w['humidity'] if w else '–'}{'%' if w else ''}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='weather-card'><h4>🌧️ Annual Rainfall</h4><h2>{st.session_state.rainfall:.0f} mm</h2></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='weather-card'><h4>🌤️ Condition</h4><h2 style='font-size:1rem; margin-top:0.5rem;'>{w['description'] if w else 'Estimated'}</h2></div>", unsafe_allow_html=True)

    if not w: st.info("Enter a city and click 'Weather' for real-time data.")

    st.markdown(f"<br><div class='section-header'>🛰️ NASA Climate Profile — {selected_country}</div>", unsafe_allow_html=True)
    if len(country_data) > 0:
        yearly = country_data.groupby('Year')[['rainfall_mm_year','avg_temp_c']].mean().reset_index()
        cl = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'color':'#e8f5e9'},
                  height=250,margin=dict(t=40,b=20,l=20,r=20),
                  xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784'),
                  yaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784'))
        c1,c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Scatter(x=yearly['Year'],y=yearly['rainfall_mm_year'],mode='lines+markers',
                line=dict(color='#40c4ff',width=2),fill='tozeroy',fillcolor='rgba(64,196,255,0.1)'))
            fig.update_layout(title=dict(text='Annual Rainfall (mm)',font=dict(color='#69f0ae')),**cl)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = go.Figure(go.Scatter(x=yearly['Year'],y=yearly['avg_temp_c'],mode='lines+markers',
                line=dict(color='#ff6e40',width=2),fill='tozeroy',fillcolor='rgba(255,110,64,0.1)'))
            fig.update_layout(title=dict(text='Avg Temperature (°C)',font=dict(color='#69f0ae')),**cl)
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 2 PREDICTOR ──
with tab2:
    if predict_btn:
        try:
            area_enc = le_area.transform([selected_country])[0]
            item_enc = le_item.transform([selected_crop])[0]
            features = np.array([[area_enc, item_enc, selected_year,
                                   st.session_state.rainfall, st.session_state.temperature,
                                   soil_moisture, temp_range]])
            pred = rf_model.predict(features)[0]
            cdata = df[(df['Area']==selected_country)&(df['Item']==selected_crop)]['yield_kg_per_ha']
            avg = cdata.mean() if len(cdata)>0 else pred
            delta = ((pred - avg) / avg) * 100

            if pred >= avg*1.1: status,sc = "🟢 Excellent Yield","#69f0ae"
            elif pred >= avg*0.9: status,sc = "🟡 Average Yield","#ffeb3b"
            else: status,sc = "🔴 Below Average","#ef9a9a"

            st.session_state.prediction = pred
            st.session_state.avg_yield = avg

            st.markdown(f"""<div class='result-box'>
                <p style='color:#81c784; font-size:0.85rem; text-transform:uppercase; letter-spacing:2px;'>
                    Random Forest · {selected_crop} · {selected_country} · {selected_year}</p>
                <h1>{pred:,.0f}</h1>
                <p>kg/ha &nbsp;|&nbsp; <span style='color:{sc};'>{status}</span></p>
            </div>""", unsafe_allow_html=True)

            sign = "+" if delta >= 0 else ""
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(f"<div class='metric-card'><h4>vs Historical Avg</h4><h2 style='color:{sc};'>{sign}{delta:.1f}%</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-card'><h4>🌡️ Temperature</h4><h2>{st.session_state.temperature}°C</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card'><h4>🌧️ Rainfall</h4><h2>{st.session_state.rainfall:.0f} mm</h2></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='metric-card'><h4>💧 Soil Moisture</h4><h2>{soil_moisture:.2f}</h2></div>", unsafe_allow_html=True)

            cl = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'color':'#e8f5e9'})
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("<div class='section-header'>📊 Yield Gauge</div>", unsafe_allow_html=True)
                max_val = df[df['Item']==selected_crop]['yield_kg_per_ha'].max()
                fig = go.Figure(go.Indicator(mode="gauge+number+delta",value=pred,
                    delta={'reference':avg,'valueformat':',.0f'},
                    number={'valueformat':',.0f','suffix':' kg/ha','font':{'color':'#69f0ae','size':22}},
                    gauge={'axis':{'range':[0,max_val*1.2],'tickcolor':'#81c784','tickfont':{'color':'#81c784'}},
                           'bar':{'color':'#69f0ae','thickness':0.3},
                           'bgcolor':'rgba(27,58,43,0.5)','bordercolor':'#2e7d32',
                           'steps':[{'range':[0,avg*0.9],'color':'rgba(62,31,31,0.5)'},
                                    {'range':[avg*0.9,avg*1.1],'color':'rgba(62,62,31,0.5)'},
                                    {'range':[avg*1.1,max_val*1.2],'color':'rgba(31,62,31,0.5)'}],
                           'threshold':{'line':{'color':'#ffeb3b','width':3},'thickness':0.75,'value':avg}}))
                fig.update_layout(**cl,height=280,margin=dict(t=30,b=10,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("<div class='section-header'>📈 Historical Trend</div>", unsafe_allow_html=True)
                hist = df[(df['Area']==selected_country)&(df['Item']==selected_crop)].groupby('Year')['yield_kg_per_ha'].mean().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist['Year'],y=hist['yield_kg_per_ha'],
                    mode='lines+markers',name='Historical',
                    line=dict(color='#69f0ae',width=2.5),
                    fill='tozeroy',fillcolor='rgba(105,240,174,0.08)'))
                fig.add_trace(go.Scatter(x=[selected_year],y=[pred],mode='markers',name='Prediction',
                    marker=dict(size=16,color='#ffeb3b',symbol='star',line=dict(color='white',width=1))))
                fig.update_layout(**cl,height=280,margin=dict(t=20,b=20,l=20,r=20),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',title='Yield (kg/ha)'),
                    legend=dict(bgcolor='rgba(27,58,43,0.7)',bordercolor='#2e7d32'))
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Prediction error: {str(e)}")
    else:
        st.markdown("""<div style='text-align:center; padding:4rem 2rem;'>
            <div style='font-size:5rem;'>🔮</div>
            <div style='font-family:Playfair Display,serif; font-size:1.8rem; color:#69f0ae; margin:1rem;'>Ready to Predict</div>
            <div style='color:#a5d6a7;'>Select country, crop and year in the sidebar, then click <b>Predict</b>!</div>
        </div>""", unsafe_allow_html=True)

# ── TAB 3 ANALYTICS ──
with tab3:
    st.markdown("<div class='section-header'>🌍 West & Central Africa Analytics</div>", unsafe_allow_html=True)
    cl = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'color':'#e8f5e9'})
    c1,c2 = st.columns(2)
    with c1:
        top_c = df.groupby('Area')['yield_kg_per_ha'].mean().sort_values(ascending=False).reset_index()
        fig = go.Figure(go.Bar(x=top_c['yield_kg_per_ha'],y=top_c['Area'],orientation='h',
            marker=dict(color=top_c['yield_kg_per_ha'],colorscale=[[0,'rgba(27,58,43,0.8)'],[1,'#69f0ae']]),
            text=[f'{v:,.0f}' for v in top_c['yield_kg_per_ha']],textposition='outside',textfont=dict(color='#e8f5e9',size=10)))
        fig.update_layout(**cl,title=dict(text='Avg Yield by Country (kg/ha)',font=dict(color='#69f0ae')),
            height=380,margin=dict(t=40,b=20,l=20,r=80),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784'),yaxis=dict(color='#81c784'))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        top_cr = df.groupby('Item')['yield_kg_per_ha'].mean().sort_values(ascending=False).head(15).reset_index()
        fig = go.Figure(go.Bar(x=top_cr['Item'],y=top_cr['yield_kg_per_ha'],
            marker=dict(color=top_cr['yield_kg_per_ha'],colorscale=[[0,'rgba(27,58,43,0.8)'],[1,'#69f0ae']]),
            text=[f'{v:,.0f}' for v in top_cr['yield_kg_per_ha']],textposition='outside',textfont=dict(color='#e8f5e9',size=9)))
        fig.update_layout(**cl,title=dict(text='Top 15 Crops by Avg Yield (kg/ha)',font=dict(color='#69f0ae')),
            height=380,margin=dict(t=40,b=80,l=20,r=20),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',tickangle=45),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',title='kg/ha'))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>📅 Yield Trends Over Time</div>", unsafe_allow_html=True)
    default_c = [c for c in ["Cameroon","Nigeria","Ghana"] if c in countries]
    selected_multi = st.multiselect("Select countries to compare", countries, default=default_c)
    crop_trend = st.selectbox("Select crop", crops)
    if selected_multi:
        colors = ['#69f0ae','#40c4ff','#ffeb3b','#ff6e40','#ea80fc','#b9f6ca','#ffab40']
        fig = go.Figure()
        for i,c in enumerate(selected_multi):
            cd = df[(df['Area']==c)&(df['Item']==crop_trend)].groupby('Year')['yield_kg_per_ha'].mean().reset_index()
            if len(cd)>0:
                fig.add_trace(go.Scatter(x=cd['Year'],y=cd['yield_kg_per_ha'],mode='lines+markers',
                    name=c,line=dict(color=colors[i%len(colors)],width=2),marker=dict(size=5)))
        fig.update_layout(**cl,height=380,margin=dict(t=20,b=20,l=20,r=20),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',title='Year'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',title='Yield (kg/ha)'),
            legend=dict(bgcolor='rgba(27,58,43,0.7)',bordercolor='#2e7d32'))
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 4 ABOUT ──
with tab4:
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("<div class='section-header'>🧠 Model Details</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='info-box'>🤖 <b>Algorithm:</b> Random Forest Regressor</div>
        <div class='info-box'>🌳 <b>Number of Trees:</b> 15 Estimators</div>
        <div class='info-box'>📊 <b>Features:</b> Country, Crop, Year, Rainfall, Temperature, Soil Moisture, Temp Range</div>
        <div class='info-box'>🎯 <b>Target:</b> Yield (kg/ha)</div>
        <div class='info-box'>✂️ <b>Train/Test Split:</b> 80% / 20%</div>
        <div class='info-box'>🛰️ <b>Climate:</b> NASA POWER (1990–2024)</div>
        <div class='info-box'>🌾 <b>Yield:</b> FAO FAOSTAT (1990–2024)</div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='section-header'>📋 Model Performance</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='info-box'>🏆 <b>R² Score:</b> 0.9724</div>
        <div class='info-box'>📊 <b>MAE:</b> 657.41 kg/ha</div>
        <div class='info-box'>📊 <b>RMSE:</b> 1,871.10 kg/ha</div>
        <div class='info-box'>🌍 <b>Countries:</b> {df['Area'].nunique()} West & Central African</div>
        <div class='info-box'>🌾 <b>Crop Types:</b> {df['Item'].nunique()}</div>
        <div class='info-box'>📋 <b>Total Records:</b> {len(df):,}</div>
        <div class='info-box'>📅 <b>Data Range:</b> 1990 – 2024</div>
        """, unsafe_allow_html=True)

    st.markdown("<br><div class='section-header'>⚙️ Feature Importance</div>", unsafe_allow_html=True)
    importances = rf_model.feature_importances_
    feat_names = ['Country','Crop Type','Year','Rainfall','Temperature','Soil Moisture','Temp Range']
    colors = ['#69f0ae','#40c4ff','#ffeb3b','#ff6e40','#ea80fc','#b9f6ca','#ffab40']
    cl = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'color':'#e8f5e9'})
    fig = go.Figure(go.Bar(x=importances,y=feat_names,orientation='h',marker=dict(color=colors),
        text=[f'{v:.1%}' for v in importances],textposition='outside',textfont=dict(color='#e8f5e9',size=12)))
    fig.update_layout(**cl,height=300,margin=dict(t=10,b=10,l=20,r=80),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)',color='#81c784',tickformat='.0%',range=[0,max(importances)*1.3]),
        yaxis=dict(color='#81c784'))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""<div style='text-align:center; color:#4a7c59; font-size:0.8rem; padding:1rem;'>
        Streamlit · Scikit-learn · Plotly · OpenWeatherMap · NASA POWER · FAO FAOSTAT<br>
        🌍 West & Central Africa Crop Yield Prediction · University of Bamenda · COLTECH · 2026
    </div>""", unsafe_allow_html=True)

# ── TAB 5 ABOUT ME ──
with tab5:
    st.markdown("<div class='section-header'>👤 About the Developer</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _,c2,_ = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div style='background:rgba(27,58,43,0.92); border:2px solid #69f0ae; border-radius:24px;
                    padding:2.5rem; text-align:center; box-shadow:0 0 40px rgba(105,240,174,0.15);
                    backdrop-filter:blur(10px);'>
            <div style='font-size:5rem; margin-bottom:1rem;'>👨‍💻</div>
            <div style='font-family:Playfair Display,serif; font-size:2rem; color:#69f0ae; font-weight:700;'>
                SHU CYRIL NDONWI</div>
            <div style='color:#81c784; font-size:0.85rem; letter-spacing:3px; text-transform:uppercase; margin-bottom:2rem;'>
                Computer Engineering & Networks · BSc 2026</div>
            <hr style='border-color:#2e7d32; opacity:0.4; margin-bottom:1.5rem;'>
            <div class='info-box'>🎓 <b>University:</b> University of Bamenda — COLTECH</div>
            <div class='info-box'>🏛️ <b>Department:</b> Computer Engineering & Networks</div>
            <div class='info-box'>🪪 <b>Registration:</b> UBa23PH131</div>
            <div class='info-box'>📱 <b>Phone:</b> +237 676980221</div>
            <div class='info-box'>📸 <b>Instagram:</b> @Lgt_cyrilo</div>
            <hr style='border-color:#2e7d32; opacity:0.4; margin:1.5rem 0;'>
            <div style='color:#4a7c59; font-size:0.85rem; line-height:1.8;'>
                📌 Project: Crop Yield Prediction Using Machine Learning<br>
                👨‍🏫 Supervisor: Mr. AYUNUI LANDRY (Assistant Lecturer)<br>
                🌐 <a href='https://cropcast-cwa-ogvhhrvkwcgf6oukms8nwx.streamlit.app/' style='color:#69f0ae;'>Live App</a><br>
                📅 June 2026
            </div>
        </div>""", unsafe_allow_html=True)
