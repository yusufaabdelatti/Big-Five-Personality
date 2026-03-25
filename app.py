import streamlit as st
import requests
import smtplib
import os
import datetime
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION — edit this section only
# ══════════════════════════════════════════════════════════════

GMAIL_ADDRESS   = "Wijdan.psyc@gmail.com"
GMAIL_PASSWORD  = "rias eeul lyuu stce"
THERAPIST_EMAIL = "Wijdan.psyc@gmail.com"

LOGO_FILE = "logo.png"   # ← name your logo file exactly this in GitHub

# ══════════════════════════════════════════════════════════════
#  BIG FIVE QUESTIONS  (50 items, scale 1–5)
# ══════════════════════════════════════════════════════════════

BFPT_QUESTIONS = [
    {"id": 1,  "text": "Am the life of the party."},
    {"id": 2,  "text": "Feel little concern for others."},
    {"id": 3,  "text": "Am always prepared."},
    {"id": 4,  "text": "Get stressed out easily."},
    {"id": 5,  "text": "Have a rich vocabulary."},
    {"id": 6,  "text": "Don't talk a lot."},
    {"id": 7,  "text": "Am interested in people."},
    {"id": 8,  "text": "Leave my belongings around."},
    {"id": 9,  "text": "Am relaxed most of the time."},
    {"id": 10, "text": "Have difficulty understanding abstract ideas."},
    {"id": 11, "text": "Feel comfortable around people."},
    {"id": 12, "text": "Insult people."},
    {"id": 13, "text": "Pay attention to details."},
    {"id": 14, "text": "Worry about things."},
    {"id": 15, "text": "Have a vivid imagination."},
    {"id": 16, "text": "Keep in the background."},
    {"id": 17, "text": "Sympathize with others' feelings."},
    {"id": 18, "text": "Make a mess of things."},
    {"id": 19, "text": "Seldom feel blue."},
    {"id": 20, "text": "Am not interested in abstract ideas."},
    {"id": 21, "text": "Start conversations."},
    {"id": 22, "text": "Am not interested in other people's problems."},
    {"id": 23, "text": "Get chores done right away."},
    {"id": 24, "text": "Am easily disturbed."},
    {"id": 25, "text": "Have excellent ideas."},
    {"id": 26, "text": "Have little to say."},
    {"id": 27, "text": "Have a soft heart."},
    {"id": 28, "text": "Often forget to put things back in their proper place."},
    {"id": 29, "text": "Get upset easily."},
    {"id": 30, "text": "Do not have a good imagination."},
    {"id": 31, "text": "Talk to a lot of different people at parties."},
    {"id": 32, "text": "Am not really interested in others."},
    {"id": 33, "text": "Like order."},
    {"id": 34, "text": "Change my mood a lot."},
    {"id": 35, "text": "Am quick to understand things."},
    {"id": 36, "text": "Don't like to draw attention to myself."},
    {"id": 37, "text": "Take time out for others."},
    {"id": 38, "text": "Shirk my duties."},
    {"id": 39, "text": "Have frequent mood swings."},
    {"id": 40, "text": "Use difficult words."},
    {"id": 41, "text": "Don't mind being the center of attention."},
    {"id": 42, "text": "Feel others' emotions."},
    {"id": 43, "text": "Follow a schedule."},
    {"id": 44, "text": "Get irritated easily."},
    {"id": 45, "text": "Spend time reflecting on things."},
    {"id": 46, "text": "Am quiet around strangers."},
    {"id": 47, "text": "Make people feel at ease."},
    {"id": 48, "text": "Am exacting in my work."},
    {"id": 49, "text": "Often feel blue."},
    {"id": 50, "text": "Am full of ideas."},
]

SCALE_OPTIONS = {
    1: "1 — Disagree",
    2: "2 — Slightly disagree",
    3: "3 — Neutral",
    4: "4 — Slightly agree",
    5: "5 — Agree",
}

# ══════════════════════════════════════════════════════════════
#  SCORING
# ══════════════════════════════════════════════════════════════

