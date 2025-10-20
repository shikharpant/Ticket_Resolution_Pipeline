"""
Data models and schemas for GST Grievance Resolution System
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Annotated
from operator import add


class GrievanceCategory(str, Enum):
    """GST grievance categories"""
    # Account Aggregators
    AA_FIU = "Account Aggregators (AA) - FIU"

    # Annual Aggregate Turnover
    AATO = "Annual Aggregate Turnover (AATO)"

    # Assessment and Adjudication
    ASSESSMENT_DETERMINATION_TAX = "Assessment and Adjudication - determination of tax - DRC06"
    ASSESSMENT_DRC03 = "Assessment and Adjudication - DRC03"
    ASSESSMENT_DRC07 = "Assessment and Adjudication - DRC07"
    ASSESSMENT_PENALTY = "Assessment and Adjudication - Penalty"
    ASSESSMENT_RECTIFICATION = "Assessment and Adjudication - Rectification"
    ASSESSMENT_RESTORATION_ATTACHMENT = "Assessment and Adjudication - Restoration of Provisional Attachment"
    ASSESSMENT_SUMMARY_ASMT10 = "Assessment and Adjudication - Summary Assessment - ASMT10"
    ASSESSMENT_SUMMARY_ASMT17 = "Assessment and Adjudication - Summary Assessment - ASMT17"

    # Compliance and Forms
    CMP_08 = "CMP-08"
    DCR = "DCR"
    DRC_03A_FILING = "DRC-03A - filing"
    ENFORCEMENT_FO = "Enforcement-FO"
    FORM_GST_SRM1 = "Form GST SRM-1"

    # GSP API
    GSP_API_REFUNDS = "GSP-API-Refunds"
    GSP_API_REGISTRATION = "GSP-API-Registration"
    GSP_API_RETURNS_GSTR1 = "GSP-API-Returns-GSTR1"
    GSP_API_RETURNS_GSTR4 = "GSP-API-Returns-GSTR4"
    GSP_API_RETURNS_IMS = "GSP-API-Returns-IMS"
    GSP_API_SANDBOX = "GSP-API-Sandbox"

    # Integration
    GSTN_MCA_INTEGRATION = "GSTN-MCA Integration"
    ICEGATE = "ICEGATE"

    # Special Issues
    WAIVER_SCHEME = "Issues related to Waiver Scheme"
    ANNEXURE_V = "Online Filing of Annexure V"

    # Payments and Refunds
    ONLINE_REFUND_RFD01 = "Online Refund-RFD01"
    PAYMENTS = "Payments"
    PAYMENTS_PMT09 = "Payments - PMT09"
    REFUND_EXPORTS = "Refund - Exports"
    REFUNDS_RFD01A = "Refunds - RFD01A"
    REFUNDS_RFD10 = "Refunds - RFD10"

    # Registration
    REG_AMENDMENT_CORE = "Registration - Amendment of core fields"
    REG_AMENDMENT_NON_CORE = "Registration - Amendment of non-core fields"
    REG_AMENDMENT_NON_CORE_MAPS = "Registration - Amendment of non-core fields - Maps"
    REG_CANCELLATION = "Registration - Cancellation application"
    REG_COMPOSITION = "Registration - Composition"
    REG_MIGRATION = "Registration - Migration"
    REG_NEW_REGISTRATION = "Registration - New Registration"
    REG_NEW_REGISTRATION_MAPS = "Registration - New Registration - Maps"
    REG_REGISTER_UPDATE_DSC = "Registration - Register_Update DSC"
    REG_SEARCH_TAXPAYER = "Registration - Search Taxpayer"
    REG_SRM_PAN_MASALA = "Registration - SRM I / SRM II - Pan Masala"
    REG_TDS_APPLICATION = "Registration - TDS application"
    REG_REVOKE_CANCELLATION = "Registration- Revocation of cancellation"
    REG_SUSPENSION_GSTIN = "Registration- Suspension of GSTIN"

    # Returns
    RETURNS_GSTR1_OFFLINE = "Returns - GSTR1 Offline Filing"
    RETURNS_GSTR1_ONLINE = "Returns - GSTR1 Online Filing"
    RETURNS_GSTR10 = "Returns - GSTR10"
    RETURNS_GSTR2A = "Returns - GSTR2A"
    RETURNS_GSTR3B = "Returns - GSTR3B"
    RETURNS_GSTR4 = "Returns - GSTR4"
    RETURNS_GSTR4_ANNUAL = "Returns - GSTR4 Annual"
    RETURNS_GSTR4A = "Returns - GSTR4A"
    RETURNS_GSTR5 = "Returns - GSTR5"
    RETURNS_GSTR6 = "Returns - GSTR6"
    RETURNS_GSTR7 = "Returns - GSTR7"
    RETURNS_GSTR8 = "Returns - GSTR8"
    RETURNS_GSTR9 = "Returns - GSTR9"
    RETURNS_GSTR9C_OFFLINE = "Returns - GSTR9C Offline Filing"
    RETURNS_ITC01 = "Returns - ITC01"
    RETURNS_ITC02 = "Returns - ITC02"
    RETURNS_ITC03 = "Returns - ITC03"
    RETURNS_ITC04_OFFLINE = "Returns - ITC04 Offline Filing"
    RETURNS_TRAN1 = "Returns - Tran1"
    RETURNS_TRAN2 = "Returns - Tran2"
    RETURNS_GSTR1 = "Returns GSTR1"
    RETURNS_IMPORTS = "Returns IMPORTS"
    RETURNS_GSTR7_ALT = "Returns GSTR7"
    RETURNS_GSTR2B = "Returns-GSTR-2B"
    RETURNS_IMS = "Returns-IMS"
    RETURNS_TAX_LIABILITIES = "Returns-Tax Liabilities and ITC Comparison"

    # Other
    SMS_ISSUES = "SMS related issue"
    OTHERS = "Others"


class IntentType(str, Enum):
    """Intent types for user queries"""
    INFORMATIONAL = "informational"
    PROCEDURAL = "procedural"
    ERROR_RESOLUTION = "error_resolution"
    COMPLIANCE_CLARIFICATION = "compliance_clarification"
    REFUND_STATUS = "refund_status"


class ExtractedEntity(BaseModel):
    """Extracted entity from user query"""
    entity_type: str
    value: str
    context: Optional[str] = None


class CoreIssue(BaseModel):
    """Core issue identified in user query"""
    issue_text: str
    keywords: List[str]
    priority: int


class PreprocessingOutput(BaseModel):
    """Output from preprocessing agent"""
    cleaned_text: str
    detected_intent: str
    core_issues: List[CoreIssue]
    entities: List[ExtractedEntity]
    language: str


class ClassificationOutput(BaseModel):
    """Output from classification agent"""
    primary_category: str
    secondary_categories: List[str]
    confidence_scores: Dict[str, float]
    sub_type: Optional[str] = None


class RetrievalSource(BaseModel):
    """Individual retrieval result from any source"""
    source_type: str
    content: str
    citation: str
    relevance_score: float
    date: Optional[str] = None


class RetrievalOutput(BaseModel):
    """Combined output from all retrieval agents"""
    twitter_results: List[RetrievalSource]
    local_results: List[RetrievalSource]
    web_results: List[RetrievalSource]
    llm_reasoning: List[RetrievalSource]
    total_sources: int
    retrieval_time: float


class IssueResolution(BaseModel):
    """Resolution for individual issue"""
    issue: str
    resolution: Optional[str]
    confidence: int
    legal_basis: Optional[str] = None
    source_citations: List[str]
    reason_for_null: Optional[str] = None


class ResolverOutput(BaseModel):
    """Output from resolver agent"""
    resolutions: List[IssueResolution]
    overall_confidence: int
    requires_escalation: bool


class FinalResponse(BaseModel):
    """Final response to user"""
    direct_answer: str
    detailed_explanation: Optional[str] = None
    legal_basis: Optional[str] = None
    additional_resources: List[str] = []
    confidence_score: int
    requires_manual_review: bool


class AgentState(TypedDict):
    """State passed between agents in workflow"""
    # Input - single values
    user_query: str
    session_id: str
    selected_category: Optional[str]  # User-selected category
    timestamp: str
    processing_time: float
    iteration_count: int
    escalation_requested: bool

    # Lists that may be accumulated
    conversation_history: Annotated[List[Dict[str, str]], add]
    errors: Annotated[List[str], add]

    # Processing results - single assignments
    preprocessing_output: Optional[PreprocessingOutput]
    classification_output: Optional[ClassificationOutput]  # Will be set based on user selection
    retrieval_output: Optional[RetrievalOutput]
    resolver_output: Optional[ResolverOutput]
    final_response: Optional[FinalResponse]
