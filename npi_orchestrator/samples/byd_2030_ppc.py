"""BYD 2030 PPC-class PHEV sample — SOR baseline from Audi PPC + E³ 1.2.

Scenario: BYD premium global platform (**Program Dynasty-P**) targeting **2030 SOP**
with a **PPC-class** plug-in hybrid at launch (2.0T PHEV + domain E/E), benchmarked
against Audi Premium Platform Combustion (A5/Q5) and **E³ 1.2** (HCP1 drive domain,
CARIAD software, OTA). Garrett supplies VNT turbo + EDU coordinated with BYD EMS
and 48 V assist (PTG-class layout, not shaft eTurbo).
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

SCENARIO_ID = "byd_2030_ppc"
SCENARIO_NAME = "BYD 2030 PPC PHEV — Dynasty-P (Audi E³ 1.2 SOR baseline)"

CUSTOMER_INPUT = """\
Program Dynasty-P (BYD premium global SUV, **2030 SOP**): We need Garrett turbo support \
for a **PHEV-at-launch** powertrain — 2.0T direct injection + 48 V assist + ~25 kWh \
battery, targeting >100 km WLTP EV range. Volume 250–300k/yr (China + EU export). \
SOR baseline: **Audi PPC + E³ 1.2** (HCP1 drive domain, OTA-capable EMS, security-by-design).

Key asks:
(1) Confirm NPI funding and concept — VNT vs eTurbo vs turbo + PTG-class 48 V layout,
(2) Fast quote Q1 2028 for series award — local content China + EU homologation,
(3) HCP1 / domain-controller interface plan (not legacy standalone ECU),
(4) Development risks: PHEV thermal soak, EV→ICE transients, OTA regression on boost maps,
(5) PPAP L3 and supplier readiness for **SOP Q2 2030** (BYD Shenzhen assembly).

Competitive context: local Chinese turbo suppliers; we want Garrett EDU + aero. Prior BYD \
4-cylinder programs used WG turbos; this is **PHEV-at-SOP** (not ICE-first like Audi Q5).
"""

PROJECT_BRIEF = (
    "Dynasty-P: BYD premium PHEV SUV 2030 SOP, 2.0T + 48V + ~25 kWh, 250–300k/yr. "
    "SOR benchmark Audi PPC MHEV plus / future PHEV + E³ 1.2 HCP1. Garrett VNT + EDU; "
    "PHEV-at-launch (compressed vs Audi ICE-first). China localization + EU export. "
    "PPAP L3, OTA-safe calibration, SOP Q2 2030."
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
### Market & customer need (VOC) — Program Dynasty-P

BYD is positioning a **premium global SUV** for 2030 against European peers. The
powertrain target is **PHEV-at-launch** — unlike Audi PPC (ICE/MHEV first, PHEV later),
BYD requires **turbo + PHEV from SOP**, compressing the NPI timeline ~12 months vs
Audi reference.

**Benchmark: latest Audi architectures (SOR baseline)**

| Audi reference | Relevance to Dynasty-P |
|----------------|------------------------|
| **PPC** (A5, Q5) | Longitudinal 2.0T, MHEV plus (48 V PTG 18 kW / 230 Nm), future PHEV 2.0T + ~26 kWh |
| **E³ 1.2** | Five HCPs; **HCP1 = drive + suspension**; CARIAD software, OTA, Gigabit Ethernet |
| **PPE** (Q6/A6 e-tron) | Not applicable — pure BEV; confirms BYD needs **PPC-class** not PPE for turbo |

**Voice of customer (BYD):**
- **Pain:** Prior WG turbo cannot meet transient + RDE targets on PHEV duty; EMS moving to
  **domain architecture** (E³-class); local supplier 15–20% cost advantage.
- **Need:** Garrett **VNT + EDU** with China assembly; HCP1-compatible interface roadmap.
- **Volume:** 250–300k/yr; 8-year program; EU + China homologation.

### Value assessment & business case

| Item | Value |
|------|-------|
| Lifetime revenue | ~¥2.1–2.4B / ~€270–300M |
| NPO request | ¥38M engineering + ¥12M tooling lead |
| Localization | Changzhou assembly target 70% local content by SOP |
| Payback | <2 yrs at 275k/yr base |

**Gate recommendation: GO WITH CONDITIONS** — fund if Concept confirms VNT + EDU
(not shaft eTurbo) matches BYD PTG layout and HCP1 interface MOU signed by Q4 2026.
""",
        deliverables=[
            {"name": "VOC / customer needs", "status": "complete", "owner": "China Application", "system": "—"},
            {"name": "Audi PPC / E³ 1.2 SOR benchmark", "status": "complete", "owner": "Systems Eng", "system": "—"},
            {"name": "Value assessment", "status": "complete", "owner": "Finance", "system": "—"},
            {"name": "Business case (NPO)", "status": "in_progress", "owner": "Program Director", "system": "—"},
        ],
        risks=[
            {"risk": "BYD switches to in-house turbo for China-only variant", "severity": "high", "mitigation": "Dual-source only for export trim; exclusive EU homologation path"},
            {"risk": "PHEV-at-SOP compresses NPI vs Audi PPC reference", "severity": "high", "mitigation": "Pull Concept/Bid forward 6 months; reuse Gen6 VNT CHRA"},
        ],
        actions=[
            "NPO gate presentation — Program Director, Q4 2026",
            "HCP1 interface workshop with BYD VCU team — Controls, 4 weeks",
            "Competitive teardown: local supplier WG vs Garrett VNT on PHEV duty",
        ],
        handoff="Fund Dynasty-P VNT program; Concept to down-select vs Audi MHEV plus layout (PTG on trans, not eTurbo) and lock E³-class EMS interface.",
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
### Needs → concept matching (benchmark: Audi PPC + E³ 1.2)

