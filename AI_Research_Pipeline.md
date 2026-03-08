# AI Research Pipeline: Step-by-Step Guide

---

## STEP 1: GAP IDENTIFICATION WITH LLM

**Tool:** ChatGPT, Claude, or Qwen (all have free tiers)

**Input:** A short paragraph describing your starting point and what you want to research.

**Prompt:**
```
I am a researcher working on "[field/topic]". Here is my starting point:

"[2-3 sentences describing what you have and what you want to do]"

Help me with the following:
1. Identify 4-6 possible research gaps my work could address. For each gap:
   a. Phrase it as a yes/no question a domain expert could answer (e.g., "Has anyone systematically tested whether X predicts Y in context Z?")
   b. Provide 2-3 short keyword queries (3-6 words each) I can use to search for existing work on that gap in Semantic Scholar
   c. Briefly explain why this gap matters and how my work could fill it
2. For each gap, rate your confidence (high/medium/low) that this is genuinely underexplored
```

**Output:** 4-6 candidate gaps, each with a yes/no question, keyword queries, and rationale.

**Filter before next step:** Select the **3 most promising gaps** based on relevance to your work and the LLM's confidence rating.

**Quick sanity check:** Before investing time in Step 2, do a 2-minute Google Scholar search for each selected gap using the yes/no question. If the first page of results already shows papers that directly answer it, the gap is likely closed — discard it and pick a different one. This prevents wasting API calls on gaps the LLM hallucinated as open.

---

## STEP 2: LITERATURE RESEARCH (Automated with Claude + Semantic Scholar API)

The entire Step 2 can be run in a single Claude session. Claude calls the Semantic Scholar API to search papers, get abstracts, check citations, and extract methods. You review the output and make decisions at each checkpoint. If the session hits its context limit, start a new session and paste the knowledge base document built so far — each substep produces a standalone output you can carry forward.

**Important:** Before starting, get a free API key at https://www.semanticscholar.org/product/api#api-key-form. Without it, you share a global rate limit with all unauthenticated users and WILL get blocked after a few calls. With a key, you get a dedicated 1 request/second limit, which is enough for the entire Step 2 (~35 calls = ~2 minutes).

### STEP 2.1: Validate Gaps

**What Claude does:**
For each of the 3 gaps, Claude searches the Semantic Scholar API using the keyword queries from Step 1 (2-3 queries per gap). For each query, it retrieves the top 5 results with titles, abstracts, years, and citation counts.

**Prompt to Claude:**
```
My Semantic Scholar API key is: [YOUR_KEY]
Use it as header "x-api-key" in all API calls. Space all calls 3 seconds apart.

I have 3 research gaps to validate. For each gap, search the Semantic Scholar
API using the keyword queries I provide. Get the top 5 results per query.
Then summarize:
- What already exists (papers that partially address this gap)
- What's still missing (the specific thing nobody has tested)
- Your assessment: is this gap OPEN, PARTIALLY FILLED, or CLOSED?

Gap 1: [yes/no question]
  Queries: "[query 1]", "[query 2]", "[query 3]"

Gap 2: [yes/no question]
  Queries: "[query 1]", "[query 2]"

Gap 3: [yes/no question]
  Queries: "[query 1]", "[query 2]", "[query 3]"
```

**API calls Claude makes:**
```
GET https://api.semanticscholar.org/graph/v1/paper/search
  ?query={keywords}&limit=5&fields=paperId,title,abstract,year,authors,citationCount
  Header: x-api-key: YOUR_KEY
```
(~6-9 calls total, one per query. **Space calls 3 seconds apart** to avoid rate limits.)

**Checkpoint:** You review Claude's summary. Keep gaps rated OPEN or PARTIALLY FILLED. Discard CLOSED gaps. Select the **top ~15 papers** across all gaps (removing duplicates and irrelevant results).

**Output:** 1-3 validated gaps + ~15 relevant papers with abstracts.

---

### STEP 2.2: Expand via Citation Network

**What Claude does:**
Takes the **5 most important papers** from Step 2.1 and retrieves their references (what they cite) and citations (who cites them) via the Semantic Scholar API. This replicates what Inciteful does with citation graphs, but programmatically.

