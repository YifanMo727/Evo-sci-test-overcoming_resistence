"""
Simulation Framework for AI Therapists Handling Non-Cooperative Clients

This module provides a modular framework for:
- Defining client resistance archetypes
- Implementing MI-consistent response strategies  
- Running simulated conversations
- Evaluating AI responses against resistance behaviors

Based on research from:
- Woebot/Wysa clinical trials (PMIDs: 41367963, 37831490, 37332481)
- Motivational Interviewing (Miller & Rollnick)
- Therapeutic Alliance with AI (PMIDs: 41591426, 39919295)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import random
import os
import re

# Optional LLM import - gracefull fallback if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# =============================================================================
# CLIENT RESISTANCE ARCHETYPES
# =============================================================================

class ResistanceArchetype(Enum):
    """Six distinct non-cooperative client archetypes based on clinical literature."""
    DEFENSIVE = "defensive"       # Denies problems, deflects blame
    AVOIDANT = "avoidant"         # Changes topics, silent responses
    HOSTILE = "hostile"           # Aggressive, sarcastic, confrontational
    SKEPTICAL = "skeptical"       # Questions AI capabilities
    WITHDRAWN = "withdrawn"       # Minimal engagement, one-word answers
    MANIPULATIVE = "manipulative" # Changes narrative, seeks harmful validation


class ResponseStrategy(Enum):
    """MI-consistent response strategies for handling resistance."""
    VALIDATION_FIRST = "validation_first"       # Acknowledge resistance before content
    AUTONOMY_RESTORATION = "autonomy_restoration"  # Offer choices, restore control
    ROLLING_WITH_RESISTANCE = "rolling"         # Join the resistance, don't confront
    ELICIT_SELF_MOTIVATION = "elicit"           # Draw out client's own reasons
    META_CONVERSATIONAL = "meta"                # Address interaction pattern directly
    STANDARD = "standard"                       # Baseline: generic empathetic response


@dataclass
class ClientArchetype:
    """Defines a client resistance archetype with behavior patterns."""
    archetype: ResistanceArchetype
    description: str
    trigger_phrases: list[str] = field(default_factory=list)
    
    # Example dialogue patterns for this archetype
    resistance_statements: list[str] = field(default_factory=list)
    
    # Preferred strategy for de-escalation (from MI literature)
    recommended_strategy: ResponseStrategy = ResponseStrategy.STANDARD
    
    # Resistance intensity scale: 0.0 (mild) to 1.0 (severe)
    typical_intensity: float = 0.5


# Archetype definitions with clinical grounding
ARCHETYPE_DEFINITIONS = {
    ResistanceArchetype.DEFENSIVE: ClientArchetype(
        archetype=ResistanceArchetype.DEFENSIVE,
        description="Client denies problems or deflects blame. Minimizes concerns.",
        trigger_phrases=["Nothing's wrong", "You're overreacting", "I don't have a problem"],
        resistance_statements=[
            "I don't know why you're making this a big deal",
            "Nothing's wrong with me",
            "You're reading too much into this"
        ],
        recommended_strategy=ResponseStrategy.ROLLING_WITH_RESISTANCE,
        typical_intensity=0.6
    ),
    ResistanceArchetype.AVOIDANT: ClientArchetype(
        archetype=ResistanceArchetype.AVOIDANT,
        description="Client changes topics or provides minimal responses.",
        trigger_phrases=["I don't want to talk about it", "Can we talk about something else"],
        resistance_statements=[
            "I don't want to talk about it",
            "Can we just move on?",
            "*silence*",
            "Let's skip this part"
        ],
        recommended_strategy=ResponseStrategy.VALIDATION_FIRST,
        typical_intensity=0.5
    ),
    ResistanceArchetype.HOSTILE: ClientArchetype(
        archetype=ResistanceArchetype.HOSTILE,
        description="Client is aggressive, sarcastic, or confrontational.",
        trigger_phrases=["You can't help me", "This is pointless", "You're useless"],
        resistance_statements=[
            "This is pointless",
            "You're just a bot, you can't help me",
            "I've heard enough of this"
        ],
        recommended_strategy=ResponseStrategy.META_CONVERSATIONAL,
        typical_intensity=0.8
    ),
    ResistanceArchetype.SKEPTICAL: ClientArchetype(
        archetype=ResistanceArchetype.SKEPTICAL,
        description="Client questions AI capabilities or doubts usefulness.",
        trigger_phrases=["How can you understand", "You're just a bot", "This won't work"],
        resistance_statements=[
            "You're just a bot, how can you understand me?",
            "This is just a programmed response, right?",
            "Why should I talk to an AI about my problems?"
        ],
        recommended_strategy=ResponseStrategy.AUTONOMY_RESTORATION,
        typical_intensity=0.4
    ),
    ResistanceArchetype.WITHDRAWN: ClientArchetype(
        archetype=ResistanceArchetype.WITHDRAWN,
        description="Client provides minimal engagement, one-word answers.",
        trigger_phrases=["Fine", "Whatever", "I don't know"],
        resistance_statements=[
            "Fine",
            "Whatever",
            "I don't know",
            "*no response*"
        ],
        recommended_strategy=ResponseStrategy.ELICIT_SELF_MOTIVATION,
        typical_intensity=0.5
    ),
    ResistanceArchetype.MANIPULATIVE: ClientArchetype(
        archetype=ResistanceArchetype.MANIPULATIVE,
        description="Client seeks validation for harmful behavior, changes narrative.",
        trigger_phrases=["It's not my fault", "They made me", "I had to"],
        resistance_statements=[
            "You don't understand what I was going through",
            "They pushed me to it",
            "It's not like I had a choice"
        ],
        recommended_strategy=ResponseStrategy.ROLLING_WITH_RESISTANCE,
        typical_intensity=0.7
    )
}


# =============================================================================
# RESPONSE STRATEGY IMPLEMENTATIONS
# =============================================================================

@dataclass
class StrategyResponse:
    """A MI-consistent response implementing a specific strategy."""
    strategy: ResponseStrategy
    response_text: str
    targets_resistance: bool  # Does this address the resistance directly?
    offers_autonomy: bool     # Does this offer client choice/control?
    maintains_alliance: bool # Does this maintain therapeutic relationship?


def get_strategy_response(
    archetype: ResistanceArchetype,
    client_statement: str,
    context: dict
) -> StrategyResponse:
    """
    Generate MI-consistent response for a given resistance archetype.
    
    Args:
        archetype: The type of resistance being displayed
        client_statement: What the client said
        context: Conversation context (client history, session info)
    
    Returns:
        StrategyResponse with appropriate MI-consistent response
    """
    
    # Try LLM first if available
    llm_response = generate_llm_response(client_statement, archetype, context)
    if llm_response is not None:
        return llm_response
    
    # Fall back to template responses if LLM unavailable
    archetype_def = ARCHETYPE_DEFINITIONS[archetype]
    strategy = archetype_def.recommended_strategy
    
    if strategy == ResponseStrategy.VALIDATION_FIRST:
        response_text = _validation_first_response(client_statement, context)
        offers_autonomy = False
        targets_resistance = True
        
    elif strategy == ResponseStrategy.AUTONOMY_RESTORATION:
        response_text = _autonomy_restoration_response(client_statement, context)
        offers_autonomy = True
        targets_resistance = False
        
    elif strategy == ResponseStrategy.ROLLING_WITH_RESISTANCE:
        response_text = _rolling_with_resistance_response(client_statement, context)
        offers_autonomy = False
        targets_resistance = True
        
    elif strategy == ResponseStrategy.ELICIT_SELF_MOTIVATION:
        response_text = _elicit_self_motivation_response(client_statement, context)
        offers_autonomy = True
        targets_resistance = False
        
    elif strategy == ResponseStrategy.META_CONVERSATIONAL:
        response_text = _meta_conversational_response(client_statement, context)
        offers_autonomy = True
        targets_resistance = True
        
    else:  # STANDARD
        response_text = _standard_response(client_statement, context)
        offers_autonomy = False
        targets_resistance = False
    
    return StrategyResponse(
        strategy=strategy,
        response_text=response_text,
        targets_resistance=targets_resistance,
        offers_autonomy=offers_autonomy,
        maintains_alliance=True  # All MI responses should maintain alliance
    )


def _validation_first_response(client_stmt: str, context: dict) -> str:
    """Acknowledge resistance before addressing content (validation-first)."""
    return (
        "It sounds like this feels uncomfortable—I hear that. "
        "You know best what you're ready to share. "
        "We can talk about this whenever feels right."
    )


def _autonomy_restoration_response(client_stmt: str, context: dict) -> str:
    """Restore client sense of control (autonomy restoration)."""
    return (
        "You're the expert on your own life and what feels right for you. "
        "I'm here to support what matters to you—not to push in any direction. "
        "What would be most helpful right now?"
    )


def _rolling_with_resistance_response(client_stmt: str, context: dict) -> str:
    """Join the resistance rather than confronting (rolling with resistance)."""
    return (
        "You're right—this is hard. It makes sense to want to pull back. "
        "Can we talk about what's making it hard? "
        "Sometimes getting clearer on that helps."
    )


def _elicit_self_motivation_response(client_stmt: str, context: dict) -> str:
    """Draw out client's own reasons for change (evocation)."""
    return (
        "I hear you. Let me ask something—if things were a bit different than they "
        "are now, what would that look like for you? What matters to you about that?"
    )


