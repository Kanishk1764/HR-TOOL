# Enterprise AI Architecture: Evaluation, Prompt Engineering, & Observability Playbook

---

## 1. Executive Summary & Motivating Case Study

When using AI to extract structured facts from dense documents like resumes, simple prompts often fail silently. They drop key skills, miss dates, and lead to false decisions.

### Case Study: Candidate Abhijit Chaudhari
During an end-to-end evaluation run against the candidate's raw resume, our pipeline produced critical false negatives that falsely disqualified an 8-year senior engineer from a 5-year requirement:

| Target Entity | Ground-Truth in Resume Text | Model Extracted Output | Failure Impact |
| :--- | :--- | :--- | :--- |
| **Java Experience** | **8.0 Years** (Used at Cognizant from 2022 to Present and Capgemini from 2018 to 2022 with Spring Boot). | **4.33 Years** (Only Cognizant credited). | Flagged as not meeting Java experience and disqualified. |
| **Frameworks & DB** | Spring Cloud, JPA, Hibernate, SQL Optimization, Stored Procedures, Payment Flows. | Only extracted REST, Spring Security, Docker, Swagger. | Dropped Hibernate, JPA, and SQL despite being in the same sentence. |
| **Project 3 Dates** | Migration of 50+ services over 18 months under Capgemini (2018 to 2022). | Start and end dates both set to null. | Undated intervals got ignored during total experience calculation. |

---

## 2. Root Cause Analysis: The 4 Evaluation Layers Explained Simply

To understand why an AI output is wrong, we divide checks into four plain-sense layers from basic formatting up to real-world logic:

* **Layer 1: Basic Structure & Dates (Formatting Rules)**  
  Checks if the data makes chronological sense. For example, an end date cannot happen before a start date, and a project done at a company must happen within the years the candidate actually worked there.
* **Layer 2: Truth in Document (No Fabrications)**  
  Checks if every single claim extracted by the AI actually exists in the original text. If the AI claims a candidate used Docker, that exact mention must exist in the resume, preventing the AI from making things up.
* **Layer 3: Completeness (Did the AI Miss Anything?)**  
  Checks if the AI left out important information. For example, if a resume sentence explicitly lists Spring Boot, Hibernate, and SQL, but the AI only extracts Spring Boot and forgets the rest, it fails this layer.
* **Layer 4: Real-World Common Sense (Technical Logic)**  
  Checks if the output respects real-world engineering reality. For example, anyone building enterprise microservices with Spring Boot is fundamentally working in Java. If the AI credits Spring Boot but claims the candidate has zero Java for that role, it fails this layer.

---

## 3. How Top AI Architects Evaluate LLMs in Production

Enterprise AI companies never rely on manual testers or end users to discover bugs. They run a continuous evaluation system with four complementary testing approaches:

```
Raw Data ──► [Pipeline] ──► Output
                │              │
                ▼              ▼
     [Tracing & Telemetry]   [Offline & Online Eval Suite]
             (Logs)           ├── 1. Deterministic Contract Tests
                              ├── 2. Golden Benchmark Dataset
                              ├── 3. LLM-as-a-Judge
                              └── 4. Production Canary / Shadow Routing
```

* **Deterministic Contract Tests:** Simple code rules that instantly check if dates are valid, numbers make sense, and required fields exist without needing an AI call.
* **Golden Benchmark Dataset:** A hand-verified collection of real sample resumes with correct answers used to test if your AI pipeline still produces accurate outputs.
* **LLM-as-a-Judge:** A second, highly capable AI model that reviews the first AI's extracted results against the original document to grade accuracy and spot errors.
* **Production Canary / Shadow Routing:** Running the new AI version quietly on a small percentage of live users or in the background to test stability before full release.

### 3.1 Do Production Teams Actually Create Golden Datasets?

Yes, 100%. A Golden Dataset is non-negotiable in production AI. Without one, you are driving blindfolded: if you tweak your prompt to fix candidate A, you might silently break candidates B, C, and D without knowing it.

#### The 80/20 Golden Dataset Strategy:
Instead of annotating thousands of files, enterprise teams curate 30 to 50 high-variance edge cases:
* **Standard Clean File:** Standard single-column resume with clear calendar dates.
* **Multi-Column Layout:** Layouts with sidebars, icons, and non-standard visual blocks.
* **Overlapping Roles:** Freelance or consulting work happening at the same time as full-time jobs.
* **Relative Timelines:** Experience described in words like 18 months rather than explicit calendar months.
* **Adversarial Resumes:** Keyword-stuffed resumes or attempts to trick the parser.

#### Automated CI/CD Regression Gate:
Whenever an engineer updates a prompt or upgrades a model, an automated test runs against these 30 to 50 verified resumes. If accuracy or skill recall drops by even 2%, the update is automatically blocked from production.

### 3.2 The Three Types of Production Evals

| Eval Type | How It Works | Cost / Speed | What It Catches |
| :--- | :--- | :--- | :--- |
| **Deterministic Invariant Checks** | Unit-test code checking logical contracts (e.g. start date <= end date). | Free, instant | Hallucinations, invalid dates, and broken formats. |
| **Golden Benchmark (Precision/Recall)** | Compares AI output JSON with human-verified correct answers. | Fast to medium (runs in CI) | Regressions, dropped skills, and missed sections. |
| **LLM-as-a-Judge (Eval Model)** | A strong model reviews the extraction against the original document text. | API cost per run | Subtle misunderstandings and summary accuracy. |

