# Simulation Framework for AI Therapists with Non-Cooperative Clients

## 1. Research Summary

**Key Finding**: A critical gap exists—no existing benchmarks specifically evaluate AI systems handling resistant or non-cooperative clients in mental health conversations. This framework addresses that gap.

### Relevant Literature
- **Woebot & Wysa**: Leading AI therapy platforms with RCT evidence, but neither specifically evaluates resistance handling
- **Therapeutic Alliance with AI**: Possible but more fragile than human interactions; autonomy support is critical
- **Motivational Interviewing (MI)**: The dominant evidence-based framework for handling resistance

---

## 2. Client Resistance Archetypes

We define **6 distinct non-cooperative client archetypes** based on clinical literature:

| Archetype | Behavior Pattern | Example Dialogue Triggers |
|-----------|------------------|---------------------------|
| **Defensive** | Denies problems, deflects blame | "Nothing's wrong," "You're overreacting" |
| **Avoidant** | Changes topics, silent responses | "I don't want to talk about it," 🦗 (silence) |
| **Hostile** | Aggressive, sarcastic, confrontational | "You can't help me," "This is pointless" |
| **Skeptical** | Questions AI capabilities, doubts usefulness | "You're just a bot," "How can you understand?" |
| **Withdrawn** | Minimal engagement, one-word answers | "Fine," "Whatever," 🦗 (silence) |
| **Manipulative** | Changes narrative, seeks validation for harmful behavior | Minimization, blame-shifting |

---

## 3. AI Therapist Response Strategies

Based on **Motivational Interviewing (MI)** principles, we propose **5 response strategy families**:

### Strategy 1: Validation-First Response
- **Principle**: Acknowledge resistance before addressing content
- **Implementation**: Reflect back the emotion without agreeing with denial
- **Example**: "It sounds like this feels uncomfortable—I hear that"

### Strategy 2: Autonomy Restoration
- **Principle**: Restore client sense of control
- **Implementation**: Offer choices, emphasize client expertise on their own life
- **Example**: "You're the expert on your own life—what feels right to you?"

### Strategy 3: Rolling with Resistance
- **Principle**: Don't confront or argue; join the resistance
- **Implementation**: Agree with truth in what client says, then gently pivot
- **Example**: "You're right that this is hard—let's talk about what's making it hard"

### Strategy 4: Elicit Self-Motivation
- **Principle**: Draw out client's own reasons for change
- **Implementation**: Ask open questions about goals, values, discrepancies
- **Example**: "What would life look like if things were a bit different?"

### Strategy 5: Meta-Conversational Repair
- **Principle**: Address the interaction pattern directly
- **Implementation**: Name what's happening in the conversation, invite collaboration
- **Example**: "It seems like this conversation feels different—want to talk about that?"

---

## 4. Simulation Scenario Design

Each scenario consists of:
1. **Initial context**: Client background, presenting issue
2. **Escalation trigger**: Event that activates resistance
3. **Expected resistance type**: Which archetype(s) manifest
4. **Ground truth response**: MI-consistent response(s)

### Example Scenario: Defensive Client

```
Context: 28-year-old discussing work stress, avoids emotional content
Trigger: AI asks about feelings about a layoff event
Response: "I don't know why you're making this a big deal"

Expected AI Response (Validation-First + Rolling):
"It makes sense you want to keep things practical—especially after what 
you've been through. Let's talk about what helps you get through the day."
```

### Scenario Matrix

| Scenario | Context | Trigger | Archetype |
|----------|---------|---------|-----------|
| 1 | Work stress, recent layoff | Ask about emotional response | Defensive |
| 2 | Grief, 3 months post-loss | Propose talking about loss | Avoidant |
| 3 | Relationship issues | Suggest communication exercise | Hostile |
| 4 | First session, general intake | Ask about mental health history | Skeptical |
| 5 | Substance use disclosure | Explore trigger patterns | Withdrawn |
| 6 | Anger management | Validate frustration level | Manipulative |

---

## 5. Evaluation Metrics

### Primary Metrics

| Metric | Description | Measurement |
|--------|-------------|-------------|
| **Resistance Recognition Accuracy (RRA)** | Does the AI correctly identify the resistance type? | Classification vs. ground truth |
| **De-escalation Success Rate (DSR)** | Does client engagement improve after AI response? | Turn-level engagement score change |
| **Therapeutic Alliance Maintenance (TAM)** | Does alliance score hold or improve through resistant moments? | Adapted Working Alliance Inventory |
| **Strategy Appropriateness (SA)** | Does AI use an MI-consistent strategy for the resistance type? | Expert annotation |

### Secondary Metrics

| Metric | Description |
|--------|-------------|
| **Response Relevance** | Does response address what client actually said? |
| **Empathy Calibration** | Is the emotional tone appropriate to client's state? |
| **Autonomy Support Score** | Does response offer choice/control to client? |
| **Conversation Completion Rate** | Does the session reach natural conclusion vs. early termination? |

---

## 6. Benchmark Design

### Dataset Structure

```python
# Proposed JSON schema for benchmark dataset
{
  "scenario_id": "str_defensive_001",
  "context": {
    "client_age": 28,
    "presenting_issue": "work_stress",
    "session_number": 2,
    "relevant_history": [...]
  },
  "turns": [
    {
      "turn_id": 1,
      "speaker": "client",
      "text": "I don't know why you're making this a big deal",
      "resistance_type": "defensive",
      "resistance_level": 0.7
    },
    {
      "turn_id": 1,
      "speaker": "therapist",
      "text": "...",
      "strategy_used": "validation_first",
      "ground_truth": true/false
    }
  ]
}
```

### Evaluation Protocol

1. **Run**: Execute test AI through all scenarios
2. **Annotate**: Human experts label resistance types and response quality
3. **Score**: Compute RRA, DSR, TAM, SA per archetype and overall
4. **Compare**: Benchmark against rule-based MI baseline and current LLMs

---

## 7. Implementation Recommendations

### Minimal Viable Benchmark
1. **50 hand-crafted scenarios** (equal distribution across archetypes)
2. **Single-turn evaluation**: Does the AI respond appropriately to initial resistance?
3. **2 human annotators** for inter-annotator agreement

### Extended Benchmark
1. **200+ multi-turn scenarios** (4-6 turns each)
2. **Longitudinal tracking**: Does AI maintain alliance across full conversation
3. **A/B testing**: Compare different strategy implementations

### Baseline Implementations to Compare
1. **Standard LLM** (GPT-4, Claude) with system prompt only
2. **MI-tuned LLM**: Fine-tuned on motivational interviewing transcripts
3. **Rule-based**: Explicit if-then logic for resistance handling
4. **Hybrid**: LLM with structured MI wrapper

---

## 8. Key Sources

- Woebot RCTs: PMID 41367963, 37831490
- Wysa RCT: PMID 37332481
- Therapeutic Alliance with AI: PMID 41591426, 39919295
- MI Spirit in AI: PMID 41632955
- MentalChat16K Benchmark: PMID 41098434
- Mindbench.ai: PMID 41360938

---

## 9. Conclusion & Next Steps

This framework addresses a critical gap in mental health AI evaluation. The primary recommendation is to **develop a resistance-specific benchmark dataset** using the scenario matrix above, then evaluate current LLMs against MI-consistent baselines.

**Suggested experiments:**
1. Annotate existing mental health dialogue datasets for resistance behaviors
2. Create synthetic resistant client dialogues using the archetype taxonomy
3. Benchmark GPT-4/Claude with/without MI-tuned prompts
4. Conduct user studies comparing engagement outcomes across response strategies
