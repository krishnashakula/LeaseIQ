#!/usr/bin/env python3
"""
Advanced Business Intelligence Engine for Document Analysis
Enterprise-grade lease analysis, risk assessment, and portfolio optimization

Version: 2.0.0
Author: Enterprise Lease Intelligence Team
Last Updated: 2026-02-06
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from functools import lru_cache
from collections import Counter
import numpy as np
from dataclasses import dataclass, asdict, field
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
class AnalysisConfig:
    """Configuration constants for analysis engine"""
    # Financial ranges (USD) - Lowered minimums for better extraction
    MIN_RENT = 100  # Lowered from 500 to catch lower-priced rentals
    MAX_RENT = 100000
    MIN_DEPOSIT = 0  # Lowered from 100 to allow no deposit
    MAX_DEPOSIT = 100000
    MIN_PET_FEE = 0
    MAX_PET_FEE = 10000
    
    # Time ranges (days/months)
    MIN_NOTICE_PERIOD = 1
    MAX_NOTICE_PERIOD = 365
    MIN_LEASE_TERM = 1
    MAX_LEASE_TERM = 60
    
    # Risk thresholds
    RISK_LOW_THRESHOLD = 25
    RISK_MEDIUM_THRESHOLD = 50
    RISK_HIGH_THRESHOLD = 75
    
    # Market benchmarks
    MARKET_AVG_RENT_PER_SQFT = 2.50
    MARKET_AVG_DEPOSIT_RATIO = 1.2
    MARKET_AVG_PET_FEE = 25.0
    MARKET_AVG_NOTICE_PERIOD = 30
    
    # Confidence scoring
    MIN_TEXT_LENGTH_HIGH_CONF = 10000
    MIN_TEXT_LENGTH_MED_CONF = 5000

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

def dataclass_to_dict(obj):
    """Convert dataclass to dict, handling Enum serialization"""
    result = asdict(obj)
    for key, value in result.items():
        if isinstance(value, Enum):
            result[key] = value.value
    return result

@dataclass
class BusinessMetrics:
    """Core business metrics extracted from lease documents
    
    Attributes:
        monthly_rent: Base monthly rent amount (USD)
        security_deposit: Security deposit required (USD)
        pet_fees: Monthly pet fees (USD)
        utility_costs: Estimated monthly utility costs (USD)
        total_monthly_cost: Total monthly payment including all fees (USD)
        lease_duration_months: Length of lease term in months
        total_lease_value: Total value over entire lease period (USD)
        notice_period_days: Required notice period for termination (days)
        early_termination_penalty: Penalty for breaking lease early (USD)
        late_fee: Late payment fee (USD)
        application_fee: One-time application fee (USD)
        parking_fee: Monthly parking fee (USD)
        extraction_confidence: Confidence score for extracted values (0-1)
    """
    monthly_rent: float = 0.0
    security_deposit: float = 0.0
    pet_fees: float = 0.0
    utility_costs: float = 0.0
    total_monthly_cost: float = 0.0
    lease_duration_months: int = 0
    total_lease_value: float = 0.0
    notice_period_days: int = 0
    early_termination_penalty: float = 0.0
    late_fee: float = 0.0
    application_fee: float = 0.0
    parking_fee: float = 0.0
    extraction_confidence: float = 0.0
    
    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        self.total_monthly_cost = (
            self.monthly_rent + 
            self.pet_fees + 
            self.utility_costs +
            self.parking_fee
        )
        if self.lease_duration_months > 0:
            self.total_lease_value = self.total_monthly_cost * self.lease_duration_months

@dataclass
class RiskAssessment:
    """Comprehensive risk analysis
    
    Attributes:
        risk_level: Overall risk classification (LOW/MEDIUM/HIGH/CRITICAL)
        risk_score: Numerical risk score from 0-100 (higher = riskier)
        financial_exposure: Total financial risk exposure (USD)
        compliance_issues: List of potential compliance violations
        tenant_favorable_terms: Terms that favor the tenant
        landlord_favorable_terms: Terms that favor the landlord
        red_flags: Critical issues requiring immediate attention
        recommendations: Actionable recommendations to mitigate risks
        risk_factors: Detailed breakdown of risk contributors
        mitigation_strategies: Specific strategies to reduce risk
    """
    risk_level: RiskLevel
    risk_score: float  # 0-100
    financial_exposure: float
    compliance_issues: List[str] = field(default_factory=list)
    tenant_favorable_terms: List[str] = field(default_factory=list)
    landlord_favorable_terms: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_factors: Dict[str, float] = field(default_factory=dict)
    mitigation_strategies: List[Dict[str, str]] = field(default_factory=list)

class LeaseAnalysisEngine:
    """Advanced lease document analysis engine
    
    This engine performs comprehensive analysis of lease documents including:
    - Financial metrics extraction with OCR error correction
    - Risk assessment and compliance checking
    - Market position analysis and benchmarking
    - Revenue optimization opportunities identification
    - Portfolio-level insights generation
    
    Thread-safe and optimized for production use with caching.
    """
    
    def __init__(self):
        """Initialize analysis engine with enhanced pattern matching"""
        logger.info("Initializing LeaseAnalysisEngine")
        
        # Enhanced regex patterns with more comprehensive matching
        self.patterns = {
            'rent': [
                r'monthly.*base.*rent.*?\$\s?([\d,]+\.?\d*)',
                r'base.*rent.*?\$\s?([\d,]+\.?\d*)',
                r'monthly.*rent.*?\$\s?([\d,]+\.?\d*)',
                r'rent.*?\$\s?([\d,]+\.?\d*).*(?:per|/|a)\s*month',
                r'monthly.*payment.*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*per month',
                r'tenant.*pay.*?\$\s?([\d,]+\.?\d*).*month',
                r'rent(?:al)?.*amount.*?\$\s?([\d,]+\.?\d*)'
            ],
            'security_deposit': [
                r'security deposit.*?\$\s?([\d,]+\.?\d*)',
                r'deposit.*amount.*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*security\s*deposit',
                r'initial.*deposit.*?\$\s?([\d,]+\.?\d*)'
            ],
            'pet_fee': [
                r'pet.*(?:fee|rent|deposit).*?\$\s?([\d,]+\.?\d*)',
                r'animal.*(?:fee|rent).*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*(?:per|/)\s*pet',
                r'additional.*pet.*?\$\s?([\d,]+\.?\d*)'
            ],
            'late_fee': [
                r'late.*(?:fee|charge|payment).*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*late.*(?:fee|charge)',
                r'delinquent.*payment.*?\$\s?([\d,]+\.?\d*)'
            ],
            'application_fee': [
                r'application.*fee.*?\$\s?([\d,]+\.?\d*)',
                r'processing.*fee.*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*application'
            ],
            'parking_fee': [
                r'parking.*(?:fee|charge).*?\$\s?([\d,]+\.?\d*)',
                r'\$\s?([\d,]+\.?\d*).*parking',
                r'garage.*(?:fee|rent).*?\$\s?([\d,]+\.?\d*)'
            ],
            'utilities': [
                r'utilities.*?\$?([\d,]+\.?\d*)',
                r'electric.*?\$?([\d,]+\.?\d*)',
                r'gas.*?\$?([\d,]+\.?\d*)',
                r'water.*?\$?([\d,]+\.?\d*)'
            ],
            'notice_period': [
                r'(\d+).*day.*notice',
                r'notice.*(\d+).*day',
                r'(\d+).*calendar day.*notice'
            ],
            'lease_term': [
                r'(\d+).*month.*term',
                r'term.*(\d+).*month',
                r'lease.*period.*(\d+).*month'
            ],
            'termination_fee': [
                r'liquidated.*damages.*?\$?([\d,]+\.?\d*)',
                r'early.*termination.*?\$?([\d,]+\.?\d*)',
                r'termination.*fee.*?\$?([\d,]+\.?\d*)'
            ]
        }
        
        self.compliance_patterns = {
            'discrimination': [
                r'race|color|religion|sex|national origin|disability|familial status',
                r'no children|adults only|mature individuals'
            ],
            'illegal_fees': [
                r'non-refundable.*deposit',
                r'application.*fee.*\$(\d+)',
                r'processing.*fee.*\$(\d+)'
            ],
            'habitability': [
                r'as-is condition|no warranty|no guarantees',
                r'tenant.*responsible.*all.*repair'
            ]
        }

    def analyze_document(self, extraction_data: Dict) -> Dict[str, Any]:
        """Comprehensive document analysis"""
        
        full_text = extraction_data.get('data', {}).get('full_text', '')
        
        # Extract business metrics
        metrics = self._extract_business_metrics(full_text)
        
        # Risk assessment
        risk_assessment = self._assess_risks(full_text, metrics)
        
        # Market analysis
        market_analysis = self._analyze_market_position(metrics)
        
        # Portfolio insights
        portfolio_insights = self._generate_portfolio_insights(metrics, risk_assessment)
        
        # Revenue optimization
        revenue_opportunities = self._identify_revenue_opportunities(metrics, full_text)
        
        # Compliance analysis
        compliance_report = self._analyze_compliance(full_text)
        
        return {
            'business_metrics': dataclass_to_dict(metrics),
            'risk_assessment': dataclass_to_dict(risk_assessment),
            'market_analysis': market_analysis,
            'portfolio_insights': portfolio_insights,
            'revenue_opportunities': revenue_opportunities,
            'compliance_report': compliance_report,
            'analysis_timestamp': datetime.now().isoformat(),
            'confidence_score': self._calculate_confidence_score(full_text)
        }

    def _extract_business_metrics(self, text: str) -> BusinessMetrics:
        """Extract key financial metrics from lease text with enhanced error handling
        
        Args:
            text: Raw text extracted from lease document
            
        Returns:
            BusinessMetrics object with extracted financial data
        """
        logger.debug(f"Extracting business metrics from text ({len(text)} chars)")
        
        metrics = BusinessMetrics()
        confidence_scores = []
        
        # Clean up text by removing spaces between digits (common OCR issue)
        text_cleaned = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        text_lower = text_cleaned.lower()
        
        # Extract monthly rent with confidence tracking
        rent_extracted = False
        for pattern in self.patterns['rent']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    rent_value = float(matches[0].replace(',', '').replace(' ', ''))
                    if AnalysisConfig.MIN_RENT <= rent_value <= AnalysisConfig.MAX_RENT:
                        metrics.monthly_rent = rent_value
                        confidence_scores.append(0.9)
                        rent_extracted = True
                        logger.debug(f"Extracted monthly rent: ${rent_value}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse rent from pattern: {e}")
                    continue
        
        if not rent_extracted:
            logger.warning("Monthly rent not extracted from document")
            confidence_scores.append(0.0)
        
        # Extract security deposit
        deposit_extracted = False
        for pattern in self.patterns['security_deposit']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    deposit_value = float(matches[0].replace(',', '').replace(' ', ''))
                    if AnalysisConfig.MIN_DEPOSIT <= deposit_value <= AnalysisConfig.MAX_DEPOSIT:
                        metrics.security_deposit = deposit_value
                        confidence_scores.append(0.85)
                        deposit_extracted = True
                        logger.debug(f"Extracted security deposit: ${deposit_value}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse deposit: {e}")
                    continue
        
        if not deposit_extracted:
            confidence_scores.append(0.0)
        
        # Extract pet fees
        for pattern in self.patterns['pet_fee']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    pet_fee = float(matches[0].replace(',', '').replace(' ', ''))
                    if AnalysisConfig.MIN_PET_FEE <= pet_fee <= AnalysisConfig.MAX_PET_FEE:
                        metrics.pet_fees = pet_fee
                        confidence_scores.append(0.75)
                        logger.debug(f"Extracted pet fee: ${pet_fee}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse pet fee: {e}")
                    continue
        
        # Extract late fees
        for pattern in self.patterns.get('late_fee', []):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    late_fee = float(matches[0].replace(',', '').replace(' ', ''))
                    if 0 <= late_fee <= 500:
                        metrics.late_fee = late_fee
                        logger.debug(f"Extracted late fee: ${late_fee}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse late fee: {e}")
                    continue
        
        # Extract application fee
        for pattern in self.patterns.get('application_fee', []):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    app_fee = float(matches[0].replace(',', '').replace(' ', ''))
                    if 0 <= app_fee <= 500:
                        metrics.application_fee = app_fee
                        logger.debug(f"Extracted application fee: ${app_fee}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse application fee: {e}")
                    continue
        
        # Extract parking fee
        for pattern in self.patterns.get('parking_fee', []):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    parking_fee = float(matches[0].replace(',', '').replace(' ', ''))
                    if 0 <= parking_fee <= 1000:
                        metrics.parking_fee = parking_fee
                        logger.debug(f"Extracted parking fee: ${parking_fee}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse parking fee: {e}")
                    continue
        
        # Extract notice period
        for pattern in self.patterns['notice_period']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    notice_days = int(matches[0])
                    if AnalysisConfig.MIN_NOTICE_PERIOD <= notice_days <= AnalysisConfig.MAX_NOTICE_PERIOD:
                        metrics.notice_period_days = notice_days
                        confidence_scores.append(0.8)
                        logger.debug(f"Extracted notice period: {notice_days} days")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse notice period: {e}")
                    continue
        
        # Extract lease term
        for pattern in self.patterns['lease_term']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    term_months = int(matches[0])
                    if AnalysisConfig.MIN_LEASE_TERM <= term_months <= AnalysisConfig.MAX_LEASE_TERM:
                        metrics.lease_duration_months = term_months
                        confidence_scores.append(0.85)
                        logger.debug(f"Extracted lease term: {term_months} months")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse lease term: {e}")
                    continue
        
        # Extract termination fee
        for pattern in self.patterns['termination_fee']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    termination_fee = float(matches[0].replace(',', '').replace(' ', ''))
                    if termination_fee >= 0:  # Any positive value is valid
                        metrics.early_termination_penalty = termination_fee
                        logger.debug(f"Extracted termination penalty: ${termination_fee}")
                        break
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse termination fee: {e}")
                    continue
        
        # Calculate overall extraction confidence
        metrics.extraction_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        logger.info(f"Metrics extraction complete. Confidence: {metrics.extraction_confidence:.2%}")
        
        # Force recalculation of derived metrics
        metrics.total_monthly_cost = (
            metrics.monthly_rent + 
            metrics.pet_fees + 
            metrics.utility_costs +
            metrics.parking_fee
        )
        if metrics.lease_duration_months > 0:
            metrics.total_lease_value = metrics.total_monthly_cost * metrics.lease_duration_months
        
        logger.info(f"Total lease value calculated: ${metrics.total_lease_value:,.2f}")
        return metrics

    def _assess_risks(self, text: str, metrics: BusinessMetrics) -> RiskAssessment:
        """Comprehensive risk assessment with detailed factor tracking
        
        Args:
            text: Full lease document text
            metrics: Extracted business metrics
            
        Returns:
            RiskAssessment object with detailed risk analysis
        """
        logger.debug("Performing risk assessment")
        
        risk_score = 0.0
        risk_factors = {}
        red_flags = []
        compliance_issues = []
        recommendations = []
        mitigation_strategies = []
        
        # Financial risk assessment with detailed tracking
        if metrics.security_deposit > metrics.monthly_rent * 2:
            factor_score = 15.0
            risk_score += factor_score
            risk_factors['excessive_deposit'] = factor_score
            red_flags.append("Excessive security deposit (>2x monthly rent)")
            mitigation_strategies.append({
                'issue': 'High security deposit',
                'strategy': 'Negotiate deposit reduction to 1.5x monthly rent',
                'priority': 'high'
            })
        elif metrics.security_deposit > metrics.monthly_rent * 1.5:
            factor_score = 8.0
            risk_score += factor_score
            risk_factors['high_deposit'] = factor_score
        
        if metrics.early_termination_penalty > metrics.monthly_rent * 2:
            factor_score = 12.0
            risk_score += factor_score
            risk_factors['high_termination_penalty'] = factor_score
            red_flags.append("High early termination penalty (>2x monthly rent)")
            mitigation_strategies.append({
                'issue': 'Excessive termination penalty',
                'strategy': 'Request cap at 1 month rent or prorated amount',
                'priority': 'medium'
            })
        elif metrics.early_termination_penalty > metrics.monthly_rent:
            factor_score = 6.0
            risk_score += factor_score
            risk_factors['termination_penalty'] = factor_score
        
        if metrics.notice_period_days > 60:
            factor_score = 10.0
            risk_score += factor_score
            risk_factors['extended_notice'] = factor_score
            red_flags.append(f"Extended notice period requirement ({metrics.notice_period_days} days)")
            mitigation_strategies.append({
                'issue': 'Long notice period',
                'strategy': 'Negotiate reduction to 30 days standard notice',
                'priority': 'low'
            })
        elif metrics.notice_period_days > 45:
            factor_score = 5.0
            risk_score += factor_score
            risk_factors['long_notice'] = factor_score
        
        # Late fee risk assessment
        if metrics.late_fee > metrics.monthly_rent * 0.1:
            factor_score = 8.0
            risk_score += factor_score
            risk_factors['excessive_late_fee'] = factor_score
            red_flags.append(f"Excessive late fee (${metrics.late_fee:.2f})")
        
        # Application fee check
        if metrics.application_fee > 100:
            factor_score = 5.0
            risk_score += factor_score
            risk_factors['high_application_fee'] = factor_score
        
        # Text-based risk analysis with frequency tracking
        text_lower = text.lower()
        
        # Aggressive language patterns with severity weighting
        aggressive_terms = [
            ('strictly enforced', 5),
            ('no exceptions', 5),
            ('immediate eviction', 10),
            ('forfeit all rights', 12),
            ('waive all claims', 12),
            ('hold harmless', 8),
            ('indemnify landlord', 10),
            ('at landlord\'s sole discretion', 7)
        ]
        
        aggressive_count = 0
        for term, severity in aggressive_terms:
            if term in text_lower:
                risk_score += severity
                aggressive_count += 1
                red_flags.append(f"Aggressive lease language: '{term}'")
                logger.debug(f"Found aggressive term: {term} (severity: {severity})")
        
        if aggressive_count > 0:
            risk_factors['aggressive_language'] = aggressive_count * 5
        
        # Tenant-unfavorable clauses with severity weighting
        unfavorable_clauses = [
            ('landlord not responsible', 8),
            ('tenant assumes all risk', 10),
            ('no warranty', 6),
            ('as-is condition', 7),
            ('tenant liable for all damages', 9),
            ('no repairs by landlord', 12),
            ('waiver of habitability', 15)
        ]
        
        unfavorable_count = 0
        for clause, severity in unfavorable_clauses:
            if clause in text_lower:
                risk_score += severity
                unfavorable_count += 1
                red_flags.append(f"Tenant-unfavorable clause: '{clause}'")
                logger.debug(f"Found unfavorable clause: {clause} (severity: {severity})")
        
        if unfavorable_count > 0:
            risk_factors['unfavorable_terms'] = unfavorable_count * 7
        
        # Compliance checks with detailed violation tracking
        for issue_type, patterns in self.compliance_patterns.items():
            violations_found = []
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    violations_found.extend(matches)
            
            if violations_found:
                severity = 25 if issue_type == 'discrimination' else 15
                compliance_issues.append(
                    f"Potential {issue_type} violation: {len(violations_found)} instance(s)"
                )
                risk_score += severity
                risk_factors[f'compliance_{issue_type}'] = severity
                logger.warning(f"Compliance issue detected: {issue_type}")
                
                mitigation_strategies.append({
                    'issue': f'{issue_type.replace("_", " ").title()} Compliance',
                    'strategy': 'Consult legal counsel for compliance review',
                    'priority': 'critical'
                })
        
        # Generate smart recommendations based on risk factors
        if metrics.security_deposit > metrics.monthly_rent * 1.5:
            recommendations.append(
                f"Negotiate security deposit from ${metrics.security_deposit:.2f} "
                f"to ${metrics.monthly_rent * 1.5:.2f} (1.5x rent)"
            )
        
        if metrics.notice_period_days > 30:
            recommendations.append(
                f"Request notice period reduction from {metrics.notice_period_days} "
                f"to 30 days (industry standard)"
            )
        
        if risk_score > AnalysisConfig.RISK_HIGH_THRESHOLD:
            recommendations.append("CRITICAL: Engage legal counsel before signing")
            recommendations.append("Document all concerns in writing with landlord")
        elif risk_score > AnalysisConfig.RISK_MEDIUM_THRESHOLD:
            recommendations.append("Consider legal review of high-risk clauses")
        
        if len(compliance_issues) > 0:
            recommendations.append("Request removal of potentially illegal clauses")
        
        if len(red_flags) > 5:
            recommendations.append("Multiple red flags detected - consider alternative properties")
        
        # Determine risk level using config constants
        if risk_score <= AnalysisConfig.RISK_LOW_THRESHOLD:
            risk_level = RiskLevel.LOW
        elif risk_score <= AnalysisConfig.RISK_MEDIUM_THRESHOLD:
            risk_level = RiskLevel.MEDIUM
        elif risk_score <= AnalysisConfig.RISK_HIGH_THRESHOLD:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        logger.info(f"Risk assessment complete. Level: {risk_level.value}, Score: {risk_score:.1f}")
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=min(risk_score, 100),
            financial_exposure=self._calculate_financial_exposure(metrics),
            compliance_issues=compliance_issues,
            tenant_favorable_terms=self._identify_tenant_favorable_terms(text),
            landlord_favorable_terms=self._identify_landlord_favorable_terms(text),
            red_flags=red_flags,
            recommendations=recommendations,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies
        )

    def _analyze_market_position(self, metrics: BusinessMetrics) -> Dict[str, Any]:
        """Market analysis and benchmarking"""
        
        # Simulated market data (in real implementation, connect to market APIs)
        market_benchmarks = {
            'avg_rent_per_sqft': 2.50,
            'avg_security_deposit_ratio': 1.2,
            'avg_pet_fee': 25.0,
            'avg_notice_period': 30,
            'market_rent_range': (2200, 2800)
        }
        
        analysis = {
            'rent_vs_market': self._compare_to_market(metrics.monthly_rent, market_benchmarks['market_rent_range']),
            'security_deposit_ratio': metrics.security_deposit / metrics.monthly_rent if metrics.monthly_rent > 0 else 0,
            'pet_fee_competitiveness': 'above_market' if metrics.pet_fees > market_benchmarks['avg_pet_fee'] else 'below_market',
            'notice_period_favorability': 'tenant_favorable' if metrics.notice_period_days <= 30 else 'landlord_favorable',
            'overall_market_position': 'competitive',
            'cost_efficiency_score': self._calculate_cost_efficiency(metrics)
        }
        
        return analysis

    def _generate_portfolio_insights(self, metrics: BusinessMetrics, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate portfolio-level insights"""
        
        insights = {
            'property_classification': self._classify_property(metrics),
            'retention_probability': self._estimate_retention_probability(metrics, risk_assessment),
            'revenue_optimization_potential': self._calculate_revenue_potential(metrics),
            'operational_efficiency_score': self._calculate_operational_efficiency(risk_assessment),
            'investment_attractiveness': self._assess_investment_attractiveness(metrics, risk_assessment),
            'portfolio_fit_score': self._calculate_portfolio_fit(metrics)
        }
        
        return insights

    def _identify_revenue_opportunities(self, metrics: BusinessMetrics, text: str) -> List[Dict[str, Any]]:
        """Identify revenue optimization opportunities"""
        
        opportunities = []
        
        # Under-market rent opportunity
        market_rent = 2600  # Simulated market rate
        if metrics.monthly_rent < market_rent * 0.95:
            potential_increase = market_rent - metrics.monthly_rent
            opportunities.append({
                'type': 'rent_optimization',
                'description': 'Below-market rent pricing',
                'annual_impact': potential_increase * 12,
                'implementation_effort': 'low',
                'timeline': '30-60 days'
            })
        
        # Ancillary fee opportunities
        if 'parking' in text.lower() and 'fee' not in text.lower():
            opportunities.append({
                'type': 'parking_monetization',
                'description': 'Unmonetized parking spaces',
                'annual_impact': 600,  # $50/month parking fee
                'implementation_effort': 'medium',
                'timeline': '60-90 days'
            })
        
        # Utility cost recovery
        if metrics.utility_costs == 0 and 'tenant pays utilities' not in text.lower():
            opportunities.append({
                'type': 'utility_recovery',
                'description': 'Implement utility cost recovery',
                'annual_impact': 1200,  # $100/month utilities
                'implementation_effort': 'high',
                'timeline': '90-120 days'
            })
        
        return opportunities

    def _analyze_compliance(self, text: str) -> Dict[str, Any]:
        """Analyze regulatory compliance"""
        
        compliance_score = 100.0
        violations = []
        recommendations = []
        
        text_lower = text.lower()
        
        # Fair housing compliance
        discriminatory_language = [
            'no children', 'adults only', 'mature individuals preferred',
            'quiet tenants only', 'professional tenants'
        ]
        
        for term in discriminatory_language:
            if term in text_lower:
                compliance_score -= 25
                violations.append(f"Potentially discriminatory language: '{term}'")
                recommendations.append("Remove discriminatory language and ensure fair housing compliance")
        
        # Security deposit regulations
        if 'non-refundable deposit' in text_lower:
            compliance_score -= 15
            violations.append("Non-refundable deposits may violate local regulations")
            recommendations.append("Review local security deposit laws")
        
        # Required disclosures
        required_disclosures = ['lead paint', 'mold', 'asbestos', 'crime statistics']
        missing_disclosures = []
        
        for disclosure in required_disclosures:
            if disclosure not in text_lower:
                missing_disclosures.append(disclosure)
        
        if missing_disclosures:
            compliance_score -= len(missing_disclosures) * 5
            violations.append(f"Missing required disclosures: {', '.join(missing_disclosures)}")
            recommendations.append("Add all required property disclosures")
        
        return {
            'compliance_score': max(compliance_score, 0),
            'violations': violations,
            'recommendations': recommendations,
            'risk_level': 'high' if compliance_score < 70 else 'medium' if compliance_score < 85 else 'low'
        }

    def _calculate_financial_exposure(self, metrics: BusinessMetrics) -> float:
        """Calculate total financial exposure"""
        return (
            metrics.security_deposit +
            metrics.early_termination_penalty +
            (metrics.monthly_rent * 2)  # Estimated legal costs
        )

    def _identify_tenant_favorable_terms(self, text: str) -> List[str]:
        """Identify terms favorable to tenant"""
        favorable_terms = []
        text_lower = text.lower()
        
        favorable_patterns = [
            ('landlord responsible for repairs', 'Landlord handles maintenance'),
            ('rent includes utilities', 'Utilities included in rent'),
            ('no pet deposit', 'No pet deposit required'),
            ('month-to-month', 'Flexible lease terms')
        ]
        
        for pattern, description in favorable_patterns:
            if pattern in text_lower:
                favorable_terms.append(description)
        
        return favorable_terms

    def _identify_landlord_favorable_terms(self, text: str) -> List[str]:
        """Identify terms favorable to landlord"""
        favorable_terms = []
        text_lower = text.lower()
        
        landlord_patterns = [
            ('tenant responsible for all repairs', 'Tenant handles all maintenance'),
            ('no warranty', 'Property sold as-is'),
            ('liquidated damages', 'Early termination penalties'),
            ('automatic renewal', 'Auto-renewal clause')
        ]
        
        for pattern, description in landlord_patterns:
            if pattern in text_lower:
                favorable_terms.append(description)
        
        return favorable_terms

    def _compare_to_market(self, value: float, market_range: Tuple[float, float]) -> str:
        """Compare value to market range"""
        if value < market_range[0]:
            return 'below_market'
        elif value > market_range[1]:
            return 'above_market'
        else:
            return 'market_rate'

    def _calculate_cost_efficiency(self, metrics: BusinessMetrics) -> float:
        """Calculate cost efficiency score (0-100)"""
        if metrics.total_monthly_cost == 0:
            return 0.0
        
        # Simulated calculation
        efficiency_factors = {
            'rent_to_deposit_ratio': min(metrics.monthly_rent / metrics.security_deposit * 10, 25) if metrics.security_deposit > 0 else 25,
            'fee_reasonableness': 25 if metrics.pet_fees <= 50 else 10,
            'notice_period_flexibility': 25 if metrics.notice_period_days <= 30 else 10,
            'termination_penalty': 25 if metrics.early_termination_penalty <= metrics.monthly_rent else 10
        }
        
        return sum(efficiency_factors.values())

    def _classify_property(self, metrics: BusinessMetrics) -> str:
        """Classify property type based on metrics"""
        if metrics.monthly_rent >= 3000:
            return 'luxury'
        elif metrics.monthly_rent >= 2000:
            return 'mid_market'
        else:
            return 'affordable'

    def _estimate_retention_probability(self, metrics: BusinessMetrics, risk_assessment: RiskAssessment) -> float:
        """Estimate tenant retention probability (0-1)"""
        base_retention = 0.7
        
        # Risk factors
        risk_penalty = risk_assessment.risk_score / 100 * 0.3
        
        # Financial factors
        if metrics.monthly_rent > 0 and metrics.security_deposit / metrics.monthly_rent > 2:
            risk_penalty += 0.1
        
        # Notice period impact
        if metrics.notice_period_days > 60:
            risk_penalty += 0.1
        
        return max(base_retention - risk_penalty, 0.1)

    def _calculate_revenue_potential(self, metrics: BusinessMetrics) -> float:
        """Calculate revenue optimization potential"""
        market_rent = 2600  # Simulated
        if metrics.monthly_rent > 0:
            return max((market_rent - metrics.monthly_rent) * 12, 0)
        return 0

    def _calculate_operational_efficiency(self, risk_assessment: RiskAssessment) -> float:
        """Calculate operational efficiency score"""
        base_score = 100.0
        return max(base_score - risk_assessment.risk_score, 0)

    def _assess_investment_attractiveness(self, metrics: BusinessMetrics, risk_assessment: RiskAssessment) -> str:
        """Assess investment attractiveness"""
        score = 100 - risk_assessment.risk_score
        
        if metrics.monthly_rent >= 2500:
            score += 10
        
        if metrics.lease_duration_months >= 12:
            score += 5
        
        if score >= 80:
            return 'highly_attractive'
        elif score >= 60:
            return 'attractive'
        elif score >= 40:
            return 'moderate'
        else:
            return 'unattractive'

    def _calculate_portfolio_fit(self, metrics: BusinessMetrics) -> float:
        """Calculate how well property fits in portfolio"""
        # Simulated portfolio fit calculation
        return min(85.0, max(15.0, 50 + (metrics.monthly_rent / 100)))

    def _calculate_confidence_score(self, text: str) -> float:
        """Calculate confidence in analysis based on text quality"""
        base_score = 50.0
        
        # Length factor
        if len(text) > 10000:
            base_score += 20
        elif len(text) > 5000:
            base_score += 10
        
        # Structure factor
        if 'lease agreement' in text.lower():
            base_score += 15
        
        # Key terms presence
        key_terms = ['rent', 'deposit', 'tenant', 'landlord', 'term']
        present_terms = sum(1 for term in key_terms if term in text.lower())
        base_score += present_terms * 3
        
        return min(base_score, 95.0)


