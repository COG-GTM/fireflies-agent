# Fireflies Meeting Agent - Migration Plan

## Overview

Migrate from Granola note-taker integration to Fireflies.ai integration. The app will:

- **Trigger**: Fireflies meeting completion (via webhook)
- **Action**: Generate a draft follow-up email and post to Slack channel

---

## Current State

- Listens to Slack channel for Granola bot messages
- Parses meeting notes from Granola message blocks
- Posts a summary reply in thread

---

## Target State

- Receive webhook from Fireflies when a meeting transcript is ready
- Fetch full transcript/notes via Fireflies GraphQL API
- Use Claude to generate a professional follow-up email draft
- Post the draft email to the existing Slack channel

---

## Implementation Steps

### 1. Research Fireflies API ✅

- [x] Understand Fireflies webhook events (meeting completed)
- [x] Understand Fireflies GraphQL API for fetching transcripts
- [x] Identify required API keys/authentication

### 2. Update App Architecture ✅

- [x] Add FastAPI HTTP endpoint for Fireflies webhook
- [x] Keep existing Slack integration for posting messages
- [x] Remove Granola-specific parsing code

### 3. Implement Fireflies Integration

- [ ] Create webhook endpoint (`POST /webhook/fireflies`)
- [ ] Parse webhook payload to extract meeting ID
- [ ] Fetch full transcript via Fireflies GraphQL API

### 4. Implement Email Draft Generation

- [ ] Create Claude prompt for generating follow-up emails
- [ ] Include meeting context: title, attendees, key points, action items
- [ ] Generate professional, customizable email draft

### 5. Update Slack Integration

- [ ] Post formatted email draft to target channel
- [ ] Include meeting metadata (title, date, attendees)
- [ ] Format for easy copy/paste

### 6. Configuration & Environment

- [ ] Add `FIREFLIES_API_KEY` to environment
- [ ] Update `TARGET_CHANNEL_NAME` if needed
- [ ] Configure Fireflies webhook URL in Fireflies dashboard

---

## Environment Variables Required

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
FIREFLIES_API_KEY=...
TARGET_CHANNEL_NAME=granola-mena-apac
```

---

## Fireflies API Reference

### Webhook Payload (meeting completed)

```json
{
  "meetingId": "abc123",
  "eventType": "Transcription completed",
  "clientReferenceId": "...",
  ...
}
```

### GraphQL Query for Transcript

```graphql
query Transcript($transcriptId: String!) {
  transcript(id: $transcriptId) {
    id
    title
    date
    duration
    organizer_email
    participants
    sentences {
      speaker_name
      text
    }
    summary {
      overview
      action_items
      keywords
    }
  }
}
```

---

## File Changes

| File               | Action                                                                |
| ------------------ | --------------------------------------------------------------------- |
| `app.py`           | Rewrite - replace Granola with Fireflies webhook + API                |
| `requirements.txt` | Add `httpx` (if not present), `gql` or keep using `httpx` for GraphQL |
| `.env`             | Add `FIREFLIES_API_KEY`                                               |
| `Dockerfile`       | May need to expose HTTP port for webhook                              |

---

## Testing Plan

1. Test webhook endpoint with sample payload
2. Test Fireflies API connection
3. Test email draft generation with Claude
4. Test Slack posting
5. End-to-end test with real Fireflies meeting