def calculate_scores(r: dict) -> dict:
    """
    r = {item_id: score (1-5)}
    Returns dict with E, A, C, N, O scores (each 0-40).
    """
    E = 20 + r[1]  - r[6]  + r[11] - r[16] + r[21] - r[26] + r[31] - r[36] + r[41] - r[46]
    A = 14 - r[2]  + r[7]  - r[12] + r[17]  - r[22] + r[27] - r[32] + r[37] + r[42] + r[47]
    C = 14 + r[3]  - r[8]  + r[13] - r[18]  + r[23] - r[28] + r[33] - r[38] + r[43] + r[48]
    N = 38 - r[4]  + r[9]  - r[14] + r[19]  - r[24] - r[29] - r[34] - r[39] - r[44] - r[49]
    O =  8 + r[5]  - r[10] + r[15] - r[20]  + r[25] - r[30] + r[35] + r[40] + r[45] + r[50]
    return {"E": E, "A": A, "C": C, "N": N, "O": O}

def get_level(score: int) -> str:
    if score <= 13:   return "Low"
    elif score <= 26: return "Moderate"
    else:             return "High"

TRAIT_META = {
    "E": {
        "name": "Extroversion",
        "color": "#4A90D9",
        "low":  "Tends to be reserved, reflective, and prefers working independently or in smaller settings.",
        "moderate": "Shows a balance between social engagement and preference for solitude depending on context.",
        "high": "Highly social, energetic, and seeks stimulation from the external environment and others.",
    },
    "A": {
        "name": "Agreeableness",
        "color": "#5CB85C",
        "low":  "Tends to be direct, competitive, and prioritizes personal goals over group harmony.",
        "moderate": "Can be cooperative and accommodating while still asserting personal needs when necessary.",
        "high": "Warm, empathic, and highly cooperative; tends to prioritize others' needs and social harmony.",
    },
    "C": {
        "name": "Conscientiousness",
        "color": "#F0AD4E",
        "low":  "May be flexible and spontaneous but can struggle with organization, follow-through, and structure.",
        "moderate": "Generally reliable and organized, with some variability in task completion and self-discipline.",
        "high": "Highly disciplined, organized, and goal-directed; demonstrates strong work ethic and attention to detail.",
    },
    "N": {
        "name": "Neuroticism",
        "color": "#D9534F",
        "low":  "Emotionally stable, calm under pressure, and less reactive to stressors.",
        "moderate": "Experiences moderate emotional reactivity; may feel stress in challenging situations but generally copes adequately.",
        "high": "Prone to emotional distress, mood fluctuations, and heightened stress reactivity; may experience anxiety, irritability, or low mood.",
    },
    "O": {
        "name": "Openness to Experience",
        "color": "#9B59B6",
        "low":  "Prefers routine, concrete thinking, and familiar environments; practical and grounded.",
        "moderate": "Shows curiosity and creativity in some domains while preferring structure and predictability in others.",
        "high": "Highly imaginative, intellectually curious, and drawn to novel ideas, creative pursuits, and abstract thinking.",
    },
}

# ══════════════════════════════════════════════════════════════
#  GROQ REPORT GENERATION
# ══════════════════════════════════════════════════════════════

