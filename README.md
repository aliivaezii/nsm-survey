# Selecting the North Star — NSM Survey

> Academic survey supporting the paper:
> **"Selecting the North Star: A Mixed-Methods Decision Framework for Growth Hacking Metric Selection"**
> University of Turin · Politecnico di Torino · 2026

---

## About

This tool collects data from growth professionals to support a mixed-methods study combining the **Best-Worst Method (BWM)** and **TOPSIS** for North Star Metric selection. The survey covers organizational demographics, NSM and OKR adoption, pairwise criteria weighting, and candidate metric evaluation.

## Research Team

| Role | Name | Institution |
|---|---|---|
| Lead Researcher & Developer | **Ali Vaezi** | Politecnico di Torino |
| Research Collaborator | Arman Karimian | University of Turin |
| Supervisor | Prof. Gabriele Santoro | University of Turin |

## Stack

| Layer | Technology |
|---|---|
| Frontend | Single-file HTML · CSS · Vanilla JS |
| Database | Supabase (free tier) |
| Hosting | Vercel (free tier) |

## Setup

### Step 1 — Supabase
1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project and wait for it to initialize
3. Go to **SQL Editor** and run the SQL schema found in the comment block at the very top of `index.html`
4. Go to **Project Settings → API** and copy your **Project URL** and **anon/public key**

### Step 2 — Configure the app

Open `index.html` and find the `CONFIG` block near the top of the script tag. Replace the placeholder values:

```js
const CONFIG = {
  SUPABASE_URL: 'https://your-project-ref.supabase.co',
  SUPABASE_ANON_KEY: 'your-anon-public-key-here',
};
```

### Step 3 — Deploy to Vercel
1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import `aliivaezii/nsm-survey`
3. Leave all settings at default → click Deploy
4. Your live survey link will be: `https://nsm-survey.vercel.app`

### Step 4 — Share the link

Send the Vercel URL to respondents. Every submission is saved automatically to your Supabase table.

## Export Data

**Option A — Supabase Dashboard:**
Go to Table Editor → `survey_responses` → Export CSV

**Option B — Python:**
```python
import pandas as pd
df = pd.read_csv('responses.csv')
```

**Option C — R:**
```r
df <- read.csv('responses.csv')
```

## Topics

`growth-hacking` `north-star-metric` `NSM` `best-worst-method` `TOPSIS` `MCDM` `academic-survey` `startup` `OKR` `decision-framework` `mixed-methods` `supabase` `vercel`

---

Built by **Ali Vaezi** · [github.com/aliivaezii](https://github.com/aliivaezii)
