import math

class HydroCalculator:
    # Preset standards for different types of water fixtures
    PRESETS = {
        "Standard Kitchen Tap": {"cd": 0.62, "nominal_d": 15.0, "target_lpm": 4.0, "base_p": 2.0},
        "Bathroom Showerhead": {"cd": 0.68, "nominal_d": 20.0, "target_lpm": 8.0, "base_p": 2.5},
        "Garden Hose Nozzle": {"cd": 0.82, "nominal_d": 12.0, "target_lpm": 12.0, "base_p": 3.0},
        "Industrial Control Valve": {"cd": 0.55, "nominal_d": 25.0, "target_lpm": 15.0, "base_p": 3.5}
    }

    def __init__(self, fixture_name, scale_mm_px, temp_c, tariff):
        preset = self.PRESETS.get(fixture_name, self.PRESETS["Standard Kitchen Tap"])
        self.fixture = fixture_name
        self.cd = preset["cd"]
        self.nominal_d = preset["nominal_d"]
        self.target_lpm = preset["target_lpm"]
        self.base_p = preset["base_p"]
        self.scale = scale_mm_px if scale_mm_px else 0.45
        self.tariff = tariff
        self.g = 9.80665
        
        # Calculate water density and viscosity based on user temperature input
        self.density = 1000.0 - (temp_c - 4.0)**2 / 180.0
        self.viscosity = max(0.0001, 1.787 / (1.0 + 0.0337 * temp_c + 0.00022 * (temp_c**2)) * 1e-3)

    def compute(self, profile_widths, h_px):
        # Convert pixel measurements to physical meters/millimeters
        d0_mm = max(0.5, profile_widths[0] * self.scale)
        d1_mm = max(0.2, profile_widths[-1] * self.scale)
        
        d0_m = d0_mm / 1000.0
        d1_m = d1_mm / 1000.0
        h_m = max(0.005, (h_px * self.scale) / 1000.0)

        # Apply continuity and Torricelli equations to find initial velocity
        ratio_fourth = (d0_m / max(0.0001, d1_m)) ** 4
        if ratio_fourth > 1.001:
            v0_sq = (2.0 * self.g * h_m) / (ratio_fourth - 1.0)
            v0 = math.sqrt(max(0.001, v0_sq))
        else:
            v0 = math.sqrt(2.0 * self.g * h_m)

        v0 = max(0.05, min(v0, 10.0))

        # Calculate flow rate in Liters Per Minute (LPM)
        area_m2 = (math.pi * (d0_m ** 2)) / 4.0
        q_m3s = area_m2 * v0
        flow_lpm = round(q_m3s * 60000.0, 2)

        # Estimate pressure using standard scaling
        pressure_bar = round(self.base_p * ((flow_lpm / max(0.1, self.target_lpm)) ** 1.5), 2)
        pressure_bar = max(0.1, min(pressure_bar, 8.0))

        # Calculate Reynolds number to find the flow regime
        reynolds = round((self.density * v0 * d0_m) / self.viscosity, 1)
        if reynolds < 2300:
            regime = "Laminar Flow"
        elif reynolds <= 4000:
            regime = "Transitional Flow"
        else:
            regime = "Turbulent Jet"

        # Check for scale buildup or clogging
        nominal_area = (math.pi * (self.nominal_d / 1000.0) ** 2) / 4.0
        if area_m2 < nominal_area:
            clog_pct = round((1.0 - (area_m2 / nominal_area)) * 100.0, 1)
        else:
            clog_pct = 0.0

        # Determine fixture health status and generate message
        if clog_pct > 20.0:
            status = "RESTRICTED_SCALE_BUILDUP"
            action = f"Scale constriction detected ({clog_pct}% restriction). Clean aerator mesh immediately."
        elif flow_lpm > self.target_lpm * 1.25:
            status = "EXCESSIVE_PRESSURE_WASTE"
            action = f"High discharge rate ({flow_lpm} LPM). Install a {self.target_lpm} LPM flow limiter."
        else:
            status = "OPTIMAL_EFFICIENCY"
            action = "Water fixture operating within green building standard parameters."

        # Estimate waste and financial costs
        excess_lpm = max(0.0, flow_lpm - self.target_lpm)
        monthly_waste_l = round(excess_lpm * 30.0 * 30.0, 1)
        cost_inr = round((monthly_waste_l / 1000.0) * self.tariff, 2)
        co2_kg = round(monthly_waste_l * 0.0003, 2)

        return {
            "flow_lpm": flow_lpm,
            "pressure_bar": pressure_bar,
            "velocity_ms": round(v0, 2),
            "reynolds": reynolds,
            "regime": regime,
            "clog_pct": clog_pct,
            "status": status,
            "action": action,
            "monthly_waste_l": monthly_waste_l,
            "cost_inr": cost_inr,
            "co2_kg": co2_kg,
            "profile_mm": [w * self.scale for w in profile_widths]
        }