---

## 4. The 6-Step Engineering Loop to Fix & Optimize Prompts

When an AI prompt underperforms, scalable engineering follows a structured, scientific improvement loop:

```
[1. Error Taxonomy] ──► [2. Baseline Score] ──► [3. Prompt Refactoring]
                                                        │
[6. Guardrail Fallback] ◄── [5. A/B Regression Delta] ◄── [4. Scratchpad/CoT]
```

### Step 1: Create an Error Taxonomy (Name the Exact Failure)
Classify the exact failure before editing any text:
* **Entity Recall Drop:** Model skipped technologies inside sentences.
* **Context Over-Filtering:** Prompt was too strict with verbatim words, dropping implied skills like Java.
* **Temporal Confusion:** Model left dates null on child projects.

### Step 2: Freeze a Prompt Eval Test Set (5 to 10 Hard Cases)
Run the current prompt against 5 to 10 difficult resumes and calculate the initial baseline score:
Baseline Recall equals Correct Skills Extracted divided by Total Skills Present in Text.

### Step 3: Refactor the Prompt Structure (The Production Blueprint)
A production prompt must have clear sections:
1. **Role & Objective:** Explicit statement of the extraction goal.
2. **Definitions:** Clear definition of what counts as a skill or claim.
3. **Extraction Policies:** Explicit instructions to extract every mentioned technology without skipping, to infer base languages when frameworks are used, and to inherit dates for nested projects.
4. **Few-Shot Examples:** One or two concrete examples showing raw input text and the ideal structured result.
5. **Output Format:** Strict definition of the required format.

### Step 4: Add a Scratchpad or Pre-Thinking Directive
Instruct the model to first write down a rough list of all detected tools, check for missing items, and verify parent languages in a temporary thinking section before it outputs the final structured data. Because language models generate words step-by-step, forcing them to review the facts first helps them remember all details when producing the final response.

### Step 5: Run A/B Delta Evaluation
Run the updated prompt on the exact same test files and compare the numbers side-by-side:

| Metric | Current Prompt | Updated Prompt | Result |
| :--- | :--- | :--- | :--- |
| **Abhijit Skills Extracted** | 9 skills | 17 skills (Hibernate, JPA, SQL included) | +88% Recall |
| **Java Experience Duration** | 4.33 years | 8.0 years (Capgemini credited) | Fixed |
| **Project 3 Dates** | null | 2018-10 to 2022-07 | Fixed |
| **Format Errors** | 3 errors | 0 errors | Passed |

### Step 6: Decide Prompt Tasks vs Deterministic Code Tasks
* **Let the Prompt do:** Reading language, identifying tools, and matching sentences.
* **Let Code do:** Calculating month durations, filling missing project dates from the main job dates, and checking formatting rules.

---

## 5. Architectural Redesign: The 3-Stage Pipeline

Instead of asking a single prompt to do everything at once, robust systems divide the work into three dedicated steps:

```
[Raw PDF Text]
      │
      ▼
┌──────────────────────────────────────────────┐
│ Stage 1: Structural Chunking & Role Tagger   │  <── Extracts Timeline & Section Graph
└──────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────┐
│ Stage 2: Parallel Deep Entity Extraction     │  <── Extracts ALL skills per bullet
└──────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────┐
│ Stage 3: Deterministic Ontology Enrichment   │  <── Python Logic (Zero Tokens)
│          & Parent-Child Date Propagation     │      Inherits dates & parent skills
└──────────────────────────────────────────────┘
      │
      ▼
[Final Verified JSON]
```

1. **Stage 1 (Structure):** Identifies company names, job titles, and calendar boundaries.
2. **Stage 2 (Entity Extraction):** Reads each bullet point and extracts every mentioned framework and tool.
3. **Stage 3 (Deterministic Code Enrichment):** Standard Python code automatically passes the job's dates down to any undated sub-projects and adds parent languages (such as linking Java whenever Spring Boot is found) at zero token cost.

---

## 6. Observability, Tracing, & Debugging

When building any data processing pipeline with AI, you need full visibility into what happened behind the scenes whenever an output looks wrong.

### How to Track and Log LLM Operations
Every time your application calls an AI model, your system should automatically record three pieces of information into a log file or database:
1. **The Exact Input:** The complete prompt, system instructions, and raw document text sent to the model.
2. **The Model's Reasoning Steps:** When using reasoning-capable models, capture the internal thinking steps or intermediate scratchpad notes where the model analyzed the problem.
3. **The Raw Output:** The exact text and structure returned by the model before any cleanup was performed.

By saving these records with a unique tracking identifier for every request, you never have to guess why a skill was missed. You can simply look up the log, read the model's intermediate thoughts, and immediately see whether the issue was caused by poor document text, an incomplete prompt instruction, or a parsing mistake.

### Tooling Options
* **Local JSONL or Database Logs:** A simple, self-contained solution where your own backend code appends each request, input, thinking step, and output directly into local log files or a database table. It has zero external dependencies and zero added cost.
* **Langfuse / Arize Phoenix:** Popular open-source platforms that you can host on your own servers. They provide a visual web dashboard where team members can search requests, view full conversation histories, inspect latency, and monitor error rates.
* **LangSmith / Helicone:** Managed cloud platforms designed for enterprise teams that provide automated logging, cost tracking, token usage alerts, and visual comparison tools for prompt updates.
