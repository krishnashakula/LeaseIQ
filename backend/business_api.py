#!/usr/bin/env python3
"""
Advanced Business Intelligence API Endpoints
Enterprise-grade lease analysis and portfolio management endpoints
"""

from flask import Flask, request, jsonify
import json
from pathlib import Path
import uuid
from datetime import datetime
from typing import Dict, List, Any
import os

# Import our business intelligence engine
from business_intelligence import (
    analyze_lease_document, 
    analyze_lease_portfolio,
    LeaseAnalysisEngine,
    PortfolioAnalyzer,
    RiskLevel
)

def register_business_intelligence_routes(app: Flask):
    """Register all business intelligence routes with the Flask app"""
    
    OUTPUT_FOLDER = Path('outputs')
    
    @app.route('/api/business/analyze/<job_id>', methods=['GET'])
    def analyze_lease_business_metrics(job_id):
        """Analyze business metrics for a specific lease document"""
        try:
            # Load the extracted document data
            output_file = OUTPUT_FOLDER / f"{job_id}.json"
            if not output_file.exists():
                return jsonify({'error': 'Document not found'}), 404
            
            with open(output_file, 'r', encoding='utf-8') as f:
                extraction_data = json.load(f)
            
            # Run business intelligence analysis
            business_analysis = analyze_lease_document(extraction_data)
            
            # Save the analysis results
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            analysis_output = {
                'status': 'success',
                'job_id': job_id,
                'analysis_type': 'business_intelligence',
                'timestamp': datetime.now().isoformat(),
                'original_filename': extraction_data.get('filename'),
                'business_intelligence': business_analysis
            }
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_output, f, indent=2, ensure_ascii=False)
            
            return jsonify(analysis_output), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Business analysis failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/portfolio/analyze', methods=['POST'])
    def analyze_portfolio():
        """Analyze entire portfolio of lease documents"""
        try:
            data = request.get_json()
            job_ids = data.get('job_ids', [])
            
            if not job_ids:
                return jsonify({'error': 'No job IDs provided'}), 400
            
            # Load all documents
            documents = []
            for job_id in job_ids:
                output_file = OUTPUT_FOLDER / f"{job_id}.json"
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        documents.append(doc_data)
            
            if not documents:
                return jsonify({'error': 'No valid documents found'}), 404
            
            # Run portfolio analysis
            portfolio_analysis = analyze_lease_portfolio(documents)
            
            # Save portfolio analysis
            portfolio_id = str(uuid.uuid4())
            portfolio_file = OUTPUT_FOLDER / f"portfolio_{portfolio_id}.json"
            
            portfolio_output = {
                'portfolio_id': portfolio_id,
                'analysis_type': 'portfolio_intelligence',
                'timestamp': datetime.now().isoformat(),
                'included_documents': job_ids,
                'analysis': portfolio_analysis
            }
            
            with open(portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio_output, f, indent=2, ensure_ascii=False)
            
            return jsonify(portfolio_output), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Portfolio analysis failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/risk-assessment/<job_id>', methods=['GET'])
    def get_risk_assessment(job_id):
        """Get detailed risk assessment for a lease document"""
        try:
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            if not analysis_file.exists():
                # Run analysis first if it doesn't exist
                return analyze_lease_business_metrics(job_id)
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            risk_assessment = analysis_data['analysis']['risk_assessment']
            
            # Add actionable recommendations
            risk_assessment['actionable_steps'] = _generate_risk_mitigation_steps(risk_assessment)
            
            return jsonify({
                'job_id': job_id,
                'risk_assessment': risk_assessment,
                'timestamp': analysis_data['timestamp']
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Risk assessment failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/revenue-optimization/<job_id>', methods=['GET'])
    def get_revenue_opportunities(job_id):
        """Get revenue optimization opportunities for a property"""
        try:
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            if not analysis_file.exists():
                return analyze_lease_business_metrics(job_id)
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            revenue_opportunities = analysis_data['analysis']['revenue_opportunities']
            market_analysis = analysis_data['analysis']['market_analysis']
            
            # Calculate total potential impact
            total_impact = sum(opp.get('annual_impact', 0) for opp in revenue_opportunities)
            
            return jsonify({
                'job_id': job_id,
                'revenue_opportunities': revenue_opportunities,
                'market_position': market_analysis,
                'total_annual_potential': total_impact,
                'roi_timeline': _calculate_roi_timeline(revenue_opportunities),
                'implementation_roadmap': _create_implementation_roadmap(revenue_opportunities)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Revenue optimization analysis failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/compliance-report/<job_id>', methods=['GET'])
    def get_compliance_report(job_id):
        """Get detailed compliance report for a lease document"""
        try:
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            if not analysis_file.exists():
                return analyze_lease_business_metrics(job_id)
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            compliance_report = analysis_data['analysis']['compliance_report']
            
            # Add regulatory guidance
            compliance_report['regulatory_guidance'] = _get_regulatory_guidance(compliance_report)
            compliance_report['priority_actions'] = _prioritize_compliance_actions(compliance_report)
            
            return jsonify({
                'job_id': job_id,
                'compliance_report': compliance_report,
                'legal_risk_level': _assess_legal_risk(compliance_report),
                'recommended_actions': _generate_compliance_actions(compliance_report)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Compliance analysis failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/portfolio/dashboard', methods=['POST'])
    def get_portfolio_dashboard():
        """Get executive dashboard data for portfolio"""
        try:
            data = request.get_json()
            job_ids = data.get('job_ids', [])
            
            # Load all individual analyses
            analyses = []
            for job_id in job_ids:
                analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
                if analysis_file.exists():
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                        analyses.append(analysis_data['analysis'])
            
            if not analyses:
                return jsonify({'error': 'No analysis data found'}), 404
            
            dashboard = _create_portfolio_dashboard(analyses)
            
            return jsonify({
                'dashboard_data': dashboard,
                'generated_at': datetime.now().isoformat(),
                'properties_analyzed': len(analyses)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Dashboard generation failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/market-intelligence/<job_id>', methods=['GET'])
    def get_market_intelligence(job_id):
        """Get market intelligence and competitive analysis"""
        try:
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            if not analysis_file.exists():
                return analyze_lease_business_metrics(job_id)
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            business_metrics = analysis_data['analysis']['business_metrics']
            market_analysis = analysis_data['analysis']['market_analysis']
            
            # Generate market intelligence
            market_intelligence = _generate_market_intelligence(business_metrics, market_analysis)
            
            return jsonify({
                'job_id': job_id,
                'market_intelligence': market_intelligence,
                'competitive_position': _assess_competitive_position(business_metrics),
                'pricing_recommendations': _generate_pricing_recommendations(market_analysis),
                'market_trends': _analyze_market_trends(business_metrics)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Market intelligence failed: {str(e)}'
            }), 500
    
    @app.route('/api/business/tenant-retention/<job_id>', methods=['GET'])
    def analyze_tenant_retention(job_id):
        """Analyze tenant retention risk and opportunities"""
        try:
            analysis_file = OUTPUT_FOLDER / f"{job_id}_analysis.json"
            if not analysis_file.exists():
                return analyze_lease_business_metrics(job_id)
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            portfolio_insights = analysis_data['analysis']['portfolio_insights']
            risk_assessment = analysis_data['analysis']['risk_assessment']
            
            retention_analysis = {
                'retention_probability': portfolio_insights['retention_probability'],
                'churn_risk_factors': _identify_churn_risk_factors(risk_assessment),
                'retention_strategies': _generate_retention_strategies(portfolio_insights),
                'intervention_timeline': _create_intervention_timeline(portfolio_insights),
                'financial_impact': _calculate_retention_financial_impact(portfolio_insights)
            }
            
            return jsonify({
                'job_id': job_id,
                'retention_analysis': retention_analysis,
                'recommended_actions': _generate_retention_actions(retention_analysis)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': f'Retention analysis failed: {str(e)}'
            }), 500

def _generate_risk_mitigation_steps(risk_assessment: Dict) -> List[Dict]:
    """Generate actionable risk mitigation steps"""
    steps = []
    
    if risk_assessment['risk_level'] in ['high', 'critical']:
        steps.append({
            'action': 'Legal Review Required',
            'priority': 'immediate',
            'timeline': '1-3 days',
            'cost_estimate': 500
        })
    
    if len(risk_assessment['compliance_issues']) > 0:
        steps.append({
            'action': 'Compliance Audit',
            'priority': 'high',
            'timeline': '1-2 weeks',
            'cost_estimate': 1500
        })
    
    if risk_assessment['financial_exposure'] > 10000:
        steps.append({
            'action': 'Insurance Review',
            'priority': 'medium',
            'timeline': '2-3 weeks',
            'cost_estimate': 300
        })
    
    return steps

def _calculate_roi_timeline(opportunities: List[Dict]) -> Dict:
    """Calculate ROI timeline for revenue opportunities"""
    timeline = {}
    
    for opp in opportunities:
        timeline_key = opp.get('timeline', 'unknown')
        if timeline_key not in timeline:
            timeline[timeline_key] = {
                'opportunities': 0,
                'total_impact': 0,
                'avg_effort': 0
            }
        
        timeline[timeline_key]['opportunities'] += 1
        timeline[timeline_key]['total_impact'] += opp.get('annual_impact', 0)
    
    return timeline

def _create_implementation_roadmap(opportunities: List[Dict]) -> List[Dict]:
    """Create implementation roadmap for revenue opportunities"""
    roadmap = []
    
    # Sort by impact and effort
    sorted_opps = sorted(opportunities, key=lambda x: x.get('annual_impact', 0), reverse=True)
    
    for i, opp in enumerate(sorted_opps):
        roadmap.append({
            'phase': i + 1,
            'opportunity': opp.get('description'),
            'timeline': opp.get('timeline'),
            'impact': opp.get('annual_impact'),
            'effort': opp.get('implementation_effort', 'medium')
        })
    
    return roadmap

def _get_regulatory_guidance(compliance_report: Dict) -> List[str]:
    """Get regulatory guidance for compliance issues"""
    guidance = []
    
    for violation in compliance_report.get('violations', []):
        if 'discriminatory' in violation.lower():
            guidance.append("Review Fair Housing Act requirements")
        elif 'deposit' in violation.lower():
            guidance.append("Check local security deposit regulations")
        elif 'disclosure' in violation.lower():
            guidance.append("Verify mandatory disclosure requirements")
    
    return guidance

def _prioritize_compliance_actions(compliance_report: Dict) -> List[Dict]:
    """Prioritize compliance actions by risk"""
    actions = []
    
    for violation in compliance_report.get('violations', []):
        if 'discriminatory' in violation.lower():
            actions.append({
                'action': 'Remove discriminatory language',
                'priority': 'critical',
                'legal_risk': 'high'
            })
        elif 'deposit' in violation.lower():
            actions.append({
                'action': 'Review deposit terms',
                'priority': 'high',
                'legal_risk': 'medium'
            })
    
    return actions

def _assess_legal_risk(compliance_report: Dict) -> str:
    """Assess legal risk level"""
    if compliance_report['compliance_score'] < 50:
        return 'critical'
    elif compliance_report['compliance_score'] < 70:
        return 'high'
    elif compliance_report['compliance_score'] < 85:
        return 'medium'
    else:
        return 'low'

def _generate_compliance_actions(compliance_report: Dict) -> List[str]:
    """Generate recommended compliance actions"""
    actions = []
    
    if compliance_report['compliance_score'] < 70:
        actions.append("Conduct immediate legal review")
        actions.append("Update lease template")
    
    if len(compliance_report['violations']) > 3:
        actions.append("Implement compliance monitoring system")
    
    return actions

def _create_portfolio_dashboard(analyses: List[Dict]) -> Dict:
    """Create executive dashboard data"""
    total_properties = len(analyses)
    total_revenue = sum(analysis['business_metrics']['total_lease_value'] for analysis in analyses)
    avg_risk_score = sum(analysis['risk_assessment']['risk_score'] for analysis in analyses) / total_properties
    
    risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    for analysis in analyses:
        risk_level = analysis['risk_assessment']['risk_level']
        risk_distribution[risk_level] += 1
    
    compliance_issues = sum(len(analysis['compliance_report']['violations']) for analysis in analyses)
    
    return {
        'overview': {
            'total_properties': total_properties,
            'total_annual_revenue': total_revenue,
            'avg_risk_score': avg_risk_score,
            'compliance_issues': compliance_issues
        },
        'risk_distribution': risk_distribution,
        'top_opportunities': _identify_top_opportunities(analyses),
        'urgent_actions': _identify_urgent_actions(analyses),
        'performance_metrics': _calculate_performance_metrics(analyses)
    }

def _identify_top_opportunities(analyses: List[Dict]) -> List[Dict]:
    """Identify top revenue opportunities across portfolio"""
    all_opportunities = []
    
    for i, analysis in enumerate(analyses):
        for opp in analysis.get('revenue_opportunities', []):
            opp['property_index'] = i
            all_opportunities.append(opp)
    
    # Sort by annual impact
    return sorted(all_opportunities, key=lambda x: x.get('annual_impact', 0), reverse=True)[:5]

def _identify_urgent_actions(analyses: List[Dict]) -> List[Dict]:
    """Identify urgent actions needed across portfolio"""
    urgent_actions = []
    
    for i, analysis in enumerate(analyses):
        risk_level = analysis['risk_assessment']['risk_level']
        if risk_level in ['high', 'critical']:
            urgent_actions.append({
                'property_index': i,
                'action': 'Risk mitigation required',
                'risk_level': risk_level,
                'priority': 'immediate'
            })
        
        compliance_score = analysis['compliance_report']['compliance_score']
        if compliance_score < 70:
            urgent_actions.append({
                'property_index': i,
                'action': 'Compliance review required',
                'compliance_score': compliance_score,
                'priority': 'high'
            })
    
    return urgent_actions

def _calculate_performance_metrics(analyses: List[Dict]) -> Dict:
    """Calculate portfolio performance metrics"""
    if not analyses:
        return {}
    
    rent_values = [analysis['business_metrics']['monthly_rent'] for analysis in analyses]
    risk_scores = [analysis['risk_assessment']['risk_score'] for analysis in analyses]
    
    return {
        'avg_monthly_rent': sum(rent_values) / len(rent_values),
        'rent_range': {'min': min(rent_values), 'max': max(rent_values)},
        'avg_risk_score': sum(risk_scores) / len(risk_scores),
        'high_risk_properties': sum(1 for score in risk_scores if score > 70),
        'portfolio_efficiency': 100 - (sum(risk_scores) / len(risk_scores))
    }

def _generate_market_intelligence(business_metrics: Dict, market_analysis: Dict) -> Dict:
    """Generate market intelligence"""
    return {
        'market_position': market_analysis.get('rent_vs_market', 'unknown'),
        'pricing_efficiency': market_analysis.get('cost_efficiency_score', 0),
        'competitive_advantage': _assess_competitive_advantage(business_metrics),
        'market_share_potential': _calculate_market_share_potential(business_metrics),
        'expansion_opportunities': _identify_expansion_opportunities(market_analysis)
    }

def _assess_competitive_position(business_metrics: Dict) -> str:
    """Assess competitive position"""
    rent = business_metrics.get('monthly_rent', 0)
    
    if rent >= 2800:
        return 'premium'
    elif rent >= 2200:
        return 'competitive'
    else:
        return 'value'

def _generate_pricing_recommendations(market_analysis: Dict) -> List[str]:
    """Generate pricing recommendations"""
    recommendations = []
    
    if market_analysis.get('rent_vs_market') == 'below_market':
        recommendations.append("Consider rent increase to market rate")
    
    if market_analysis.get('cost_efficiency_score', 0) < 70:
        recommendations.append("Review fee structure for optimization")
    
    return recommendations

def _analyze_market_trends(business_metrics: Dict) -> Dict:
    """Analyze market trends"""
    # Simulated market trend analysis
    return {
        'rent_growth_trend': '3.2% annually',
        'demand_level': 'high',
        'supply_constraint': 'moderate',
        'forecast': 'continued growth expected'
    }

def _assess_competitive_advantage(business_metrics: Dict) -> List[str]:
    """Assess competitive advantages"""
    advantages = []
    
    if business_metrics.get('pet_fees', 0) < 25:
        advantages.append("Pet-friendly pricing")
    
    if business_metrics.get('security_deposit', 0) < business_metrics.get('monthly_rent', 0) * 1.5:
        advantages.append("Reasonable security deposit")
    
    return advantages

def _calculate_market_share_potential(business_metrics: Dict) -> str:
    """Calculate market share potential"""
    # Simplified market share calculation
    rent = business_metrics.get('monthly_rent', 0)
    
    if rent >= 2500:
        return 'high_potential'
    elif rent >= 2000:
        return 'moderate_potential'
    else:
        return 'limited_potential'

def _identify_expansion_opportunities(market_analysis: Dict) -> List[str]:
    """Identify expansion opportunities"""
    opportunities = []
    
    if market_analysis.get('rent_vs_market') == 'below_market':
        opportunities.append("Rent optimization potential")
    
    if market_analysis.get('cost_efficiency_score', 0) < 80:
        opportunities.append("Operational efficiency improvements")
    
    return opportunities

def _identify_churn_risk_factors(risk_assessment: Dict) -> List[str]:
    """Identify tenant churn risk factors"""
    risk_factors = []
    
    if risk_assessment['risk_score'] > 70:
        risk_factors.append("High lease complexity")
    
    if len(risk_assessment['red_flags']) > 3:
        risk_factors.append("Multiple tenant-unfavorable terms")
    
    return risk_factors

def _generate_retention_strategies(portfolio_insights: Dict) -> List[Dict]:
    """Generate tenant retention strategies"""
    strategies = []
    
    retention_prob = portfolio_insights.get('retention_probability', 0.5)
    
    if retention_prob < 0.7:
        strategies.append({
            'strategy': 'Proactive engagement program',
            'timeline': '90 days before lease expiration',
            'expected_improvement': '15-20%'
        })
    
    if retention_prob < 0.6:
        strategies.append({
            'strategy': 'Incentive program',
            'timeline': '60 days before lease expiration',
            'expected_improvement': '10-15%'
        })
    
    return strategies

def _create_intervention_timeline(portfolio_insights: Dict) -> List[Dict]:
    """Create intervention timeline"""
    timeline = [
        {
            'timeline': '6 months before expiration',
            'action': 'Satisfaction survey',
            'purpose': 'Identify potential issues'
        },
        {
            'timeline': '90 days before expiration',
            'action': 'Renewal conversation',
            'purpose': 'Gauge renewal interest'
        },
        {
            'timeline': '60 days before expiration',
            'action': 'Formal renewal offer',
            'purpose': 'Present competitive terms'
        }
    ]
    
    return timeline

def _calculate_retention_financial_impact(portfolio_insights: Dict) -> Dict:
    """Calculate financial impact of retention"""
    # Simplified calculation
    retention_prob = portfolio_insights.get('retention_probability', 0.5)
    
    return {
        'cost_of_turnover': 5000,  # Estimated
        'revenue_at_risk': 28000,  # Annual rent
        'retention_value': 33000,  # Total value of retention
        'probability_weighted_impact': 33000 * retention_prob
    }

def _generate_retention_actions(retention_analysis: Dict) -> List[str]:
    """Generate recommended retention actions"""
    actions = []
    
    if retention_analysis['retention_probability'] < 0.6:
        actions.append("Implement immediate retention program")
        actions.append("Address identified risk factors")
    
    if len(retention_analysis['churn_risk_factors']) > 2:
        actions.append("Conduct detailed satisfaction assessment")
    
    return actions


# Example usage function for integration
def setup_business_intelligence(app: Flask):
    """Setup business intelligence routes in existing Flask app"""
    register_business_intelligence_routes(app)
    
    # Add any additional configuration
    app.config['BUSINESS_INTELLIGENCE_ENABLED'] = True
    app.config['BI_CACHE_TIMEOUT'] = 3600  # 1 hour cache
    
    return app