**Prompt to Claude:**
```
My Semantic Scholar API key is: [YOUR_KEY]
Use it as header "x-api-key" in all API calls. Space all calls 3 seconds apart.

For each of these 5 papers, use the Semantic Scholar API to:
1. Get their references (papers they cite) — top 10 most cited
2. Get their citations (papers that cite them) — top 10 most recent/cited

Then identify:
- Papers that appear in multiple citation lists (bridge papers)
- Recent papers (last 2-3 years) that cite the originals (new developments)
- Papers I don't already have that are highly relevant to my gaps

My gaps are: [list surviving gaps]
My existing papers are: [list titles]
```

**API calls Claude makes:**
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references
  ?fields=title,abstract,year,authors,citationCount&limit=10
  Header: x-api-key: YOUR_KEY

GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations
  ?fields=title,abstract,year,authors,citationCount&limit=10
  Header: x-api-key: YOUR_KEY
```
(~10 calls total: 2 per paper. **Space calls 3 seconds apart.**)

**Checkpoint:** You review the expanded list. Pick the **10 most relevant new papers** you didn't have before. Your total collection is now ~20-25 papers.

**Output:** ~20-25 papers total (15 from Step 2.1 + 10 new from citation network).

---

### STEP 2.3: Extract Methods, Metrics, and Design

**What Claude does:**
For the ~20-25 papers, Claude already has abstracts from Steps 2.1-2.2. For the **10 most methodologically relevant papers**, it fetches full details and extracts a comparison table.

**Prompt to Claude:**
```
From these papers, build a comparison table with these columns:
- Paper (author, year)
- Publication status (peer-reviewed / preprint / workshop)
- Method/approach
- Dataset used
- Evaluation metrics (computational)
- Effect size measures reported
- Human evaluation method (if any)
- Sample size (participants or stimuli)
- Key finding

Focus on the papers most relevant to experimental design, not surveys.

Papers: [list the 10 most relevant]
```

**What Claude uses:** Abstracts already retrieved. For papers where the abstract lacks detail, Claude can fetch the paper's full metadata:
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}
  ?fields=title,abstract,year,authors,citationCount,fieldsOfStudy,publicationTypes
  Header: x-api-key: YOUR_KEY
```
(**Space calls 3 seconds apart.**)

**Note:** Claude can only extract what's in the abstract and metadata. For detailed methods (exact parameters, statistical tests, etc.), you'll need to read the full papers. Flag 5-8 papers for full reading.

**Output:** Comparison table + list of 5-8 papers to read in full.

---

### STEP 2.4: Check Citation Context and Limitations

**What Claude does:**
For the **5 most important papers**, retrieves citation contexts — the actual sentences where other papers cite them. The Semantic Scholar API provides context snippets and citation intent (background, methodology, result comparison).

**Prompt to Claude:**
```
My Semantic Scholar API key is: [YOUR_KEY]
Use it as header "x-api-key" in all API calls. Space all calls 3 seconds apart.

For each of these 5 key papers, get their citation contexts from the
Semantic Scholar API. Focus on:
1. Citations that CHALLENGE or CRITICIZE the paper (contrasting intent)
2. Citations that identify LIMITATIONS
3. Citations from papers I don't already have (potential additions)

For each paper, give me:
- 2-3 limitations others have noted
- Any competitor/alternative approaches cited
- Whether my gap is mentioned as future work by anyone

Papers:
1. [title] (Semantic Scholar ID: ...)
2. [title] (Semantic Scholar ID: ...)
...
```

**API calls Claude makes:**
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations
  ?fields=title,abstract,year,citationCount,contexts,intents,isInfluential
  &limit=20
  Header: x-api-key: YOUR_KEY
```
(5 calls total, one per paper. **Space calls 3 seconds apart.**)

**Output:** For each paper: limitations, criticisms, and 3-5 new papers to consider. This feeds directly into your Introduction (gap justification) and Discussion (limitations).

---

### STEP 2.5: Build Structured Knowledge Base

**What Claude does:**
Synthesizes everything from Steps 2.1-2.4 into a structured document that becomes the skeleton of your paper.

**Prompt to Claude:**
```
Based on everything we've found, create a structured knowledge base document
with these sections:

## 1. GAP EVIDENCE
For each surviving gap:
- What exists (paper, what they did, what they found)
- What's missing (the specific thing nobody tested)
- Key citation for the gap

## 2. METHODS TO REUSE
- Paradigms, metrics, and designs I can adapt
- Sample sizes in similar studies
- Common computational metrics
- Common human evaluation approaches

## 3. LIMITATIONS OF EXISTING WORK
- Paper X acknowledges [limitation] → my study addresses this
- Paper Y was criticized for [thing] → I should avoid this

