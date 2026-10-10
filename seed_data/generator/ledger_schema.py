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
AssistKind = Literal["clarify", "term_mismatch", "disambiguate"]

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
# Adım 5 (Tansu §3.1): holding renamed ABC Enerji A.Ş. -> XYZ Enerji A.Ş.; the old single
# shared "DEF Enerji Üretim A.Ş." SPV name no longer applies (7 SPVs, each with its own
# name, all listed in company.yaml's name_whitelist) — docs/SPEC_05_*.md §4 needs the same
# update (flagged, not applied here; out of scope for Aşama A).
SPEC_FICTIONAL_NAMES = (
    "XYZ Enerji A.Ş.",
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


ConflictKind = Literal["genuine_conflict", "version_difference", "duplicate", "missing_document"]


class Fact(_Strict):
    value: int | float | str | bool | date
    tag: Tag
    source_doc: str | None = None
    note: str | None = None
    # Adım 5 (09.10.2026, ADIM5_ASAMA_A_REPORT.md §5): a value that disagrees with another
    # one on purpose (Tansu's "kasıtlı tuzak" demo traps — Karatepe's signed-vs-drawn credit
    # amount, Yeşilova's two interest figures). `conflict_group` names the pair/group; the
    # validator (`check_conflict_groups`) accepts a disagreement only inside a named group
    # and only when every member of that group carries `deliberate_conflict: true` — an
    # unmarked disagreement, or a group of one, is still an error.
    deliberate_conflict: bool = False
    conflict_group: str | None = None
    # Adım 5 İş 4a (10.10.2026, ADIM5_PF_PARTISI_PLAN §4): what *kind* of trap a
    # `conflict_group` member is — only `genuine_conflict` actually uses `conflict_group`
    # today (version_difference uses `supersedes`/`version` instead; duplicate/
    # missing_document need no ledger mechanism at all, per the plan's general rule).
    # The validator requires every member of one `conflict_group` to share one kind.
    conflict_kind: ConflictKind | None = None


class Money(_Strict):
    value: int | float
    currency: Currency
    tag: Tag
    source_doc: str | None = None
    note: str | None = None
    deliberate_conflict: bool = False
    conflict_group: str | None = None
    conflict_kind: ConflictKind | None = None


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
    # Adım 5 Aşama C (10.10.2026): `count` optional — Yeşilova's turbine model (Vestas V136)
    # is given but its count is not; Karatepe/Boztepe always give both, unaffected.
    count: Fact | None = None
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
    # Adım 5: Karatepe's margin changed with the 2nd amendment (Tansu §3.2) — same
    # initial/current/changed_by shape already used by `dscr_covenant`/`tenor_years`.
    margin_pct: ChangedFact


class SingleLenderInterest(_Strict):
    """Adım 5 Aşama C (10.10.2026): a lighter `Interest` for single-lender facilities with
    no margin-change history (Yeşilova: Term SOFR + 1,50%, never amended) — `Interest`
    itself stays untouched (Karatepe's own shape, margin genuinely changed once)."""

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
    # Adım 5 Aşama C (10.10.2026): some facilities state a per-instalment interest figure
    # directly (Karatepe's interest is computed by `debt_math.py`, never stored here —
    # this stays `None` for Karatepe). Yeşilova's instalment #11 is a deliberate conflict
    # against `BankInterestNotice` (schedule says 18.240, the bank's own notice says 18.912).
    interest: Money | None = None


class BankInterestNotice(_Strict):
    """Adım 5 Aşama C (10.10.2026): a lender's own interest notice for one instalment,
    kept distinct from the repayment schedule's own figure — not every facility has a
    deliberate gap between the two (Yeşilova's #11 does, Tansu §3.2)."""

    instalment_date: date
    amount: Money
    tag: Tag


class QuarterCfads(_Strict):
    period: str = Field(pattern=r"^Q[1-4]_\d{4}$")
    cfads: Money
    tag: Tag


class GuaranteeLetter(_Strict):
    """Adım 5 İş 4a/4b (10.10.2026, NACI_CEVAP §3.2): Karatepe's forest-permit guarantee
    letter, due for renewal January 2027 — only the purpose and renewal month are given
    (no exact day), the issuing bank and amount are not. `renewal_date` is a `Fact` (its
    `value` a string like "Ocak 2027"), not a strict `date` — a real `date` would force a
    day Tansu never gave (no fabrication)."""

    purpose: Fact
    renewal_date: Fact
    lender: Fact | None = None
    amount: Money | None = None
    doc: str | None = None
    tag: Tag


class Finance(_Strict):
    # Adım 5 Aşama C (10.10.2026): reused for Yeşilova/Boztepe (ADIM5_ASAMA_C_REPORT.md
    # §2) — most fields below are Optional/default-empty *only* because Tansu's
    # NACI_CEVAP §3.2 doesn't give them for these two (no fabrication, ADIM5_ASAMA_C_PLAN
    # kuralı). Karatepe's own `ankara_res.yaml` populates every one of them, so none of
    # this loosening changes Karatepe's behavior.
    capex: Money | None = None
    equity: Money | None = None
    total_debt: Money | None = None
    local_debt: Money | None = None
    eca_debt: Money | None = None
    lenders: Lenders | None = None
    # Single-lender facilities (Yeşilova, Boztepe) that don't split local/ECA.
    lender: Fact | None = None
    interest: Interest | SingleLenderInterest | None = None
    tenor_years: ChangedFact | None = None
    grace_months: Fact | None = None
    repayment_profile: Fact | None = None
    dscr_covenant: ChangedFact | Fact | None = None
    drawdowns: list[Drawdown] = Field(default_factory=list)
    outstanding_debt_as_of_demo_today: Money | None = None
    # Adım 5 (Tansu §3.2): DSRA balance — a new, optional fact (not every SPV has one yet).
    dsra_balance: Money | None = None
    # Adım 5 (Tansu §3.2, kasıtlı tuzak): the signed facility size, kept distinct from
    # `total_debt` (the actually drawn/repaid amount) — not every SPV has this gap.
    contract_amount: Money | None = None
    covenant_tests: list[CovenantTest] = Field(default_factory=list)
    facility_chain: list[str] = Field(default_factory=list)
    # Phase 4.2 (Financial Model inputs)
    base_rate_pct_by_year: list[BaseRate] = Field(default_factory=list)
    repayment_schedule: list[Instalment] = Field(default_factory=list)
    cfads_by_quarter: list[QuarterCfads] = Field(default_factory=list)
    # Adım 5 Aşama C: Yeşilova's dedicated debt-service account balance.
    debt_service_account_balance: Money | None = None
    # Adım 5 Aşama C: Yeşilova instalment #11's bank-notice interest, deliberately
    # conflicting with that instalment's own `repayment_schedule.interest` figure.
    bank_interest_notices: list[BankInterestNotice] = Field(default_factory=list)
    # Adım 5 İş 4a: Karatepe's forest-permit guarantee letter (not every SPV has one).
    guarantee_letters: list[GuaranteeLetter] = Field(default_factory=list)
    # Adım 5 İş 4b: Yeşilova's Annex F reporting request (NACI_CEVAP §3.2) — request
    # e-mail date, deadline, and the reporting year the request covers.
    annex_f_request_date: date | None = None
    annex_f_deadline: date | None = None
    annex_f_reporting_year: int | None = None


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
    # Adım 5 Aşama C (10.10.2026): reused for Yeşilova/Boztepe/Güneşalan, none of which
    # Tansu gave monthly production/budget figures for — Karatepe's `ankara_res.yaml`
    # still populates every one of these, unaffected.
    operating_year_on_demo_today: Fact | None = None
    monthly_production: list[MonthlyProduction] = Field(default_factory=list)
    budget_vs_actual: list[BudgetVsActual] = Field(default_factory=list)
    incidents: list[Incident] = Field(default_factory=list)
    # Adım 5 Aşama C: O&M contractor + contract price (Enercon Servis Türkiye 38.500
    # EUR/ay, Vestas Bakım Hizmetleri 396.000 EUR/yıl, Solaris 3.240.000 TRY/yıl).
    om_contractor: Fact | None = None
    om_contract_price: Money | None = None
    # Insurance policy expiry (Boztepe 10.11.2026, Yeşilova 31.03.2027).
    insurance_expiry: date | None = None
    # Adım 5 İş 4b (NACI_CEVAP §3.7): policy number, for the endorsement/renewal notices.
    insurance_policy_no: Fact | None = None


class AnkaraProject(_Strict):
    code: Literal["ANK_RES"]
    # Adım 5 (Ç-9 B, Tansu §3): display name only — the code/file/`DOC-ANK-*` prefix is
    # unchanged (Naci SORU 1, 09.10.2026) so every cross-reference stays valid.
    name: Literal["Karatepe RES"]
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
    # Adım 5 Aşama C (10.10.2026): reused for Akyar/Demirci — Tansu's NACI_CEVAP §3.1
    # gives only each one's pre-licence date/expiry, nothing about development start,
    # land acquisition or a ÇED application; Kızılova's own data still populates every
    # one of these, so loosening them to Optional doesn't change Kızılova's behavior.
    development_start: Event | None = None
    pre_licence_application: Event | None = None
    pre_licence: Event
    # Adım 5 (Tansu §3.1): the pre-licence itself has an expiry — a new fact, not present
    # when İzmir/Kızılova was pure "nothing granted yet" development.
    pre_licence_expiry: Event
    land_acquisition_start: Event | None = None
    ced_application: Event | None = None
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


class SignedUndrawnFacility(_Strict):
    """Adım 5 Aşama C (10.10.2026, NACI_CEVAP §3.2, 2026-KZ) — Kızılova-specific, not
    shared with `Finance` or the generic development shape (Naci's correction): a credit
    that is signed but undrawn, conditional on the licence. No interest accrues and no
    repayment schedule exists yet, so `Finance`'s shape doesn't fit."""

    lender: Fact
    contract_amount: Money
    # Tansu confirms only the signing *year* (the "2026-KZ" code itself, §3.2's "kod yılı
    # = imza yılı"), not an exact day — stays unset rather than a guessed date.
    signed_date: date | None = None
    drawdown_condition: Fact | None = None
    commitment_fee: Money | None = None
    commitment_fee_date: date | None = None


class SignedUnstartedEpc(_Strict):
    """Adım 5 Aşama C: Kızılova's EPC is signed (LNTP issued) but construction hasn't
    started. Tansu's İ-1 scope note (NACI_CEVAP §3.3) is explicit: no CAR/EAR insurance,
    no drawdown request, no construction progress report exist for Kızılova yet — this
    shape only carries what *does* exist (the contract, the advance, its guarantee)."""

    contractor: Fact
    contract_price: Money
    signed_date: date
    lntp: bool = True
    advance_pct: float | None = None
    advance_amount: Money | None = None
    advance_guarantee: Fact | None = None
    advance_guarantee_amount: Money | None = None
    advance_guarantee_expiry: date | None = None
    # Adım 5 İş 4b (10.10.2026): promoted out of `advance_amount.note` into structured
    # fields — the Avans Faturası document needs them as real `key_facts` paths.
    advance_invoice_no: Fact | None = None
    advance_invoice_dispute_deadline: date | None = None
    advance_invoice_due_date: date | None = None
    advance_invoice_paid_date: date | None = None


class IzmirProject(_Strict):
    code: Literal["IZM_RES"]
    name: Literal["Kızılova RES"]
    stage: Literal["development"]
    spv: Spv
    capacity_mw: TargetCapacity
    turbines: None
    timeline: IzmirTimeline
    finance: None
    construction: None
    operations: None
    development: Development
    # Adım 5 Aşama C: Kızılova-specific (not Akyar/Demirci's `GenericDevelopmentProject`).
    signed_undrawn_facility: SignedUndrawnFacility | None = None
    signed_unstarted_epc: SignedUnstartedEpc | None = None


# ---------------------------------------------------------------- documents inventory


class Document(_Strict):
    id: str = Field(
        pattern=r"^DOC-(ANK|IZM|CO|YSV|BOZ|GNS|AKY|DMR)-(DEV|FIN|EPC|OPS|LEG|ADM)-\d{3}$"
    )
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


# ---------------------------------------------------------------- Adım 5 Aşama C: shared
# project shapes (ADIM5_ASAMA_C_REPORT.md §2). Additive only — AnkaraProject/AnkaraLedger
# and IzmirProject/IzmirLedger above are never touched; these two new shapes exist
# alongside them for the other 5 SPVs (NACI_CEVAP §3.1):
#   OperatingProject            -> Yeşilova RES, Boztepe RES, Güneşalan GES
#   GenericDevelopmentProject   -> Akyar GES, Demirci RES
# A project's exact `code`/`name` are plain `str` (pattern-checked), not a per-project
# Literal — adding an 8th/9th SPV later needs a new ledger file, not a new schema class.
_PROJECT_CODE_PATTERN = r"^[A-Z]{3}_(RES|GES)$"


class OperatingCapacity(_Strict):
    """A single current capacity value — unlike `Capacity`, no amendment history is
    claimed (Tansu's NACI_CEVAP §3.1 gives one number per SPV, nothing about a change)."""

    current: Fact


class OperatingTimeline(_Strict):
    """Deliberately thin: Tansu's NACI_CEVAP §3 restates only each SPV's *current*
    operating facts (capacity, credit, O&M), not its development/construction history —
    unlike `AnkaraTimeline`, nothing here is required."""

    commissioning: Event | None = None
    operation_start: Event | None = None
    cod_actual: Event | None = None


class OperatingProject(_Strict):
    code: str = Field(pattern=_PROJECT_CODE_PATTERN)
    name: str
    stage: Literal["operation"]
    spv: Spv
    capacity_mw: OperatingCapacity
    turbines: Turbines | None = None
    timeline: OperatingTimeline
    finance: Finance | None = None
    # No EPC/construction history is given for an already-operating SPV in this round
    # (ADIM5_ASAMA_C_REPORT.md §2) — structurally `None`, same as `IzmirProject`'s.
    construction: None = None
    operations: Operations | None = None


class GenericDevelopmentProject(_Strict):
    """Same shape as `IzmirProject`, generalized: `IzmirTimeline`/`Development`/
    `TargetCapacity` were already project-agnostic, only `IzmirProject` itself was
    Literal-locked to Kızılova's code/name."""

    code: str = Field(pattern=_PROJECT_CODE_PATTERN)
    name: str
    stage: Literal["development"]
    spv: Spv
    capacity_mw: TargetCapacity
    turbines: None = None
    timeline: IzmirTimeline
    finance: None = None
    construction: None = None
    operations: None = None
    # Akyar/Demirci: Tansu gives only the pre-licence date/expiry (in `timeline`), no ÇED
    # status or permit history — `development` stays unset rather than fabricated.
    development: Development | None = None


class OperatingLedger(_Strict):
    meta: Meta
    project: OperatingProject
    documents: list[Document]


class GenericDevelopmentLedger(_Strict):
    meta: Meta
    project: GenericDevelopmentProject
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
    # Adım 5 (09.10.2026): 5 new SPVs registered as a lightweight company-level entry
    # (name + shareholders) only — none has its own deep `*Ledger` yet (no documents exist
    # for them in this round; ADIM5_ASAMA_A_REPORT.md §2 flags the full per-SPV ledger as a
    # prerequisite for the Enerji/Hukuk/Mali parties, not done here).
    project_code: Literal[
        "ANK_RES", "IZM_RES", "YSV_RES", "BOZ_RES", "GNS_GES", "AKY_GES", "DMR_RES"
    ]
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
    expected_project: (
        Literal[
            "Karatepe RES",
            "Kızılova RES",
            "Yeşilova RES",
            "Boztepe RES",
            "Güneşalan GES",
            "Akyar GES",
            "Demirci RES",
        ]
        | None
    )
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