def generate_report(client_name, scores, responses):
    trait_lines = "\n".join(
        f"  {TRAIT_META[t]['name']} ({t}): {scores[t]}/40 — {get_level(scores[t])}"
        for t in ["E", "A", "C", "N", "O"]
    )

    prompt = f"""You are a licensed clinical psychologist writing a confidential professional personality assessment report.

CLIENT: {client_name}
ASSESSMENT: Big Five Personality Test (BFPT) — 50 items, scale 1–5 per item, scores 0–40 per trait

TRAIT SCORES:
{trait_lines}

SCORE INTERPRETATION GUIDE:
- 0–13: Low  |  14–26: Moderate  |  27–40: High

TRAIT DESCRIPTIONS:
- Extroversion (E): Seeking fulfillment from external sources/community. High = very social; Low = prefers independent work.
- Agreeableness (A): Adjusting behavior to suit others. High = polite, people-oriented; Low = direct, tells it like it is.
- Conscientiousness (C): Being honest and hardworking. High = rule-following, organized; Low = flexible, may be messy.
- Neuroticism (N): Emotional reactivity. High = mood swings, stress-prone; Low = emotionally stable.
- Openness to Experience (O): Intellectual curiosity and novelty-seeking. High = imaginative, creative; Low = practical, routine-oriented.

---
Write a full professional personality assessment report with the following sections:

1. ASSESSMENT OVERVIEW
   - Instrument used, purpose, administration context.

2. PERSONALITY PROFILE SUMMARY
   - Narrative summary of the client's overall Big Five profile. Reference all five scores.
   - Note dominant traits and any clinically notable patterns or contrasts between traits.

3. TRAIT-BY-TRAIT ANALYSIS
   For each of the five traits, write a clinical paragraph that:
   - States the score and level (Low / Moderate / High)
   - Interprets what this means for this specific client
   - Notes any implications for behavior, relationships, work, or wellbeing

4. TRAIT INTERACTIONS & CLINICAL PATTERNS
   - Discuss how the combination of scores creates a coherent personality picture.
   - Highlight any notable interactions (e.g., high N + low E, high C + high A, etc.)

5. STRENGTHS & GROWTH AREAS
   - Based on the profile, identify key psychological strengths.
   - Identify areas that may benefit from therapeutic attention or development.

6. THERAPEUTIC & PRACTICAL IMPLICATIONS
   - Evidence-based suggestions for therapy approach, communication style, and practical recommendations.
   - How this profile may affect the therapeutic relationship.

7. SUMMARY
   - One concise paragraph suitable for clinical records, as per BFPT documentation format:
     "According to the Big Five Personality Test (BFPT), [client] self-reports [describe each trait with score]."

Use formal clinical language. Be specific to the scores — avoid generic personality descriptions. Ready for placement in a clinical file."""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from Streamlit secrets.")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2500,
            "temperature": 0.4,
        },
        timeout=60,
    )

    if not response.ok:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise Exception(f"Groq API error {response.status_code}: {error_detail}")

    return response.json()["choices"][0]["message"]["content"].strip()

# ══════════════════════════════════════════════════════════════
#  PDF CREATION
# ══════════════════════════════════════════════════════════════

