from typing import Optional
from pydantic import BaseModel, Field


class ClientFeatures(BaseModel):
   	# Requis par feature_engineering
    DAYS_BIRTH: float = Field(..., lt=0)
    DAYS_EMPLOYED: float
    AMT_INCOME_TOTAL: float = Field(..., gt=0)
    AMT_CREDIT: float = Field(..., gt=0)
    AMT_ANNUITY: float = Field(..., gt=0)

    # Optionnels
    CODE_GENDER: Optional[str] = None
    CNT_CHILDREN: Optional[int] = None
    CNT_FAM_MEMBERS: Optional[float] = None
    NAME_CONTRACT_TYPE: Optional[str] = None
    NAME_FAMILY_STATUS: Optional[str] = None
    NAME_HOUSING_TYPE: Optional[str] = None
    NAME_INCOME_TYPE: Optional[str] = None
    NAME_EDUCATION_TYPE: Optional[str] = None
    NAME_TYPE_SUITE: Optional[str] = None
    OCCUPATION_TYPE: Optional[str] = None
    ORGANIZATION_TYPE: Optional[str] = None
    FLAG_OWN_CAR: Optional[str] = None
    FLAG_OWN_REALTY: Optional[str] = None
    AMT_GOODS_PRICE: Optional[float] = None
    DAYS_REGISTRATION: Optional[float] = None
    DAYS_ID_PUBLISH: Optional[float] = None
    DAYS_LAST_PHONE_CHANGE: Optional[float] = None
    DAYS_EMPLOYED_ANOM: Optional[bool] = None
    HOUR_APPR_PROCESS_START: Optional[int] = None
    WEEKDAY_APPR_PROCESS_START: Optional[str] = None
    EXT_SOURCE_1: Optional[float] = None
    EXT_SOURCE_2: Optional[float] = None
    EXT_SOURCE_3: Optional[float] = None
    REGION_POPULATION_RELATIVE: Optional[float] = None
    REGION_RATING_CLIENT: Optional[int] = None
    REGION_RATING_CLIENT_W_CITY: Optional[int] = None
    REG_REGION_NOT_LIVE_REGION: Optional[int] = None
    REG_REGION_NOT_WORK_REGION: Optional[int] = None
    REG_CITY_NOT_LIVE_CITY: Optional[int] = None
    REG_CITY_NOT_WORK_CITY: Optional[int] = None
    LIVE_REGION_NOT_WORK_REGION: Optional[int] = None
    LIVE_CITY_NOT_WORK_CITY: Optional[int] = None
    FLOORSMAX_AVG: Optional[float] = None
    FLOORSMAX_MODE: Optional[float] = None
    FLOORSMAX_MEDI: Optional[float] = None
    TOTALAREA_MODE: Optional[float] = None
    YEARS_BEGINEXPLUATATION_AVG: Optional[float] = None
    YEARS_BEGINEXPLUATATION_MODE: Optional[float] = None
    YEARS_BEGINEXPLUATATION_MEDI: Optional[float] = None
    EMERGENCYSTATE_MODE: Optional[str] = None
    FLAG_MOBIL: Optional[int] = None
    FLAG_EMP_PHONE: Optional[int] = None
    FLAG_WORK_PHONE: Optional[int] = None
    FLAG_CONT_MOBILE: Optional[int] = None
    FLAG_PHONE: Optional[int] = None
    FLAG_EMAIL: Optional[int] = None
    FLAG_DOCUMENT_2: Optional[int] = None
    FLAG_DOCUMENT_3: Optional[int] = None
    FLAG_DOCUMENT_4: Optional[int] = None
    FLAG_DOCUMENT_5: Optional[int] = None
    FLAG_DOCUMENT_6: Optional[int] = None
    FLAG_DOCUMENT_7: Optional[int] = None
    FLAG_DOCUMENT_8: Optional[int] = None
    FLAG_DOCUMENT_9: Optional[int] = None
    FLAG_DOCUMENT_10: Optional[int] = None
    FLAG_DOCUMENT_11: Optional[int] = None
    FLAG_DOCUMENT_12: Optional[int] = None
    FLAG_DOCUMENT_13: Optional[int] = None
    FLAG_DOCUMENT_14: Optional[int] = None
    FLAG_DOCUMENT_15: Optional[int] = None
    FLAG_DOCUMENT_16: Optional[int] = None
    FLAG_DOCUMENT_17: Optional[int] = None
    FLAG_DOCUMENT_18: Optional[int] = None
    FLAG_DOCUMENT_19: Optional[int] = None
    FLAG_DOCUMENT_20: Optional[int] = None
    FLAG_DOCUMENT_21: Optional[int] = None
    OBS_30_CNT_SOCIAL_CIRCLE: Optional[float] = None
    DEF_30_CNT_SOCIAL_CIRCLE: Optional[float] = None
    OBS_60_CNT_SOCIAL_CIRCLE: Optional[float] = None
    DEF_60_CNT_SOCIAL_CIRCLE: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_HOUR: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_DAY: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_WEEK: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_MON: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_QRT: Optional[float] = None
    AMT_REQ_CREDIT_BUREAU_YEAR: Optional[float] = None
    bureau_count: Optional[float] = None
    bureau_active_count: Optional[float] = None
    actif_count: Optional[float] = None
    cloture_count: Optional[float] = None
    bureau_overdue_mean: Optional[float] = None
    bureau_debt_mean: Optional[float] = None
    actif_debt_mean: Optional[float] = None
    cloture_debt_mean: Optional[float] = None
    prev_count: Optional[float] = None
    approve_count: Optional[float] = None
    refuse_count: Optional[float] = None
    prev_refused_count: Optional[float] = None
    taux_refus: Optional[float] = None
    prev_credit_mean: Optional[float] = None
    approve_credit_mean: Optional[float] = None
    refuse_credit_mean: Optional[float] = None
    a_carte_credit: Optional[float] = None
    cc_balance_mean: Optional[float] = None
    cc_dpd_mean: Optional[float] = None
    cc_utilisation_mean: Optional[float] = None
    pos_dpd_mean: Optional[float] = None
    pos_dpd_max: Optional[float] = None
    inst_retard_mean: Optional[float] = None
    inst_retard_max: Optional[float] = None
    inst_diff_mean: Optional[float] = None
    a_eu_retard: Optional[float] = None


class PredictionResponse(BaseModel):
    score: float = Field(..., ge=0, le=1, description="Probabilité de défaut (0 = bon payeur, 1 = défaut)")
    decision: str = Field(..., description="'approved' ou 'rejected'")
