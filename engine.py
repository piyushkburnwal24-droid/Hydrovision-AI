# engine.py
import numpy as np

class HydroCalculator:
    """
    Core physics and telemetry engine for Hydrovision-AI.
    Computes discharge rate, pressure, Reynolds number, and clog index
    with rigorous physical boundary clamps.
    """
    
    # Fixture presets expected by the user interface UI
    PRESETS = {
        "Standard Kitchen Tap": {"baseline_width": 12.0, "nominal_flow": 3.8},
        "Bathroom Faucet": {"baseline_width": 9.0, "nominal_flow": 2.5},
        "Shower Head": {"baseline_width": 20.0, "nominal_flow": 8.0}
    }

    def __init__(self, fixture_choice="Standard Kitchen Tap", custom_scale=12.0, water_temp=25.0, tariff_rate=0.0, cv_metrics=None):
        self.fixture_choice = fixture_choice
        self.custom_scale = custom_scale
        self.water_temp = water_temp
        self.tariff_rate = tariff_rate
        self.cv_metrics = cv_metrics or {}
        self.preset = self.PRESETS.get(fixture_choice, {"baseline_width": custom_scale, "nominal_flow": 3.8})

    @staticmethod
    def compute_diagnostics(cv_metrics, preset_name="Standard Kitchen Tap"):
        """
        Computes fluid dynamics telemetry based on optical stream measurements.
        """
        width_px = cv_metrics.get("stream_width_px", 12.0)
        continuity = cv_metrics.get("continuity_score", 85.0)
        
        preset_data = HydroCalculator.PRESETS.get(preset_name, HydroCalculator.PRESETS["Standard Kitchen Tap"])
        baseline_width = preset_data["baseline_width"]
        nominal_flow = preset_data["nominal_flow"]
        
        # 1. Discharge Rate (LPM) calculation mapped from stream thickness
        raw_discharge = (width_px / baseline_width) * nominal_flow
        discharge_rate = round(min(max(raw_discharge, 1.5), 15.0), 2)
        
        # 2. Pressure (Bar) estimation based on flow velocity proxy
        raw_pressure = (discharge_rate / 5.0) * 1.2
        pressure_bar = round(min(max(raw_pressure, 0.4), 3.5), 2)
        
        # 3. Reynolds Number (Re) calculation for flow regime classification
        reynolds_number = int(discharge_rate * 1150)
        
        if reynolds_number < 2300:
            flow_regime = "Laminar Flow"
        elif reynolds_number <= 4000:
            flow_regime = "Transitional Flow"
        else:
            flow_regime = "Turbulent Flow"
            
        # 4. Clog Index (%) calculated using deviation from normal stream profile
        width_deviation = abs(baseline_width - width_px) / baseline_width
        clog_factor = (width_deviation * 40.0) + ((100.0 - continuity) * 0.4)
        clog_index = round(min(max(clog_factor, 1.0), 35.0), 1)
        
        # 5. Diagnostic Health Status
        if clog_index > 20.0:
            diagnostic_status = "RESTRICTED / SCALE BUILDUP DETECTED"
        elif pressure_bar > 2.8:
            diagnostic_status = "EXCESSIVE PRESSURE WARNING"
        else:
            diagnostic_status = "OPTIMAL FLUID PATHWAY"

        return {
            "discharge_rate": discharge_rate,
            "pressure_bar": pressure_bar,
            "reynolds_number": reynolds_number,
            "flow_regime": flow_regime,
            "clog_index": clog_index,
            "diagnostic_status": diagnostic_status
        }