def _meta_conversational_response(client_stmt: str, context: dict) -> str:
    """Address the interaction pattern directly (meta-conversational)."""
    return (
        "It seems like this conversation feels different than expected. "
        "I want to make this work for you—what would feel more useful?"
    )


def _standard_response(client_stmt: str, context: dict) -> str:
    """Baseline: generic empathetic response."""
    return "I understand. Thank you for sharing that. Can you tell me more?"


# =============================================================================
# LLM RESPONSE GENERATION
# =============================================================================

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # "openai" or "anthropic"
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4")

# System prompt for MI-consistent therapist responses
THERAPIST_SYSTEM_PROMPT = """You are an AI therapist assistant using Motivational Interviewing (MI) techniques.
Your goal is to respond to client statements that show resistance to discussing certain topics.

MI principles to follow:
1. Express empathy through reflective listening
2. Develop discrepancy between client goals and current behavior  
3. Roll with resistance - don't confront directly
4. Support self-efficacy and autonomy

When responding to resistant clients:
- Acknowledge their feelings before probing
- Offer choice and autonomy
- Don't push too hard on sensitive topics
- Use open-ended questions
- Avoid judgmental or confrontational language

Respond with a therapeutic response that:
1. Validates the client's emotional state
2. Offers autonomy/choice about what to discuss
3. Maintains the therapeutic alliance
4. Gently explores the topic if appropriate

Return your response as a JSON object with these fields:
- response_text: the therapist's response
- targets_resistance: whether this addresses the resistance directly (true/false)
- offers_autonomy: whether this offers client choice/control (true/false)
- maintains_alliance: whether this maintains therapeutic relationship (true/false)"""