**SOR recap:** 2.0T PHEV, >100 km EV range, 48 V assist, HCP1-managed drive domain.

| Option | Offering | Fit to Dynasty-P | vs Audi PPC |
|--------|----------|------------------|-------------|
| **A — WG turbo (incumbent)** | Cost-down WG | Poor transient / RDE on PHEV | Below A5/Q5 MHEV plus responsiveness |
| **B — VNT + BYD PTG (48 V on trans)** | **G-Series VNT + EDU** | **Best fit** — matches Audi PTG architecture | Aligns with MHEV plus; turbo separate from e-assist |
| **C — Shaft eTurbo 48V** | G-Series eTurbo | Strong response; **misaligned** with BYD PTG on transmission | Audi uses PTG, not shaft eTurbo on PPC |
| **D — VNT + discrete e-compressor** | Dual unit | Package penalty on BYD front architecture | Not used on Audi PPC |

**Down-select: Option B — G-Series VNT + EDU**, coordinated with BYD 48 V PTG (18–20 kW class).

### Technologies to meet PHEV-at-SOP (new vs prior BYD WG programs)

1. **VNT with fast pneumatic / electric actuation** — <400 ms tip response for EV→ICE transitions.
2. **EDU with HCP1 AUTOSAR Adaptive interface** — boost maps OTA-delivered via domain controller.
3. **PHEV thermal strategy** — turbine housing for repeated EV-off / ICE-on events (soak-back mitigation).
4. **RDE-calibrated WG authority maps** — λ>1 cruise compatible with BYD hybrid EMS.
5. **China-local CHRA** — common global aero, local machining per export content rules.

### Concept freeze

- **Architecture:** VNT + EDU; **no shaft e-machine** (BYD PTG provides electric fill).
- **Performance:** Meets BYD transient template; 15% margin vs Audi Q5 2.0T MHEV plus benchmark torque trace.
- **E³ alignment:** EDU diagnostic over DoIP/Ethernet; calibration packages signed for OTA.

