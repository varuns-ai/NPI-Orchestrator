"""Automotive eTurbo NPI sample — realistic phase outputs for a turbocharger program.

Scenario: European premium OEM (Program **Aurora-S**) requests a 48V electric-assisted
turbo (eTurbo) for a new mild-hybrid inline-4 launched on STLA Medium / similar
platforms. Garrett is incumbent on prior VNT programs; this is a **new need** for
e-assist at 2.0L displacement class.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..customer_router import CustomerRoutePlan
from ..orchestrator import NPIOrchestrator, PhaseResult
from ..phases import PHASES
from ..response_synth import CustomerResponse
from ..runtime_env import DEFAULT_BACKEND
from ..workflow import CustomerWorkflowResult

SCENARIO_ID = "automotive_eturbo"
SCENARIO_NAME = "Automotive eTurbo — Aurora-S (48V mild-hybrid I4)"

CUSTOMER_INPUT = """\
Program Aurora-S (European premium OEM, 2028 SOP): We need Garrett support for a \
48V eTurbo on our new 2.0L Miller-cycle mild-hybrid I4 (~220 kW system, 48V belt \
architecture). Target 180–220k vehicles/year across EU and NA. Key asks:
(1) match or beat competitor e-boost response (<350 ms torque fill from 1,000 rpm),
(2) confirm funding and technical feasibility vs our updated combustion targets,
(3) fast quote for series bid in Q3 — SOR Rev C attached conceptually (λ>1 cruise,
RDE NOx margin, 42V bus EMC per LV 148),
(4) outline development risks for high e-assist duty (25–30% of WLTC energy),
(5) PPAP and launch readiness plan for our Zwickau assembly plant.
Prior Garrett VNT on our 2.0L Gen3; this eTurbo is a new need for us.
"""

PROJECT_BRIEF = (
    "Aurora-S: 48V eTurbo for OEM premium 2.0L Miller MHEV I4, 180–220k/yr, "
    "2028 SOP Zwickau. Incumbent VNT supplier; new e-assist architecture. "
    "SOR Rev C: <350 ms boost response, RDE compliance, 48V EMC LV 148. "
    "Series bid Q3; PPAP L3; run-at-rate before SOP."
)

_NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ph1_need() -> PhaseResult:
    return PhaseResult(
        phase_id="PH1",
        scope="NEEDS",
        gate="Project Funding",
        agent_name="Need",
        gate_decision="GO_WITH_CONDITIONS",
        visible="""\
### Market & customer need (VOC)

**Program Aurora-S** is aligned with the industry's shift to **downsized Miller-cycle /
mild-hybrid I4** platforms where **electric assist** closes the low-end torque gap
without oversizing the turbine.

**Recently introduced / refreshed OEM engine families (benchmark context):**

| OEM / platform | Engine family | Relevance to Aurora-S |
|----------------|---------------|------------------------|
| Stellantis STLA Medium | 2.0L Hurricane-4 / GME evo | Direct segment peer; hybrid variants announced 2026+ |
| VW Group | EA888 evo5 2.0 TSI | Miller + 48V MHEV on MQB evo; e-boost roadmaps public |
| BMW | B58 3.0 (tech cascade) | 48V e-compressor learnings flow to I4 cost targets |
| Mercedes-Benz | M254 2.0 | Integrated starter-generator + boosting strategy reference |
| Hyundai-Kia | Theta III 1.6T / Smartstream G2.5 | Aggressive e-boost cost positioning in C/D SUV |
| Ford | 2.0L EcoBoost refresh | NA/EU RDE-focused Miller tuning; supplier dual-sourcing |

**Voice of customer (Aurora-S):**
- **Pain:** Gen3 fixed-geometry + external WG cannot meet <350 ms torque fill without
  unacceptable turbine sizing (fuel penalty at λ>1 cruise).
- **Need:** Integrated **48V eTurbo** with Garrett controls know-how; reuse compressor
  aero heritage from G-Series where possible.
- **Volume:** 180–220k/yr; 7-year life; peak 220 kW system power.

### Value assessment & business case (summary)

