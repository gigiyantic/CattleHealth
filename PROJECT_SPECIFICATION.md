# Ultra-Low-Cost Cattle Health Monitoring System (CattleHealth AI)
## Comprehensive Technical & Business Specification (BRD / TRS)

**Document Version**: 1.0.0  
**Repository**: [gigiyantic/CattleHealth](https://github.com/gigiyantic/CattleHealth)  
**Target Unit Cost**: < ₹200 INR ($2.50 USD)  
**Target Market**: Smallholder Dairy Farmers in India & Global Emerging Markets  

---

## 1. Executive Summary & Market Imperative

Over **80% of milk in India** is produced by smallholder farmers owning 2 to 5 cows. With a national herd exceeding **305 million cattle and buffaloes**, less than 0.5% currently use health monitoring technology. 

Existing solutions (CowManager, Allflex, Stellapps) cost **₹4,000 to ₹15,000 per animal**, creating an insurmountable financial barrier for smallholders. **CattleHealth AI** disrupts this space by introducing an ultra-lean **sub-₹200 hardware collar tag** coupled with a **Hardware-as-a-Service (HaaS)** model: **Free Hardware + ₹39/month WhatsApp subscription**.

---

## 2. Ultra-Lean Hardware Architecture & Bill of Materials (BOM)

### 2.1 Component Selection & Cost Structure (At 1,000+ Volume Scale)

| Layer | Component Selection | Function | Cost (INR) | Cost (USD) |
| :--- | :--- | :--- | :--- | :--- |
| **System-on-Chip (SoC)** | **PhyPlus PHY6222 / Telink TLSR8251** | 32-bit ARM MCU + BLE 5.0 Radio | **₹38** | $0.45 |
| **Motion Sensor** | **Silan SC7A20 / LIS3DH** | 3-Axis Accelerometer (1Hz chewing & SVM activity) | **₹21** | $0.25 |
| **Temperature Sensor** | **NTC 10K 1% Precision Thermistor** | Waterproof contact body temperature sensor | **₹3** | $0.03 |
| **Battery Power** | **CR2477 (3V 1000mAh) / ER14505** | Primary Lithium power (1.5 - 2 yr battery life) | **₹38** | $0.45 |
| **PCB & Antenna** | **2-Layer FR4 PCB (25mm x 25mm)** | Compact PCB with etched PCB antenna ($0 cost) | **₹8** | $0.10 |
| **Passives & Crystal** | **32.768kHz RTC + Resistors/Caps** | Deep sleep clock & decoupling passives | **₹7** | $0.08 |
| **Casing & Strap** | **Ultrasonic IP67 Plastic Pod + Strap** | Weatherproof, mud-resistant neck collar | **₹30** | $0.35 |
| **SMT Assembly** | **Automated Factory Pick-and-Place** | SMT soldering, firmware flash & testing | **₹13** | $0.15 |
| **TOTAL BOM COST** | | | **~₹158 – ₹165** | **~$1.86** |

---

## 3. Veterinary Biometrics & Algorithms

### 3.1 Relative Body Temperature Monitoring
* **Baseline Normal**: $38.0^\circ\text{C} – 39.3^\circ\text{C}$ ($100.4^\circ\text{F} – 102.8^\circ\text{F}$).
* **Trigger Threshold**: Relative increase $\Delta T \ge +1.0^\circ\text{C}$ sustained over two 15-minute readings.
* **Clinical Signal**: Early detection of Mastitis, Bovine Viral Diarrhea (BVD), and Respiratory Infections **24 to 48 hours before physical milk drop**.

### 3.2 Rumination & Chewing Frequency
* **Baseline Normal**: $450 – 550 \text{ minutes/day}$, chewing at a steady rhythm of $0.8 – 1.2 \text{ Hz}$ (~50–70 chews/min).
* **Signal Processing**: Accelerometer raw $Z/Y$-axis data evaluated via peak counting. Drops below 300 mins/day trigger a **Digestive Distress Alert**.

### 3.3 Estrus / Heat Cycle Detection
* **Motion Metric**: Signal Vector Magnitude (SVM):
  $$\text{SVM} = \sqrt{a_x^2 + a_y^2 + a_z^2}$$
* **Trigger Threshold**: 3-hour moving average SVM exceeds $3.0\times$ the cow's 7-day baseline.
* **Alert Signal**: Instant WhatsApp notification: *"Cow #05 in Heat. Optimal Insemination Window: Next 12 Hours."*

---

## 4. Software & Cloud Ecosystem

1. **BLE Firmware**: Ultra-low power state machine. Wakes up for 20ms every 15 minutes, reads NTC and Accelerometer, broadcasts BLE 5.0 advertisement payload, returns to $4\,\mu\text{A}$ deep sleep.
2. **ESP32 Farm Gateway**: Plugs into wall outlet in shed. Receives BLE packets from up to 50 collars within 150m radius and relays to cloud via 4G/Wi-Fi.
3. **Farmer UX (WhatsApp Bot + PWA)**: Zero app installation friction. Direct localized messages (Hindi, Marathi, Gujarati, Tamil, English) via WhatsApp API.

---

## 5. Financial Model & Unit Economics (HaaS)

* **Seed Investment Example**: ₹1,000,000 (1 Lakh INR).
* **Production**: 400 Collar Units + 20 Gateway Units + Packaging.
* **Payback Period**: 5 Months @ ₹39/month subscription per cow.
* **5-Year LTV Return**: **₹2,140 Net Profit per collar** (10x Return on Hardware Cost).

---

## 6. Manufacturing & Government Funding Roadmap

### 6.1 Make in India Supply Chain
* **SMT PCB Assembly**: LionCircuits (Bengaluru) / Sahasra (Noida) / PCB Power (Gujarat).
* **Enclosure**: Tooling & plastic injection molding in Pune / Rajkot.

### 6.2 Government Grants & Subsidies
* **BIRAC BIG Grant**: Up to ₹50 Lakhs non-dilutive R&D grant.
* **NABARD Agri-Innovation Fund**: Subsidized loans & dairy tech grants.
* **DPIIT Startup India**: 3-year tax exemption & IP/Patent support.
