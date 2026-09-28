# engine.py
import numpy as np

class HydroCalculator:
    """
    Core physics and telemetry engine for Hydrovision-AI.
    Computes discharge rate, pressure, Reynolds number, and clog index
    with rigorous physical boundary clamps.
    """
    def __init__(self, cv_metrics=None):
        self.cv_metrics = cv_metrics or {}

    @staticmethod
    def compute_diagnostics(cv_metrics):
        """
        Computes fluid dynamics telemetry based on optical stream measurements.
        """
        width_px = cv_metrics.get("stream_width_px", 12.0)
        continuity = cv_metrics.get("continuity_score", 85.0)
        
        # Baseline calibration reference (standard tap width in pixels)
        baseline_width = 12.0
        
        # 1. Discharge Rate (LPM) calculation mapped from stream thickness
        raw_discharge = (width_px / baseline_width) * 3.8
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