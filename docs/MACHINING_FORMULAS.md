# CNC Machining Formulas Reference

A comprehensive guide to feeds, speeds, and machining calculations for CNC operations. This document provides the essential formulas, material properties, and practical guidelines needed for optimal machining performance.

## Table of Contents

1. [Core Formulas](#core-formulas)
2. [Material Properties](#material-properties)
3. [Tool Recommendations](#tool-recommendations)
4. [Power Calculations](#power-calculations)
5. [Unit Conversions](#unit-conversions)
6. [Practical Examples](#practical-examples)
7. [Safety Guidelines](#safety-guidelines)

---

## Core Formulas

### RPM (Spindle Speed) Calculation

**Metric System:**
```
RPM = (Surface Speed × 1000) / (π × Tool Diameter)
RPM = (SMM × 1000) / (π × D)
```

**Imperial System:**
```
RPM = (Surface Speed × 12) / (π × Tool Diameter)
RPM = (SFM × 12) / (π × D)
```

Where:
- SMM = Surface speed in meters per minute
- SFM = Surface speed in feet per minute  
- D = Tool diameter (mm or inches)

### Feed Rate Calculation

**Milling:**
```
Feed Rate = RPM × Number of Flutes × Chip Load
Vf = N × Z × fz
```

**Turning:**
```
Feed Rate = Feed per Revolution × RPM
F = fr × N
```

Where:
- Vf = Feed rate (mm/min or in/min)
- N = Spindle speed (RPM)
- Z = Number of flutes/teeth
- fz = Feed per tooth (mm/tooth or in/tooth)
- fr = Feed per revolution (mm/rev or in/rev)

### Material Removal Rate (MRR)

**Milling:**
```
MRR = Depth of Cut × Width of Cut × Feed Rate / 1000
MRR = ap × ae × Vf / 1000  [cm³/min]
```

**Turning:**
```
MRR = Depth of Cut × Feed Rate × Surface Speed
MRR = ap × f × Vc  [cm³/min]
```

**Drilling:**
```
MRR = (π/4) × D² × Feed Rate / 1000
MRR = (π/4) × D² × Vf / 1000  [cm³/min]
```

Where:
- ap = Depth of cut (mm)
- ae = Width of cut (mm)
- Vf = Feed rate (mm/min)
- D = Tool diameter (mm)
- f = Feed per revolution (mm/rev)
- Vc = Cutting speed (m/min)

---

## Material Properties

### Surface Speeds (Cutting Speeds)

| Material | SFM Range | SMM Range | Comments |
|----------|-----------|-----------|----------|
| **Aluminum (6061)** | 600-1000 | 183-305 | High speeds possible, excellent heat dissipation |
| **Mild Steel (1018)** | 80-120 | 24-37 | Moderate speeds, good machinability |
| **Stainless Steel (304/316)** | 50-100 | 15-30 | Lower speeds, avoid work hardening |
| **Cast Iron (Grey)** | 50-150 | 15-46 | Varies by hardness, abrasive |
| **Titanium (Ti-6Al-4V)** | 50-100 | 15-30 | Conservative speeds, excellent strength |
| **Brass** | 300-600 | 91-183 | High speeds, watch for built-up edge |
| **Copper** | 200-400 | 61-122 | Moderate speeds, gummy material |

### Specific Cutting Force (Kc) Values

Critical for power calculations and cutting force predictions.

| Material | Kc Range (N/mm²) | Typical Value | Hardness (HB) |
|----------|------------------|---------------|----------------|
| **Aluminum Alloys** | 700-900 | 800 | 95-150 |
| **Mild Steel** | 1800-2200 | 2000 | 120-200 |
| **Stainless Steel (Austenitic)** | 2400-2800 | 2600 | 150-250 |
| **Stainless Steel (Martensitic)** | 2800-3200 | 3000 | 250-400 |
| **Cast Iron (Grey)** | 1200-1500 | 1350 | 150-250 |
| **Cast Iron (Ductile)** | 1800-2200 | 2000 | 200-300 |
| **Titanium Alloys** | 2300-2800 | 2550 | 300-400 |
| **Tool Steel (Annealed)** | 2500-3000 | 2750 | 200-250 |
| **Tool Steel (Hardened)** | 3000-3500 | 3250 | 45-62 HRC |

### Chip Load Recommendations (Carbide Tools)

| Material | Tool Diameter Range | Chip Load (mm/tooth) | Chip Load (in/tooth) |
|----------|---------------------|----------------------|----------------------|
| **Aluminum** | 3-25mm | 0.08-0.25 | 0.003-0.010 |
| **Mild Steel** | 3-25mm | 0.05-0.15 | 0.002-0.006 |
| **Stainless Steel** | 3-25mm | 0.03-0.10 | 0.001-0.004 |
| **Cast Iron** | 3-25mm | 0.05-0.12 | 0.002-0.005 |
| **Titanium** | 3-25mm | 0.03-0.08 | 0.001-0.003 |

**Rule of Thumb:** Chip Load ≈ Tool Diameter / 200 (in mm)

---

## Tool Recommendations

### Carbide vs HSS Guidelines

**Use Carbide When:**
- High production requirements
- Harder materials (>200 HB)
- High surface speeds desired
- Consistent, rigid setup available

**Use HSS When:**
- Interrupted cuts
- Variable geometry workpieces  
- Lower surface speeds required
- Cost is primary concern

### Flute Count Selection

| Material Type | 2-Flute | 3-Flute | 4+ Flute |
|---------------|---------|---------|----------|
| **Aluminum** | Roughing, high MRR | General purpose | Finishing |
| **Steel** | Roughing, soft steels | General purpose | Finishing, hard steels |
| **Stainless** | Roughing | General purpose | Light finishing only |

### Coating Recommendations

| Material | Uncoated | TiN | TiCN | TiAlN | AlCrN |
|----------|----------|-----|------|-------|-------|
| **Aluminum** | ✓ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **Steel** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Stainless** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Cast Iron** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Titanium** | ✓ | ⚠️ | ⚠️ | ✓ | ✓ |

*Note: ⚠️ indicates potential aluminum pickup/welding issues*

---

## Power Calculations

### Spindle Power Requirements

**Basic Formula:**
```
Power (kW) = (MRR × Kc) / 60,000 × ηm
```

Where:
- MRR = Material removal rate (cm³/min)
- Kc = Specific cutting force (N/mm²)
- ηm = Machine efficiency (typically 0.7-0.9)

**Torque Calculation:**
```
Torque (Nm) = Power (kW) × 9549 / RPM
```

**Horsepower Conversion:**
```
HP = kW × 1.34102
kW = HP / 1.34102
```

### Machine Efficiency Factors

| Drive Type | Typical Efficiency |
|------------|-------------------|
| **Direct Drive Spindle** | 80-90% |
| **Belt Drive** | 70-85% |
| **Gear Drive** | 70-80% |

### Power Requirements by Material

| Material | Unit Power (UHP) | Power Factor |
|----------|------------------|--------------|
| **Aluminum** | 0.25 | 1.0× |
| **Mild Steel** | 1.4-2.5 | 2-3× |
| **Stainless Steel** | 2.0-3.3 | 3-4× |
| **Cast Iron** | 1.0-2.0 | 1.5-2.5× |
| **Titanium** | 2.5-3.5 | 3-4× |

*Relative to aluminum at same cutting conditions*

---

## Unit Conversions

### Length Conversions
```
1 inch = 25.4 mm
1 mm = 0.0393701 inches
1 thou (0.001") = 0.0254 mm
```

### Speed Conversions
```
SFM to SMM: SMM = SFM × 0.3048
SMM to SFM: SFM = SMM / 0.3048
```

### Power Conversions
```
HP to kW: kW = HP / 1.34102
kW to HP: HP = kW × 1.34102
```

### Force Conversions
```
N/mm² = MPa
1 psi = 0.00689476 MPa
1 MPa = 145.038 psi
```

---

## Practical Examples

### Example 1: Aluminum Roughing Operation

**Given:**
- Material: 6061 Aluminum
- Tool: 12mm carbide end mill, 3-flute
- Operation: Roughing cut
- DOC: 3mm, WOC: 8mm

**Calculations:**
1. **Surface Speed:** 800 SFM = 244 SMM
2. **RPM:** (244 × 1000) / (π × 12) = 6,476 RPM
3. **Chip Load:** 0.15 mm/tooth (from table)
4. **Feed Rate:** 6,476 × 3 × 0.15 = 2,914 mm/min
5. **MRR:** (3 × 8 × 2,914) / 1000 = 70.0 cm³/min
6. **Power:** (70.0 × 800) / 60,000 = 0.93 kW

### Example 2: Steel Finishing Operation

**Given:**
- Material: 1018 Mild Steel
- Tool: 6mm carbide end mill, 4-flute
- Operation: Finishing cut
- DOC: 0.5mm, WOC: 1mm

**Calculations:**
1. **Surface Speed:** 100 SFM = 30.5 SMM
2. **RPM:** (30.5 × 1000) / (π × 6) = 1,617 RPM
3. **Chip Load:** 0.05 mm/tooth (conservative for finishing)
4. **Feed Rate:** 1,617 × 4 × 0.05 = 323 mm/min
5. **MRR:** (0.5 × 1 × 323) / 1000 = 0.16 cm³/min
6. **Power:** (0.16 × 2000) / 60,000 = 0.005 kW (very light cut)

---

## Safety Guidelines

### Starting Parameters
- **Always start conservative** - 75% of recommended values
- **Gradually increase** speeds and feeds based on results
- **Monitor tool condition** and surface finish continuously

### Warning Signs
- **Excessive noise** - reduce speed or feed
- **Poor surface finish** - adjust chip load
- **Rapid tool wear** - reduce cutting speed
- **Chatter** - reduce DOC/WOC, increase rigidity
- **Built-up edge** - increase speed or use coolant

### Machine Limitations
- **Stay within spindle power** - use calculations to verify
- **Check spindle speed limits** - both minimum and maximum
- **Consider machine rigidity** - lighter cuts on flexible setups
- **Account for workholding** - reduce forces if clamping is light

### Tool Life Optimization
- **Use flood coolant** when possible for steel/stainless
- **Avoid dwells** in the cut (keep moving)
- **Use proper climb milling** direction
- **Maintain sharp tools** - replace at first sign of wear

---

## Formula Validation

All formulas in this document are based on industry-standard references including:
- Sandvik Coromant Technical Guidelines
- Kennametal Speed & Feed Calculators  
- Harvey Tool Machining Guidelines
- Machining Doctor Technical Resources
- Practical machinist community expertise

For specific applications, always consult tool manufacturer recommendations and perform test cuts to validate parameters.

---

*Last Updated: 2025-09-02*
*Version: 1.0*