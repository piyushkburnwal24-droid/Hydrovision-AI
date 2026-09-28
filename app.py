import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
import tempfile
import os
import pandas as pd

from engine import HydroCalculator
from cv_processor import extract_stream_profile
from database import init_database, save_audit, load_audit_history
from report_generator import create_pdf

# Initialize database table when the app starts
init_database()

st.set_page_config(
    page_title="HydroVision AI | Optical Fluid Diagnostics",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom modern CSS styling for user interface
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 100%);
        color: #f1f5f9;
    }
    
    .app-header {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
    }
    
    .app-title {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #38bdf8 0%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
    }
    
    .metric-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .metric-lbl {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-top: 4px;
        font-weight: 600;
    }
    
    @keyframes pulse-glow {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(52, 211, 153, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }
    
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(52, 211, 153, 0.3);
        color: #34d399;
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #34d399;
        border-radius: 50%;
        animation: pulse-glow 2s infinite;
    }
    
    [data-testid="stSidebar"] {
        background-color: #070a12;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings
st.sidebar.markdown("### 🎛️ Control Panel")
fixture_choice = st.sidebar.selectbox("Fixture Profile Preset", list(HydroCalculator.PRESETS.keys()))
tariff_rate = st.sidebar.number_input("Water Tariff (₹ per 1,000 Liters)", value=80.0, step=5.0)
water_temp = st.sidebar.slider("Water Temperature (°C)", 5.0, 50.0, 25.0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📐 Calibration")
override_scale = st.sidebar.checkbox("Custom Pixel Scale Override")
custom_scale = st.sidebar.number_input("Scale Factor (mm/pixel)", value=0.45, step=0.01) if override_scale else None

# Main title header
st.markdown("""
    <div class="app-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="app-title">💧 HydroVision AI</h1>
                <p style="color: #94a3b8; margin-top: 6px; font-size: 1rem; margin-bottom: 0;">
                    Optical Fluid Diagnostics & Non-Invasive Flow Metering Engine
                </p>
            </div>
            <div>
                <div class="status-pill">
                    <div class="pulse-dot"></div> Engine Active & Ready
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

tab_live, tab_mesh, tab_history, tab_theory = st.tabs([
    "⚡ Live Jet Analysis", "🧊 3D Reconstruction", "📋 Audit Database & CSV", "🔬 Mathematical Model"
])

with tab_live:
    col_upload, col_telemetry = st.columns([1.1, 0.9], gap="large")
    
    with col_upload:
        st.markdown("### 📷 Stream Input & Processing")
        uploaded_media = st.file_uploader("Upload water stream capture (Image or Video)", type=["jpg", "jpeg", "png", "mp4", "mov"])
        
        frame_bgr = None
        profile_w = [30.0, 27.0, 24.0, 22.0, 20.0]
        h_val = 180.0
        
        if uploaded_media is not None:
            file_bytes = uploaded_media.read()
            ext = os.path.splitext(uploaded_media.name)[1].lower()
            
            if ext in [".mp4", ".mov", ".avi"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                cap = cv2.VideoCapture(tmp_path)
                ret, frame_bgr = cap.read()
                cap.release()
                try: os.remove(tmp_path)
                except: pass
            else:
                arr = np.asarray(bytearray(file_bytes), dtype=np.uint8)
                frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                
            if frame_bgr is not None:
                annotated_img, profile_w, h_val, fallback_triggered = extract_stream_profile(frame_bgr)
                st.image(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB), caption="OpenCV Edge Contraction Analysis", use_container_width=True)
                if fallback_triggered:
                    st.warning("Notice: Clear stream edges not fully resolved; using adaptive profile estimations.")
        else:
            dummy_img = np.zeros((400, 400, 3), dtype=np.uint8) + 25
            cv2.putText(dummy_img, "Awaiting Media Upload...", (65, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
            st.image(cv2.cvtColor(dummy_img, cv2.COLOR_BGR2RGB), caption="Idle State Preview", use_container_width=True)

    with col_telemetry:
        st.markdown("### 📊 Diagnostic Telemetry")
        calc = HydroCalculator(fixture_choice, custom_scale, water_temp, tariff_rate)
        results = calc.compute(profile_w, h_val)
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=results["flow_lpm"],
            title={'text': "Discharge Rate (LPM)", 'font': {'color': '#f1f5f9', 'size': 14}},
            number={'font': {'color': '#38bdf8', 'size': 28, 'family': 'JetBrains Mono'}},
            gauge={
                'axis': {'range': [0, 25], 'tickcolor': "#94a3b8"},
                'bar': {'color': "#38bdf8"},
                'bgcolor': "rgba(15, 23, 42, 0.6)", 
                'borderwidth': 0,
                'steps': [
                    {'range': [0, calc.target_lpm], 'color': "rgba(52, 211, 153, 0.15)"},
                    {'range': [calc.target_lpm, 15], 'color': "rgba(251, 191, 36, 0.15)"},
                    {'range': [15, 25], 'color': "rgba(248, 113, 113, 0.15)"}
                ]
            }
        ))
        fig_gauge.update_layout(height=185, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="glass-card" style="text-align: center;"><div class="metric-val">{results["pressure_bar"]}</div><div class="metric-lbl">Pressure (Bar)</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="glass-card" style="text-align: center;"><div class="metric-val">{results["reynolds"]}</div><div class="metric-lbl">Reynolds (Re)</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="glass-card" style="text-align: center;"><div class="metric-val">{results["clog_pct"]}%</div><div class="metric-lbl">Clog Index</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        status_color = "#34d399" if results["status"] == "OPTIMAL_EFFICIENCY" else ("#fbbf24" if "RESTRICTED" in results["status"] else "#f87171")
        st.markdown(f"**Diagnostic Status:** <span style='color: {status_color}; font-weight: 700;'>{results['status']}</span>", unsafe_allow_html=True)
        st.info(results["action"])
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("💾 Save to Database", use_container_width=True):
                save_audit(
                    fixture_choice, results["flow_lpm"], results["pressure_bar"], 
                    results["reynolds"], results["clog_pct"], results["status"], 
                    results["monthly_waste_l"], results["cost_inr"]
                )
                st.success("Record saved successfully!")
        with c_btn2:
            pdf_file_path = create_pdf(results, fixture_choice)
            if os.path.exists(pdf_file_path):
                with open(pdf_file_path, "rb") as f:
                    st.download_button("📄 Export PDF", f, file_name="HydroVision_Report.pdf", mime="application/pdf", use_container_width=True)

with tab_mesh:
    st.markdown("### 🧊 3D Water Jet Contraction Surface Mesh")
    try:
        z_coords = np.linspace(0, 10, 30)
        theta_angles = np.linspace(0, 2 * np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta_angles, z_coords)
        
        r0 = max(0.5, results["profile_mm"][0] / 2.0)
        r_end = max(0.2, results["profile_mm"][-1] / 2.0)
        
        radius_z = r0 * (1 + (z_grid / 10.0) * ((r_end / r0)**4 - 1))**(-0.25)
        x_mesh = radius_z * np.cos(theta_grid)
        y_mesh = radius_z * np.sin(theta_grid)
        
        fig_3d = go.Figure(data=[go.Surface(x=x_mesh, y=y_mesh, z=z_grid, colorscale='Tealgrn')])
        fig_3d.update_layout(
            title="Optical Sliced Contraction Profile",
            scene=dict(xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Length (cm)", aspectratio=dict(x=1, y=1, z=2)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_3d, use_container_width=True)
    except Exception as e:
        st.error(f"3D rendering error: {e}")

with tab_history:
    st.markdown("### 📋 Stored Audit History & CSV Export")
    records = load_audit_history()
    if records:
        df_history = pd.DataFrame(records, columns=["Timestamp", "Fixture", "Flow (LPM)", "Pressure (Bar)", "Reynolds", "Clog %", "Status", "Cost (INR)"])
        st.dataframe(df_history, use_container_width=True)
        
        csv_data = df_history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Audit Data as CSV", csv_data, file_name="hydrovision_audit_logs.csv", mime="text/csv")
    else:
        st.info("No audit logs found in the database yet. Run an analysis and save an entry.")

with tab_theory:
    st.markdown("### 🔬 Fluid Dynamics & Governing Equations")
    st.markdown("""
    #### 1. Inverted Continuity & Torricelli Velocity Equation
    For a liquid stream accelerating vertically under the influence of gravity ($g$):
    * **Continuity Equation:** $A_0 v_0 = A(y) v(y) \implies v(y) = v_0 \left(\frac{d_0}{d(y)}\right)^2$
    * **Torricelli's Theorem:** $v(y)^2 = v_0^2 + 2gy$
    * **Solved Initial Velocity ($v_0$):** $v_0 = \sqrt{\frac{2gy}{\left(\frac{d_0}{d(y)}\right)^4 - 1}}$

    #### 2. Reynolds Number & Flow Regime Classification
    The flow regime is determined using temperature-corrected dynamic viscosity ($\mu(T)$) and fluid density ($\rho(T)$):
    $Re = \frac{\rho \cdot v_0 \cdot d_0}{\mu}$
    * $Re < 2300$: Laminar flow regime
    * $2300 \le Re \le 4000$: Transitional jet behavior
    * $Re > 4000$: Turbulent jet structure
    """)