def create_pdf_report(path, client_name, scores, report_text, timestamp):
    DARK   = colors.HexColor("#1C1917")
    WARM   = colors.HexColor("#6B5B45")
    LIGHT  = colors.HexColor("#F7F4F0")
    BORDER = colors.HexColor("#DDD5C8")
    WHITE  = colors.white

    TRAIT_COLORS = {
        "E": colors.HexColor("#4A90D9"),
        "A": colors.HexColor("#5CB85C"),
        "C": colors.HexColor("#F0AD4E"),
        "N": colors.HexColor("#D9534F"),
        "O": colors.HexColor("#9B59B6"),
    }

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    title_s   = ParagraphStyle("T",  fontName="Times-Roman",      fontSize=20, textColor=DARK,  alignment=TA_CENTER, spaceAfter=3)
    sub_s     = ParagraphStyle("S",  fontName="Times-Italic",      fontSize=10, textColor=WARM,  alignment=TA_CENTER, spaceAfter=2)
    meta_s    = ParagraphStyle("M",  fontName="Helvetica",         fontSize=8,  textColor=WARM,  alignment=TA_CENTER, spaceAfter=12)
    section_s = ParagraphStyle("Se", fontName="Helvetica-Bold",    fontSize=10, textColor=WARM,  spaceBefore=12, spaceAfter=4)
    body_s    = ParagraphStyle("B",  fontName="Helvetica",         fontSize=9.5,textColor=DARK,  leading=15, spaceAfter=5)
    small_s   = ParagraphStyle("Sm", fontName="Helvetica",         fontSize=8.5,textColor=WARM,  leading=13)
    footer_s  = ParagraphStyle("Ft", fontName="Helvetica-Oblique", fontSize=7.5,textColor=WARM,  leading=11, alignment=TA_CENTER)

    story = []
    date_str = datetime.datetime.now().strftime("%B %d, %Y  |  %H:%M")

    # Logo
    if os.path.exists(LOGO_FILE):
        try:
            logo = RLImage(LOGO_FILE, width=4*cm, height=2*cm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    story.append(Paragraph("Big Five Personality Test", title_s))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Clinical Personality Assessment Report", sub_s))
    story.append(Paragraph(f"CONFIDENTIAL  ·  {date_str}", meta_s))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.3*cm))

    # Client info
    sev_s = ParagraphStyle("SL", fontName="Helvetica-Bold", fontSize=9.5, textColor=DARK)
    info_data = [
        [Paragraph("<b>Client</b>", small_s), Paragraph(client_name, body_s),
         Paragraph("<b>Assessment</b>", small_s), Paragraph("BFPT (50 items)", body_s)],
        [Paragraph("<b>Date</b>", small_s), Paragraph(date_str, body_s),
         Paragraph("<b>Score Range</b>", small_s), Paragraph("0 – 40 per trait", body_s)],
    ]
    it = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), LIGHT),
        ("BOX",        (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story.append(it)
    story.append(Spacer(1, 0.4*cm))

    # Trait scores table
    story.append(Paragraph("TRAIT SCORE SUMMARY", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    score_header = [
        Paragraph("<b>Trait</b>", small_s),
        Paragraph("<b>Score</b>", small_s),
        Paragraph("<b>Level</b>", small_s),
        Paragraph("<b>Range Bar (0 ──────────────── 40)</b>", small_s),
    ]
    score_rows = [score_header]
    for t in ["E", "A", "C", "N", "O"]:
        sc   = scores[t]
        lvl  = get_level(sc)
        meta = TRAIT_META[t]
        tc   = TRAIT_COLORS[t]
        bar_filled = int((sc / 40) * 28)
        bar = "█" * bar_filled + "░" * (28 - bar_filled)
        score_rows.append([
            Paragraph(f"<b>{meta['name']} ({t})</b>",
                      ParagraphStyle("TN", fontName="Helvetica-Bold", fontSize=9, textColor=tc)),
            Paragraph(f"<b>{sc}/40</b>",
                      ParagraphStyle("SC", fontName="Helvetica-Bold", fontSize=9, textColor=tc, alignment=TA_CENTER)),
            Paragraph(lvl,
                      ParagraphStyle("LV", fontName="Helvetica", fontSize=9, textColor=DARK, alignment=TA_CENTER)),
            Paragraph(f'<font color="#{tc.hexval()[2:]}">{bar}</font>',
                      ParagraphStyle("BR", fontName="Courier", fontSize=7, textColor=tc)),
        ])

    st_table = Table(score_rows, colWidths=[4.5*cm, 2*cm, 2.5*cm, 8*cm])
    st_styles = [
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#EDE9E3")),
        ("BOX",        (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN", (1,0),(2,-1), "CENTER"),
    ]
    for row_i, t in enumerate(["E", "A", "C", "N", "O"], start=1):
        if row_i % 2 == 0:
            st_styles.append(("BACKGROUND", (0,row_i),(-1,row_i), LIGHT))
    st_table.setStyle(TableStyle(st_styles))
    story.append(st_table)
    story.append(Spacer(1, 0.5*cm))

    # AI report
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("CLINICAL REPORT", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    for line in report_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.18*cm))
        elif line.isupper() or (line.endswith(":") and len(line) < 60):
            story.append(Paragraph(line, section_s))
        else:
            story.append(Paragraph(line, body_s))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This report is strictly confidential and intended solely for the treating clinician. "
        "It is not to be shared with the client or any third party without explicit written consent. "
        "AI-assisted analysis should be reviewed in conjunction with clinical judgment.",
        footer_s
    ))
    doc.build(story)

# ══════════════════════════════════════════════════════════════
#  EMAIL SENDER
# ══════════════════════════════════════════════════════════════

def send_report_email(pdf_path, client_name, scores, filename):
    date_str = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")

    trait_rows = "".join(
        f"<tr><td style='padding:6px 0;color:#6B5B45;width:40%;'>{TRAIT_META[t]['name']} ({t})</td>"
        f"<td><strong style='color:{TRAIT_META[t]['color']};'>{scores[t]}/40 — {get_level(scores[t])}</strong></td></tr>"
        for t in ["E", "A", "C", "N", "O"]
    )

    msg = MIMEMultipart("mixed")
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = THERAPIST_EMAIL
    msg["Subject"] = f"[BFPT Report] {client_name} — {date_str}"

    body_html = f"""
    <html><body style="font-family:Georgia,serif;color:#1C1917;background:#F7F4F0;padding:24px;">
      <div style="max-width:580px;margin:0 auto;background:white;border:1px solid #DDD5C8;border-radius:4px;padding:32px;">
        <h2 style="font-weight:300;font-size:22px;margin-bottom:2px;">Big Five Personality Test</h2>
        <p style="color:#6B5B45;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;margin-top:0;">
          New Assessment Submitted
        </p>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <table style="width:100%;font-size:14px;border-collapse:collapse;">
          <tr>
            <td style="padding:6px 0;color:#6B5B45;width:40%;">Client</td>
            <td><strong>{client_name}</strong></td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B5B45;">Date &amp; Time</td>
            <td>{date_str}</td>
          </tr>
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;color:#6B5B45;margin-bottom:8px;font-weight:bold;">Trait Scores</p>
        <table style="width:100%;font-size:13px;border-collapse:collapse;">
          {trait_rows}
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;line-height:1.6;">The full clinical report is attached as a PDF.</p>
        <p style="font-size:11px;color:#6B5B45;margin-top:20px;font-style:italic;">
          This message is confidential and intended only for the treating clinician.</p>
      </div>
    </body></html>"""

    msg.attach(MIMEText(body_html, "html"))
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, THERAPIST_EMAIL, msg.as_string())

# ══════════════════════════════════════════════════════════════
#  STREAMLIT APP
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Big Five Personality Assessment",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #F7F4F0;
    --white: #FFFFFF;
    --deep: #1C1917;
    --warm: #6B5B45;
    --accent: #8B6F47;
    --border: #DDD5C8;
    --selected: #2D2926;
    --E: #4A90D9;
    --A: #5CB85C;
    --C: #F0AD4E;
    --N: #D9534F;
    --O: #9B59B6;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--deep);
}
.stApp { background-color: var(--bg); }

.page-header {
    text-align: center;
    padding: 2.5rem 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.page-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 400;
    letter-spacing: 0.02em;
    margin-bottom: 0.3rem;
    color: var(--deep);
}
.page-header p {
    color: var(--warm);
    font-size: 0.82rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 400;
}

.trait-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

.question-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.5rem 1.8rem 0.5rem 1.8rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.question-card:hover { border-color: var(--accent); }

.q-number {
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.3rem;
    font-weight: 500;
}
.q-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.08rem;
    color: var(--deep);
    margin-bottom: 1rem;
    line-height: 1.5;
}
.q-stem {
    font-size: 0.8rem;
    color: var(--warm);
    font-style: italic;
    margin-bottom: 0.8rem;
}

