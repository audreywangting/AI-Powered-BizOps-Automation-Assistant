# AI-Powered BizOps Automation Assistant

Local MVP that turns messy Slack operations requests into structured Notion tasks.

Demo video: https://youtu.be/dSuHFV1Mn7E

Workflow:

```text
Slack user -> @BizOpsBot -> FastAPI -> OpenAI Structured Outputs -> Pydantic validation -> Notion page -> Slack thread reply
```

## Architecture

```text
Slack
→ FastAPI
→ OpenAI Structured Outputs
→ Pydantic Validation
→ Notion API
→ Slack Confirmation
```

## Project Structure

```text
app/
  main.py
  config.py
  api/
    health.py
    slack_events.py
  schemas/
    task.py
    slack.py
  services/
    extraction_service.py
    workflow_service.py
    notion_service.py
    slack_service.py
  clients/
    openai_client.py
    notion_client.py
    slack_client.py
  prompts/
    task_extraction.txt
  utils/
    logger.py
demo.py
benchmark/
  mock_requests.json
  golden_labels.json
  evaluate.py
  results.json
telemetry/
  workflow_logs.jsonl
requirements.txt
.env.example
README.md
.gitignore
```

## 1. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure `.env`

```bash
cp .env.example .env
```

Fill in:

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
ALLOW_OPENAI_CALLS=false
MOCK_MODE=true
DEBUG_MODE=true

SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=...

NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=...
```

### OpenAI Safety and Cost Controls

Secrets are loaded only from environment variables. Do not paste real keys into source files, README examples, logs, or commits.

Use these local development flags:

```bash
ALLOW_OPENAI_CALLS=false
MOCK_MODE=true
DEBUG_MODE=true
```

Behavior:

```text
ALLOW_OPENAI_CALLS=false -> never calls OpenAI; returns mock structured output.
MOCK_MODE=true -> returns mock structured output even if ALLOW_OPENAI_CALLS=true.
DEBUG_MODE=true -> adds local development logs without printing credentials.
```

For a real extraction call, set:

```bash
ALLOW_OPENAI_CALLS=true
MOCK_MODE=false
```

The app uses `gpt-4.1-mini` by default to keep demo costs low. Each `/demo/parse` request or Slack mention makes at most one OpenAI extraction call, and only when real calls are explicitly enabled.

Check local usage counters:

```bash
curl http://localhost:8000/debug/usage
```

Expected shape:

```json
{
  "openai_extraction_calls": 0,
  "mock_extraction_calls": 1
}
```

## 4. Run FastAPI

```bash
uvicorn app.main:app --reload --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 5. Run Ngrok

In a second terminal:

```bash
ngrok http 8000
```

Copy the public HTTPS forwarding URL. Your Slack events URL will be:

```text
https://YOUR-NGROK-DOMAIN.ngrok-free.app/slack/events
```

## 6. Create the Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps).
2. Click **Create New App**.
3. Choose **From scratch**.
4. Name it `BizOpsBot`.
5. Pick your workspace.

### Bot Token Scopes

Go to **OAuth & Permissions** and add these bot token scopes:

```text
app_mentions:read
chat:write
```

Click **Install to Workspace** and copy the bot token into `SLACK_BOT_TOKEN`.

### Signing Secret

Go to **Basic Information**, copy **Signing Secret**, and paste it into `SLACK_SIGNING_SECRET`.

## 7. Configure Slack Event Subscriptions

1. Go to **Event Subscriptions**.
2. Turn events **On**.
3. Set **Request URL** to:

```text
https://YOUR-NGROK-DOMAIN.ngrok-free.app/slack/events
```

Slack should verify the URL challenge automatically.

4. Under **Subscribe to bot events**, add:

```text
app_mention
```

5. Save changes.
6. Invite the bot to a channel:

```text
/invite @BizOpsBot
```

## 8. Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations).
2. Create a new internal integration.
3. Copy the integration secret into `NOTION_API_KEY`.
4. Open your Notion database page.
5. Click **...** then connect your integration.

## 9. Create the Notion Database

Create a Notion database with these exact property names:

| Property | Type |
| --- | --- |
| Title | Title |
| Priority | Select |
| Category | Select |
| Assignee | Text |
| Customer | Text |
| Summary | Text |
| Recommended Action | Text |
| Status | Select |
| Source Message | Text |

Recommended select options:

Priority:

```text
Low, Medium, High, Urgent
```

Category:

```text
Frontend Bug, Backend Bug, Customer Complaint, Billing, Data Request, Access Issue, Integration Issue, Device Issue, Other
```

Status:

```text
Not Started, In Progress, Done
```

Copy the database ID from the database URL and paste it into `NOTION_DATABASE_ID`.

## 10. Test Parsing Without Slack

With FastAPI running:

```bash
curl -X POST http://localhost:8000/demo/parse \
  -H "Content-Type: application/json" \
  -d '{"message":"Hey @BizOpsBot, Acme Corp just reported that the login button is not working on Chrome. This is urgent because their team cannot access the dashboard before tomorrow board meeting. Please assign it to Alex from Engineering."}'
```