def generate_llm_response(
    client_statement: str,
    archetype: ResistanceArchetype,
    context: dict,
    provider: str = LLM_PROVIDER,
    model: str = LLM_MODEL
) -> Optional[StrategyResponse]:
    """
    Generate an LLM-based therapist response using OpenAI or Anthropic.
    
    Args:
        client_statement: What the client said
        archetype: The resistance archetype being displayed
        context: Conversation context
        provider: "openai" or "anthropic"
        model: Model name to use
    
    Returns:
        StrategyResponse with generated response and metadata, or None if failed
    """
    archetype_info = ARCHETYPE_DEFINITIONS[archetype]
    
    user_prompt = f"""Client archetype: {archetype.value}
Description: {archetype_info.description}
Recommended strategy: {archetype_info.recommended_strategy.value}

Client statement: "{client_statement}"

Context: {json.dumps(context)}

Generate a therapeutic response following MI principles.""" 
    
    try:
        if provider == "openai" and OPENAI_AVAILABLE:
            return _generate_openai_response(client_statement, archetype, context, model)
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            return _generate_anthropic_response(client_statement, archetype, context, model)
        else:
            print(f"Warning: LLM provider '{provider}' not available. Using template response.")
            return None
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return None


def _generate_openai_response(
    client_statement: str,
    archetype: ResistanceArchetype,
    context: dict,
    model: str
) -> Optional[StrategyResponse]:
    """Generate response using OpenAI API."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    archetype_info = ARCHETYPE_DEFINITIONS[archetype]
    user_prompt = f"""Client archetype: {archetype.value}