| Item | Value |
|------|-------|
| Lifetime revenue (turbo + e-machine + EDU share) | ~€340–380M (scenario range) |
| Gross margin target | Program hurdle 18%; incumbent advantage on VNT |
| NPO request (ePEP) | €4.2M engineering + €1.1M tooling lead |
| Payback | <2.5 yrs at 200k/yr base volume |

### Gate readiness — Project Funding

**Recommendation: GO WITH CONDITIONS**

Funding is justified if Concept phase confirms **e-machine thermal envelope** at
30% e-assist duty and OEM shares **SOR Rev C** freeze date (target 8 weeks).
""",
        deliverables=[
            {"name": "VOC / customer needs", "status": "complete", "owner": "Application Sales", "system": "MV"},
            {"name": "Technology roadmap alignment", "status": "complete", "owner": "Product Line", "system": "—"},
            {"name": "Value assessment", "status": "complete", "owner": "Finance / PL", "system": "PQF"},
            {"name": "Business case (NPO funding)", "status": "in_progress", "owner": "Program Director", "system": "ePEP"},
        ],
        risks=[
            {"risk": "OEM delays SOR Rev C freeze beyond Q3 bid window", "severity": "high", "mitigation": "Parallel concept studies on Rev B + change budget in quote"},
            {"risk": "Competitor eTurbo reference sets unrealistic <300 ms claim", "severity": "medium", "mitigation": "Publish measured response envelope with boundary conditions in Concept gate"},
        ],
        actions=[
            "Secure NPO €4.2M release at PL gate — Owner: Program Director, due 2 weeks",
            "Obtain OEM powertrain roadmap letter for STLA-class I4 — Owner: Sales, due 3 weeks",
            "Benchmark 5 recent OEM engine launches (table above) in Concept kickoff pack",
        ],
        handoff="Funded need confirmed for 48V eTurbo on Aurora-S; proceed to concept down-select against G-Series e-assist variants and competitor e-boost benchmarks.",
        ran_at=_NOW,
    )


def _ph2_concept() -> PhaseResult:
    return PhaseResult(
        phase_id="PH2",
        scope="CONCEPT",
        gate="Concept Design Freeze",
        agent_name="Concept",
        gate_decision="GO",
        visible="""\
### Needs → concept matching (Garrett turbocharger portfolio)

**Customer need recap:** 2.0L Miller MHEV, <350 ms torque fill, λ>1 cruise efficiency,
48V bus, high e-assist duty (25–30% WLTC energy).

| Option | Garrett offering | Fit to Aurora-S | TRL / readiness |
|--------|----------------|-----------------|-----------------|
| **A — Baseline VNT + WG** (incumbent Gen3 path) | G-Series VNT, floating bearing | **Poor** for <350 ms; lowest cost | TRL 9 — does not meet need |
| **B — VNT + 48V e-compressor (split)** | G-Series VNT + discrete e-compressor | Good response; packaging & cost penalty | TRL 7 — two units, dual control |
| **C — eTurbo (integrated e-machine on shaft)** | **G-Series eTurbo 48V** (preferred) | **Best** response & package; matches SOR | TRL 6→7 with Aurora-S |
| **D — Variable turbine + electric assist (eVNT)** | eVNT prototype line | Excellent low-end; turbine cost high | TRL 5 — new need, longer lead |
| **E — Wastegate turbo + 12V e-assist** | Cost-down WG + small e-motor | Marginal vs <350 ms target | TRL 8 — insufficient for SOR |

**Down-select: Option C — G-Series eTurbo 48V** (with eVNT as backup if thermal limits bite).

### New-need technologies to solve customer requirement

Because eTurbo is a **new need** vs prior VNT-only supply:

1. **Ultra-low inertia shaft group** — titanium aluminide turbine + milled aluminium compressor;
   target 35% inertia reduction vs Gen3.
2. **48V hairpin e-machine** — 10–12 kW continuous assist; peak 15 kW ≤30 s; oil-jet cooled.
3. **Model-based boost coordination** — joint OEM EMS / Garrett EDU interface; torque fill
   algorithm validated on HiL.
4. **Ceramic ball bearing cartridge** — required for repeated e-assist spool cycles.
5. **Compressor recirculation + surge margin** — active valve strategy for Miller transient lambda.

### Concept design freeze summary

