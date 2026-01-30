"""Prompt template for generating follow-up email drafts."""

from pathlib import Path


def load_email_template() -> str:
    """Load the email template from file."""
    template_path = Path(__file__).parent.parent / "templates" / "email_template.txt"
    with open(template_path, "r") as f:
        return f.read()


EMAIL_TEMPLATE = load_email_template()

SYSTEM_PROMPT = """You are an executive assistant helping to draft a professional follow-up email after a business meeting.

Your task is to create a substantive, professional follow-up email that:

1. PERSONALIZATION:
   - Use a personalized greeting with the primary contact's name if identifiable from the transcript
   - Reference the specific meeting date/day if mentioned
   - Acknowledge the relationship context (e.g., "Thank you again for your time")

2. SUBSTANTIVE SUMMARY:
   - Extract and summarize the KEY BUSINESS POINTS discussed, not generic pleasantries
   - Include specific details: numbers, percentages, technologies, company names, constraints
   - Organize the summary into clear thematic sections if multiple topics were discussed
   - Focus on what was actually discussed, not generic meeting summaries

3. ACTION ITEMS AND NEXT STEPS:
   - Clearly state any commitments made by either party
   - Include specific next steps with clear asks
   - If licenses, demos, or follow-up meetings were discussed, mention them explicitly

4. TONE AND FORMAT:
   - Warm but professional tone
   - Do NOT use bold formatting or markdown
   - Do NOT use bullet points in the email body - write in flowing paragraphs
   - Keep the email focused and substantive (aim for 200-400 words depending on meeting complexity)

IMPORTANT: Extract REAL content from the transcript. Do not generate generic placeholder text. If the transcript discusses specific technologies, companies, numbers, or constraints, include those details."""


def build_email_prompt(
    title: str,
    attendee_names: str,
    overview: str,
    keywords: list[str],
    action_items: list[str],
    key_discussion: str,
    entities: dict | None = None,
    date_string: str = "",
) -> str:
    """Build the full prompt for generating an email draft.
    
    Args:
        title: Meeting title
        attendee_names: Comma-separated attendee names
        overview: Meeting overview from summary
        keywords: List of key topics
        action_items: List of action items
        key_discussion: Formatted key discussion points
        entities: Optional dict with extracted entities (people, companies, technologies)
        date_string: Meeting date string
    """
    entities_section = ""
    if entities:
        tech_list = ", ".join(entities.get("technologies", [])) or "None identified"
        entities_section = f"\nTechnologies/Tools Mentioned: {tech_list}"
    
    return f"""{SYSTEM_PROMPT}

Meeting Details:
- Title: {title}
- Date: {date_string}
- Attendees: {attendee_names}
- Overview: {overview if overview else 'Not provided - extract from transcript'}
- Key Topics: {', '.join(keywords) if keywords else 'Extract from transcript'}
- Action Items: {', '.join(action_items) if action_items else 'Extract from transcript'}{entities_section}

Transcript Discussion Points (filtered for substantive content):
{key_discussion}

Based on the above transcript, generate a professional follow-up email. Extract specific details, names, technologies, and commitments from the transcript. Do not use generic placeholder text.

Use the following template structure as a loose guide (adapt based on actual content):

{EMAIL_TEMPLATE}"""
