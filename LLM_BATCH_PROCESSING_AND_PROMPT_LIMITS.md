# LLM Batch Processing, Token Limits, & Prompt Engineering Guide

---

## Part 1: Demystifying LLM Batch Processing (How Batch APIs Actually Work)

Batch API calling works completely differently from standard real-time API calls.

### 1. Real-Time API vs. Batch API

* **Real-Time API (Synchronous):**  
  You send 1 prompt $\to$ your application freezes and waits 2 to 5 seconds $\to$ the model responds. If your network disconnects or rates spike, the call fails. You pay 100% full price.
* **Batch API (Asynchronous):**  
  You bundle hundreds or thousands of prompts into a single file (typically `.jsonl`), upload it to the provider (OpenAI, Anthropic, or Google), and disconnect. The provider processes them on their idle GPU capacity over the next 24 hours. When finished, you download the results.  
  * **Primary Benefits:** You get an automatic **50% discount on API costs** and bypass real-time rate limits.

---

### 2. Is Batch Dependent on Size or Tokens? What is the Max Batch Size?

**A batch is bounded by BOTH (a file size limit, a request count limit, and an enqueued token limit), whichever limit is reached first.**

Every major AI provider sets hard limits per batch:

| Provider | Max Requests per Batch | Max File Size | Total Enqueued Token Limit | Processing Window |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI (GPT-4o, o3-mini)** | **50,000 requests** per batch file | **100 MB** | Up to **100M tokens** queued across all active batches | Within 24 hours (often < 2 hours) |
| **Anthropic (Claude Sonnet/Haiku)** | **10,000 requests** per batch | **32 MB** | Up to **20M to 100M tokens** depending on your Tier | Within 24 hours |
| **Google Gemini (Batch API)** | Variable by quota tier | **100 MB** | Tier-dependent (millions of tokens) | Within 24 hours |

#### The Recommended Batch Sizing Rule
You do not need to fill a batch to its theoretical ceiling.
* **Recommended Batch Size:** **500 to 2,000 requests** (or ~15–20 MB) per batch file.
* **Why?** If a single line in a 50,000-item batch file contains corrupted JSON, the entire batch upload can be rejected. Smaller batches of 1,000 items process faster, finish sooner, and isolate errors cleanly.

---

## Part 2: Input Token Limits & Context Windows

### 1. Is there any limit to the input tokens or prompt?
**Yes, there is a hard physical limit determined by the model's Context Window.**

If a model has a 128,000-token context window, attempting to send 129,000 tokens causes the API call to immediately fail with an error (`context_window_exceeded`).

* **Claude 3.5 / 3.7 Sonnet & Haiku:** 200,000 tokens (~150,000 words).
* **OpenAI GPT-4o / o1 / o3-mini:** 128,000 to 200,000 tokens (~95,000 to 150,000 words).
* **Google Gemini 1.5 Pro:** 2,000,000 tokens (~1,500,000 words).

However, having a 200,000-token window **does not mean** you should pack it with 200,000 tokens of complex instructions.

---

## Part 3: Why a 1600+ Line Prompt is 40% Wrong (And Why Big Models Still Fail)

A prompt that is 1,600+ lines long will fail on **any** model (whether Claude Sonnet, GPT-4o, or Haiku). The three underlying causes are:

### 1. Attention Dilution & Context Saturation
Transformers use Multi-Head Self-Attention. Attention is a finite mathematical probability distribution where all weights sum to 1.0:
* In a **50-line prompt**, the model assigns high mathematical weight to each individual rule.
* In a **1,600-line prompt**, attention is stretched thin over thousands of words. The model physically cannot attend to 150 rules simultaneously and begins ignoring constraints.

### 2. Instruction Collision (The Contradiction Trap)
In a 1,600-line prompt, unintended contradictions are inevitable:
* One section asks the model to be extremely concise.
* Another section asks the model to capture deep nuance and elaborate.
* One rule says never infer skills not explicitly written.
* Another rule says always infer ecosystem foundations.

When instructions conflict, the model's internal entropy spikes and it randomly chooses which rule to follow, causing hallucinations, dropped data, and inconsistent results.

### 3. The "Lost in the Middle" Phenomenon
Research confirms that LLMs pay the highest attention to the **beginning (first 10%)** and the **end (last 10%)** of an input prompt. Rules located in the middle of a massive 1,600-line prompt are virtually skipped during inference.
