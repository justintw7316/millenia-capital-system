# Millenia Ventures — Capital Formation Automation System

**Non-Technical Operator Guide**

This system automates the 14-step Capital Formation Process used to take a startup client from initial onboarding to a fully funded raise. It handles investor research, outreach, campaign management, reporting, and content generation — so the team focuses on relationships, not admin.

---

## What This System Does

In plain English: when you onboard a new startup client, you run this system and it:

1. **Creates a 90-day timeline** with weekly outreach milestones
2. **Sets up their Box folder** and audits their documents (pitch deck, tear sheet, NDA, etc.)
3. **Researches 10 alternative funding sources** (grants, loans, sponsored capital) and drafts outreach emails
4. **Writes a 170-second founder video script** and gives them a recording checklist
5. **Generates 20 investor interview questions** and schedules a Streamyard session
6. **Notifies Philip** about GT Securities coordination (Philip handles this step personally)
7. **Finds 20 target investors** and enriches their contact info
8. **Drafts 6 platform messages per investor** (LinkedIn, email, SMS, WhatsApp, X, web form)
9. **Creates a LinkedIn MeetAlfred campaign** (requires Phil approval before Das launches)
10. **Generates 12 weeks of follow-up messages** per investor, per platform
11. **Produces campaign launch materials** — Alignable setup, investor groups, broker-dealer portal if $5M+
12. **Finds top 10 podcasts** in the client's industry and drafts podcast outreach emails
13. **Creates investor vetting forms** and Facebook ad briefs for the Indian/Sacramento team
14. **Generates weekly reports** with response rates, pipeline value, alerts, and wire verification checklists

---

## First-Time Setup

