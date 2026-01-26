#!/usr/bin/env python3
"""
ONTO ROI Calculator

Quantifies the financial value of epistemic risk management.
Use in sales conversations to justify pricing.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class CompanyProfile:
    """Customer profile for ROI calculation"""
    annual_revenue: float  # USD
    ai_transactions_per_year: int  # Number of AI-generated outputs
    industry: str  # healthcare, finance, legal, general
    enterprise_customers: bool
    regulated: bool


@dataclass
class RiskScenarios:
    """Potential liability scenarios"""
    lawsuit_probability: float  # Per year
    lawsuit_cost: float
    regulatory_fine_probability: float
    regulatory_fine_cost: float
    lost_deal_probability: float
    lost_deal_cost: float
    brand_damage_cost: float


@dataclass 
class ROIResult:
    """ROI calculation result"""
    expected_annual_loss: float
    onto_annual_cost: float
    risk_reduction: float
    net_savings: float
    roi_multiple: float
    payback_months: float


def get_industry_risk_factors(industry: str) -> dict:
    """Get risk multipliers by industry"""
    factors = {
        "healthcare": {
            "lawsuit_mult": 2.5,
            "regulatory_mult": 2.0,
            "deal_mult": 1.5,
        },
        "finance": {
            "lawsuit_mult": 2.0,
            "regulatory_mult": 2.5,
            "deal_mult": 2.0,
        },
        "legal": {
            "lawsuit_mult": 3.0,
            "regulatory_mult": 1.5,
            "deal_mult": 1.5,
        },
        "general": {
            "lawsuit_mult": 1.0,
            "regulatory_mult": 1.0,
            "deal_mult": 1.0,
        },
    }
    return factors.get(industry, factors["general"])


def calculate_risk_scenarios(profile: CompanyProfile) -> RiskScenarios:
    """Calculate risk scenarios based on company profile"""
    
    factors = get_industry_risk_factors(profile.industry)
    
    # Base probabilities (per year)
    base_lawsuit_prob = 0.02  # 2% base chance of lawsuit
    base_regulatory_prob = 0.05  # 5% base chance of regulatory action
    base_lost_deal_prob = 0.10  # 10% chance of losing deal due to AI concerns
    
    # Adjust for profile
    if profile.enterprise_customers:
        base_lawsuit_prob *= 1.5
        base_lost_deal_prob *= 2.0
    
    if profile.regulated:
        base_regulatory_prob *= 2.0
    
    # Calculate costs
    lawsuit_cost = max(1_000_000, profile.annual_revenue * 0.1)  # 10% of revenue or $1M
    regulatory_fine = profile.annual_revenue * 0.06  # EU AI Act max: 6%
    lost_deal_cost = profile.annual_revenue * 0.05  # 5% of revenue per lost deal
    brand_damage = profile.annual_revenue * 0.02  # 2% ongoing brand impact
    
    return RiskScenarios(
        lawsuit_probability=base_lawsuit_prob * factors["lawsuit_mult"],
        lawsuit_cost=lawsuit_cost,
        regulatory_fine_probability=base_regulatory_prob * factors["regulatory_mult"],
        regulatory_fine_cost=regulatory_fine,
        lost_deal_probability=base_lost_deal_prob * factors["deal_mult"],
        lost_deal_cost=lost_deal_cost,
        brand_damage_cost=brand_damage,
    )


def calculate_roi(
    profile: CompanyProfile,
    onto_annual_cost: float = 120_000,  # $10K/month
    risk_reduction: float = 0.7,  # ONTO reduces risk by 70%
) -> ROIResult:
    """
    Calculate ROI of ONTO implementation.
    
    Args:
        profile: Company profile
        onto_annual_cost: Annual cost of ONTO service
        risk_reduction: Percentage of risk reduced by ONTO
    
    Returns:
        ROI calculation result
    """
    
    scenarios = calculate_risk_scenarios(profile)
    
    # Calculate expected annual loss without ONTO
    expected_loss = (
        scenarios.lawsuit_probability * scenarios.lawsuit_cost +
        scenarios.regulatory_fine_probability * scenarios.regulatory_fine_cost +
        scenarios.lost_deal_probability * scenarios.lost_deal_cost +
        scenarios.brand_damage_cost * 0.5  # 50% chance of some brand impact
    )
    
    # Calculate savings with ONTO
    loss_with_onto = expected_loss * (1 - risk_reduction)
    net_savings = expected_loss - loss_with_onto - onto_annual_cost
    
    # ROI calculation
    if onto_annual_cost > 0:
        roi_multiple = net_savings / onto_annual_cost
        payback_months = (onto_annual_cost / (expected_loss * risk_reduction)) * 12
    else:
        roi_multiple = float('inf')
        payback_months = 0
    
    return ROIResult(
        expected_annual_loss=expected_loss,
        onto_annual_cost=onto_annual_cost,
        risk_reduction=risk_reduction,
        net_savings=net_savings,
        roi_multiple=roi_multiple,
        payback_months=payback_months,
    )


def generate_roi_summary(profile: CompanyProfile, result: ROIResult) -> str:
    """Generate human-readable ROI summary for sales"""
    
    return f"""