## 4. CONTRADICTIONS IN THE LITERATURE
- Where papers disagree and why → I need to discuss both

## 5. HYPOTHESES (derived from gaps + methods)
- H1: ... (based on gap + methods from Paper X)
- H2: ... (based on gap + findings from Paper Y)

## 6. DESIGN DECISIONS (justified by literature)
- Why I chose [design element]: because [paper] shows [evidence]

## 7. PAPERS TO READ IN FULL
- The 5-8 papers that need careful reading beyond the abstract

## 8. FULL PAPER LIST
- All ~25 papers organized by category with citation info
```

**Output:** A single document that contains everything you need for Steps 3-6.

#### Checkpoint: Verify knowledge base against raw data

Before moving on, spot-check Claude's synthesis in Section 2.5 against the raw outputs from 2.1-2.4:
- Do the "CONTRADICTIONS" match what you actually saw in the abstracts? (Check 2-3 claims)
- Are the "METHODS TO REUSE" accurately described, or did Claude embellish capabilities?
- Do the hypotheses follow logically from the gaps + evidence, or did Claude add unsupported theoretical connections?

This takes 10-15 minutes. Fix anything wrong before it propagates into your research question and experimental design.

---

### STEP 2.6: Crystallize Research Question

**Tool:** Same Claude session (or a new LLM session)

**Input:** The knowledge base document from Step 2.5.

**Prompt:**
```
Based on the knowledge base we built, help me formulate:
1. A specific, testable research question
2. A one-sentence contribution statement ("We are the first to..." or "We provide...")
3. Why this question matters (motivation in 2-3 sentences)
4. How this extends or differs from the closest existing work
```

**Process:** Review the output. The question must be specific enough to design an experiment around. If too broad, ask the LLM to narrow it.

**Output:** One clear research question + contribution statement.

---

### Step 2 summary: API usage

| What | API endpoint | Calls | Rate limit |
|------|-------------|-------|------------|
| Gap validation (2.1) | `/paper/search` | ~6-9 | 1/sec free |
| Citation network (2.2) | `/paper/{id}/references` + `/citations` | ~10 | 1/sec free |
| Paper details (2.3) | `/paper/{id}` | ~10 | 1/sec free |
| Citation context (2.4) | `/paper/{id}/citations` with contexts | ~5 | 1/sec free |
| **Total** | | **~30-35 calls** | **~2 min of API time** |

All free. A free API key is strongly recommended (see Step 2 introduction). The prompts say "space calls 3 seconds apart" — this adds a safety margin over the 1 req/sec limit to avoid intermittent 429 errors.

**Get a free API key at:** https://www.semanticscholar.org/product/api#api-key-form

**What you still do manually after Step 2:**
- **Read the 5-8 flagged papers in full** — this is the one verification pass before moving on
- Upload the ~25 papers to Zotero (browser extension, one click each)
- Upload the 8-10 most important PDFs to NotebookLM for grounded Q&A
- Before submission: check every cited number against source PDFs, verify every paper exists

---

### When to still use Inciteful manually

The API-based citation expansion (Step 2.2) covers 80% of what Inciteful does. But Inciteful's **visual graph** is useful for one thing Claude can't replicate: **seeing clusters**. If after Step 2 you feel like you might be missing an entire subfield, go to https://inciteful.xyz/, paste your top 3 papers, and visually check if there's a cluster of papers you missed.

Think of it as a sanity check, not a required step.

**Coverage check:** Semantic Scholar does not index all venues equally. After completing Step 2, do a quick Google Scholar search for your top 2-3 keyword queries to confirm you haven't missed major work from venues Semantic Scholar doesn't cover well.

---

## STEP 3: KNOWLEDGE MANAGEMENT

### STEP 3.1: Organize Papers — Zotero

**Tool:** https://www.zotero.org/ (100% free, unlimited, with browser extension)

**Input:** The ~20-25 papers from Step 2. (Tip: save papers to Zotero as you find them during Steps 2.1-2.2 using the browser extension. This makes Step 3.1 a verification pass rather than a batch task.)

**Process:** For each paper, open it in browser and click the Zotero extension to save. Create a collection for your project. Tag papers by role: `methods`, `evaluation`, `dataset`, `related-work`, `motivation`.

**Output:** Organized, tagged library. Use later for citation export (Step 6) and quick reference.

### STEP 3.2: Grounded Q&A — NotebookLM

**Tool:** https://notebooklm.google/ (free with Google account, up to 50 sources per notebook)

**Input:** Upload PDFs of the **8-10 most relevant papers** + your knowledge base document from Step 2.5 + your own technical documents if any.

**Why this matters for the automated pipeline:** In Step 2, Claude analyzed papers from abstracts and metadata only. NotebookLM is a different AI (Google Gemini) working from **full PDFs**. This gives you an independent second opinion. If NotebookLM contradicts something Claude concluded from an abstract, the full-text answer is more reliable — flag and fix the discrepancy in your knowledge base before Step 4.

**Process:** Ask questions driven by your research question from Step 2.6:
- "What evaluation metrics are used for [your specific topic]?"
- "What sample sizes did studies on [your topic] use?"
- "What datasets exist for [your specific variables]?"
- "What are the main limitations reported in these papers related to [my gap]?"
- "How do these papers describe their experimental setup?"

**How many times:** 5-8 questions. No limit on NotebookLM free tier.

**Output:** Grounded answers with citations to your uploaded papers. Save these — they feed directly into Step 4 (metrics, sample sizes) and Step 6 (writing).

---

## STEP 4: EXPERIMENTAL DESIGN

### STEP 4.1: Define Goal and Hypotheses

**Tool:** ChatGPT, Claude, or Qwen (free tiers)

**Prompt:**
```
My research question is: "[paste from 2.6]"