- **Freeze concept:** G-Series eTurbo 48V, CHRA commonality 82% with Gen3 compressor housing.
- **Performance preview (1D + CFD):** 340 ms torque fill (cold); **290 ms** with pre-spool
  strategy — meets <350 ms SOR.
- **TRL status:** System TRL 6; e-machine module TRL 7 (prior EU program); target TRL 7 at Bid gate.

**Gate recommendation: GO** — concept frozen for bid package.
""",
        deliverables=[
            {"name": "Test plan (concept)", "status": "complete", "owner": "Validation", "system": "WRS"},
            {"name": "Design review / TRL status", "status": "complete", "owner": "Chief Engineer", "system": "—"},
            {"name": "Business case update", "status": "complete", "owner": "Finance", "system": "PQF"},
            {"name": "NPI checklist (concept)", "status": "complete", "owner": "NPI Lead", "system": "eLaunch"},
            {"name": "Component quotes (e-machine, bearing)", "status": "in_progress", "owner": "Sourcing", "system": "ISS"},
        ],
        risks=[
            {"risk": "e-machine continuous power limited at 115°C oil sump (OEM envelope)", "severity": "high", "mitigation": "Oil scavenge enhancement + derate map agreed with OEM EMS"},
            {"risk": "eVNT backup adds 6-month delay if Option C fails thermal sign-off", "severity": "medium", "mitigation": "Parallel turbine aero sprint in Develop phase week 1–8"},
        ],
        actions=[
            "Release concept specification to 3DD / BOM — Owner: Design, due 1 week",
            "TurboMatching sign-off with OEM EMS team — Owner: Application, due 2 weeks",
            "Proto build request for two Aurora-S representative CHRAs — Owner: Proto cell",
        ],
        handoff="Concept frozen on G-Series eTurbo 48V; proceed to fast-track bid with SOR Rev C compliance matrix and provisional tooling plan.",
        ran_at=_NOW,
    )


def _ph3_bid() -> PhaseResult:
    return PhaseResult(
        phase_id="PH3",
        scope="BID",
        gate="Bid & Value Confirmation",
        agent_name="Bid",
        gate_decision="GO_WITH_CONDITIONS",
        visible="""\
### Bid package — fast-track for Q3 award (Program Aurora-S)

**Objective:** Meet OEM bid criteria **in 6 weeks** with priced technical offer,
plant capacity, and risk-adjusted commercial terms.

#### SOR Rev C compliance matrix (excerpt)

| Requirement | Offer position | Evidence |
|-------------|----------------|----------|
| Torque fill <350 ms @ 1000 rpm | **Compliant** (290 ms w/ pre-spool) | 1D + HiL data pack |
| RDE NOx margin (λ>1 cruise) | **Compliant** | Miller map + WG authority |
| 48V EMC LV 148 | **Compliant w/ test** | Pre-scan EDU layout |
| 15 yr / 300k km durability | **Compliant** | Bearing e-duty accelerated test plan |
| Local content EU | **Compliant** | Assembly Zwickau + EU rotor stack |

#### Commercial offer (indicative)

| Line | Value |
|------|-------|
| Series price (FOB EU, 200k/yr) | €487 / unit (eTurbo assy + EDU) |
| Tooling (amortized 5 yr) | €12 / unit |
| Engineering recoup | €8 / unit (one-time profile) |
| Lead time to SOP | 82 weeks from award |
| Plant | **Garrett Brno** assembly → OEM Zwickau |

#### Award criteria scoring (OEM rubric)

| Criterion (weight) | Garrett score | Notes |
|--------------------|---------------|-------|
| Technical (40%) | **38/40** | Incumbent aero + proven e-machine stack |
| Cost (30%) | **24/30** | Competitive; e-machine scale-up savings at 200k+ |
| Execution (20%) | **17/20** | Fast bid; proto slots reserved |
| Sustainability (10%) | **9/10** | EU manufacturing, recycled Al housing option |

