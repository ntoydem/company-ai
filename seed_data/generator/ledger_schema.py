"""Truth ledger schema (SPEC_05 §3, docs/plans/PHASE_2_1_PLAN.md §1–§2).

Every piece of information lives inside a tagged mapping (`Fact`, `Money`, `Event` or a
tagged list record); only identity/structure keys are untagged. `extra="forbid"` turns a
misspelled key into a validation error instead of silently ignored data.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Tag = Literal["USER_FACT", "AI_ASSUMPTION"]
Currency = Literal["EUR", "USD", "TRY"]
Stage = Literal["development", "construction", "operation"]
DocumentStatus = Literal["draft", "executed", "amended", "superseded", "active"]
Confidentiality = Literal["normal", "restricted", "board"]
GeneratePhase = Literal["3.1", "4.2", "5.1", "never"]
QuestionCategory = Literal[
    "document",
    "temporal",
    "data",
    "mixed",
    "isolation",
    "hallucination",
    "authorization",
    "comparison",
    # ADR-027 (Tansu Not 2): a question that cannot be answered without knowing what the
    # user means, and a question whose wording matches no document term — both expect the
    # fixed no-answer sentence *plus* a code-generated assist block of the given kind.
    "ambiguous",
    "term_mismatch",
    # Tansu Ürün 1 notu §B (08.10.2026): "X var mı / nerede" discovery questions — the answer
    # must *show* the relevant documents and ask/offer, whichever way (answered with citations
    # or the fixed sentence + assist.available + assist.question); the fixed sentence alone
    # fails. Scored by `eval_lib.discovery_check`, threshold 80 %.
    "discovery",
]
# `finans_mudur`: the finance department_manager (sees `restricted`, B-08) — B ölçümü teşhis
# tekrarı (08.10.2026) asks the restricted-workbook questions with the right role.
DemoUser = Literal["admin", "yonetim", "finans", "hukuk", "enerji", "finans_mudur"]
AssistKind = Literal["clarify", "term_mismatch"]

DEPARTMENT_SLUGS = (
    "enerji_grubu",
    "enerji_gelistirme",
    "enerji_epc_insaat",
    "enerji_bakim",
    "finans",
    "hukuk",
    "mali_isler",
    "idari_isler",
)
DepartmentSlug = Literal[
    "enerji_grubu",
    "enerji_gelistirme",
    "enerji_epc_insaat",
    "enerji_bakim",
    "finans",
    "hukuk",
    "mali_isler",
    "idari_isler",
]

# SPEC_03 §2 pre-licence steps (fixed vocabulary for İzmir).
PRE_LICENCE_STEPS = (
    "Önlisans",
    "Süre Uzatımı Başvurusu",
    "Arazi Edinimi",
    "İmar Kesinleşme",
    "Kat'i Proje Onayı",
    "Bağlantı Anlaşması",
    "Askeri Yasak Yazısı",
    "TEA Yazısı",
    "ÇED",
    "Yapı Ruhsatı",
    "Üretim Lisansı",
)
PreLicenceStep = Literal[
    "Önlisans",
    "Süre Uzatımı Başvurusu",
    "Arazi Edinimi",
    "İmar Kesinleşme",
    "Kat'i Proje Onayı",
    "Bağlantı Anlaşması",
    "Askeri Yasak Yazısı",
    "TEA Yazısı",
    "ÇED",
    "Yapı Ruhsatı",
    "Üretim Lisansı",
]

FACILITY_CHAIN_VERSIONS = ("DRAFT", "V01", "V02", "EXECUTED", "AMD01", "AMD02")

# SPEC_03 §3 finance document types — İzmir may not carry any of these (SPEC_05 §6).
FINANCE_DOCUMENT_TYPES = frozenset(
    {
        "Term Sheet",
        "Mandate Letter",
        "Facility Agreement",
        "Common Terms Agreement",
        "ECA Facility Agreement",
        "Intercreditor Agreement",
        "Security Agreement",
        "Share Pledge",
        "Account Pledge",
        "Assignment Agreement",
        "Mortgage",
        "Direct Agreement",
        "Sponsor Support Agreement",
        "Conditions Precedent Checklist",
        "Financial Close Documentation",
        "Drawdown Notice",
        "Repayment Schedule",
        "Covenant Report",
        "Financial Model",
        "Debt Schedule",
    }
)

# SPEC_05 §4 — the fictional names every ledger must stay within (plus company.yaml's list).
SPEC_FICTIONAL_NAMES = (
    "ABC Enerji A.Ş.",
    "DEF Enerji Üretim A.Ş.",
    "GHI Yatırım A.Ş.",
    "JKL İnşaat A.Ş.",
    "MNO Teknik Danışmanlık Ltd.",
    "PQR Bank",
    "STU Sigorta",
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Meta(_Strict):
    schema_version: int
    demo_today: date
    currency_note: str


class Fact(_Strict):
    value: int | float | str | bool | date
    tag: Tag
    source_doc: str | None = None
    note: str | None = None


class Money(_Strict):
    value: int | float
    currency: Currency
    tag: Tag
    source_doc: str | None = None
    note: str | None = None


class Event(_Strict):
    date: date | None
    doc: str | None = None
    tag: Tag
    note: str | None = None


class Shareholder(_Strict):
    name: Fact
    share_pct: Fact


class Spv(_Strict):
    name: Fact
    shareholders: list[Shareholder]


# ---------------------------------------------------------------- Ankara


class Capacity(_Strict):
    initial: Fact
    current: Fact


class Turbines(_Strict):
    count: Fact
    model_generic: Fact


class AnkaraTimeline(_Strict):
    development_start: Event
    pre_licence: Event
    licence: Event
    licence_amendment: Event
    financing_signed: Event
    financial_close: Event
    epc_signed: Event
    construction_start: Event
    construction_end: Event
    commissioning: Event
    cod_expected_initial: Event
    cod_actual: Event
    operation_start: Event


class Lenders(_Strict):
    local_bank: Fact
    eca: Fact


class Interest(_Strict):
    base: Fact
    margin_pct: Fact


class ChangedFact(_Strict):
    initial: Fact
    current: Fact
    changed_by: str


class Drawdown(_Strict):
    date: date
    amount: Money
    doc: str | None = None
    tag: Tag


class CovenantTest(_Strict):
    period: str = Field(pattern=r"^Q[1-4]_\d{4}$")
    dscr: float
    result: Literal["pass", "fail"]
    doc: str | None = None
    tag: Tag


class BaseRate(_Strict):
    year: int
    rate_pct: float
    tag: Tag


class Instalment(_Strict):
    date: date
    principal: Money
    tag: Tag


class QuarterCfads(_Strict):
    period: str = Field(pattern=r"^Q[1-4]_\d{4}$")
    cfads: Money
    tag: Tag


class Finance(_Strict):
    capex: Money
    equity: Money
    total_debt: Money
    local_debt: Money
    eca_debt: Money
    lenders: Lenders
    interest: Interest
    tenor_years: ChangedFact
    grace_months: Fact
    repayment_profile: Fact
    dscr_covenant: ChangedFact
    drawdowns: list[Drawdown]
    outstanding_debt_as_of_demo_today: Money
    covenant_tests: list[CovenantTest]
    facility_chain: list[str]
    # Phase 4.2 (Financial Model inputs)
    base_rate_pct_by_year: list[BaseRate]
    repayment_schedule: list[Instalment]
    cfads_by_quarter: list[QuarterCfads]


class ChangeOrder(_Strict):
    date: date
    subject: Fact
    doc: str | None = None
    tag: Tag


class Construction(_Strict):
    epc_contractor: Fact
    turbine_supplier: Fact
    epc_contract_price: Money
    epc_contract_current_doc: str
    change_orders: list[ChangeOrder]


class MonthlyProduction(_Strict):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    mwh: float
    availability_pct: float
    capacity_factor_pct: float
    tag: Tag


class BudgetVsActual(_Strict):
    period: str = Field(pattern=r"^Q[1-4]_\d{4}$")
    budget: Money
    actual: Money
    tag: Tag


class Incident(_Strict):
    date: date
    type: Fact
    doc: str | None = None
    tag: Tag


class Operations(_Strict):
    operating_year_on_demo_today: Fact
    monthly_production: list[MonthlyProduction]
    budget_vs_actual: list[BudgetVsActual]
    incidents: list[Incident]


class AnkaraProject(_Strict):
    code: Literal["ANK_RES"]
    name: Literal["Ankara RES"]
    stage: Literal["operation"]
    spv: Spv
    capacity_mw: Capacity
    turbines: Turbines
    timeline: AnkaraTimeline
    finance: Finance
    construction: Construction
    operations: Operations


# ---------------------------------------------------------------- İzmir


class TargetCapacity(_Strict):
    target: Fact


class IzmirTimeline(_Strict):
    development_start: Event
    pre_licence_application: Event
    pre_licence: Event
    land_acquisition_start: Event
    ced_application: Event
    # Post-licence fields: must be null by design (SPEC_03 §1, kabul kriteri).
    licence: None
    financing_signed: None
    financial_close: None
    epc_signed: None
    construction_start: None
    construction_end: None
    commissioning: None
    cod_expected_initial: None
    cod_actual: None
    operation_start: None


class PermitCompleted(_Strict):
    step: PreLicenceStep
    date: date
    doc: str | None = None
    tag: Tag
    note: str | None = None


class PendingStep(_Strict):
    step: PreLicenceStep
    expected: str | None = None
    tag: Tag


class Development(_Strict):
    ced_status: Fact
    permits_completed: list[PermitCompleted]
    pending_steps: list[PendingStep]
    latest_event: Event


class IzmirProject(_Strict):
    code: Literal["IZM_RES"]
    name: Literal["İzmir RES"]
    stage: Literal["development"]
    spv: Spv
    capacity_mw: TargetCapacity
    turbines: None
    timeline: IzmirTimeline
    finance: None
    construction: None
    operations: None
    development: Development


# ---------------------------------------------------------------- documents inventory


class Document(_Strict):
    id: str = Field(pattern=r"^DOC-(ANK|IZM|CO)-(DEV|FIN|EPC|OPS|LEG|ADM)-\d{3}$")
    department: DepartmentSlug
    subdepartment: DepartmentSlug | None
    folder: str
    type: str
    name: Fact
    document_date: Fact
    effective_date: Fact | None
    # ADR-026: validity end, when the document type has one (e.g. a renewal notice without a
    # successor on file). `null` for everything else — most documents never expire.
    expiration_date: Fact | None
    version: str
    status: DocumentStatus
    parties: list[str]
    key_facts: dict[str, str]
    supersedes: str | None
    superseded_by: str | None
    related: list[str]
    source_type: Literal["digital_pdf", "scanned_pdf", "xlsx"]
    language: Literal["en", "tr"]
    confidentiality: Confidentiality
    generate_in_phase: GeneratePhase
    tag: Tag


class AnkaraLedger(_Strict):
    meta: Meta
    project: AnkaraProject
    documents: list[Document]


class IzmirLedger(_Strict):
    meta: Meta
    project: IzmirProject
    documents: list[Document]


# ---------------------------------------------------------------- company


PartyRole = Literal[
    "sponsor",
    "spv",
    "local_bank",
    "eca",
    "epc_contractor",
    "turbine_supplier",
    "technical_advisor",
    "insurer",
    "legal_counsel",
]


class Party(_Strict):
    name: Fact
    role: PartyRole
    kind: Literal["company", "bank", "agency"]


class CompanySpv(_Strict):
    project_code: Literal["ANK_RES", "IZM_RES"]
    name: Fact
    shareholders: list[Shareholder]


class DemoBanners(_Strict):
    all: str
    contracts: str


class Holding(_Strict):
    name: Fact
    role: str


class CompanyLedger(_Strict):
    meta: Meta
    holding: Holding
    parties: list[Party]
    spvs: list[CompanySpv]
    public_institutions: list[str]
    name_whitelist: list[str]
    demo_banners: DemoBanners
    documents: list[Document]


# ---------------------------------------------------------------- fx


class FxRate(_Strict):
    pair: Literal["EUR/TRY", "USD/TRY", "EUR/USD"]
    period: str = Field(pattern=r"^(\d{4}|\d{4}-Q[1-4]|\d{4}-\d{2}-\d{2})$")
    rate: float = Field(gt=0)
    tag: Tag


class FxLedger(_Strict):
    meta: Meta
    base_note: str
    rates: list[FxRate]


# ---------------------------------------------------------------- questions


class Question(_Strict):
    # `CO-` = company-level (no project) questions; an optional `-X` suffix marks a variant of
    # the same question asked as another user (GEN-AMB-003-F, BELIRSIZLIK_PLAN §3).
    # `HO-` + two digits = held-out block ids (Tansu/Naci, 08.10.2026).
    id: str = Field(pattern=r"^(ANK|IZM|GEN|CO|HO)-[A-Z]{3}-\d{2,3}(-[A-Z])?$")
    category: QuestionCategory
    question: str
    # One ledger path, or several for a question spanning projects (Ürün 1 uyum turu):
    # every path becomes one value group the answer must contain.
    expected_answer: str | list[str] | None
    expected_answer_aliases: list[str]
    expected_project: Literal["Ankara RES", "İzmir RES"] | None
    expected_department: DepartmentSlug | None
    required_sources: list[str]
    forbidden_sources: list[str]
    ask_as_user: DemoUser
    expect_no_answer: bool
    notes: str | None = None
    # Text checks on the answer (normalised substring): every required phrase present, no
    # forbidden phrase present. Used by `comparison` (Ü-3) — the fixed notice must appear,
    # comparative wording must not.
    required_phrases: list[str] = []
    forbidden_phrases: list[str] = []
    # ADR-027: which `assist.kind` the answer must carry (ASSIST_MODE on). Only meaningful
    # with `expect_no_answer: true`; scored as "skipped" when the response has no assist
    # block (flag off), so the same question set measures both modes.
    expect_assist: AssistKind | None = None


class QuestionSet(_Strict):
    version: int
    demo_today: date
    questions: list[Question]
    # Held-out questions (Tansu, pending Naci's approval): validated like the others, never
    # asked by `run_eval` until moved into `questions`; `scripts/dry_run_ambiguity.py --held-out`
    # runs the LLM-free check on them.
    held_out: list[Question] = []