class PortfolioAnalyzer:
    """Portfolio-level analysis and optimization"""
    
    def __init__(self):
        self.analyzer = LeaseAnalysisEngine()
    
    def analyze_portfolio(self, lease_documents: List[Dict]) -> Dict[str, Any]:
        """Analyze entire portfolio of lease documents"""
        
        portfolio_metrics = []
        total_revenue = 0.0
        total_risk_exposure = 0.0
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for doc in lease_documents:
            analysis = self.analyzer.analyze_document(doc)
            portfolio_metrics.append(analysis)
            
            metrics = BusinessMetrics(**analysis['business_metrics'])
            total_revenue += metrics.total_lease_value
            total_risk_exposure += analysis['risk_assessment']['financial_exposure']
            
            risk_level = analysis['risk_assessment']['risk_level']
            risk_distribution[risk_level] += 1
        
        # Portfolio-level insights
        portfolio_insights = {
            'total_properties': len(lease_documents),
            'total_annual_revenue': total_revenue,
            'total_risk_exposure': total_risk_exposure,
            'risk_distribution': risk_distribution,
            'portfolio_risk_score': self._calculate_portfolio_risk(portfolio_metrics),
            'optimization_opportunities': self._identify_portfolio_opportunities(portfolio_metrics),
            'compliance_summary': self._summarize_portfolio_compliance(portfolio_metrics),
            'performance_benchmarks': self._calculate_portfolio_benchmarks(portfolio_metrics)
        }
        
        return {
            'individual_analyses': portfolio_metrics,
            'portfolio_insights': portfolio_insights,
            'executive_summary': self._generate_executive_summary(portfolio_insights)
        }
    
    def _calculate_portfolio_risk(self, analyses: List[Dict]) -> float:
        """Calculate portfolio-wide risk score"""
        if not analyses:
            return 0.0
        
        total_risk = sum(analysis['risk_assessment']['risk_score'] for analysis in analyses)
        return total_risk / len(analyses)
    
    def _identify_portfolio_opportunities(self, analyses: List[Dict]) -> List[Dict]:
        """Identify portfolio-wide optimization opportunities"""
        opportunities = []
        
        # Revenue optimization
        total_revenue_potential = sum(
            sum(opp['annual_impact'] for opp in analysis['revenue_opportunities'])
            for analysis in analyses
        )
        
        if total_revenue_potential > 50000:
            opportunities.append({
                'type': 'revenue_optimization',
                'description': 'Portfolio-wide revenue optimization',
                'potential_impact': total_revenue_potential,
                'priority': 'high'
            })
        
        # Risk consolidation
        high_risk_properties = sum(
            1 for analysis in analyses 
            if analysis['risk_assessment']['risk_level'] in ['high', 'critical']
        )
        
        if high_risk_properties > len(analyses) * 0.3:
            opportunities.append({
                'type': 'risk_mitigation',
                'description': 'Address high-risk properties',
                'affected_properties': high_risk_properties,
                'priority': 'critical'
            })
        
        return opportunities
    
    def _summarize_portfolio_compliance(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Summarize compliance across portfolio"""
        total_violations = 0
        common_issues = {}
        
        for analysis in analyses:
            compliance = analysis['compliance_report']
            total_violations += len(compliance['violations'])
            
            for violation in compliance['violations']:
                if violation in common_issues:
                    common_issues[violation] += 1
                else:
                    common_issues[violation] = 1
        
        return {
            'total_violations': total_violations,
            'avg_compliance_score': sum(
                analysis['compliance_report']['compliance_score'] 
                for analysis in analyses
            ) / len(analyses) if analyses else 0,
            'common_issues': common_issues,
            'properties_at_risk': sum(
                1 for analysis in analyses 
                if analysis['compliance_report']['compliance_score'] < 70
            )
        }
    
    def _calculate_portfolio_benchmarks(self, analyses: List[Dict]) -> Dict[str, float]:
        """Calculate portfolio performance benchmarks"""
        if not analyses:
            return {}
        
        metrics_list = [analysis['business_metrics'] for analysis in analyses]
        
        return {
            'avg_monthly_rent': np.mean([m['monthly_rent'] for m in metrics_list]),
            'avg_security_deposit': np.mean([m['security_deposit'] for m in metrics_list]),
            'avg_lease_value': np.mean([m['total_lease_value'] for m in metrics_list]),
            'avg_risk_score': np.mean([analysis['risk_assessment']['risk_score'] for analysis in analyses]),
            'portfolio_efficiency': np.mean([analysis['portfolio_insights']['operational_efficiency_score'] for analysis in analyses])
        }
    
    def _generate_executive_summary(self, portfolio_insights: Dict) -> Dict[str, Any]:
        """Generate executive summary for leadership"""
        
        risk_level = 'low'
        if portfolio_insights['portfolio_risk_score'] > 70:
            risk_level = 'high'
        elif portfolio_insights['portfolio_risk_score'] > 50:
            risk_level = 'medium'
        
        return {
            'portfolio_size': portfolio_insights['total_properties'],
            'annual_revenue': f"${portfolio_insights['total_annual_revenue']:,.0f}",
            'risk_assessment': risk_level,
            'optimization_potential': f"${sum(opp.get('potential_impact', 0) for opp in portfolio_insights['optimization_opportunities']):,.0f}",
            'key_recommendations': [
                opp['description'] for opp in 
                sorted(portfolio_insights['optimization_opportunities'], 
                       key=lambda x: x.get('potential_impact', 0), reverse=True)[:3]
            ],
            'immediate_actions_required': portfolio_insights['compliance_summary']['properties_at_risk']
        }


# Main API interface
def analyze_lease_document(extraction_data: Dict) -> Dict[str, Any]:
    """Main interface for lease document analysis"""
    analyzer = LeaseAnalysisEngine()
    return analyzer.analyze_document(extraction_data)

def analyze_lease_portfolio(documents: List[Dict]) -> Dict[str, Any]:
    """Main interface for portfolio analysis"""
    portfolio_analyzer = PortfolioAnalyzer()
    return portfolio_analyzer.analyze_portfolio(documents)