Description: {archetype_info.description}
Recommended strategy: {archetype_info.recommended_strategy.value}

Client statement: "{client_statement}"

Context: {json.dumps(context)}

Generate a therapeutic response following MI principles. Return JSON with:
- response_text: the therapist's response
- targets_resistance: true/false
- offers_autonomy: true/false
- maintains_alliance: true/false"""
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": THERAPIST_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return _parse_llm_json_response(
        response.choices[0].message.content,
        archetype_info.recommended_strategy
    )


def _generate_anthropic_response(
    client_statement: str,
    archetype: ResistanceArchetype,
    context: dict,
    model: str
) -> Optional[StrategyResponse]:
    """Generate response using Anthropic API."""
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    archetype_info = ARCHETYPE_DEFINITIONS[archetype]
    user_prompt = f"""Client archetype: {archetype.value}
Description: {archetype_info.description}
Recommended strategy: {archetype_info.recommended_strategy.value}

Client statement: "{client_statement}"

Context: {json.dumps(context)}

Generate a therapeutic response following MI principles. Return JSON with:
- response_text: the therapist's response
- targets_resistance: true/false
- offers_autonomy: true/false
- maintains_alliance: true/false"""
    
    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=THERAPIST_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    return _parse_llm_json_response(
        response.content[0].text,
        archetype_info.recommended_strategy
    )


def _parse_llm_json_response(response_text: str, strategy: ResponseStrategy) -> StrategyResponse:
    """Parse LLM JSON response into StrategyResponse object."""
    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        # If no JSON found, use entire response as text
        return StrategyResponse(
            strategy=strategy,
            response_text=response_text.strip(),
            targets_resistance=True,
            offers_autonomy=True,
            maintains_alliance=True
        )
    
    try:
        data = json.loads(json_match.group())
        return StrategyResponse(
            strategy=strategy,
            response_text=data.get("response_text", response_text),
            targets_resistance=str(data.get("targets_resistance", "true")).lower() == "true",
            offers_autonomy=str(data.get("offers_autonomy", "true")).lower() == "true",
            maintains_alliance=str(data.get("maintains_alliance", "true")).lower() == "true"
        )
    except json.JSONDecodeError:
        # If JSON parsing fails, return raw response
        return StrategyResponse(
            strategy=strategy,
            response_text=response_text.strip(),
            targets_resistance=True,
            offers_autonomy=True,
            maintains_alliance=True
        )


# =============================================================================
# CONVERSATION SIMULATION
# =============================================================================

@dataclass
class ConversationTurn:
    """Single turn in a therapy conversation."""
    turn_id: int
    speaker: str  # "client" or "therapist"
    text: str
    resistance_type: Optional[ResistanceArchetype] = None
    resistance_level: Optional[float] = None
    strategy_used: Optional[ResponseStrategy] = None


@dataclass
class SimulationScenario:
    """A complete scenario for testing AI therapist responses."""
    scenario_id: str
    context: dict  # Client background, presenting issue, etc.
    initial_prompt: str
    trigger_event: str
    expected_archetype: ResistanceArchetype
    expected_resistance_level: float
    ground_truth_strategy: ResponseStrategy
    turns: list[ConversationTurn] = field(default_factory=list)


def generate_scenario(archetype: ResistanceArchetype) -> SimulationScenario:
    """Generate a test scenario for a given resistance archetype."""
    import uuid
    
    archetype_def = ARCHETYPE_DEFINITIONS[archetype]
    
    # Select a resistance statement
    resistance_stmt = random.choice(archetype_def.resistance_statements)
    
    scenario_contexts = {
        ResistanceArchetype.DEFENSIVE: {
            "client_age": 28,
            "presenting_issue": "work_stress",
            "session_number": 2,
            "recent_event": "recent_layoff_at_work"
        },
        ResistanceArchetype.AVOIDANT: {
            "client_age": 45,
            "presenting_issue": "grief",
            "session_number": 3,
            "recent_event": "loss_3_months_ago"
        },
        ResistanceArchetype.HOSTILE: {
            "client_age": 35,
            "presenting_issue": "relationship_difficulties",
            "session_number": 1
        },
        ResistanceArchetype.SKEPTICAL: {
            "client_age": 32,
            "presenting_issue": "anxiety",
            "session_number": 1
        },
        ResistanceArchetype.WITHDRAWN: {
            "client_age": 24,
            "presenting_issue": "depression",
            "session_number": 2
        },
        ResistanceArchetype.MANIPULATIVE: {
            "client_age": 41,
            "presenting_issue": "anger_management",
            "session_number": 4
        }
    }
    
    return SimulationScenario(
        scenario_id=str(uuid.uuid4())[:8],
        context=scenario_contexts.get(archetype, {}),
        initial_prompt=f"Client presents with {archetype_def.description}",
        trigger_event=f"Therapist asks about {archetype} trigger topic",
        expected_archetype=archetype,
        expected_resistance_level=archetype_def.typical_intensity,
        ground_truth_strategy=archetype_def.recommended_strategy,
        turns=[
            ConversationTurn(
                turn_id=1,
                speaker="therapist",
                text="[Therapist asks about trigger topic]"
            ),
            ConversationTurn(
                turn_id=2,
                speaker="client",
                text=resistance_stmt,
                resistance_type=archetype,
                resistance_level=archetype_def.typical_intensity
            )
        ]
    )


# =============================================================================
# EVALUATION METRICS
# =============================================================================

@dataclass
class EvaluationMetrics:
    """Metrics for evaluating AI therapist responses to resistance."""
    
    # Primary metrics
    resistance_recognition_accuracy: float = 0.0
    de_escalation_success_rate: float = 0.0
    therapeutic_alliance_maintained: float = 0.0
    strategy_appropriateness: float = 0.0
    
    # Secondary metrics
    response_relevance: float = 0.0
    empathy_calibration: float = 0.0
    autonomy_support_score: float = 0.0
    conversation_completion_rate: float = 0.0


def evaluate_response(
    generated_response: str,
    archetype: ResistanceArchetype,
    expected_strategy: ResponseStrategy,
    client_statement: str
) -> EvaluationMetrics:
    """
    Evaluate an AI response against resistance.
    
    This is a simplified heuristic-based evaluation.
    In practice, use human annotation or LLM-as-judge for full evaluation.
    """
    
    metrics = EvaluationMetrics()
    
    # Strategy appropriateness: does response match expected MI strategy?
    # This is a simplified check - in practice, use expert annotation
    strategy_keywords = {
        ResponseStrategy.VALIDATION_FIRST: ["understand", "hear", "makes sense", "comfortable"],
        ResponseStrategy.AUTONOMY_RESTORATION: ["you choose", "you decide", "expert", "your life"],
        ResponseStrategy.ROLLING_WITH_RESISTANCE: ["right", "hard", "makes sense to"],
        ResponseStrategy.ELICIT_SELF_MOTIVATION: ["what would", "if things were", "matters to you"],
        ResponseStrategy.META_CONVERSATIONAL: ["conversation feels", "different", "work for you"],
    }
    
    # Simple keyword matching for strategy detection
    response_lower = generated_response.lower()
    for strategy, keywords in strategy_keywords.items():
        if any(kw in response_lower for kw in keywords):
            if strategy == expected_strategy:
                metrics.strategy_appropriateness = 1.0
                break
    else:
        metrics.strategy_appropriateness = 0.3  # Baseline for standard response
    
    # Autonomy support: does response offer choice?
    autonomy_markers = ["you choose", "you decide", "what would", "what matters to you", 
                       "what feels right", "your expertise", "expert on"]
    metrics.autonomy_support_score = 1.0 if any(m in response_lower for m in autonomy_markers) else 0.2
    
    # Empathy calibration: does response acknowledge emotion?
    empathy_markers = ["understand", "hear", "makes sense", "sounds like", "feel"]
    metrics.empathy_calibration = 1.0 if any(m in response_lower for m in empathy_markers) else 0.3
    
    # Response relevance: is response related to what client said?
    metrics.response_relevance = 0.7  # Simplified - in practice use semantic similarity
    
    # Placeholder for other metrics (require more complex annotation)
    metrics.resistance_recognition_accuracy = 0.5
    metrics.de_escalation_success_rate = 0.5
    metrics.therapeutic_alliance_maintained = 0.6
    metrics.conversation_completion_rate = 0.7
    
    return metrics


def compute_average_metrics(all_metrics: list[EvaluationMetrics]) -> dict:
    """Compute average metrics across multiple evaluations."""
    if not all_metrics:
        return {}
    
    return {
        "resistance_recognition_accuracy": sum(m.resistance_recognition_accuracy for m in all_metrics) / len(all_metrics),
        "de_escalation_success_rate": sum(m.de_escalation_success_rate for m in all_metrics) / len(all_metrics),
        "therapeutic_alliance_maintained": sum(m.therapeutic_alliance_maintained for m in all_metrics) / len(all_metrics),
        "strategy_appropriateness": sum(m.strategy_appropriateness for m in all_metrics) / len(all_metrics),
        "response_relevance": sum(m.response_relevance for m in all_metrics) / len(all_metrics),
        "empathy_calibration": sum(m.empathy_calibration for m in all_metrics) / len(all_metrics),
        "autonomy_support_score": sum(m.autonomy_support_score for m in all_metrics) / len(all_metrics),
        "conversation_completion_rate": sum(m.conversation_completion_rate for m in all_metrics) / len(all_metrics),
    }


# =============================================================================
# EXAMPLE USAGE & BENCHMARKING
# =============================================================================

def run_benchmark_simulation():
    """Run a complete benchmark simulation across all archetypes."""
    
    results = {}
    
    print("=" * 60)
    print("AI THERAPIST RESISTANCE BENCHMARK SIMULATION")
    print("=" * 60)
    
    for archetype in ResistanceArchetype:
        print(f"\n--- Testing {archetype.value.upper()} Client ---")
        
        # Generate scenario
        scenario = generate_scenario(archetype)
        
        # Get client statement
        client_stmt = scenario.turns[1].text
        print(f"Client says: {client_stmt}")
        
        # Get MI-consistent response using ground truth strategy
        mi_response_obj = get_strategy_response(
            archetype, 
            client_stmt, 
            scenario.context
        )
        response_text = mi_response_obj.response_text
        
        print(f"AI Therapist: {response_text[:100]}...")
        print(f"Strategy used: {mi_response_obj.strategy.value}")
        
        # Evaluate
        metrics = evaluate_response(
            response_text,
            archetype,
            scenario.ground_truth_strategy,
            client_stmt
        )
        
        results[archetype.value] = {
            "response": response_text,
            "response_strategy": mi_response_obj.strategy.value,
            "metrics": {
                "strategy_appropriateness": metrics.strategy_appropriateness,
                "autonomy_support": metrics.autonomy_support_score,
                "empathy_calibration": metrics.empathy_calibration
            }
        }
        
        print(f"  Strategy Appropriateness: {metrics.strategy_appropriateness:.2f}")
        print(f"  Autonomy Support: {metrics.autonomy_support_score:.2f}")
    
    # Compute averages
    print("\n" + "=" * 60)
    print("AVERAGE METRICS ACROSS ALL ARCHETYPES")
    print("=" * 60)
    
    # This would be more comprehensive with actual generated responses
    print("\nBenchmark ready for LLM evaluation.")
    print("Next: Integrate with GPT-4/Claude API for response generation.")
    
    return results


if __name__ == "__main__":
    results = run_benchmark_simulation()
