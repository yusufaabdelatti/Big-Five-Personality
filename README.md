# Big Five Personality Test — Deployment Guide

A professional, confidential Big Five Personality Test app built with Streamlit + Groq AI.

---

## What It Does

| Who | Experience |
|-----|-----------|
| **Client** | Answers 50 personality statements on a 1–5 scale → clicks Submit → sees "Thank you" only |
| **You (therapist)** | Receive a full PDF clinical personality report by email instantly |
| **You (admin view)** | Log in at `/?page=admin` → browse & download all reports |

---

## Scoring Logic (BFPT)

| Trait | Formula |
|-------|---------|
| **Extroversion (E)** | 20 + Q1 − Q6 + Q11 − Q16 + Q21 − Q26 + Q31 − Q36 + Q41 − Q46 |
| **Agreeableness (A)** | 14 − Q2 + Q7 − Q12 + Q17 − Q22 + Q27 − Q32 + Q37 + Q42 + Q47 |
| **Conscientiousness (C)** | 14 + Q3 − Q8 + Q13 − Q18 + Q23 − Q28 + Q33 − Q38 + Q43 + Q48 |
| **Neuroticism (N)** | 38 − Q4 + Q9 − Q14 + Q19 − Q24 − Q29 − Q34 − Q39 − Q44 − Q49 |
| **Openness (O)** | 8 + Q5 − Q10 + Q15 − Q20 + Q25 − Q30 + Q35 + Q40 + Q45 + Q50 |

Score range: 0–40 per trait. Low = 0–13 | Moderate = 14–26 | High = 27–40

---

## File Structure

```
your-repo/
├── app.py            ← Everything in one file
├── requirements.txt  ← 3 dependencies
├── README.md         ← This file
└── logo.png          ← Your logo (name it exactly this)
```

---

## Logo

Name your logo file exactly: **`logo.png`**
Place it in the root of your GitHub repo alongside `app.py`.
It will appear at the top of the client form and on every PDF report.

---

## Setup Steps

### 1. Streamlit Cloud Secrets

In your Streamlit Cloud dashboard → Settings → Secrets:

```toml
GROQ_API_KEY   = "gsk_..."
ADMIN_PASSWORD = "your_chosen_password"
```

### 2. Deploy

- Connect GitHub repo to Streamlit Cloud
- Main file: `app.py`
- Push `logo.png` to the repo root

### 3. Admin Portal

Visit: `https://your-app.streamlit.app/?page=admin`

---

## PDF Report Sections

1. Assessment Overview
2. Personality Profile Summary
3. Trait-by-Trait Analysis (E, A, C, N, O)
4. Trait Interactions & Clinical Patterns
5. Strengths & Growth Areas
6. Therapeutic & Practical Implications
7. Summary (in standard BFPT documentation format)
