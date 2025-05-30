# utils/prompt_templates.py

def build_prompt(
    persona_data,
    user_input="",
    file_context="",
    file_description="",
    scenario="General Q&A",
    brand_context=None,
):
    is_brandience = brand_context is not None and isinstance(brand_context, dict)

    # Define scenario-specific behavior
    scenario_instructions = {
        "General Q&A": "Respond naturally to any idea or question from the user, offering realistic and relevant feedback.",
        "Messaging Tester": "Evaluate the messaging shared. Is it clear, credible, and compelling for someone in your role?",
        "Differentiation Analyzer": "Assess whether this idea would stand out in a crowded market. What makes it unique or weak?",
        "Expectation Explorer": "Describe what you would expect to hear if someone pitched this idea to you.",
        "Negotiation Simulator": "Assume you're interested, but have concerns. Respond with strategic pushback or clarifying questions."
    }

    def get_val(d, key, fallback="N/A"):
        return d.get(key) or d.get(key.lower(), fallback)

    def format_persona(data):
        vertical = data.get("name", data.get("industry", "Unknown")).lower()
        vertical_overrides = {
            "restaurant": {
                "Revenue Range": "$100M–$1B+",
                "Geography": "National (U.S.) with regional franchise systems",
                "Org Size": "1,000+ units (corporate + franchise)",
                "Terms": ["LTOs", "guest count", "ticket averages", "digital conversions", "franchisee alignment"]
            },
            "retail": {
                "Revenue Range": "$500M–$2B",
                "Geography": "Multi-state U.S. operations",
                "Org Size": "500+ locations or omnichannel footprint",
                "Terms": ["foot traffic", "omnichannel", "conversion rate", "merchandising alignment", "brand halo"]
            },
            "franchise": {
                "Revenue Range": "$100M–$5B",
                "Geography": "Global and national U.S. presence",
                "Org Size": "Hundreds of franchisees and locations",
                "Terms": ["system-wide sales", "franchisee engagement", "co-op marketing", "compliance", "field marketing"]
            },
            "healthcare": {
                "Revenue Range": "$50M–$1B",
                "Geography": "Regional to multi-state systems",
                "Org Size": "Dozens to hundreds of care sites",
                "Terms": ["patient retention", "provider network growth", "cost of care", "compliance", "payer alignment"]
            }
        }
        overrides = vertical_overrides.get(vertical, {})

        return f"""
- **Roles**: {get_val(data, 'roles')}
- **Industry**: {get_val(data, 'industry')}
- **Goals**: {', '.join(get_val(data, 'goals', []))}
- **Pain Points**: {', '.join(get_val(data, 'pain_points', []))}
- **Communication Style**: {get_val(data, 'communication_style', get_val(data, 'Style'))}
- **Decision-Making**: {get_val(data, 'decision_making', get_val(data, 'DecisionMaking'))}
- **Triggers**: {', '.join(get_val(data, 'triggers', []))}
- **Marketing Channels**: {', '.join(get_val(data, 'marketing_channels', []))}
- **Tech Stack**: {', '.join(get_val(data, 'tech_stack', []))}
- **Content Preferences**: {', '.join(get_val(data, 'content_preferences', []))}
- **Success Metrics**: {', '.join(get_val(data, 'success_metrics', []))}
- **Engagement Preferences**: {get_val(data, 'engagement_preferences', '')}
- **Revenue Range**: {overrides.get('Revenue Range')}
- **Geography**: {overrides.get('Geography')}
- **Org Size**: {overrides.get('Org Size')}
- **Vertical KPIs & Terms to Reflect**: {', '.join(overrides.get('Terms', []))}
"""

    prompt = f"""
You are simulating a conversation with a senior marketing decision-maker persona.

### Persona Profile
{format_persona(persona_data)}

### Scenario: {scenario}
{scenario_instructions.get(scenario, '')}
"""

    if is_brandience:
        prompt += f"""
### Brandience Positioning Context
- **Tone**: {brand_context.get('tone', 'Consultative, Insightful')}
- **Services**: {', '.join(brand_context.get('services', []))}
- **Ideal Clients**: {', '.join(brand_context.get('ideal_client_traits', []))}
- **Fit Examples**: {', '.join(brand_context.get('examples_of_fit', []))}
- **Misfit Examples**: {', '.join(brand_context.get('examples_of_misfit', []))}

As the persona, speak honestly and critically in response to Brandience messaging.
Reflect expectations such as:
- Appreciation for nimble, responsive, and collaborative agency partners
- Need for franchise expertise and multi-stakeholder alignment
- Frustration with overpromising, slow, or rigid agencies
- Value for transparency, field marketing fluency, and co-op execution

Use marketing-specific language across:
- Strategic planning (e.g., brand positioning, GTM strategy, A/B testing)
- Performance metrics (e.g., ROI, CAC, LTV, engagement rates)
- Customer behavior (e.g., conversion funnels, churn risk, loyalty)
- Operational collaboration (e.g., marketing + ops + finance sync)
"""
    else:
        prompt += """
Speak as a seasoned CMO-level marketer. Be analytical, brand-savvy, and impact-focused.
Use terms like ROI, funnel conversion, marketing mix, retention rate, CAC, LTV, attribution models, channel optimization, KPI dashboards, and stakeholder buy-in.
If no user input is provided, reflect on common priorities like agency evaluation, campaign performance, budget allocation, and innovation readiness.
"""

    if file_context:
        prompt += f"""

### Context From Uploaded File
- **Description**: {file_description}
- **Content**:
{file_context}
"""

    prompt += f"""

### User Input
{user_input or '[No specific input given – respond based on your role and industry context]'}

### Your Response (in-character as persona):
"""
    return prompt.strip()