**Gate recommendation: GO WITH CONDITIONS** — submit bid; award contingent on SOR Rev C
freeze and EDU software interface agreement by week 4 post-submittal.
""",
        deliverables=[
            {"name": "Requirements (SOR) traceability", "status": "complete", "owner": "Systems Eng", "system": "—"},
            {"name": "Technical offer", "status": "complete", "owner": "Application", "system": "—"},
            {"name": "Quote / pricing", "status": "complete", "owner": "Commercial", "system": "PQF"},
            {"name": "Award letter (pending)", "status": "in_progress", "owner": "Sales", "system": "SFDC"},
            {"name": "Plant selection", "status": "complete", "owner": "Operations", "system": "—"},
        ],
        risks=[
            {"risk": "Raw material (NdFeB) escalation between bid and award", "severity": "medium", "mitigation": "Indexed pricing clause + dual magnet supplier RFQ"},
            {"risk": "OEM requests 10% cost reduction at BAFO", "severity": "high", "mitigation": "Pre-approved VA/VE list (housing commonality, EDU single PCB)"},
        ],
        actions=[
            "Submit technical + commercial offer — Owner: Bid Manager, Q3 Wk2",
            "Lock EDU software interface spec with OEM EMS — Owner: Controls, Q3 Wk4",
            "Reserve Brno line capacity 2027 — Owner: Ops Planning",
        ],
        handoff="Bid submitted; on award execute Develop with focus on e-duty thermal, surge, and EDU integration risks below.",
        ran_at=_NOW,
    )


def _ph4_develop() -> PhaseResult:
    return PhaseResult(
        phase_id="PH4",
        scope="DEVELOP",
        gate="Application Design Freeze",
        agent_name="Develop",
        gate_decision="GO_WITH_CONDITIONS",
        visible="""\
### Development — risks, mitigations & results (turbocharger applications)

Cross-application learnings from **eTurbo / high-boost gasoline** programs applied
to Aurora-S.

#### Risk register & mitigation outcomes