═══════════════════════════════════════════════════════════════
                    ONTO ROI ANALYSIS
                    {profile.industry.upper()} INDUSTRY
═══════════════════════════════════════════════════════════════

COMPANY PROFILE
───────────────────────────────────────────────────────────────
Annual Revenue:           ${profile.annual_revenue:,.0f}
AI Transactions/Year:     {profile.ai_transactions_per_year:,}
Enterprise Customers:     {'Yes' if profile.enterprise_customers else 'No'}
Regulated Industry:       {'Yes' if profile.regulated else 'No'}

RISK EXPOSURE (Without ONTO)
───────────────────────────────────────────────────────────────
Expected Annual Loss:     ${result.expected_annual_loss:,.0f}

Breakdown:
• Lawsuit liability exposure
• Regulatory fine exposure (EU AI Act: up to 6% revenue)
• Lost enterprise deals
• Brand/reputation damage

ONTO INVESTMENT
───────────────────────────────────────────────────────────────
Annual Cost:              ${result.onto_annual_cost:,.0f}
Risk Reduction:           {result.risk_reduction:.0%}

FINANCIAL IMPACT
───────────────────────────────────────────────────────────────
Net Annual Savings:       ${result.net_savings:,.0f}
ROI Multiple:             {result.roi_multiple:.0f}x
Payback Period:           {result.payback_months:.1f} months

═══════════════════════════════════════════════════════════════
BOTTOM LINE: For every $1 spent on ONTO, you avoid ${result.roi_multiple:.0f} in risk.
═══════════════════════════════════════════════════════════════
"""


def generate_one_liner(result: ROIResult) -> str:
    """Generate one-liner for email/call"""
    return (
        f"ROI: {result.roi_multiple:.0f}x return. "
        f"${result.onto_annual_cost/1000:.0f}K investment prevents "
        f"${result.expected_annual_loss/1_000_000:.1f}M+ in potential liability."
    )


# ============================================================
# PRESET SCENARIOS
# ============================================================

SCENARIOS = {
    "ai_startup_series_a": CompanyProfile(
        annual_revenue=5_000_000,
        ai_transactions_per_year=1_000_000,
        industry="general",
        enterprise_customers=True,
        regulated=False,
    ),
    "ai_startup_series_b": CompanyProfile(
        annual_revenue=20_000_000,
        ai_transactions_per_year=10_000_000,
        industry="general",
        enterprise_customers=True,
        regulated=False,
    ),
    "healthcare_ai": CompanyProfile(
        annual_revenue=10_000_000,
        ai_transactions_per_year=500_000,
        industry="healthcare",
        enterprise_customers=True,
        regulated=True,
    ),
    "legal_ai": CompanyProfile(
        annual_revenue=15_000_000,
        ai_transactions_per_year=200_000,
        industry="legal",
        enterprise_customers=True,
        regulated=True,
    ),
    "fintech_ai": CompanyProfile(
        annual_revenue=50_000_000,
        ai_transactions_per_year=5_000_000,
        industry="finance",
        enterprise_customers=True,
        regulated=True,
    ),
    "enterprise_copilot": CompanyProfile(
        annual_revenue=100_000_000,
        ai_transactions_per_year=50_000_000,
        industry="general",
        enterprise_customers=True,
        regulated=False,
    ),
}


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    print("ONTO ROI Calculator - Sample Scenarios\n")
    print("=" * 70)
    
    for name, profile in SCENARIOS.items():
        # Calculate for different ONTO tiers
        starter = calculate_roi(profile, onto_annual_cost=24_000)  # $2K/mo
        pro = calculate_roi(profile, onto_annual_cost=120_000)  # $10K/mo
        
        print(f"\n{name.upper().replace('_', ' ')}")
        print(f"Revenue: ${profile.annual_revenue/1_000_000:.0f}M | Industry: {profile.industry}")
        print(f"Expected Annual Risk: ${starter.expected_annual_loss/1_000_000:.2f}M")
        print(f"Starter Plan ($2K/mo): {starter.roi_multiple:.0f}x ROI, {starter.payback_months:.1f}mo payback")
        print(f"Pro Plan ($10K/mo): {pro.roi_multiple:.0f}x ROI, {pro.payback_months:.1f}mo payback")
    
    print("\n" + "=" * 70)
    print("\nDETAILED EXAMPLE: Healthcare AI Startup")
    print(generate_roi_summary(SCENARIOS["healthcare_ai"], 
                               calculate_roi(SCENARIOS["healthcare_ai"])))
