"""Prompt template for generating follow-up email drafts."""

from pathlib import Path

def load_email_template() -> str:
    """Load the email template from file."""
    template_path = Path(__file__).parent.parent / "templates" / "email_template.txt"
    with open(template_path, "r") as f:
        return f.read()

EMAIL_TEMPLATE = load_email_template()

SYSTEM_PROMPT = """You are an executive assistant helping to draft a professional follow-up email after a meeting.

Your task is to create a concise, professional follow-up email that:
1. Thanks attendees for their time
2. Summarizes the key discussion points
3. Lists any action items with clear ownership if possible
4. Suggests next steps if appropriate
5. Maintains a warm but professional tone
6. Don't bold anything

Keep the email under 300 words. Format it ready to send."""

def build_email_prompt(
    title: str,
    attendee_names: str,
    overview: str,
    keywords: list[str],
    action_items: list[str],
    key_discussion: str
) -> str:
    """Build the full prompt for generating an email draft."""
    
    return f"""{SYSTEM_PROMPT}

Meeting Details:
- Title: {title}
- Attendees: {attendee_names}
- Overview: {overview}
- Key Topics: {', '.join(keywords) if keywords else 'N/A'}
- Action Items: {', '.join(action_items) if action_items else 'None identified'}

Key Discussion Points:
{key_discussion}

Use the following template structure as a guide (adapt as needed):

{EMAIL_TEMPLATE}"""