**Gate recommendation: GO**
""",
        deliverables=[
            {"name": "Concept specification", "status": "complete", "owner": "Chief Engineer", "system": "—"},
            {"name": "TRL / design review", "status": "complete", "owner": "Validation", "system": "—"},
            {"name": "HCP1 interface concept", "status": "complete", "owner": "Controls", "system": "—"},
            {"name": "Business case update", "status": "complete", "owner": "Finance", "system": "—"},
        ],
        risks=[
            {"risk": "BYD EMS not AUTOSAR Adaptive on first silicon", "severity": "high", "mitigation": "Wrapper ECU bridge for SOP-0; native HCP1 by SOP+1 yr"},
            {"risk": "VNT cost gap vs local WG", "severity": "medium", "mitigation": "China CHRA + VA/VE on actuator"},
        ],
        actions=[
            "Release concept DWG to BYD — Design, 2 weeks",
            "Joint dyno plan vs Audi PPC torque trace — Application",
            "Local supplier RFQ (housing, actuator) — Sourcing",
        ],
        handoff="Concept frozen on VNT + EDU with HCP1 bridge; proceed to fast bid for Q1 2028 award.",
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
### Bid package — Dynasty-P (fast track vs Audi award cadence)

**Objective:** Win Q1 2028 award with **PHEV-at-SOP** compliant offer and China localization.

#### SOR compliance (Audi PPC / E³ 1.2 baseline)

| Requirement | Offer | Evidence |
|-------------|-------|----------|
| 2.0T PHEV transient response | **Compliant** | Dyno vs BYD template + Audi Q5 trace |
| >100 km WLTP EV range (system) | **Compliant** (system) | Turbo loss map minimized at λ>1 |
| 48 V assist coordination | **Compliant** | EDU ↔ BYD PTG interface spec rev A |
| HCP1 / domain EMS interface | **Compliant w/ bridge** | AUTOSAR Adaptive + bridge ECU at SOP |
| OTA calibration update | **Compliant** | Signed map packages, rollback |
| EU + China homologation | **Compliant** | Dual emission kits |
| Local content (China) | **68% at SOP** | Changzhou assembly plan |

#### Commercial offer (indicative)

| Line | Value |
|------|-------|
| Series price (China FOB, 275k/yr) | ¥2,180 / unit (VNT assy + EDU) |
| Tooling amortized | ¥85 / unit (5 yr) |
| Engineering recoup | ¥55 / unit |
| Lead time to SOP | 78 weeks from award (aggressive) |
| Plant | **Garrett Changzhou** → BYD Shenzhen |

#### Award score (BYD rubric)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Technical (35%) | 33/35 | VNT + E³-class EDU roadmap |
| Cost (35%) | 28/35 | Gap vs Hunan Tyen; VA plan submitted |
| Localization (20%) | 18/20 | Changzhou + local housing |
| Execution (10%) | 8/10 | PHEV-at-SOP risk flagged |

**Gate recommendation: GO WITH CONDITIONS** — submit; award contingent on HCP1 bridge acceptance and 5% cost gap closure at BAFO.
""",
        deliverables=[
            {"name": "SOR traceability matrix", "status": "complete", "owner": "Systems Eng", "system": "—"},
            {"name": "Technical offer", "status": "complete", "owner": "Application", "system": "—"},
            {"name": "Quote / localization plan", "status": "complete", "owner": "Commercial", "system": "—"},
            {"name": "Award letter", "status": "in_progress", "owner": "Sales", "system": "—"},
        ],
        risks=[
            {"risk": "BAFO 8% reduction request", "severity": "high", "mitigation": "Pre-approved VA: housing, actuator, EDU PCB single-layer"},
            {"risk": "Export control on EDU chipset", "severity": "medium", "mitigation": "Dual MCU qual (China + global)"},
        ],
        actions=[
            "Submit bid — Bid Manager, Q1 2028 Wk6",
            "BYD HCP1 interface sign-off — Controls, Q1 2028 Wk10",
            "Reserve Changzhou capacity 2029 — Operations",
        ],
        handoff="Bid submitted; Develop to close HCP1 integration, PHEV thermal, and OTA regression risks.",
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
### Development — PHEV turbo risks (Audi PPC duty + BYD PHEV-at-SOP)