You should receive a structured `BizOpsTask` JSON response.

With the default safety settings in `.env.example`, this returns a mock structured result and does not call OpenAI.

You can also run:

```bash
python demo.py
```

## 11. Test Local Notion Creation Without Slack

This endpoint extracts a task and creates the Notion page, but does not send any Slack messages:

```bash
curl -X POST http://localhost:8000/demo/create-task \
  -H "Content-Type: application/json" \
  -d '{"message":"Hey @BizOpsBot, Acme Corp just reported that the login button is not working on Chrome. This is urgent because their team cannot access the dashboard before tomorrow board meeting. Please assign it to Alex from Engineering."}'
```

Response shape:

```json
{
  "task": {
    "title": "Acme Corp login button not working on Chrome",
    "priority": "Urgent",
    "category": "Frontend Bug",
    "assignee": "Alex",
    "customer": "Acme Corp",
    "summary": "Acme Corp reported that the login button is not working on Chrome, preventing dashboard access before an upcoming board meeting.",
    "recommended_action": "Create a frontend bug ticket and assign it to Alex."
  },
  "notion_url": "https://www.notion.so/..."
}
```

## 12. Test the Complete Slack to Notion Workflow

In Slack, send a message in a channel where the bot has been invited:

```text
Hey @BizOpsBot, Acme Corp just reported that the login button isn't working on Chrome. This is pretty urgent because their team can't access the dashboard before tomorrow's board meeting. Can you create a ticket and assign it to Alex from Engineering?
```

Expected behavior:

1. Slack thread receives:

```text
👀 Parsing request and creating a Notion task...
```

2. A Notion task is created.

3. Slack thread receives:

```text
✅ Task successfully created.

Title: Acme Corp login button not working on Chrome

Priority: Urgent

Category: Frontend Bug

Assignee: Alex

View Task: <Notion URL>
```

## Demo Video Checklist

For a 20-30 second demo recording:

1. Show the FastAPI server running locally.
2. Show ngrok forwarding to `localhost:8000`.
3. Send the Slack mention.
4. Show the immediate parsing reply.
5. Show the Notion task created.
6. Show the final Slack success reply with the Notion URL.

## Telemetry

Every Slack workflow request appends one JSONL event to:

```text
telemetry/workflow_logs.jsonl
```

Each event records:

```json
{
  "request_id": "...",
  "timestamp": "...",
  "success": true,
  "latency_ms": 3200,
  "priority": "Urgent",
  "category": "Frontend Bug",
  "assignee_extracted": true,
  "notion_created": true
}
```

This gives local evidence for automation success, latency, extracted routing fields, and Notion creation.

## Benchmark Results

The benchmark evaluates 20 realistic SaaS BizOps scenarios using OpenAI extraction against golden labels.

| Metric | Result |
| --- | --- |
| Benchmark scenarios | 20 |
| Workflow success rate | 100% |
| Average latency | 2.3 seconds |
| Category accuracy | 95% |
| Assignee accuracy | 100% |
| Priority accuracy | 70% |
| Extraction mode | OpenAI |

Raw benchmark output:

```json
{
  "num_requests": 20,
  "attempted_requests": 20,
  "success_rate": 1.0,
  "avg_latency_ms": 2309,
  "priority_accuracy": 0.7,
  "category_accuracy": 0.95,
  "assignee_accuracy": 1.0,
  "extraction_mode": "openai"
}
```

## Evaluation Methodology

The evaluation uses 20 realistic SaaS BizOps requests across support, customer success, sales, billing, data, access, integration, frontend, backend, and device scenarios. Each OpenAI extraction is compared against golden labels for priority, category, and assignee. Metrics include workflow success rate, average latency, category accuracy, assignee accuracy, and priority accuracy.

## Key Findings

- Category extraction achieved high reliability at 95%.
- Assignee extraction achieved perfect benchmark accuracy at 100%.
- Most extraction errors occurred in priority classification.
- Priority classification remains partially subjective and depends on operational definitions of urgency.

## Business Impact

The workflow automates request intake, task creation, routing, and status notification. It reduces repetitive manual task-entry work by replacing a multi-step process of reading Slack requests, classifying urgency, creating Notion tasks, filling fields, and notifying owners with an automated pipeline.

## Error Handling

If OpenAI extraction fails, the Slack thread receives:

```text
❌ Failed to extract task information.
```

If Notion creation fails, the Slack thread receives:

```text
❌ Failed to create Notion task.
```

Errors are logged in the FastAPI terminal.

## macOS Python SSL Note

If Slack posting fails with:

```text
SSL: CERTIFICATE_VERIFY_FAILED
```

the usual cause on framework-installed macOS Python is that Python's OpenSSL
default certificate file is missing or not populated. You can inspect it with:

```bash
python -c "import ssl; print(ssl.get_default_verify_paths())"
```

This app posts Slack messages with `httpx` and `certifi`, so it uses the
certificate bundle installed in the virtual environment instead of relying on
the missing macOS Python OpenSSL file.

Optional machine-level fixes:

```bash
pip install --upgrade certifi
```

If your Python installer includes it, run `Install Certificates.command` from
the Python application folder.