From the literature I found that:
- Standard metrics: [paste from knowledge base or 3.2]
- Typical sample sizes: [paste from knowledge base or 3.2]
- Existing datasets: [paste from knowledge base or 3.2]

Help me define:
1. The main hypothesis (what do I expect to find?)
2. Secondary hypotheses (if any)
3. What a positive result looks like
4. What a negative result would mean (and whether it's still publishable)
```

**Output:** Clear hypotheses and expected outcomes.

### STEP 4.2: Design Variables and Conditions

**Tool:** ChatGPT, Claude, or Qwen (same conversation)

**Prompt:**
```
Given these hypotheses, help me design the experiment:
1. Define all independent variables and their levels
2. Define all dependent variables and how to measure each one
3. Choose within-subjects vs between-subjects design and justify
4. Identify confounding variables I must control for
5. Recommend the appropriate statistical test
6. If multiple comparisons are involved, specify the correction method (e.g., Bonferroni, Benjamini-Hochberg FDR)
7. Specify which effect size measure is appropriate for each test (e.g., Cohen's d, eta-squared, odds ratio)
8. Estimate required sample size — specify expected effect size (from literature), alpha, and desired power (≥0.80)
9. Define exclusion criteria for participants/data
```

**Important:** Do NOT rely on the LLM's sample size estimate as final. Use G\*Power (free: https://www.psychologie.hhu.de/gpower) or equivalent to compute the required N from the expected effect size, alpha, and power. The LLM can help choose the right test family and effect size type, but the computation must come from a dedicated tool.

**Output:** Complete experimental design with justification.

### STEP 4.3: Draft Preregistration

**Tool:** ChatGPT, Claude, or Qwen (same conversation)

**Prompt:**
```
Now draft a preregistration for this study following these 8 questions:
1. Have any data been collected for this study already?
2. What is the main question being asked or hypothesis being tested?
3. Describe the key dependent variable(s) specifying how they will be measured.
4. How many and which conditions will participants be assigned to?
5. Specify exactly which analyses you will conduct to examine the main question/hypothesis.
6. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.
7. How many observations will be collected or what will determine sample size?
8. Anything else you would like to pre-register?
```

**Output:** A complete preregistration draft. File it at https://aspredicted.org/ (free) or https://osf.io/ (free) **before proceeding to Step 5**. A preregistration filed after seeing results is not a preregistration.

### STEP 4.3b: Ethics and Institutional Approval

If your study involves human participants, animal subjects, or sensitive data, submit your experimental design and preregistration to your institution's IRB/ethics board **before collecting data**. Do not proceed to data collection until approval is granted. Record the approval number for inclusion in the Methods section (Step 6.3).

If your study is purely computational with no human subjects, document why ethics review was not required — many journals now require this statement explicitly.

### STEP 4.4: Plan Implementation Steps

**Tool:** ChatGPT, Claude, or Qwen (same conversation)

**Prompt:**
```
I need to implement this experiment. My current system is: [brief technical description].

Break down the implementation into concrete coding tasks:
1. What needs to be built or modified?
2. What data needs to be generated or collected?
3. What scripts are needed for running the experiment?
4. What scripts are needed for analysis?

For each task, describe inputs, outputs, and dependencies on other tasks.
```

**Output:** A task list for Step 5. Each task becomes a coding prompt.

### CHECKPOINT: Review Experimental Design

Before coding, verify the LLM-generated design makes sense:
- Is the statistical test appropriate for your data type and design? Cross-check with what papers in your comparison table (Step 2.3) used.
- Is the sample size justified by G\*Power, not just the LLM's estimate?
- Does the design actually test your hypothesis?
- If possible, have a colleague or advisor review the design. Catching a flaw here saves weeks of wasted implementation.

---

## STEP 5: CODING

**Tool:** Claude Code, Cursor, or preferred AI coding assistant

**Input:** Task list from Step 4.4, given one task at a time.

**Setup:** Initialize a Git repository for your project now. Commit code as you develop. Step 8 covers the final public release, but version control should start here.

**Process:** For each task from 4.4, give the coding assistant the context it needs (relevant files, the experimental design, the expected inputs/outputs). Implement, test, iterate.

**Before running:** Test each analysis script with synthetic or expected data to verify it produces correct output. Review AI-generated code for logic errors, especially in data processing and statistical test implementations. Ensure the code matches the preregistered analysis plan from Step 4.3.

**Output:** Working, tested code ready to run the experiment.

---

## DO ACTUAL EXPERIMENT

**Pilot first:** If your experiment uses novel stimuli, a new task, or untested measures, run a small pilot (N=5-10) before the full study. Verify: (1) data collection works as designed, (2) output format matches what analysis scripts expect, (3) results are plausible. Fix issues before running the full experiment.

Then run the full experiment, collect data, run the analysis scripts from Step 5.

---

## STEP 6: WRITING

**Before starting:** Complete Step 7 (Visualization) first — create your methodology figure and results figures/tables before drafting. Having figures ready ensures they're properly referenced in the text and helps structure each section.

**Identify your reporting standard:** Determine which reporting guideline applies to your study type (APA for psychology, CONSORT for clinical trials, STROBE for observational). Use the EQUATOR Network (https://www.equator-network.org/) to find the right checklist.

**How drafting works in the automated pipeline:** Claude produced a structured knowledge base in Step 2.5 containing all papers, gaps, methods, and limitations from API data. Use this document as the **single source of truth** for every drafting prompt below. Paste the relevant section of the knowledge base into each prompt — this forces the LLM to draft from specific data rather than its general knowledge, which reduces hallucination. If you're still in the same Claude session from Step 2, it already has this context.

### STEP 6.1: Introduction

**Tools:** NotebookLM (free) + LLM (free tier) + Writefull (free limited / ~$5/mo) + Zotero (free)

**Process:**

1. **Get building blocks from NotebookLM.** Ask:
   - "Summarize the main motivation for studying [your topic] based on these papers"
   - "What is the current state of [your field] and what gap exists?"
   - "What are the key references I should cite when introducing [your topic]?"

2. **Draft with LLM:**
   ```
   Help me draft an Introduction section for a research paper.

   Research question: [from 2.6]
   Contribution: [from 2.6]
   Motivation and gap: [paste NotebookLM answers]
   Key references to cite: [paste NotebookLM answers]

   Structure it as:
   - Paragraph 1: Why this field matters (broad context)
   - Paragraph 2: What has been done (state of the art)
   - Paragraph 3: What is missing (the gap)
   - Paragraph 4: What we do (contribution and paper overview)
   ```

3. **Polish with Writefull.** Writefull's Sentence Palette suggests common academic phrases for each section type — select a section (e.g., Introduction), then a function (e.g., "Topic Importance", "Research Gap", "Stating Aim"). The Academizer rewrites informal sentences in formal academic style. Both are available in the Writefull browser extension or Word add-in. Use the Academizer on informal sentences.

4. **Add citations from Zotero.** Word: Zotero plugin inserts directly. Overleaf: export BibTeX, use `\cite{}`.

**Output:** Draft Introduction with proper citations.

### STEP 6.2: Related Work

**Tools:** NotebookLM (free) + LLM (free tier) + Zotero (free)

**Process:**

1. **Get summaries from NotebookLM.** For each gap/topic area, ask:
   - "Summarize the main approaches related to [gap topic] based on these papers"
   - "What are the strengths and limitations of each approach?"

2. **Draft with LLM:**
   ```
   Help me write a Related Work section organized into these subsections:
   - [Topic 1 from gap area]: [paste NotebookLM summary]
   - [Topic 2 from gap area]: [paste NotebookLM summary]
   - [Topic 3 from gap area]: [paste NotebookLM summary]

   End with a paragraph explaining how our work differs from all of the above.
   Our contribution is: [from 2.6]
   ```

3. **Add citations from Zotero** for every claim.

**Output:** Draft Related Work with citations.

### STEP 6.3: Methods

**Tools:** Writefull (free limited / ~$5/mo) + LLM (free tier)

**Process:**

1. **Write informally first.** Summarize what you did in plain language. Use your documents from Steps 4 and 5 as reference.

2. **Academize with Writefull.** Select each paragraph -> Academizer. Use Sentence Palette (Methods section) for standard phrases.

3. **Check completeness with LLM:**
   ```
   Here is my Methods section draft. Check if I am missing any
   of the following: participant description, materials,
   procedure, measures, statistical analysis plan, ethical
   approval statement. Flag anything missing.
   ```

**Output:** Draft Methods section.

### STEP 6.4: Results

**Tools:** LLM (free tier) + Writefull (free limited / ~$5/mo)

**Process:**

1. **Prepare statistical output.** Have your analysis results ready: test statistics, p-values, effect sizes, confidence intervals. Ensure your analysis scripts already computed effect sizes and CIs — do NOT ask the LLM to calculate them (it will hallucinate numbers).

2. **Draft with LLM:**
   ```
   Help me write a Results section for these findings:
   [paste statistical output or summary table]

   Requirements:
   - Report exact p-values (not just p<0.05)
   - Include effect sizes and confidence intervals
   - Report the number of exclusions and reasons (e.g., "N=3 excluded for failing attention checks, final N=47")
   - If any hypotheses were not supported, report these with the same detail as supported hypotheses. Do not minimize null findings.
   - Describe results without interpretation (save that for Discussion)
   - Follow APA reporting style
   ```

3. **Polish with Writefull.** Use Sentence Palette (Results section) for reporting phrases.

**Output:** Draft Results section.

### STEP 6.5: Discussion

**Tools:** NotebookLM (free) + LLM (free tier) + Writefull (free limited / ~$5/mo) + Zotero (free)

**Process:**

1. **Compare with literature via NotebookLM.** Ask:
   - "How do my results compare to [specific paper]? They found [X], I found [Y]."
   - "What explanations have been proposed in these papers for [specific finding]?"

2. **Draft with LLM:**
   ```
   Help me write a Discussion section.

   My key findings were: [paste from Results]
   How they compare to literature: [paste NotebookLM answers]
   My research question was: [from 2.6]

   Structure:
   - Paragraph 1: Summary of key findings
   - Paragraph 2-3: Interpretation and comparison with literature
   - Paragraph 4: Limitations (be honest — include all limitations, not just minor ones)
   - Paragraph 5: Future work
   - Paragraph 6: Conclusion

   Important: if results are null or negative, discuss them honestly.
   Do not spin non-significant results as "trending" or "marginally significant."
   Discuss what the null result means for the field.
   ```

3. **Polish with Writefull.** Use Sentence Palette (Discussion > "Key Findings", "Limitations", "Future Research").

4. **Add citations from Zotero** where you compare with other work.

**Output:** Draft Discussion section.

### STEP 6.6: Abstract

**Tools:** LLM (free tier) + Writefull (free limited / ~$5/mo)

**Process:** Write this last, after all other sections are done.

```
Write an abstract for this paper (max 250 words). Include:
- Background (1-2 sentences)
- Gap/objective (1 sentence)
- Methods (2-3 sentences)
- Key results (2-3 sentences)
- Conclusion (1 sentence)

Paper content:
- Introduction: [paste first and last paragraphs]
- Methods: [paste summary]
- Results: [paste key findings]
- Conclusion: [paste from Discussion]
```

**Output:** Draft Abstract.

### STEP 6.7: Factual Review

**Input:** Complete draft from Steps 6.1-6.6.

**Why this step exists:** Steps 6.1-6.6 used LLMs to draft every section. LLMs can subtly change numbers, over-interpret findings, fabricate theoretical connections, or misrepresent what a cited paper actually said. Writefull and Penelope check *style and format* — neither checks *factual accuracy*. This is the step that catches content-level hallucinations.

**Part A — AI-assisted pre-check (~5 min):**

Since Claude built the knowledge base in Step 2.5, you can use it to catch obvious inconsistencies before your manual review. Ask Claude:
```
Compare the following draft against the knowledge base we built in Step 2.5.
Flag any claims, numbers, or attributions in the draft that:
- Don't appear in the knowledge base
- Contradict the knowledge base
- Go beyond what the knowledge base supports (overclaims)

Draft:
[paste full draft]
```
This catches the easy errors. It does NOT replace human review — Claude can miss its own hallucinations.

**Part B — Human verification (1-3 hours):**

Go through the draft with source PDFs open and verify each item:

1. **Numbers:** Every statistic you cite (sample sizes, accuracy percentages, p-values, effect sizes) — open the source PDF and confirm the exact number matches.
2. **Paper existence:** Every paper in your reference list actually exists. Search each title in Semantic Scholar or Google Scholar. LLMs occasionally invent plausible-sounding paper titles.
3. **Attribution accuracy:** Every "Paper X found that Y" — open Paper X and confirm they actually found Y, not a distorted version of Y. Pay special attention to comparative claims ("better than", "outperformed", "first to").
4. **Your own results:** Every number in your Results section matches your actual statistical output. LLMs sometimes round, flip signs, or change significance levels when redrafting.
5. **Theoretical connections:** Any claim like "this suggests that..." or "consistent with the theory of..." — verify the connection is actually supported by the cited source, not invented by the LLM to make the narrative flow better.
6. **Scope of claims:** Check that the Discussion doesn't overclaim. If your study tested X on dataset Y, the LLM should not generalize to "this works for all Z."

**Output:** Fact-checked manuscript ready for formatting check.

---

### STEP 6.8: Manuscript Check — Penelope.ai

**Tool:** https://www.penelope.ai/journals/demo (free: pass/fail report; $9.50: full track-changes)

**Input:** Complete manuscript draft saved as .docx.

**Process:** Upload to Penelope. Review the pass/fail report. Fix flagged issues: missing ethics statement, wrong citation format, unreferenced figures, vague p-values, missing sections.

**How many times:** 1-2 uploads (check, fix, re-check).

**Output:** Checked manuscript ready for declarations.

### STEP 6.9: Required Declarations

Add to the manuscript before submission:
1. **Conflict of Interest statement** — required by most journals
2. **Funding sources** — list all grants, institutions, or sponsors
3. **Author contributions** — use CRediT taxonomy if the target journal requires it (https://credit.niso.org/)
4. **AI Use Disclosure** — most publishers (Nature, Science, IEEE, ACM) now require disclosure of AI tools used. List all AI tools: LLMs for gap identification and drafting, Claude for literature analysis, Writefull for style polishing, etc. Check your target journal's specific AI-use policy.

**Output:** Complete manuscript with all required declarations.

---

## STEP 7: VISUALIZATION

**When to do this:** Before Step 6 (Writing), not after. Create your methodology figure from your experimental design (Step 4) and results figures from your analysis output before drafting. This ensures figures are properly referenced in each writing substep.

**Tool:** PaperBanana — https://paper-banana.org/ (free tier available)

**Input:** Your Methods section from Step 6.3.

**Process:** Describe your methodology as a sequence of stages:
```
Create a methodology diagram for: [describe each stage,
inputs, outputs, and connections between stages]
```

**Output:** Publication-ready methodology figure.

---

## STEP 8: REPRODUCIBILITY

**Tool:** Git (free) + OSF https://osf.io/ (free)

**Input:** Code from Step 5, data from experiment, preregistration from Step 4.3.

**Process:**
- Push code to GitHub repository (should already be version-controlled from Step 5)
- Upload dataset, preregistration, and supplementary materials to OSF
- Link OSF project to GitHub repo
- Add OSF badge and data availability statement to manuscript:
  ```
  Data availability statement template:
  "The dataset, analysis code, and preregistration for this study are
  available at [OSF URL with DOI]. The stimuli and materials are
  available at [GitHub URL]."
  ```
  Specify any access restrictions and what is included (raw data, processed data, analysis scripts, stimuli).

**Output:** Reproducible, open-science package.

---

## QUICK REFERENCE: Tool Flow

```
STEP 1: LLM
  -> 4-6 gaps with keyword queries, select best 3
  * SANITY CHECK: Quick Google Scholar search per gap (~5 min) *
  |
STEP 2.1: Claude + Semantic Scholar API (automated)
  -> search ~6-9 queries -> validate gaps -> ~15 papers
STEP 2.2: Claude + Semantic Scholar API (automated)
  -> citation network of top 5 papers -> ~10 new papers
STEP 2.3: Claude (automated, from collected abstracts)
  -> comparison table of methods/metrics/design
STEP 2.4: Claude + Semantic Scholar API (automated)
  -> citation contexts for 5 key papers -> limitations + new papers
STEP 2.5: Claude (automated)
  -> structured knowledge base document
  * CHECKPOINT: Verify knowledge base against raw data (~15 min) *
STEP 2.6: LLM
  -> RESEARCH QUESTION + CONTRIBUTION
  |
  * Optional: Inciteful visual sanity check + Google Scholar coverage check *
  * READ 5-8 KEY PAPERS IN FULL (2-4 hours) *
  |
STEP 3.1: Zotero (manual) -> save ~20-25 papers, tag by role
STEP 3.2: NotebookLM (manual) -> upload 8-10 key PDFs -> grounded Q&A
  |
STEP 4.1: LLM -> hypotheses
STEP 4.2: LLM + G*Power -> experimental design + power analysis
STEP 4.3: LLM -> preregistration -> FILE before Step 5
STEP 4.3b: Ethics/IRB approval (if human participants)
STEP 4.4: LLM -> implementation tasks
  * CHECKPOINT: Review experimental design before coding *
  |
STEP 5: AI Coding -> working code (with Git from the start)
  |
  * PILOT (N=5-10) -> verify pipeline works *
  * DO FULL EXPERIMENT *
  |
STEP 7: PaperBanana -> methodology + results figures (do BEFORE writing)
  |
STEP 6.1: NotebookLM + LLM + Writefull + Zotero -> Introduction
STEP 6.2: NotebookLM + LLM + Zotero -> Related Work
STEP 6.3: Writefull + LLM -> Methods
STEP 6.4: LLM + Writefull -> Results
STEP 6.5: NotebookLM + LLM + Writefull + Zotero -> Discussion
STEP 6.6: LLM + Writefull -> Abstract
STEP 6.7: YOU -> factual review (numbers, attributions, paper existence)
STEP 6.8: Penelope.ai -> manuscript format check
STEP 6.9: Declarations (COI, funding, AI disclosure, author contributions)
  |
STEP 8: Git + OSF -> reproducibility + data availability statement
```

---

## TOOL COST SUMMARY

### All tools used in this pipeline

| Tool | Uses AI? | Role | Used in steps |
|------|----------|------|---------------|
| LLM (ChatGPT/Claude/Qwen) | Yes | Gap identification, synthesis, drafting | 1, 2.5, 2.6, 4, 6 |
| **Semantic Scholar API** | Yes (TLDRs, citation intent) | Search, citation network, extraction, citation context | 2.1, 2.2, 2.3, 2.4 |
| **Claude** | Yes | Orchestrates all API calls, analyzes results, builds knowledge base | 2.1-2.5 |
| **Inciteful** | No (graph algorithms) | Visual citation graph sanity check | Optional |
| **Zotero** | No | Store papers, manage citations | 3.1, 6 |
| **NotebookLM** | Yes (Google Gemini) | Cross-paper Q&A grounded in your PDFs | 3.2, 6 |
| Writefull | Yes | Academic style polishing | 6 |
| Penelope.ai | Mostly no (rules) | Manuscript format checking | 6.8 |
| PaperBanana | Yes | Methodology diagrams | 7 |
| Git + OSF | No | Reproducibility | 8 |

This is the most AI-heavy version: Claude automates the entire literature research (Step 2) by calling the Semantic Scholar API, analyzing results, building comparison tables, and producing a structured knowledge base — all in one session.

**Core pipeline: $0/month.** The Semantic Scholar API key is free. Optional paid tiers: Writefull (~$5/mo for full features), Penelope.ai ($9.50 for full report).

### Verification rule — 4 checkpoints

Claude does the heavy lifting. You verify at four points:

1. **After Step 1 (gap sanity check):** Quick Google Scholar search per gap to catch LLM-hallucinated gaps. (~5 min)
2. **After Step 2.5 (knowledge base):** Spot-check Claude's synthesis against raw data from 2.1-2.4. Fix distortions before they enter your research question. (~15 min)
3. **Before Step 3 (read papers):** Read 5-8 key papers in full. This grounds you in the actual literature before experimental design. (~2-4 hours)
4. **Step 6.7 (factual review):** Go through the complete draft with the 6-item checklist. Verify every number, every attribution, every paper's existence against source PDFs. (~1-3 hours)

Plus one design checkpoint: review experimental design (Step 4) before coding (Step 5).

Total human verification: ~4-8 hours across the entire pipeline. Everything else is AI-accelerated.