#### Risk register & results

| # | Risk | Mitigation | Result |
|---|------|------------|--------|
| R1 | **EV→ICE boost transient** — tip response | Fast VNT actuator + EMS pre-position | **Closed** — 380 ms vs 450 ms target |
| R2 | **Thermal soak-back** after long EV mode | Insulated turbine housing + cool-down map | **Open** — 6°C above target; v2 shield in PP |
| R3 | **HCP1 OTA regression** on boost maps | CI pipeline 2,200 scenarios; signed packages | **In progress** — 91% pass (target 97%) |
| R4 | **PHEV RDE NOx** — λ>1 cruise | WG authority + BYD catalyst strategy | **Closed** |
| R5 | **48 V PTG interaction** — torque overlay | Joint EMS limiter map with BYD | **Closed** |
| R6 | **China vs EU calibrations** | Dual map sets, common hardware | **Closed** |
| R7 | **Compressor surge** — cold start + high altitude | Recirc valve + altitude comp table | **Closed** |
| R8 | **Local CHRA quality** — Changzhou ramp | Early PPAP sub-suppliers | **In progress** |

#### Design freeze status

- **Turbo:** G-Series VNT, map **DY-VNT-02** frozen.
- **EDU:** Software **v3.0.4** — HCP1 bridge + native path; OTA package format agreed.
- **DVPR:** 38/44 complete; 6 open (soak-back, OTA winter, 2 durability).

**Gate recommendation: GO WITH CONDITIONS** — freeze pending R2 + R3 closure (6 weeks).
""",
        deliverables=[
            {"name": "Application design freeze", "status": "in_progress", "owner": "Chief Engineer", "system": "—"},
            {"name": "HCP1 interface release", "status": "in_progress", "owner": "Controls", "system": "—"},
            {"name": "DVPR results", "status": "in_progress", "owner": "Validation", "system": "—"},
            {"name": "Pre-production (n=18)", "status": "in_progress", "owner": "Manufacturing", "system": "—"},
        ],
        risks=[
            {"risk": "R3 blocks OTA sign-off for PPAP", "severity": "high", "mitigation": "Dedicated BYD-Garrett CI sprint; freeze map set for PSW"},
            {"risk": "R2 waiver rejected by BYD EU homologation", "severity": "high", "mitigation": "Fleet trial 35 vehicles EU + CN"},
        ],
        actions=[
            "Close R2 on PP hardware — Thermal, 6 weeks",
            "HCP1 native interface on BYD beta HCP — Controls, Q3 2029",
            "Supplier PPAP kickoff Changzhou — SQE",
        ],
        handoff="Design substantially frozen; Validate runs PPAP L3 and fleet waiver for R2.",
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
### PPAP — Dynasty-P VNT assy (PN **GT5522DYN-P**) | Level 3 | SOP Q2 2030

#### PPAP element status (AIAG)

| Element | Status |
|---------|--------|
| 1–7 Design / FMEA / control plan | ✅ Approved (CP-CZ-52 Rev 03) |
| 8 MSA | ✅ Cgk 1.38 |
| 9 Dimensional | ✅ 32/32 in spec |
| 10 Performance (map, burst, EMC) | ✅ Pass (R2 waiver **W-DYN-04**) |
| 11 Initial Ppk | ✅ >1.67 on critical dims |
| 12 Lab docs | ✅ Complete |
| 14 Sample production parts | ✅ 350 pcs Changzhou |
| 17 Customer-specific (BYD + EU) | ✅ 44/44 (1 waiver) |
| 18 PSW | 🟡 Pending R2 fleet acceptance |

#### Production Launch Authorization

| Item | Status |
|------|--------|
| Run-at-rate (3×3 shifts) | ✅ 96.8% OEE |
| EU homologation sample | ✅ UNECE pack submitted |
| China CCC sample | ✅ Submitted |

**Gate recommendation: GO WITH CONDITIONS** — PSW upon waiver W-DYN-04 acceptance.
""",
        deliverables=[
            {"name": "PPAP L3 package", "status": "in_progress", "owner": "SQE", "system": "—"},
            {"name": "PLA sign-off", "status": "complete", "owner": "Plant Manager", "system": "—"},
            {"name": "EU / CN homologation", "status": "in_progress", "owner": "Homologation", "system": "—"},
        ],
        risks=[
            {"risk": "BYD rejects W-DYN-04 without 35-vehicle EU fleet", "severity": "high", "mitigation": "Fleet data delivery Q1 2030"},
            {"risk": "Changzhou sub-supplier actuator PPAP late", "severity": "medium", "mitigation": "Air freight + sort at Shenzhen"},
        ],
        actions=[
            "PSW signature — Customer SQE upon waiver",
            "Upload PPAP BYD portal — Program SQE",
            "Close R3 OTA to 97% before SOP",
        ],
        handoff="PPAP ready; Launch executes SOP ramp Shenzhen + NPO closure.",
        ran_at=_NOW,
    )


