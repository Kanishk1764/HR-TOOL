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
Raw Data â”€â”€â–º [Pipeline] â”€â”€â–º Output
                â”‚              â”‚
                â–¼              â–¼
     [Tracing & Telemetry]   [Offline & Online Eval Suite]
             (Logs)           â”œâ”€â”€ 1. Deterministic Contract Tests
                              â”œâ”€â”€ 2. Golden Benchmark Dataset
                              â”œâ”€â”€ 3. LLM-as-a-Judge
                              â””â”€â”€ 4. Production Canary / Shadow Routing
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

