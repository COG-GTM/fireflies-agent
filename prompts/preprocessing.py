"""Preprocessing module for transcript data before email generation."""

import re
from typing import Optional


FILLER_PATTERNS = [
    r"^(okay|ok|yeah|yes|no|hi|hello|hey|bye|cool|sure|right|so|um|uh|hmm|ah|oh)\.?$",
    r"^(thank you|thanks)\.?$",
    r"^(good|great|awesome|nice|perfect)\.?$",
    r"^(i see|i think|i mean|you know)\.?$",
]

FILLER_REGEX = re.compile("|".join(FILLER_PATTERNS), re.IGNORECASE)


def is_filler_sentence(text: str) -> bool:
    """Check if a sentence is filler/low-content."""
    text = text.strip()
    if len(text) < 15:
        return FILLER_REGEX.match(text) is not None
    return False


def is_substantive_sentence(text: str) -> bool:
    """Check if a sentence contains substantive content."""
    text = text.strip()
    if len(text) < 10:
        return False
    if is_filler_sentence(text):
        return False
    return True


def extract_sentences_text(sentences: list[dict]) -> list[str]:
    """Extract text from sentence objects, filtering out filler."""
    result = []
    for sentence in sentences:
        text = sentence.get("text", "").strip()
        if is_substantive_sentence(text):
            speaker = sentence.get("speaker_name")
            if speaker:
                result.append(f"{speaker}: {text}")
            else:
                result.append(text)
    return result


def extract_key_discussion(sentences: list[dict], max_sentences: int = 300) -> str:
    """Extract key discussion points from transcript sentences.
    
    Uses more of the transcript and filters out filler content.
    """
    substantive = extract_sentences_text(sentences)
    selected = substantive[:max_sentences]
    return "\n".join([f"- {s}" for s in selected])


def extract_entities_from_text(text: str) -> dict:
    """Extract potential entities (people, companies, technologies) from text."""
    entities = {
        "people": set(),
        "companies": set(),
        "technologies": set(),
    }
    
    common_tech_terms = [
        "AI", "ChatGPT", "Claude", "Cursor", "Copilot", "GitHub", "Azure", "DevOps",
        "AWS", "GCP", "Jira", "Devin", "Windsurf", "SaaS", "API", "GraphQL",
        "Python", "JavaScript", "TypeScript", "React", "Node", "Docker", "Kubernetes",
    ]
    
    for tech in common_tech_terms:
        if tech.lower() in text.lower():
            entities["technologies"].add(tech)
    
    return {k: list(v) for k, v in entities.items()}


def preprocess_transcript(transcript_data: dict) -> dict:
    """Preprocess transcript data for email generation.
    
    Returns a dictionary with:
    - title: Meeting title
    - date_string: Meeting date
    - attendee_names: Formatted attendee names
    - overview: Meeting overview from summary
    - keywords: Key topics
    - action_items: Action items from summary
    - key_discussion: Filtered and formatted discussion points
    - entities: Extracted entities (people, companies, technologies)
    - full_transcript_text: Full text for LLM context
    """
    title = transcript_data.get("title") or "Meeting"
    date_string = transcript_data.get("dateString") or ""
    
    attendees = transcript_data.get("meeting_attendees") or []
    attendee_names = ", ".join([
        a.get("displayName") or a.get("name", "Unknown") 
        for a in attendees
    ]) if attendees else "Not specified"
    
    summary_data = transcript_data.get("summary") or {}
    overview = summary_data.get("overview") or ""
    action_items = summary_data.get("action_items") or []
    keywords = summary_data.get("keywords") or []
    
    sentences = transcript_data.get("sentences") or []
    key_discussion = extract_key_discussion(sentences, max_sentences=300)
    
    full_text = " ".join([s.get("text", "") for s in sentences])
    entities = extract_entities_from_text(full_text)
    
    return {
        "title": title,
        "date_string": date_string,
        "attendee_names": attendee_names,
        "overview": overview,
        "keywords": keywords,
        "action_items": action_items,
        "key_discussion": key_discussion,
        "entities": entities,
        "full_transcript_text": full_text,
    }
