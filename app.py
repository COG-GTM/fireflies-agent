from fastapi import FastAPI, Request, HTTPException
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import anthropic
import httpx
import os
import json
import uvicorn
from dotenv import load_dotenv
import asyncio
from typing import Optional
from prompts import build_email_prompt

load_dotenv()

app = FastAPI()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

FIREFLIES_API_KEY = os.environ["FIREFLIES_API_KEY"]
FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"

TARGET_CHANNEL_NAME = os.environ.get("TARGET_CHANNEL_NAME", "granola-mena-apac")
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

def get_channel_id_by_name(channel_name: str) -> Optional[str]:
    """Get channel ID by channel name"""
    try:
        result = slack_client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    except SlackApiError as e:
        print(f"Error fetching channel ID: {e}")
    return None

async def fetch_fireflies_transcript(meeting_id: str) -> Optional[dict]:
    """Fetch full transcript from Fireflies GraphQL API"""
    query = """
    query Transcript($transcriptId: String!) {
        transcript(id: $transcriptId) {
            id
            title
            date
            dateString
            duration
            organizer_email
            host_email
            participants
            meeting_attendees {
                displayName
                email
                name
            }
            sentences {
                speaker_name
                text
                start_time
            }
            summary {
                action_items
                overview
                keywords
                topics_discussed
            }
            transcript_url
        }
    }
    """
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FIREFLIES_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {FIREFLIES_API_KEY}"
                },
                json={
                    "query": query,
                    "variables": {"transcriptId": meeting_id}
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[FIREFLIES] Raw API response: {json.dumps(data, indent=2)}")
                if "data" in data and "transcript" in data["data"]:
                    transcript = data["data"]["transcript"]
                    print(f"[FIREFLIES] Transcript keys: {transcript.keys() if transcript else 'None'}")
                    return transcript
                else:
                    print(f"Error in GraphQL response: {data}")
                    return None
            else:
                print(f"Fireflies API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error fetching Fireflies transcript: {e}")
        return None

def generate_email_draft(transcript_data: dict) -> str:
    """Generate a follow-up email draft using Claude"""
    
    title = transcript_data.get("title") or "Meeting"
    attendees = transcript_data.get("meeting_attendees") or []
    attendee_names = ", ".join([a.get("displayName") or a.get("name", "Unknown") for a in attendees]) if attendees else "Not specified"
    
    summary_data = transcript_data.get("summary") or {}
    overview = summary_data.get("overview") or ""
    action_items = summary_data.get("action_items") or []
    keywords = summary_data.get("keywords") or []
    
    sentences = transcript_data.get("sentences") or []
    key_discussion = "\n".join([f"- {s.get('speaker_name', 'Unknown')}: {s.get('text', '')}" for s in sentences[:20]]) if sentences else "No transcript available"
    
    prompt = build_email_prompt(
        title=title,
        attendee_names=attendee_names,
        overview=overview,
        keywords=keywords,
        action_items=action_items,
        key_discussion=key_discussion
    )
    
    try:
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error generating email with Claude: {e}")
        return "Error generating email draft. Please try again."

def post_to_slack(email_draft: str, transcript_data: dict, channel_id: str):
    """Post the email draft to Slack channel"""
    
    title = transcript_data.get("title") or "Meeting"
    date_string = transcript_data.get("dateString") or ""
    duration = transcript_data.get("duration") or 0
    transcript_url = transcript_data.get("transcript_url") or ""
    
    duration_mins = int(duration / 60) if duration else 0
    
    message = f"""📧 *Draft Follow-up Email Generated*

*Meeting:* {title}
*Date:* {date_string}
*Duration:* {duration_mins} minutes
{f'*Transcript:* <{transcript_url}|View in Fireflies>' if transcript_url else ''}

---

*Email Draft:*

{email_draft}

---

_Generated by Fireflies AI Agent. Edit as needed before sending._"""
    
    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            unfurl_links=False
        )
        print(f"✅ Posted email draft to Slack channel: {channel_id}")
    except SlackApiError as e:
        print(f"Error posting to Slack: {e}")

async def process_fireflies_webhook(request: Request):
    """Process Fireflies webhook payload"""
    try:
        payload = await request.json()
        print(f"[FIREFLIES] Received webhook: {json.dumps(payload, indent=2)}")
        
        event_type = payload.get("eventType")
        meeting_id = payload.get("meetingId")
        
        if event_type != "Transcription completed":
            print(f"[FIREFLIES] Ignoring event type: {event_type}")
            return {"status": "ignored", "reason": "Not a transcription completed event"}
        
        if not meeting_id:
            raise HTTPException(status_code=400, detail="Missing meetingId in payload")
        
        print(f"[FIREFLIES] Processing meeting: {meeting_id}")
        
        transcript_data = await fetch_fireflies_transcript(meeting_id)
        
        if not transcript_data:
            raise HTTPException(status_code=500, detail="Failed to fetch transcript from Fireflies")
        
        print(f"[FIREFLIES] Fetched transcript: {transcript_data.get('title')}")
        
        email_draft = generate_email_draft(transcript_data)
        print(f"[CLAUDE] Generated email draft ({len(email_draft)} chars)")
        
        global TARGET_CHANNEL_ID
        if TARGET_CHANNEL_ID is None:
            TARGET_CHANNEL_ID = get_channel_id_by_name(TARGET_CHANNEL_NAME)
            if TARGET_CHANNEL_ID is None:
                raise HTTPException(status_code=500, detail=f"Channel '{TARGET_CHANNEL_NAME}' not found")
        
        post_to_slack(email_draft, transcript_data, TARGET_CHANNEL_ID)
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "title": transcript_data.get("title")
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        print(f"[ERROR] Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/")
async def fireflies_webhook_root(request: Request):
    """Handle Fireflies webhook at root path"""
    return await process_fireflies_webhook(request)

@app.post("/webhook/fireflies")
async def fireflies_webhook(request: Request):
    """Handle incoming Fireflies webhook for completed transcriptions"""
    return await process_fireflies_webhook(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fireflies-slack-agent"}

if __name__ == "__main__":
    print(f"🚀 Starting Fireflies webhook server...")
    print(f"📢 Will post to Slack channel: {TARGET_CHANNEL_NAME}")
    print(f"🔗 Webhook endpoint: http://localhost:8000/webhook/fireflies")
    uvicorn.run(app, host="0.0.0.0", port=8000)