def _ph6_launch() -> PhaseResult:
    return PhaseResult(
        phase_id="PH6",
        scope="LAUNCH",
        gate="SOP / NPO Closure",
        agent_name="Launch",
        gate_decision="GO_WITH_CONDITIONS",
        visible="""\
### Launch readiness — Dynasty-P SOP Q2 2030

**SOP:** 2030-04-15 | **Plant:** BYD Shenzhen | **Supply:** Garrett Changzhou

#### Supplier readiness

| Supplier | Part | PPAP | OTD | PPM | Status |
|----------|------|------|-----|-----|--------|
| Local actuator (CN) | VNT actuator | L3 | 96% | 32 | ✅ |
| SKF | Bearing cartridge | L3 | 98% | 14 | ✅ |
| BYD internal | PTG (48 V) | L3 | 99% | 18 | ✅ (system) |
| MCU supplier A | EDU processor | L3 | 93% | 52 | 🟡 L3 SOP-3 wk |
| Seals local | Kits | L3 | 97% | 22 | ✅ |

#### Quality readiness

| Check | Target | Actual | Status |
|-------|--------|--------|--------|
| Control plan production | Approved | CP-CZ-52 Rev 04 | ✅ |
| LPA | 100% | 100% | ✅ |
| Customer PPM (pilot) | <25 | 19 | ✅ |
| OTA regression (SOP build) | 97% | 95% | 🟡 |
| SIOP / demand | 3 mo frozen | 275k/yr loaded | ✅ |
| Run-at-rate sign-off | BYD | Signed 2030-03-01 | ✅ |

#### SOP ramp

| Period | Volume | Notes |
|--------|--------|-------|
| SOP | 3,000/wk | 100% EDU bus test |
| SOP+8 | 12,000/wk | 2-shift |
| SOP+16 | 5,300/wk steady | Full rate |

**Gate recommendation: GO WITH CONDITIONS** — SOP authorized; monitor EDU MCU supplier and OTA 97% target.
""",
        deliverables=[
            {"name": "NPI checklist (launch)", "status": "complete", "owner": "NPI Lead", "system": "—"},
            {"name": "SOP run-at-rate", "status": "complete", "owner": "Plant Manager", "system": "—"},
            {"name": "NPO closure", "status": "in_progress", "owner": "Program Director", "system": "—"},
        ],
        risks=[
            {"risk": "OTA gap at SOP causes field reflash", "severity": "medium", "mitigation": "SOP+30 day patch release with BYD"},
        ],
        actions=[
            "Execute SOP 2030-04-15",
            "Close NPO 30 days post-SOP",
            "Lessons learned vs Audi PPC timing — Program Director",
        ],
        handoff="Dynasty-P in production; transition to sustaining; target HCP1 native interface SOP+12 mo.",
        ran_at=_NOW,
    )