| # | Risk (application) | Mitigation | Result / status |
|---|-------------------|------------|-----------------|
| R1 | **Bearing life** — repeated 48V assist cycles (passenger + light commercial duty) | Ceramic ball bearing + oil jet sizing; accelerated 1,200-cycle matrix | **Closed** — L10 > target (FELA report #AS-447) |
| R2 | **Compressor surge** — Miller transient with λ>1 | Active recirc valve + OEM EMS limiter map | **Closed** — 12% surge margin @ worst case (hot 45°C) |
| R3 | **Thermal soak-back** to e-machine after key-off | Pump-down strategy + heat shield v2 | **Open** — 8°C above target; VA heat shield in PP build |
| R4 | **Oil coking** — high turbine inlet temp on SUV grade load | Bearing housing cooling ribs + OEM oil spec DEU-V2 | **Closed** — coking test 500 h pass |
| R5 | **NVH** — e-machine whine at 4–6 kHz | Skew winding + housing isolation | **Closed** — 4 dB below OEM limit |
| R6 | **EMC** — 48V inverter harmonics on vehicle bus | Filter revision + cable routing guide | **Closed** — LV 148 pre-compliance pass |
| R7 | **Tip speed / blade stress** — 220 kW peak | Titanium aluminide turbine + FEA sign-off | **Closed** — SF 1.15 at 95th percentile speed |
| R8 | **EDU software regression** — OEM EMS release drift | Joint CI pipeline + 1,800 scenario HiL | **In progress** — 94% pass; target 98% at design freeze |

#### Application design freeze

- **Compressor:** G-Series 71 mm inducer, map revision **AS-CMP-03** frozen.
- **Turbine:** e-compatible volute; inlet temp 980°C continuous class.
- **EDU:** Software **v2.3.1** — torque fill algorithm frozen; thermal derate map conditional on R3.
- **DVPR:** 42/48 tests complete; 6 remaining (hot soak, EMC re-run, 2 durability).

**Gate recommendation: GO WITH CONDITIONS** — freeze design pending R3 thermal soak-back
closure on PP hardware (target 4 weeks).
""",
        deliverables=[
            {"name": "Design review (application freeze)", "status": "in_progress", "owner": "Chief Engineer", "system": "—"},
            {"name": "NPI checklist (TRA, RL)", "status": "complete", "owner": "NPI Lead", "system": "eLaunch"},
            {"name": "DVPR / test results", "status": "in_progress", "owner": "Validation", "system": "WRS"},
            {"name": "Pre-production units (n=12)", "status": "in_progress", "owner": "Manufacturing", "system": "SCC"},
        ],
        risks=[
            {"risk": "R3 thermal soak-back delays PPAP component submission", "severity": "high", "mitigation": "Expedite heat shield tooled parts; parallel OEM validation at 10°C relaxed limit for IAT only"},
            {"risk": "R8 HiL coverage gap on winter fuel scenarios", "severity": "medium", "mitigation": "Add 120 winter transients; complete by Validate gate"},
        ],
        actions=[
            "Complete R3 heat shield PP build & test — Owner: Thermal, 4 weeks",
            "Release design freeze package to Validate / PPAP — Owner: Design, after R3",
            "Supplier PPAP kickoff (bearing, e-machine rotor) — Owner: SQE",
        ],
        handoff="Application design substantially frozen; Validate to run PPAP L3, production trial, and close R3/R8 before launch readiness gate.",
        ran_at=_NOW,
    )


def _ph5_validate() -> PhaseResult:
    return PhaseResult(
        phase_id="PH5",
        scope="VALIDATE",
        gate="PPAP / Launch Readiness",
        agent_name="Validate",
        gate_decision="GO_WITH_CONDITIONS",
        visible="""\
### PPAP sample output — Program Aurora-S eTurbo (PSW package summary)

**Part:** G-Series eTurbo 48V assy — PN **GT3788AUR-S** | **PPAP Level 3** | Customer: Aurora-S OEM

#### PPAP element status (AIAG 4th ed.)

| Element | Document / result | Status |
|---------|-------------------|--------|
| 1. Design records | DWG GT3788AUR-S Rev 04 | ✅ Approved |
| 2. Engineering change documents | ECO-AS-112 (heat shield v2) | ✅ Approved |
| 3. Customer engineering approval | Perf map sign-off MAP-AS-09 | ✅ Approved |
| 4. Design FMEA | DFMEA Rev 03, RPN max 96 | ✅ Accepted |
| 5. Process flow diagram | Brno line flow PFD-BRN-88 | ✅ Approved |
| 6. Process FMEA | PFMEA Rev 02 | ✅ Accepted |
| 7. Control plan | CP-BRN-88 Rev 02 (pre-launch) | ✅ Approved |
| 8. MSA studies | Torque audit MSA Cgk 1.44 | ✅ Pass |
| 9. Dimensional results | 28/28 characteristics in spec | ✅ Pass |
| 10. Material / performance tests | Bearing life, burst, map, EMC | ✅ Pass (R3 waiver doc #W-09) |
| 11. Initial process studies | Ppk > 1.67 on 5 critical dims | ✅ Pass |
| 12. Qualified laboratory documentation | ISO 17025 reports bundled | ✅ Complete |
| 13. Appearance approval (AAR) | N/A (functional) | — |
| 14. Sample production parts | 300 pcs run @ Brno | ✅ Delivered |
| 15. Master sample | GT3788AUR-S #001 retained | ✅ |
| 16. Checking aids | Go/no-go gauges GNG-88 | ✅ |
| 17. Customer-specific requirements | SOR Rev C checklist 41/41 | ✅ (1 waiver) |
| 18. Part submission warrant (PSW) | **Ready for signature** | 🟡 Pending R3 closure |

#### Production Launch Authorization (PLA) checklist

| Item | Status |
|------|--------|
| Run-at-rate (3 shifts × 3 days @ takt) | ✅ 98.2% OEE |
| Line stop / escalation tested | ✅ |
| Containment plan for launch month | ✅ |
| Service parts initial stock | ✅ |

**Gate recommendation: GO WITH CONDITIONS** — PPAP PSW submission with documented
thermal soak-back waiver (#W-09); full closure before SOP.
""",
        deliverables=[
            {"name": "PPAP package (L3)", "status": "in_progress", "owner": "SQE", "system": "SCC"},
            {"name": "Production Launch Authorization", "status": "complete", "owner": "Plant Manager", "system": "—"},
            {"name": "Design review for production", "status": "complete", "owner": "Manufacturing Eng", "system": "—"},
            {"name": "PPAP management", "status": "in_progress", "owner": "Customer SQE", "system": "—"},
        ],
        risks=[
            {"risk": "Customer rejects waiver W-09 without additional 1,000 km fleet data", "severity": "high", "mitigation": "Fleet trial data from OEM pilot 40 vehicles — due 3 weeks"},
            {"risk": "Sub-supplier e-machine coil PPAP late", "severity": "medium", "mitigation": "Air freight PP parts + daily SQE stand-up"},
        ],
        actions=[
            "Obtain PSW signature — Owner: Customer SQE, upon waiver acceptance",
            "Close R3 with PP hardware retest — Owner: Validation",
            "Upload PPAP to OEM portal — Owner: Program SQE",
        ],
        handoff="PPAP substantially complete; Launch to execute SOP ramp, supplier scorecard, and NPO closure.",
        ran_at=_NOW,
    )


def _ph6_launch() -> PhaseResult:
    return PhaseResult(
        phase_id="PH6",
        scope="LAUNCH",
        gate="SOP / NPO Closure",
        agent_name="Launch",
        gate_decision="GO",
        visible="""\
### Launch readiness — SOP & production ramp (Program Aurora-S)

**Target SOP:** 2028-03-15 | **Plant:** OEM Zwickau | **Supply:** Garrett Brno

#### Supplier readiness

| Supplier | Part | PPAP | OTD (12 wk) | Quality (PPM) | Status |
|----------|------|------|-------------|---------------|--------|
| SKF (bearings) | Cartridge | L3 signed | 99% | 12 | ✅ Ready |
| Remy e-machines | Rotor/stator | L3 signed | 97% | 28 | ✅ Ready |
| Alcoa EU | Compressor housing | L3 signed | 100% | 8 | ✅ Ready |
| Flextronics | EDU PCB | L2→L3 | 94% | 45 | 🟡 L3 by SOP-4 wk |
| Local seals | O-rings / gaskets | L3 signed | 98% | 15 | ✅ Ready |

#### Quality readiness

| Check | Target | Actual | Status |
|-------|--------|--------|--------|
| Control plan production Rev | Approved | CP-BRN-88 Rev 03 | ✅ |
| Layered process audits (LPA) | 100% week | 100% | ✅ |
| Containment / escalation | Tested | Drill 2028-02-10 pass | ✅ |
| Customer PPM (pilot) | <20 | 14 | ✅ |
| Scrap + rework (pilot) | <0.5% | 0.3% | ✅ |
| SIOP / demand plan alignment | 3 mo frozen | MP3 loaded 200k/yr | ✅ |
| Run-at-rate sign-off | Customer | Signed 2028-02-01 | ✅ |

#### SOP ramp plan

| Week | Volume | Notes |
|------|--------|-------|
| SOP | 2,500 units | 1-shift ramp; 100% sort on EDU bus test |
| SOP+4 | 8,000 units | 2-shift; sort to sampling |
| SOP+12 | 15,000 units | Full rate; NPO closure review |

#### NPO closure

- Engineering spend: 96% consumed; remaining → service warranty reserve.
- Lessons learned captured (LL-AS-2028-01); NPS survey scheduled SOP+90 days.

**Gate recommendation: GO** — SOP authorized; Flextronics EDU L3 is only monitored risk.
""",
        deliverables=[
            {"name": "NPI checklist (launch)", "status": "complete", "owner": "NPI Lead", "system": "eLaunch"},
            {"name": "SOP run-at-rate", "status": "complete", "owner": "Plant Manager", "system": "—"},
            {"name": "Demand plan / SIOP", "status": "complete", "owner": "Supply Chain", "system": "SAP"},
            {"name": "NPO closure", "status": "in_progress", "owner": "Program Director", "system": "ePEP"},
        ],
        risks=[
            {"risk": "Flextronics EDU L3 slip impacts SOP+2 capacity", "severity": "medium", "mitigation": "Buffer stock 2 weeks + backup test at Brno"},
        ],
        actions=[
            "Execute SOP 2028-03-15 — Owner: Plant Manager",
            "Close NPO within 30 days post-SOP — Owner: Program Director",
            "Capture NPS at SOP+90 — Owner: Sales / Quality",
        ],
        handoff="Program Aurora-S in serial production; transition to sustaining engineering and annual VA/VE reviews.",
        ran_at=_NOW,
    )


def _customer_response() -> CustomerResponse:
    return CustomerResponse(
        visible="""\
Dear Aurora-S Program Team,

Thank you for your request on **48V eTurbo** support for your new 2.0L Miller mild-hybrid
I4 (Program Aurora-S, 2028 SOP). We have completed a full NPI assessment across funding,
concept, bid, development, validation, and launch readiness.

**Summary**

Garrett recommends proceeding with our **G-Series eTurbo 48V** solution. Against your
SOR Rev C targets we project **290 ms torque fill** (with pre-spool), full RDE λ>1 cruise
compliance, and LV 148 EMC readiness. Our Q3 bid position is **€487/unit** (series, FOB EU)
with Brno assembly supporting your Zwickau plant.

**Where we are**

- **Funding & concept:** Approved — eTurbo down-selected over incumbent VNT; TRL 7 path clear.
- **Bid:** Submitted; award pending SOR Rev C freeze and EDU interface lock.
- **Development:** Application design frozen except thermal soak-back (mitigation on PP hardware).
- **PPAP:** Level 3 package ready for PSW; one documented waiver on soak-back pending your fleet data review.
- **Launch:** SOP **15 March 2028** authorized; supplier and quality readiness confirmed.

**Next steps**

1. Confirm SOR Rev C freeze date and EDU software interface approval (week 4 post-bid).
2. Review PPAP waiver **W-09** and fleet trial data (40 vehicles) for thermal soak-back.
3. Attend run-at-rate sign-off walkthrough (completed 1 Feb 2028 — report attached).

We are committed to meeting your <350 ms response target and stand ready for award and
immediate program kick-off.

Best regards,
Garrett Program Aurora-S Team
""",
        overall_status="on_track",
        key_points=[
            "G-Series eTurbo 48V selected; 290 ms torque fill vs 350 ms SOR target",
            "Bid submitted €487/unit; Brno assembly for Zwickau SOP Mar 2028",
            "PPAP L3 ready; PSW pending thermal soak-back waiver acceptance",
            "Supplier & quality readiness confirmed; SOP GO",
        ],
        next_steps=[
            "Freeze SOR Rev C and EDU interface — OEM EMS + Garrett Controls, 4 weeks",
            "Accept PPAP waiver W-09 or request extended fleet validation",
            "Issue award letter to trigger final NPO closure and SOP ramp",
        ],
        gates_summary="Overall program ON TRACK — GO at Launch; conditional items on thermal waiver and EDU supplier L3.",
    )


def _route_plan() -> CustomerRoutePlan:
    return CustomerRoutePlan(
        customer_input=CUSTOMER_INPUT,
        project_brief=PROJECT_BRIEF,
        current_phase_id="PH1",
        start_phase_id="PH1",
        end_phase_id="PH6",
        phases_to_run=[p.id for p in PHASES],
        rationale="Full NPI lifecycle requested: funding through SOP/PPAP for new 48V eTurbo need.",
    )


def customer_input() -> str:
    return CUSTOMER_INPUT


def project_brief() -> str:
    return PROJECT_BRIEF


def build_sample_orchestrator(workspace: Path) -> NPIOrchestrator:
    """Return an orchestrator pre-loaded with all six phase sample results."""
    orch = NPIOrchestrator(
        workspace=workspace,
        project_name=SCENARIO_NAME,
        project_brief=PROJECT_BRIEF,
        backend=DEFAULT_BACKEND,
    )
    orch.route_plan = _route_plan()
    for builder in (_ph1_need, _ph2_concept, _ph3_bid, _ph4_develop, _ph5_validate, _ph6_launch):
        res = builder()
        orch.results[res.phase_id] = res
    orch.customer_response = _customer_response()
    return orch


def build_sample_workflow(workspace: Path) -> CustomerWorkflowResult:
    """Return a complete workflow result for the automotive eTurbo scenario."""
    orch = build_sample_orchestrator(workspace)
    return CustomerWorkflowResult(
        customer_input=CUSTOMER_INPUT,
        route_plan=orch.route_plan,  # type: ignore[arg-type]
        phase_results=[
            orch.results[p.id] for p in PHASES if p.id in orch.results
        ],
        customer_response=_customer_response(),
        backend=DEFAULT_BACKEND,
        ran_at=_NOW,
    )
