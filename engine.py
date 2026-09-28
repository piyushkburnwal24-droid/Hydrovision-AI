# engine.py
import numpy as np

class HydroCalculator:
    """
    Core physics and telemetry engine for Hydrovision-AI.
    Computes discharge rate, pressure, Reynolds number, and clog index
    with absolute type safety and robust boundary clamping.
    """
    
    PRESETS = {
        "Standard Kitchen Tap": {"baseline_width": 12.0, "nominal_flow": 3.8},
        "Bathroom Faucet": {"baseline_width": 9.0, "nominal_flow": 2.5},
        "Shower Head": {"baseline_width": 20.0, "nominal_flow": 8.0}
    }

    def __init__(self, fixture_choice="Standard Kitchen Tap", custom_scale=12.0, water_temp=25.0, tariff_rate=0.0, cv_metrics=None):
        self.fixture_choice = fixture_choice if isinstance(fixture_choice, str) else "Standard Kitchen Tap"
        self.custom_scale = float(custom_scale) if custom_scale is not None else 12.0
        self.water_temp = float(water_temp) if water_temp is not None else 25.0
        self.tariff_rate = float(tariff_rate) if tariff_rate is not None else 0.0
        self.cv_metrics = cv_metrics or {}
        
        preset_data = self.PRESETS.get(self.fixture_choice, {"baseline_width": self.custom_scale, "nominal_flow": 3.8})
        self.baseline_width = float(preset_data.get("baseline_width", 12.0))
        self.nominal_flow = float(preset_data.get("nominal_flow", 3.8))

    def compute(self, width_px, continuity_score=85.0):
        """
        Instance method called by app.py with strict type-checking and coercion
        to prevent any TypeError regardless of input format.
        """
        # Safe type conversion for width_px (handles tuples, lists, strings, or None)
        try:
            if isinstance(width_px, (list, tuple)):
                width_px = width_px[0] if len(width_px) > 0 else self.baseline_width
            width_px = float(width_px) if width_px is not None else self.baseline_width
        except (ValueError, TypeError):
            width_px = self.baseline_width

        if width_px <= 0:
            width_px = self.baseline_width

        # Safe type conversion for continuity_score
        try:
            if isinstance(continuity_score, (list, tuple)):
                continuity_score = continuity_score[0] if len(continuity_score) > 0 else 85.0
            continuity_score = float(continuity_score) if continuity_score is not None else 85.0
        except (ValueError, TypeError):
            continuity_score = 85.0

        # 1. Discharge Rate (LPM) calculation mapped from stream thickness
        raw_discharge = (width_px / self.baseline_width) * self.nominal_flow
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
        width_deviation = abs(self.baseline_width - width_px) / self.baseline_width
        clog_factor = (width_deviation * 40.0) + ((100.0 - continuity_score) * 0.4)
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

    @staticmethod
    def compute_diagnostics(cv_metrics, preset_name="Standard Kitchen Tap"):
        """
        Static compatibility wrapper.
        """
        width_px = cv_metrics.get("stream_width_px", 12.0) if isinstance(cv_metrics, dict) else 12.0
        continuity = cv_metrics.get("continuity_score", 85.0) if isinstance(cv_metrics, dict) else 85.0
        calc = HydroCalculator(fixture_choice=preset_name)
        return calc.compute(width_px, continuity)