div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div { gap: 0.4rem !important; flex-direction: row !important; flex-wrap: wrap !important; }
div[data-testid="stRadio"] > div > label {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    padding: 0.5rem 0.9rem !important;
    cursor: pointer !important;
    font-size: 0.82rem !important;
    color: var(--deep) !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.15s ease !important;
    min-width: 140px !important;
}
div[data-testid="stRadio"] > div > label:hover {
    border-color: var(--accent) !important;
    background: #F0EBE3 !important;
}

.progress-wrap { background: var(--border); border-radius: 2px; height: 3px; margin: 1.5rem 0 0.5rem 0; }
.progress-fill { height: 3px; border-radius: 2px; background: linear-gradient(90deg, var(--warm), var(--accent)); }

.stButton > button {
    background: var(--selected) !important;
    color: var(--bg) !important;
    border: none !important;
    padding: 0.8rem 2.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 2px !important;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: var(--warm) !important; }

.thank-you {
    text-align: center;
    padding: 5rem 2rem;
}
.thank-you h2 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 400;
    margin-bottom: 1rem;
}
.thank-you p {
    color: var(--warm);
    font-size: 0.95rem;
    max-width: 380px;
    margin: 0 auto;
    line-height: 1.8;
}

.section-label {
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--warm);
    font-weight: 500;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}

div[data-testid="stTextInput"] input {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--deep) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Routing ────────────────────────────────────────────────────────────────────
page = st.query_params.get("page", "client")