def _customer_response() -> CustomerResponse:
    return CustomerResponse(
        visible="""\
Dear BYD Dynasty-P Program Team,

Thank you for your 2030 SOP **PHEV-at-launch** turbocharger request. We have assessed
your program against the **Audi PPC + E³ 1.2** SOR baseline (HCP1 drive domain, 48 V
assist, OTA-capable EMS) and completed our full NPI review.

**Summary**

Garrett recommends **G-Series VNT + EDU** assembled in **Changzhou**, coordinated with
your **48 V PTG** (Audi MHEV plus-class layout). Shaft eTurbo was **not** down-selected —
it misaligns with your transmission-mounted PTG architecture used on Audi PPC.

**Program status**

- **Need / Concept:** GO — VNT + EDU frozen; HCP1 bridge at SOP, native path SOP+12 mo.
- **Bid:** Submitted ¥2,180/unit; award pending BAFO and interface sign-off.
- **Develop:** Design freeze conditional on thermal soak-back (waiver W-DYN-04) and OTA CI 97%.
- **Validate:** PPAP L3 ready; PSW pending fleet data (35 EU vehicles).
- **Launch:** SOP **15 April 2030** GO with conditions on EDU MCU supplier and OTA.

**vs Audi PPC reference**

Your **PHEV-at-SOP** requirement compresses NPI ~12 months vs Audi (ICE-first on Q5).
We have absorbed this in the bid lead time (78 weeks from award) but flag **thermal** and
**OTA** as the critical path — same class of risks seen on premium EU PHEV programs.

**Next steps**

1. Accept PPAP waiver **W-DYN-04** or confirm extended EU fleet trial protocol.
2. Sign HCP1 interface release **v3.0.4** for OTA map delivery.
3. Issue award letter to lock Changzhou capacity for 2029 PP build.

We are ready for award and immediate program execution.

Best regards,
Garrett Dynasty-P Program Team
""",
        overall_status="at_risk",
        key_points=[
            "VNT + EDU selected (not eTurbo) — aligned with Audi PPC PTG architecture",
            "PHEP-at-SOP compresses timeline vs Audi ICE-first PPC rollout",
            "HCP1 / OTA integration is critical path; bridge ECU at SOP",
            "PPAP L3 ready; thermal waiver W-DYN-04 pending",
            "SOP 15 Apr 2030 GO with conditions",
        ],
        next_steps=[
            "BAFO cost closure and award — Commercial, Q1 2028",
            "HCP1 interface v3.0.4 sign-off — BYD VCU + Garrett Controls",
            "Fleet trial for waiver W-DYN-04 — 35 EU vehicles, Q1 2030",
        ],
        gates_summary="AT RISK — GO at Launch with conditions; thermal + OTA + localization are gating items.",
    )


def _route_plan() -> CustomerRoutePlan:
    return CustomerRoutePlan(
        customer_input=CUSTOMER_INPUT,
        project_brief=PROJECT_BRIEF,
        current_phase_id="PH1",
        start_phase_id="PH1",
        end_phase_id="PH6",
        phases_to_run=[p.id for p in PHASES],
        rationale="Full NPI for BYD 2030 PHEV-at-SOP; SOR benchmark Audi PPC + E³ 1.2; funding through launch.",
    )


def build_sample_orchestrator(workspace: Path) -> NPIOrchestrator:
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
    orch = build_sample_orchestrator(workspace)
    return CustomerWorkflowResult(
        customer_input=CUSTOMER_INPUT,
        route_plan=orch.route_plan,  # type: ignore[arg-type]
        phase_results=[orch.results[p.id] for p in PHASES if p.id in orch.results],
        customer_response=_customer_response(),
        backend=DEFAULT_BACKEND,
        ran_at=_NOW,
    )
