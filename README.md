# Resume Intelligence & Senior Java Vacancy Matcher

Precision resume data extraction, deterministic skill duration interval calculation, and JD-anchored Knowledge Graph transferability matcher.

---

## 🏗️ Project Architecture

```
HR TASK/
├── assests/                    # Raw input resumes (.pdf, .docx)
├── Vacancy details.txt         # Senior Software Engineer – Java Backend JD
├── resumeParsingTask.html      # Technical assessment specification
│
├── backend/                    # Python Backend (FastAPI)
│   ├── app/
│   │   ├── models/schemas.py   # Strict Pydantic models (Roles, Projects, SkillClaims, SkillSummary)
│   │   ├── parsers/
│   │   │   ├── pdf_parser.py   # Catch 1: Two-column / block-aware PyMuPDF layout extractor
│   │   │   ├── docx_parser.py  # python-docx reader
│   │   │   └── vacancy_parser.py # Reads Vacancy details.txt
│   │   ├── engine/
│   │   │   ├── interval_engine.py  # Catch 2 & 4: Interval union math & duration status rules
│   │   │   ├── quote_verifier.py   # Catch 3: Anti-hallucination exact-quote verifier
│   │   │   ├── knowledge_graph.py  # JD-driven tech transferability graph (C -> C++, Stripe -> Razorpay)
│   │   │   └── scoring_engine.py   # Direct & Transferable candidate match scorer
│   │   ├── llm/
│   │   │   ├── prompts.py      # Maximum packed batch prompts with injection defense
│   │   │   ├── client.py       # LLM client (gpt-5.6-luna / fallback deterministic extractor)
│   │   │   └── batch_worker.py # Economic batch dispatcher (Default: 10 resumes, option for all)
│   │   └── main.py             # FastAPI REST endpoints & file exporters
│   ├── tests/
│   │   └── test_interval_engine.py # Pytest suite matching Section 5 minimum test cases
│   ├── outputs/                # Generated batch deliverables (results.jsonl, skills.csv)
│   └── requirements.txt
│
└── frontend/                   # Minimalist Next.js Dashboard
    ├── src/
    │   ├── app/                # App Router (page.tsx, layout.tsx, globals.css)
    │   ├── components/
    │   │   ├── VacancyHeader.tsx       # JD summary & experience requirements
    │   │   ├── BatchControlBar.tsx     # Cost-control mode (Default: 10 fixed resumes)
    │   │   ├── KnowledgeGraphCard.tsx  # Interactive HR toggles for skill proxies
    │   │   ├── CandidateTable.tsx      # Ranked leaderboard (Direct % vs Transferable %)
    │   │   └── TraceabilityDrawer.tsx  # Verifiable quote cards & interval math audit
    │   └── lib/
    │       ├── api.ts          # Backend API client
    │       └── types.ts        # TypeScript interfaces
    └── package.json
```

---

## 🚀 Quick Start Guide

### 1. Start the Python Backend (Port 8000)
From the root directory, simply run:
```powershell
python main.py
```
*(Or from inside `backend/`: `python main.py`)*
- Server URL: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### 2. Start the Next.js Frontend (Port 3000)
In a separate terminal:
```powershell
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Run Automated Tests
Verifies all 6 minimum test cases from Section 5 of `resumeParsingTask.html`:
```powershell
python -m pytest backend/tests/test_interval_engine.py -v
```

---

## 💡 Key Design Highlights

1. **Catch 1 (Layout Chaos):** Two-column column-block sorting via `PyMuPDF` prevents sidebar text from bleeding into employment dates.
2. **Catch 2 & 4 (Math & Ambiguity):** Disjoint interval union logic calculates discrete calendar months ($\bigcup [start_i, end_i]$) and divides by 12. AI is strictly forbidden from doing math.
3. **Catch 3 (Prompt Injections & Fakes):** Every claim requires a `supportingText` quotation verified as an exact substring in the source document.
4. **JD-Driven Knowledge Graph:** Allows adjacent foundation skills (e.g., candidate with 3 yrs `C` gets transferable credit for `C++`, or `Stripe` for `Razorpay`). HR can toggle any proxy rule directly from the UI with real-time recalculation.
5. **Economic Cost Control:** Defaults strictly to **10 fixed resumes** to protect API quota, with batch prompt packing rather than 1-by-1 single calls.
