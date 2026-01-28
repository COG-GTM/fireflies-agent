# Granola Slack Bot - Implementation Plan

## Overview

Build a Slack bot using `slack_bolt` that listens for meeting notes in a specific channel, generates follow-up email drafts using Claude 4.5 Sonnet, and replies in the Slack thread.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Slack Channel      │────▶│  Slack Bot       │────▶│  Anthropic API      │
│  (granola-mena-apac)│     │  (slack_bolt)    │     │  (claude-4.5-sonnet)│
└─────────────────────┘     └──────────────────┘     └─────────────────────┘
        │                           │                          │
        │                           ▼                          │
        │                   ┌──────────────────┐               │
        │                   │  Parse Meeting   │               │
        │                   │  Notes           │               │
        │                   └──────────────────┘               │
        │                           │                          │
        │                           ▼                          │
        │                   ┌──────────────────┐               │
        │◀──────────────────│  Reply in Thread │◀──────────────│
        │                   │  with Draft      │               │
        │                   └──────────────────┘               │
```

---

## Implementation Steps

### ✅ Step 1: Environment Setup

**Required Environment Variables** (add to `.env`):

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
ANTHROPIC_API_KEY=sk-ant-...
TARGET_CHANNEL_NAME=granola-mena-apac
```

**Dependencies** (add to `requirements.txt`):

```
anthropic
```

---

### ✅ Step 2: Core Bot Structure

```python
# app.py structure
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
```

---

### ✅ Step 3: Message Listener

Listen for messages **only** in `granola-mena-apac` channel:

```python
@app.event("message")
def handle_message(event, say, client):
    # Filter by channel name
    # Ignore bot messages and subtypes (edits, deletes, etc.)
    # Trigger workflow for valid meeting notes
```

**Channel Filtering Approach**:

1. Get channel ID for "granola-mena-apac" on startup (cache it)
2. Compare incoming message's `channel` field against cached ID

---

### Step 4: Parse Meeting Notes (Step A)

Extract structured context from the message text:

```python
def parse_meeting_notes(message_text: str) -> dict:
    """
    Parse meeting notes to extract:
    - Client name
    - Meeting participants
    - Key discussion points
    - Action items
    - Next steps
    """
    return {
        "client_name": extracted_client,
        "participants": participants_list,
        "discussion_points": points,
        "action_items": items,
        "raw_notes": message_text
    }
```

**Parsing Strategies**:

- Use Claude to intelligently extract structured data from unstructured notes
- Or use regex/keyword patterns if notes follow a consistent format

---

### Step 5: Email Templates

Create a `templates/` directory with sample follow-up emails:

```
templates/
├── follow_up_general.txt
├── follow_up_proposal.txt
├── follow_up_demo.txt
└── follow_up_intro.txt
```

**Example Template** (`follow_up_general.txt`):

```
Subject: Follow-up: {meeting_topic}

Dear {client_name},

Thank you for taking the time to meet with us today.

[Summary of discussion points]

As discussed, our next steps are:
[Action items]

Please let me know if you have any questions.

Best regards,
[Your Name]
```

---

### Step 6: Claude Integration (Step C)

Generate email draft using Claude 4.5 Sonnet:

```python
def generate_email_draft(meeting_context: dict, templates: list[str]) -> str:
    prompt = f"""
    Based on the following meeting notes, generate a professional follow-up email.

    Meeting Notes:
    {meeting_context['raw_notes']}

    Client Name: {meeting_context['client_name']}

    Reference these email templates for tone and structure:
    {templates}

    Generate a concise, professional follow-up email that:
    1. Thanks them for their time
    2. Summarizes key discussion points
    3. Lists agreed action items
    4. Proposes next steps
    """

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

---

### Step 7: Thread Reply

Reply in the original message thread:

````python
def reply_with_draft(client, channel_id, thread_ts, client_name, email_draft):
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=f"✅ Draft created for *{client_name}*.\n\n```{email_draft}```"
    )
````

---

## Complete Workflow

````python
@app.event("message")
def handle_meeting_notes(event, say, client):
    # 1. Filter: Only process messages from target channel
    if event.get("channel") != TARGET_CHANNEL_ID:
        return

    # 2. Ignore bot messages and message edits
    if event.get("bot_id") or event.get("subtype"):
        return

    message_text = event.get("text", "")
    thread_ts = event.get("ts")
    channel_id = event["channel"]

    # 3. Parse meeting notes
    meeting_context = parse_meeting_notes(message_text)

    # 4. Load email templates
    templates = load_email_templates()

    # 5. Generate email draft with Claude
    email_draft = generate_email_draft(meeting_context, templates)

    # 6. Reply in thread
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=f"✅ Draft created for *{meeting_context['client_name']}*.\n\n```{email_draft}```"
    )
````

---

## File Structure

```
granola-agent/
├── app.py                 # Main Slack bot application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── Dockerfile            # Container config
├── templates/            # Email templates directory
│   ├── follow_up_general.txt
│   └── follow_up_proposal.txt
└── utils/
    ├── __init__.py
    ├── parser.py         # Meeting notes parser
    └── claude_client.py  # Anthropic API wrapper
```

---

## Error Handling

1. **API Failures**: Wrap Anthropic calls in try/except, post error to thread
2. **Parsing Failures**: Default to "Unknown Client" if extraction fails
3. **Rate Limits**: Implement exponential backoff for API calls
4. **Channel Not Found**: Log warning if target channel doesn't exist

---

## Testing Checklist

- [ ] Bot connects to Slack workspace
- [ ] Bot only responds in `granola-mena-apac` channel
- [ ] Bot ignores its own messages
- [ ] Meeting notes are parsed correctly
- [ ] Claude generates coherent email drafts
- [ ] Thread replies appear correctly
- [ ] Error cases are handled gracefully

---

## Next Steps

1. Add `anthropic` to `requirements.txt`
2. Implement the bot in `app.py`
3. Create email templates
4. Test with sample meeting notes
5. Deploy
