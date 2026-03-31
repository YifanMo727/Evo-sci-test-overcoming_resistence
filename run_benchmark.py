#!/usr/bin/env python3
"""
Benchmark Runner for AI Therapist Resistance Simulation

Evaluates the LLM-based therapist response generator against 50 scenarios
across 6 resistance archetypes with ground truth strategies.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Add the artifacts directory to path
ARTIFACTS_DIR = '/Users/yifanmo/Documents/Reading_group/EvoSci-test/artifacts'
sys.path.insert(0, ARTIFACTS_DIR)

from resistance_simulation import (
    get_strategy_response,
    ResistanceArchetype,
    ResponseStrategy,
    StrategyResponse,
    LLM_PROVIDER,
    LLM_MODEL,
    OPENAI_AVAILABLE,
    ANTHROPIC_AVAILABLE
)


def load_benchmark_dataset(path: str = None) -> List[Dict]:
    """Load benchmark scenarios from JSON."""
    if path is None:
        path = os.path.join(ARTIFACTS_DIR, "benchmark_dataset.json")
    with open(path, 'r') as f:
        data = json.load(f)
    return data['scenarios']


def strategy_match(generated: ResponseStrategy, ground_truth: str) -> bool:
    """Check if generated strategy matches ground truth (with fuzzy matching)."""
    # Map ground truth string to ResponseStrategy
    strategy_map = {
        "rolling_with_resistance": ResponseStrategy.ROLLING_WITH_RESISTANCE,
        "validation_first": ResponseStrategy.VALIDATION_FIRST,
        "autonomy_restoration": ResponseStrategy.AUTONOMY_RESTORATION,
        "elicit_self_motivation": ResponseStrategy.ELICIT_SELF_MOTIVATION,
        "meta_conversational_repair": ResponseStrategy.META_CONVERSATIONAL,
    }
    
    expected_strategy = strategy_map.get(ground_truth)
    if expected_strategy is None:
        return False
    
    return generated == expected_strategy


def evaluate_response(
    scenario: Dict,
    response: StrategyResponse,
    provider_used: str,
    llm_generated: bool
) -> Dict[str, Any]:
    """Evaluate a single response against ground truth."""
    
    ground_truth = scenario['ground_truth_strategy']
    archetype = scenario['archetype']
    
    # Check strategy match
    strategy_correct = strategy_match(response.strategy, ground_truth)
    
    # Calculate quality metrics
    quality_score = 0
    if response.maintains_alliance:
        quality_score += 1
    if response.targets_resistance and archetype not in ['withdrawn', 'avoidant']:
        quality_score += 1
    if response.offers_autonomy and archetype in ['skeptical', 'defensive']:
        quality_score += 1
    
    return {
        'scenario_id': scenario['id'],
        'archetype': archetype,
        'ground_truth_strategy': ground_truth,
        'generated_strategy': response.strategy.value,
        'strategy_match': strategy_correct,
        'maintains_alliance': response.maintains_alliance,
        'targets_resistance': response.targets_resistance,
        'offers_autonomy': response.offers_autonomy,
        'quality_score': quality_score,
        'response_preview': response.response_text[:100] + "..." if len(response.response_text) > 100 else response.response_text,
        'provider': provider_used,
        'llm_generated': llm_generated
    }


def run_benchmark(scenarios: List[Dict]) -> Dict[str, Any]:
    """Run benchmark on all scenarios."""
    
    results = []
    llm_call_count = 0
    fallback_count = 0
    
    print(f"\n{'='*60}")
    print(f"Running benchmark on {len(scenarios)} scenarios")
    print(f"LLM Provider: {LLM_PROVIDER}")
    print(f"LLM Model: {LLM_MODEL}")
    print(f"OpenAI Available: {OPENAI_AVAILABLE}")
    print(f"Anthropic Available: {ANTHROPIC_AVAILABLE}")
    print(f"{'='*60}\n")
    
    for i, scenario in enumerate(scenarios, 1):
        archetype = ResistanceArchetype(scenario['archetype'])
        client_statement = scenario['client_statement']
        context = scenario['context']
        
        # Track if we'll use LLM or fallback
        provider_used = "N/A"
        llm_generated = False
        
        if (LLM_PROVIDER == "openai" and OPENAI_AVAILABLE) or \
           (LLM_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE):
            provider_used = f"{LLM_PROVIDER}-{LLM_MODEL}"
            llm_generated = True
            llm_call_count += 1
        else:
            provider_used = "template"
            fallback_count += 1
        
        # Generate response
        response = get_strategy_response(archetype, client_statement, context)
        
        # Evaluate
        eval_result = evaluate_response(scenario, response, provider_used, llm_generated)
        results.append(eval_result)
        
        # Print progress every 10 scenarios
        if i % 10 == 0 or i == 1:
            print(f"[{i:2d}/{len(scenarios)}] {scenario['id']}: "
                  f"{archetype.value:12s} → {response.strategy.value:25s} "
                  f"(match: {eval_result['strategy_match']})")
    
    return {
        'results': results,
        'llm_call_count': llm_call_count,
        'fallback_count': fallback_count
    }


def compute_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Compute aggregate metrics from benchmark results."""
    
    total = len(results)
    strategy_matches = sum(1 for r in results if r['strategy_match'])
    alliance_maintained = sum(1 for r in results if r['maintains_alliance'])
    resistance_targeted = sum(1 for r in results if r['targets_resistance'])
    autonomy_offered = sum(1 for r in results if r['offers_autonomy'])
    
    # Per-archetype breakdown
    archetype_stats = defaultdict(lambda: {
        'count': 0,
        'matches': 0,
        'alliance': 0,
        'resistance_targeted': 0,
        'autonomy': 0,
        'quality_scores': []
    })
    
    for r in results:
        arch = r['archetype']
        archetype_stats[arch]['count'] += 1
        if r['strategy_match']:
            archetype_stats[arch]['matches'] += 1
        if r['maintains_alliance']:
            archetype_stats[arch]['alliance'] += 1
        if r['targets_resistance']:
            archetype_stats[arch]['resistance_targeted'] += 1
        if r['offers_autonomy']:
            archetype_stats[arch]['autonomy'] += 1
        archetype_stats[arch]['quality_scores'].append(r['quality_score'])
    
    # Calculate percentages per archetype
    for arch in archetype_stats:
        stats = archetype_stats[arch]
        stats['match_rate'] = stats['matches'] / stats['count'] * 100 if stats['count'] > 0 else 0
        stats['alliance_rate'] = stats['alliance'] / stats['count'] * 100 if stats['count'] > 0 else 0
        stats['avg_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0
    
    return {
        'total_scenarios': total,
        'overall_strategy_match_rate': strategy_matches / total * 100,
        'alliance_maintained_rate': alliance_maintained / total * 100,
        'resistance_targeted_rate': resistance_targeted / total * 100,
        'autonomy_offered_rate': autonomy_offered / total * 100,
        'archetype_stats': dict(archetype_stats),
        'llm_generated': results[0]['llm_generated'] if results else False,
        'provider': results[0]['provider'] if results else "N/A"
    }


def generate_report(metrics: Dict, output_path: str = None):
    """Generate detailed benchmark report."""
    if output_path is None:
        output_path = os.path.join(ARTIFACTS_DIR, "benchmark_report.json")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_scenarios': metrics['total_scenarios'],
            'llm_generated': metrics['llm_generated'],
            'provider': metrics['provider'],
            'strategy_match_rate': f"{metrics['overall_strategy_match_rate']:.1f}%",
            'alliance_maintained_rate': f"{metrics['alliance_maintained_rate']:.1f}%",
            'resistance_targeted_rate': f"{metrics['resistance_targeted_rate']:.1f}%",
            'autonomy_offered_rate': f"{metrics['autonomy_offered_rate']:.1f}%"
        },
        'per_archetype': {},
        'recommendations': []
    }
    
    # Per-archetype details
    for arch, stats in metrics['archetype_stats'].items():
        report['per_archetype'][arch] = {
            'scenarios': stats['count'],
            'strategy_match_rate': f"{stats['match_rate']:.1f}%",
            'alliance_maintained_rate': f"{stats['alliance_rate']:.1f}%",
            'avg_quality_score': f"{stats['avg_quality']:.2f}/3",
            'details': {
                'matches': stats['matches'],
                'alliance_maintained': stats['alliance'],
                'resistance_targeted': stats['resistance_targeted'],
                'autonomy_offered': stats['autonomy']
            }
        }
    
    # Generate recommendations
    if metrics['overall_strategy_match_rate'] < 70:
        report['recommendations'].append("Consider refining strategy selection logic for better ground truth alignment")
    if metrics['alliance_maintained_rate'] < 90:
        report['recommendations'].append("Review responses to ensure therapeutic alliance is maintained")
    if metrics['autonomy_offered_rate'] < 50:
        report['recommendations'].append("Increase autonomy offerings, especially for skeptical and defensive clients")
    
    # Find weakest archetype
    weak_arch = min(metrics['archetype_stats'].items(), key=lambda x: x[1]['match_rate'])
    if weak_arch[1]['match_rate'] < 60:
        report['recommendations'].append(f"Weakest performance on {weak_arch[0]} archetype - consider archetype-specific prompt tuning")
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def print_summary(metrics: Dict):
    """Print benchmark summary to console."""
    
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Scenarios: {metrics['total_scenarios']}")
    print(f"LLM Generated: {metrics['llm_generated']} ({metrics['provider']})")
    print()
    print("Overall Metrics:")
    print(f"  Strategy Match Rate:    {metrics['overall_strategy_match_rate']:.1f}%")
    print(f"  Alliance Maintained:    {metrics['alliance_maintained_rate']:.1f}%")
    print(f"  Resistance Targeted:   {metrics['resistance_targeted_rate']:.1f}%")
    print(f"  Autonomy Offered:       {metrics['autonomy_offered_rate']:.1f}%")
    print()
    print("Per-Archetype Performance:")
    print(f"  {'Archetype':<12} {'Match':<8} {'Alliance':<10} {'Quality':<8}")
    print(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*6}")
    
    for arch, stats in sorted(metrics['archetype_stats'].items()):
        print(f"  {arch:<12} {stats['match_rate']:>5.1f}%   {stats['alliance_rate']:>6.1f}%   {stats['avg_quality']:.2f}")
    
    print(f"{'='*60}\n")


def main():
    """Main entry point."""
    
    # Load benchmark dataset
    scenarios = load_benchmark_dataset()
    print(f"Loaded {len(scenarios)} benchmark scenarios")
    
    # Run benchmark
    benchmark_output = run_benchmark(scenarios)
    
    # Compute metrics
    metrics = compute_metrics(benchmark_output['results'])
    
    # Add provider info
    metrics['llm_call_count'] = benchmark_output['llm_call_count']
    metrics['fallback_count'] = benchmark_output['fallback_count']
    
    # Generate and save report
    report = generate_report(metrics)
    output_path = os.path.join(ARTIFACTS_DIR, "benchmark_report.json")
    print(f"Report saved to: {output_path}")
    
    # Print summary
    print_summary(metrics)
    
    # Print provider usage
    print(f"LLM calls: {metrics['llm_call_count']}, Fallbacks: {metrics['fallback_count']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())