if page == "admin":
    st.markdown("""
    <div class="page-header">
        <p>Therapist Portal</p>
        <h1>Assessment Reports</h1>
    </div>""", unsafe_allow_html=True)

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("Enter admin password", type="password", placeholder="Password")
        if st.button("Access Portal"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        files = sorted([f for f in os.listdir(reports_dir) if f.endswith(".pdf")], reverse=True)

        if not files:
            st.info("No reports submitted yet.")
        else:
            st.markdown(f"**{len(files)} report(s) on file**")
            for fname in files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 `{fname}`")
                with col2:
                    with open(os.path.join(reports_dir, fname), "rb") as f:
                        st.download_button("Download", data=f, file_name=fname,
                                           mime="application/pdf", key=fname)
        if st.button("Log out"):
            st.session_state.admin_auth = False
            st.rerun()

else:
    # ── CLIENT VIEW ────────────────────────────────────────────────────────────
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.submitted:
        st.markdown("""
        <div class="thank-you">
            <h2>Thank You</h2>
            <p>Your responses have been submitted successfully.<br>
            Your clinician will be in touch with you shortly.</p>
        </div>""", unsafe_allow_html=True)
    else:
        # Logo
        if os.path.exists(LOGO_FILE):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(LOGO_FILE, use_container_width=True)

        st.markdown("""
        <div class="page-header">
            <p>Confidential Personality Assessment</p>
            <h1>Big Five Personality Test</h1>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:0.5rem;line-height:1.8;">
        For each statement below, indicate how much you agree or disagree.<br>
        Begin each statement with <strong>"I…"</strong> and answer based on how you generally are.
        </p>""", unsafe_allow_html=True)

        client_name = st.text_input("Your name (optional)", placeholder="First name or initials")
        st.markdown("<br>", unsafe_allow_html=True)

        responses = {}
        all_answered = True

        for q in BFPT_QUESTIONS:
            qid = q["id"]
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">Question {qid} of 50</div>
                <div class="q-stem">I…</div>
                <div class="q-text">{q['text']}</div>
            </div>""", unsafe_allow_html=True)

            choice = st.radio(
                label=f"q_{qid}",
                options=list(SCALE_OPTIONS.values()),
                index=None,
                key=f"q_{qid}",
                label_visibility="collapsed",
                horizontal=True,
            )

            if choice is None:
                all_answered = False
            else:
                score_val = next(k for k, v in SCALE_OPTIONS.items() if v == choice)
                responses[qid] = score_val

        answered_count = len(responses)
        pct = int((answered_count / 50) * 100)
        st.markdown(f"""
        <div style="text-align:center;font-size:0.78rem;color:#6B5B45;
                    letter-spacing:0.08em;margin-top:1.5rem;">
            {answered_count} of 50 answered
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%"></div>
        </div>""", unsafe_allow_html=True)

        if not all_answered and answered_count > 0:
            st.markdown("""
            <div style="background:#FFF8F0;border-left:3px solid #E07B39;
                        padding:1rem 1.2rem;border-radius:0 4px 4px 0;
                        font-size:0.88rem;color:#7A3D1A;margin:1rem 0;">
                ⚠ Please answer all 50 questions before submitting.
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="text-align:center;padding:2rem 0 3rem 0;">', unsafe_allow_html=True)
        submit = st.button("Submit Assessment", disabled=not all_answered)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit and all_answered:
            with st.spinner("Submitting your responses..."):
                scores = calculate_scores(responses)
                report_text = generate_report(client_name or "Anonymous", scores, responses)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = (client_name or "anonymous").replace(" ", "_").lower()
                filename  = f"BFPT_{safe_name}_{timestamp}.pdf"
                os.makedirs("reports", exist_ok=True)
                pdf_path  = os.path.join("reports", filename)

                create_pdf_report(pdf_path, client_name or "Anonymous", scores, report_text, timestamp)

                try:
                    send_report_email(pdf_path, client_name or "Anonymous", scores, filename)
                except Exception as e:
                    st.warning(f"Report saved but email failed: {e}")

                st.session_state.submitted = True
                st.rerun()