### Requirements
- Python 3.11 or later ([download here](https://python.org))
- Git (to clone this repository)
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

**Step 1:** Open Terminal and navigate to where you want to install the system:
```bash
cd ~/Documents
```

**Step 2:** Clone the repository (or copy the folder here)
```bash
# If using git:
git clone [repository-url]
cd millenia-capital-system

# Or if you received the folder, just:
cd millenia-capital-system
```

**Step 3:** Install Python dependencies:
```bash
pip install -r requirements.txt
```

**Step 4:** Set up your environment file:
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your Anthropic API key:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

The other fields (Box.com, Apollo, MeetAlfred, Gmail) are currently stubbed — the system works without them and generates mock data for testing.

---

## Onboarding a New Deal

### Step 1: Create the Deal File

Each deal needs a JSON file in `data/mock_deals/`. Copy the example and edit it:

```bash
cp data/mock_deals/deal_acme_corp.json data/mock_deals/deal_YOURCOMPANY.json
```

Open the file and fill in the company details:

```json
{
  "deal_id": "deal_002",
  "company_name": "Your Company Name",
  "company_website": "https://yourcompany.com",
  "industry": "artificial intelligence",
  "raise_amount": 3000000,
  "founder_name": "Founder Full Name",
  "founder_email": "founder@company.com",
  "founder_linkedin": "https://linkedin.com/in/founderprofile",
  "stage": "onboarded",
  "documents": {
    "tear_sheet": "missing",
    "pitch_deck": "missing",
    "financial_projections": "missing",
    "nda": "missing",
    "ppm": "missing",
    "subscription_agreement": "missing",
    "wiring_instructions": "missing",
    "use_of_funds": "missing"
  },
  "created_at": "2026-02-24"
}
```

**Document status options:** `missing` | `draft` | `approved` | `distributed`

Fill in each document's current status based on what the client has provided.

---

## Running the System

Open Terminal in the `millenia-capital-system` folder and use these commands:

### Run the Full 14-Step Pipeline
```bash
python main.py run --deal data/mock_deals/deal_acme_corp.json
```

This will run all 14 steps in order, generate all outputs, and save them to `outputs/deal_001/`.

### Run a Single Step
```bash
python main.py step --deal data/mock_deals/deal_acme_corp.json --step 7a
```

Replace `7a` with any step number: `1`, `2`, `3`, `4`, `5`, `6`, `7a`, `7b`, `7c`, `8`, `9`, `10`, `11`, `12`, `13`, `14`

### Resume After a Crash or Pause
```bash
python main.py resume --deal data/mock_deals/deal_acme_corp.json --from-step 3
```

The system saves your progress after every step. If it crashes at step 6, you can pick up from step 6 — no duplicate work.

### Check Deal Status
```bash
python main.py status --deal data/mock_deals/deal_acme_corp.json
```

Shows a dashboard of all 14 steps (which are done, pending, or blocked) plus key metrics.

### Generate Weekly Report Only
```bash
python main.py report --deal data/mock_deals/deal_acme_corp.json --week 3
```

---

## Where to Find the Outputs

All outputs land in:
```
outputs/
  deal_001/
    timeline.json                    ← 90-day schedule
    data_room_audit.json             ← Document checklist
    tear_sheet_draft.md              ← AI-generated tear sheet
    pitch_deck_outline.md            ← 11-slide pitch deck outline
    sequoia_review.md                ← Investor-grade document review
    alt_funding_sources.json         ← 10 alternative funding sources
    alt_funding_emails.md            ← Custom outreach emails
    founder_video_script.md          ← 170-second video script
    investor_list.json               ← 20 ranked investors
    investor_contacts_enriched.csv   ← Investor contact sheet
    outreach_bundle.json             ← All outreach messages
    outreach_messages/               ← Per-investor message files
    followup_campaign/               ← 12-week follow-up schedule
    campaign_launch_checklist.md     ← Pre-launch checklist
    podcast_emails.md                ← Podcast outreach emails
    press_release_draft.md           ← Press release
    facebook_ad_brief.md             ← Ad brief for Indian/Sacramento team
    investor_vetting_form.md         ← Investor pre-qualification form
    reports/
      week_01_report.md              ← Weekly reports
      week_02_report.md
    checkpoint.json                  ← Auto-save (do not delete)
    logs/                            ← Step-by-step logs
```

---

## What Steps Require Human Action

The system will flag these automatically in the output, but here's the summary:

| Step | Who Does It | What's Needed |
|------|------------|---------------|
| Step 2 | Founder + Abby | Provide missing documents; Abby designs tear sheet and pitch deck |
| Step 4 | Founder | Record 170-second founder video using Streamyard |
| Step 5 | Millenia team | Schedule and record 20-question investor interview |
| Step 6 | **Philip only** | GT Securities coordination — Philip handles personally |
| Step 7a | Phil + team | Review and approve investor list before outreach starts |
| Step 7c | Phil + Das | Phil approves MeetAlfred campaign; Das launches it |
| Step 9 | Das | Launch MeetAlfred campaign after Phil approval |
| Step 9 | Phil ($5M+) | Submit to broker-dealer portal if raise ≥ $5M |
| Step 10 | Phil or Das | Distribute press release to media |
| Step 11 | Indian/Sacramento team | Build Facebook funnels and run ads |
| Step 12 | Phil + Das | Execute warm market and GT Securities outreach manually |
| Step 14 | Phil | Review wire transfers — dual confirmation required |

---

## How to Escalate to Phil (Alert Thresholds)

The system auto-generates a **Phil Alert** in the weekly report when:

- **Response rate drops below 20%** (e.g., 100 outreaches, fewer than 20 responses) → Review messaging and investor list immediately
- **Meeting conversion drops below 5%** (e.g., 20 responses, fewer than 1 meeting booked) → Review pitch approach and investor fit

When you see `⚠️ PHIL ALERT` in a report:
1. Open the weekly report in `outputs/[deal_id]/reports/week_XX_report.md`
2. Review the specific stats
3. Forward the report to Phil immediately
4. Phil reviews outreach strategy and decides if targeting or messaging needs to change

---

## Running the Tests

To verify everything is working correctly:

```bash
pytest tests/ -v
```

To run a specific test file:
```bash
pytest tests/test_edge_cases.py -v
```

---

## Glossary

| Term | Meaning |
|------|---------|
| Deal | A startup client we're helping raise capital for |
| Deal ID | Unique identifier for each client deal (e.g., `deal_001`) |
| Tear sheet | 1-2 page investor summary of the company |
| PPM | Private Placement Memorandum — legal document for private raises |
| NDA | Non-Disclosure Agreement — must be signed before sharing the pitch deck |
| TAM/SAM/SOM | Total/Serviceable/Obtainable Market — market size metrics |
| FCFF | Free Cash Flow to Firm — key financial metric |
| WACC | Weighted Average Cost of Capital — valuation input |
| MeetAlfred | LinkedIn automation tool for connection request campaigns |
| Sales Navigator | LinkedIn's premium search tool for finding investor contacts |
| Apollo.io | Contact data enrichment platform (email, phone, LinkedIn) |
| Alignable | Business networking platform with strong investor community |
| Box.com | Cloud storage for deal data rooms and investor materials |
| Sequoia review | AI-powered grading of materials from a top-tier VC perspective |
| Checkpoint | Auto-saved progress file — allows the system to resume after a crash |
| Phil | Philip — Millenia Ventures principal who handles GT Securities and approvals |
| Das | Team member who executes MeetAlfred campaigns and tech tasks |
| Dock Walls | Legal partner for PPM, subscription agreements, and wire verification |
| Response rate | % of investors contacted who replied (target: ≥ 20%) |
| Meeting conversion | % of responses that convert to a scheduled meeting (target: ≥ 5%) |
| Broker-dealer portal | Required for raises ≥ $5M — platforms like DealMaker, Republic, StartEngine |

---

## Getting Help

If something isn't working:
1. Check the log files in `outputs/[deal_id]/logs/` — they show exactly what happened at each step
2. Check `outputs/[deal_id]/checkpoint.json` to see where the system last successfully ran
3. Run `python main.py status --deal [deal_file]` to see the full pipeline status

If you need to start a deal completely fresh:
1. Delete the `outputs/[deal_id]/` folder
2. Run the pipeline again from step 1

---

*Millenia Ventures Capital Formation Automation System*
