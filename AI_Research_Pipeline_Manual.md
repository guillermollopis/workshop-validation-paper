# AI Research Pipeline: Manual Version

Use this version when you want more hands-on control over the literature search, prefer visual exploration, or don't have a Semantic Scholar API key. For the automated version (Claude + Semantic Scholar API), see `AI_Research_Pipeline.md`.

---

## SEQUENTIAL FLOW SUMMARY (Steps 1-8)

Every substep has either a **Prompt** (paste into LLM) or a **Command** (run in terminal). The output of each substep feeds into the next. Follow this sequence:

| Step | Action | What you do | Output file |
|------|--------|-------------|-------------|
| **1** | Prompt → LLM | Paste the Step 1 prompt with your topic description | `step1_output.md` (gaps + queries) |
| **2.1** | Search + Prompt → LLM | Search Semantic Scholar with keyword queries, then paste results into the Step 2.1 prompt | `step2_1_output.md` (validated gaps + ~10-15 papers) |
| **2.2** | Prompt → LLM + search + graphs | Paste paper list into Step 2.2 prompt, run new searches, build citation graphs, tier papers | Update `step2_1_output.md` + `zotero_import_ids.txt` |
| | Command | `python3 zotero_auto_import.py --ids zotero_import_ids.txt --collection "Project"` | Zotero library with PDFs |
| **2.3** | Prompt → LLM | Paste top-tier abstracts into Step 2.3 prompt, then verify (!) cells from PDFs | `step2_3_output.md` (comparison table) |
| **2.4** | Command | `python3 step2_4_citation_context.py --s2-key YOUR_KEY --output step2_4_output.md` | `step2_4_output.md` (limitations) |
| **2.5** | Prompt → LLM | Paste outputs from 2.1-2.4 into Step 2.5 prompt | `step2_5_output.md` (research question) |
| | **CHECKPOINT 1** | Verify LLM synthesis against raw data; read 5-8 papers in full | — |
| **3.1** | Command | `python3 zotero_tag_papers.py --collection "Project"` | Tagged Zotero library |
| **3.2** | Command | `python3 step3_2_gemini_qa.py --pdf-dir ./pdfs` | `step3_2_output.md` (grounded Q&A) |
| **4.1** | Prompt → LLM | Paste research question (2.5) + metrics/datasets/sample sizes (3.2) into Step 4.1 prompt | `step4_1_output.md` (hypotheses) |
| **4.2** | Prompt → LLM | Paste hypotheses (4.1) into Step 4.2 prompt; then verify sample size with G*Power | `step4_2_output.md` (experimental design) |
| **4.3** | Prompt → LLM | Paste design (4.2) into Step 4.3 prompt; file at AsPredicted/OSF **before Step 5** | `step4_3_output.md` (preregistration) |
| **4.3b** | Manual | Submit to IRB if human participants; document if purely computational | Approval number |
| **4.4** | Prompt → LLM | Paste design (4.2) into Step 4.4 prompt | `step4_4_output.md` (implementation tasks) |
| | **CHECKPOINT 2** | Review design: correct statistical test? G*Power verified? Design tests hypothesis? | — |
| **5a** | Prompt → Claude Code | Paste task list (4.4) + design (4.2) and ask it to enter plan mode | Implementation plan (approved by you) |
| **5b** | Unattended execution | Launch Claude Code with `--dangerously-skip-permissions`; it implements, runs, and fixes everything | Code + stimuli + metrics CSV + figures |
| | **CHECKPOINT 3** | Spot-check generated stimuli, verify metrics CSV, review figures and stats | — |
| **6.0** | PaperBanana or Claude Code | Generate methodology figure | `figures/fig1_methodology.pdf` |
| **6.1-6.5** | Gemini File Search → Claude Code → style tools | Ground in PDFs, draft each section, check quality | `manuscript.tex` (sections) |
| **6.6-6.6b** | Claude Code | Abstract (last) + Conclusion | `manuscript.tex` (complete draft) |
| **6.7** | statcheck + LanguageTool + Claude Code + S2 API + YOU | Verify stats, check style, cross-check facts, confirm papers exist, final read | Verified manuscript |
| **6.8** | Manual | Add declarations (COI, funding, AI disclosure, author contributions) | Final manuscript |
| **7.1** | Claude Code → Marp CLI | Generate slide deck from paper + data files | `slides.md` + `slides.html` |
| **7.2** | Marp CLI + Playwright | Compile to PDF/PPTX | `slides.pdf` / `slides.pptx` |
| **7.3** | Claude Code (screenshot review) | Validate all tables visible, no overflow, numbers match | Verified slides |

**What you need before starting:**
- A Semantic Scholar API key (free): https://www.semanticscholar.org/product/api#api-key-form
- A Gemini API key (free): https://aistudio.google.com/apikey
- Zotero installed with browser extension
- Python 3 with: `pip install pyzotero requests google-genai`
- Node.js (for Claude Code and Marp CLI): https://nodejs.org/
- Claude Code CLI (for Step 5): `npm install -g @anthropic-ai/claude-code`
- Marp CLI (for Step 7): `npm install -g @marp-team/marp-cli`

---

## STEP 1: GAP IDENTIFICATION WITH LLM

**Tool:** ChatGPT, Claude, or Qwen

**Input:** A short paragraph describing your starting point and what you want to research.

**Prompt:**
```
I am a researcher working on "[field/topic]". Here is my starting point:

"[2-3 sentences describing what you have and what you want to do]"

Help me with the following:
1. Identify 4-6 possible research gaps my work could address. For each gap:
   a. Phrase it as a yes/no question a domain expert could answer (e.g., "Has anyone systematically tested whether X predicts Y in context Z?")
   b. Provide 2-3 short keyword queries (3-6 words each) I can use to search for existing work on that gap in Semantic Scholar or Consensus
   c. Briefly explain why this gap matters and how my work could fill it
2. For each gap, rate your confidence (high/medium/low) that this is genuinely underexplored
```

**Output file:** `step1_output.md` — save the LLM response. Contains 4-6 candidate gaps, each with a yes/no question, keyword queries, and rationale.

**Filter before next step:** Select the **3 most promising gaps** based on relevance to your work and the LLM's confidence rating.

**Quick sanity check:** Before investing time in Step 2, do a 2-minute Google Scholar search for each selected gap using the yes/no question. If the first page of results already shows papers that directly answer it, the gap is likely closed — discard it and pick a different one. This prevents wasting time on gaps the LLM hallucinated as open.

---

## STEP 2: LITERATURE RESEARCH

Each substep takes the output of the previous one as input. The data builds up cumulatively:

```
Step 1 output: 3 gaps + keyword queries
      |
      v
2.1: Validate gaps (Semantic Scholar + Consensus) -> 1-3 validated gaps + ~10-15 papers
      |
      v
2.2: Map landscape (terminology expansion + citation graphs) -> +10-15 new papers (~25-50 total)
      |  Bulk import all DOIs/arXiv IDs into Zotero -> metadata + PDFs
      |  Tier papers: "read in full" (5-8) / "read abstract" (~15-20) / "skim/cite" (rest)
      |
      v
2.3: Extract methods (from "read in full" tier only, 5-8 papers — PDFs from Zotero) -> comparison table
      |
      v
2.4: Check citations (of 5 best papers from 2.1+2.2) -> limitations + 3-5 new papers
      |
      v
2.5: Crystallize question (using everything from 2.1-2.4) -> research question
```

---

### STEP 2.1: Validate Gaps and Collect First Papers

**Tool (primary):** https://www.semanticscholar.org/ (unlimited search + TLDR summaries, free)
**Tool (secondary):** https://consensus.app/ (10 AI summaries/month free, then $11.99/mo)

**Input from Step 1:** The 3 selected gaps, each with its yes/no question and 2-3 keyword queries.

**Process:**

1. **Semantic Scholar first.** For each of the 3 gaps, run the 2-3 keyword queries (not the full question — keyword queries work better here). Read the TLDR + abstracts of the top 5 results per query. Save ~10-15 total relevant papers (removing duplicates and irrelevant results).

2. **Assess each gap:** If few or no results address it directly, the gap is real (OPEN). If many results answer the question, the gap is filled (CLOSED) — discard it. If all 3 gaps come back CLOSED, return to Step 1 and generate new gaps — provide the LLM with the papers you found so it can identify finer-grained gaps. A gap can also be PARTIALLY FILLED (addressed but with different methods, populations, or datasets) — these are often the best publishable gaps.

3. **Consensus second, only for the 1-2 most promising gaps.** Paste the yes/no question directly into Consensus. It synthesizes an answer across papers and shows you the evidence. Use this to confirm your Semantic Scholar assessment — a quick second opinion. This preserves your Consensus quota (10/month free) and avoids relying too heavily on AI summaries.

**Important:** As you search, **save the papers you find.** These search results are your first paper collection — don't discard them after validating the gap. **Record the DOI or arXiv ID for every paper you save** (visible on Semantic Scholar's paper page). You'll batch-import these into Zotero later.

**How many times:** 6-9 searches on Semantic Scholar (2-3 keyword queries per gap) + 1-2 Consensus queries (strongest gaps only).

**After searching, use this prompt to assess your gaps and structure the output:**

**Prompt (LLM — paste your search results):**
```
I searched Semantic Scholar for 3 research gaps using keyword queries. Here are my search results:

Gap 1: "[yes/no question from Step 1]"
Keyword queries used: [list queries]
Papers found:
[For each paper: title, year, citation count, TLDR or abstract summary]

Gap 2: "[yes/no question from Step 1]"
[same format]

Gap 3: "[yes/no question from Step 1]"
[same format]

For each gap, assess:
1. Status: OPEN (few/no results address it), PARTIALLY FILLED (addressed but with different methods/populations/datasets), or CLOSED (many results answer the question directly)
2. Evidence: Which specific papers support your assessment?
3. If PARTIALLY FILLED: What exactly is missing that makes it still worth pursuing?

Then organize all papers found into a table with columns:
| # | Paper title | Year | Venue | DOI or arXiv ID | Which gap it relates to | Why it matters for my work |

Rate your confidence (high/medium/low) in each gap assessment.
```

**Output file:** `step2_1_output.md` — validated gaps + paper collection with DOIs/arXiv IDs.

**Output (carry forward to 2.2):**
- 1-3 validated gaps rated OPEN or PARTIALLY FILLED
- ~10-15 papers found during the searches, each with its DOI or arXiv ID recorded

---

### STEP 2.2: Map Landscape — Terminology Expansion + Citation Graphs

**Tools:**
- https://www.semanticscholar.org/ (unlimited, free) — for terminology expansion searches
- https://www.connectedpapers.com/ (5 graphs/month free, then $3-5/mo) — content-similarity graphs
- https://inciteful.xyz/ (unlimited, no account needed) — citation network graphs
- https://openknowledgemaps.org/ (unlimited, keyword-based topic maps) — thematic cluster maps

**Input from Step 2.1:** The 3-5 most important papers from your ~10-15 papers.

**Process — Part A: Terminology expansion (~15-20 min).** Most false gaps survive because you searched *your* wording, but the field uses slightly different terminology. Before building citation graphs, expand your search vocabulary.

**Prompt (LLM — paste your paper list from Step 2.1):**
```
Here are the ~10-15 papers I found during gap validation in Step 2.1:

[paste paper table from step2_1_output.md]

My research gaps are:
[paste validated gaps from step2_1_output.md]

From these papers, extract:
1. Alternative task names for what I'm studying (e.g., synonyms used in different communities)
2. Dataset names mentioned (with brief description of each)
3. Benchmark names mentioned
4. Adjacent community terms (other fields studying similar problems)
5. Broader umbrella terms

Then generate 6-10 new Semantic Scholar keyword queries by combining:
- "task synonym" + evaluation
- "dataset name" + method
- "related community term" + core concept
- "benchmark name" + comparison

For each query, explain what gap it targets and what you'd expect to find.
```

After running these new searches on Semantic Scholar, re-assess your gaps:

1. **Extract alternative terms** from the LLM output and your papers. Look for:
   - Alternative task names (e.g., "talking head generation" vs. "facial reenactment" vs. "audio-driven face synthesis")
   - Dataset names (e.g., MEAD, LRS2, HDTF, VoxCeleb)
   - Benchmark names (e.g., THEval, SyncNet)
   - Adjacent community terms (e.g., "computational paralinguistics" vs. "affective computing" vs. "speech emotion recognition")
   - Broader umbrella terms (e.g., "deepfake generation" vs. "synthetic media")

2. **Run 3-6 new Semantic Scholar searches** using these new terms. Especially combine:
   - `"task synonym" + evaluation` (e.g., "facial reenactment evaluation")
   - `"dataset name" + method` (e.g., "MEAD benchmark comparison")
   - `"related community term" + core concept` (e.g., "computational paralinguistics emotion transfer")

3. **Re-assess gaps.** Check if any new papers directly address your gaps under different terminology. Reclassify if needed: OPEN → PARTIALLY FILLED, or PARTIALLY FILLED → CLOSED.

**Process — Part B: Citation graphs.** Using your best papers from Step 2.1 *and* any key papers discovered in Part A as seeds, enter them one by one into a graph tool:

- **Inciteful (free, recommended):** Shows a citation network (who cites whom). Look for: papers that appear in multiple graphs (bridge papers), and recent papers (last 2-3 years) you didn't find by keyword.
- **Connected Papers:** Shows a content-similarity graph. Good for finding conceptually related work that doesn't share citations.
- **Open Knowledge Maps:** Enter your gap keywords — including the expanded terms from Part A (not papers). Creates a thematic cluster map. Good for spotting entire subfields you might have missed.

**Why both parts in one step:** Terminology expansion and citation graphs are complementary discovery methods — one catches different wording, the other catches structural connections. Doing terminology expansion first means you feed better seed papers into your citation graphs, and you can use your expanded terms in Open Knowledge Maps.

**How many times:** 3-6 Semantic Scholar searches (Part A) + 3-5 citation graphs (Part B). Unlimited on Semantic Scholar, Inciteful, and Open Knowledge Maps. 5/month on Connected Papers.

**Output files:** Update `step2_1_output.md` with new papers and reclassified gaps. Save `zotero_import_ids.txt` (one ID per line) and `zotero_import_clean.txt` (with section comments) for the Zotero import.

**Output (carry forward to 2.3):**
- ~10-15 new papers you didn't have before (from both terminology expansion and citation graphs), each with its DOI or arXiv ID recorded
- Updated gap assessments (possibly reclassified from Part A)
- Your total collection is now ~25-50 papers (~10-15 from 2.1 + 10-35 from 2.2)
- A list of alternative terms to use in future searches throughout the pipeline
- Screenshots of the graphs (useful for understanding the field structure later)

**Import papers into Zotero now.** Before tiering, batch-import all your papers into Zotero using the DOIs/arXiv IDs you collected during 2.1 and 2.2:

**Option A — Manual (simple, no setup):**
1. Open Zotero desktop. Create a collection for your project.
2. Click the **magic wand icon** ("Add Item by Identifier") in the toolbar.
3. Press **Shift+Enter** to expand into multi-line mode.
4. Paste all your DOIs/arXiv IDs (one per line). Press **Shift+Enter** to start.
5. Zotero fetches metadata + PDFs automatically for each paper.
6. For any papers missing PDFs: select all → right-click → **"Find Available PDF(s)"**.

**Option B — Automated with `zotero_auto_import.py` (faster for large collections):**
1. Save all your DOIs/arXiv IDs in a text file (one per line, comments with `#`).
2. Open Zotero desktop.
3. Run: `python3 zotero_auto_import.py --ids your_ids.txt --collection "Your Project Name"`
4. The script creates the collection, fetches metadata from Semantic Scholar (with CrossRef fallback), and imports every paper automatically.
5. After import: select all in Zotero → right-click → **"Find Available PDF(s)"** to download PDFs.
6. Use `--dry-run` to preview what would be imported. Use `--s2-key YOUR_KEY` to avoid rate limits.

This gives you an organized library with PDFs ready for Steps 2.3, 3.2, and 6.7. Doing it here (rather than at Step 3.1) means you have the PDFs when you need to read papers in depth for extraction.

**Tier your papers before moving on.** Not every paper needs deep analysis. Classify each paper into one of three tiers:
- **Read in full** (5-8 papers): Papers closest to your gap — the ones whose methodology, metrics, or findings directly shape your experimental design. These go into Steps 2.3 and 2.4.
- **Read abstract/methods** (~15-20 papers): Papers that provide context, comparison points, or related methods. Skim to confirm they say what you think. Cite in Related Work.
- **Skim/cite** (rest): Surveys, tool papers, tangentially related work. Read intro/conclusions only. Cite for broad context in Introduction.

This tiering is not a separate step — it happens naturally as you organize your collection. The point is: **Steps 2.3 and 2.4 only apply to your top tier.**

---

### STEP 2.3: Extract Methods and Metrics

**Goal:** Build a structured comparison table that shows exactly what existing work did, how they measured it, and what they found. This table directly informs your experimental design (Step 4) and Related Work (Step 6.2).

**Tool:** Read the PDFs from Zotero (imported at the end of Step 2.2). Optionally use https://elicit.com/ for AI-assisted extraction (free tier: ~20 extractions/month, 2 custom columns), but for 5-8 papers this is usually faster to do manually.

**Input from Steps 2.1 + 2.2:** Your **"read in full" tier** (5-8 papers) — the ones closest to your gap whose methods you'll build on or compare against. Not all 25-50 papers; only the top tier from your 2.2 classification. You should have their PDFs in Zotero from the bulk import.

**Process — two passes:**

**Pass 1: Abstract-level extraction (~20 min).** Before deep-reading PDFs, do a quick first pass using just the abstracts from Semantic Scholar. This gives you a partial table fast and helps you prioritize which PDFs need the most careful reading.

**Prompt (LLM — paste the abstracts of your 5-8 top-tier papers):**
```
I need to extract methods and metrics from my top-tier papers for a comparison table.
Here are the abstracts of my "read in full" papers:

Paper 1: [title, authors, year, venue]
Abstract: [paste abstract]

Paper 2: [title, authors, year, venue]
Abstract: [paste abstract]

[...repeat for all 5-8 papers]

For each paper, extract what you can into this table format:
| Paper (author, year) | Publication status | Method/approach | Dataset | Computational metrics | Effect sizes reported | Human evaluation method | Sample size | Key finding |

Mark cells you cannot determine from the abstract alone with (!).

After the table, write a summary of:
1. What metrics are standard across these papers?
2. What datasets are commonly used?
3. What human evaluation approaches are typical?
4. What sample sizes are typical?
5. Where is the clearest methodological gap?
```

For each of your 5-8 top-tier papers, fill in what you can from the abstract alone. Mark cells you cannot fill with `(!)` — these are what you'll target in pass 2.

**Pass 2: PDF deep read (1-3 hours).** Open each PDF in Zotero and fill the `(!)` cells from pass 1. Focus on the Methods and Results sections. For each paper, answer: what did they measure, how did they measure it, what data did they use, and what did they find? This is also when you verify that what the abstract claims matches what the paper actually did.

**Table columns to extract:**

| Paper (author, year) | Publication status | Method/approach | Dataset | Computational metrics | Effect sizes reported | Human evaluation method | Sample size | Key finding |
|---|---|---|---|---|---|---|---|---|

Column guide:
- **Method/approach:** What technique or system did they use or propose?
- **Dataset:** Which datasets, how many samples, what characteristics (e.g., emotional vs. neutral)?
- **Computational metrics:** Which automatic metrics did they report (e.g., FID, LSE-C, WER, MOS)?
- **Effect sizes reported:** Correlation coefficients, Cohen's d, percentage improvements — any quantitative measure of magnitude, not just p-values.
- **Human evaluation method:** Did they run a user study? What design (MOS, A/B preference, Likert scale)?
- **Sample size:** How many models compared, how many stimuli, how many human participants?
- **Key finding:** One sentence: what is the main takeaway relevant to your gap?

**After filling the table, write a brief summary** of the patterns you see across papers:
- What metrics are standard in your field?
- What datasets are commonly used?
- What human evaluation approaches are typical?
- What sample sizes are typical?
- Where is the clearest methodological gap (what nobody does)?

**How many times:** 1-2 searches on Elicit, plus manual extraction for remaining top-tier papers.

**Output file:** `step2_3_output.md` — the comparison table + summary of standard practices.

**Output (carry forward to 2.4):**
- Completed comparison table (5-8 rows from your top tier)
- A summary of: standard metrics in your field, typical sample sizes, common datasets, common human evaluation approaches
- Any papers you need to re-tier (e.g., a "read abstract" paper turns out to be more important than expected — promote it to "read in full")

---

### STEP 2.4: Check Citation Context and Limitations

**Goal:** Find out what other researchers think is wrong with or missing from the papers closest to your gap. This gives you limitations for your Introduction/Discussion and may reveal competitor approaches you missed.

**Tool (Option A — manual with Scite):** https://scite.ai/ (7-day free trial, then ~$10/mo)
**Tool (Option B — manual with Semantic Scholar):** https://www.semanticscholar.org/ (unlimited — has citation intent + context snippets, but no supporting/contrasting labels)
**Tool (Option C — automated with script):** `step2_4_citation_context.py` (uses Semantic Scholar API, free, fully automated)

**Input from Steps 2.1 + 2.2:** The **5 most important papers** from your collection — the ones closest to your gap.

**Process:**

- **Option A — Scite.ai (fastest manual method):** Search each paper. Scite classifies every citation as "supporting", "contrasting", or "mentioning". Filter by **contrasting** — these reveal limitations and criticisms instantly.
- **Option B — Semantic Scholar website (free manual method):** Search each paper, click "Citations". Look at citation intent (background, methodology, result) and influential citation flags. Click into individual citations to read context snippets. Works, but slower — you have to read each snippet and judge tone yourself.
- **Option C — Automated script (recommended for automation):** Edit the `TOP_PAPERS` list at the top of the script to match your papers, then run:

**Command:**
```
python3 step2_4_citation_context.py --s2-key YOUR_S2_KEY --output step2_4_output.md
```

The script fetches all citations for your top 5 papers via the Semantic Scholar API, extracts context snippets, detects limitation/criticism keywords, flags "future work" mentions, and identifies influential citations. Output goes to `step2_4_output.md`.

**Note on very recent papers:** If your top papers are from the last 1-2 years, they may have very few citations (0-15). This is normal — it actually confirms your topic is new and your gaps are open. Supplement with manual reading of the papers' own Limitations/Future Work sections.

For each paper, note:
- 2-3 limitations others have identified (or that the authors themselves state)
- Any competitor/alternative approaches you missed
- Whether your gap is mentioned as "future work" by anyone

**How many times:** 5 paper lookups. 7-day trial on Scite; no limit on Semantic Scholar or the script.

**Output file:** `step2_4_output.md` — limitations list + new papers + citation context snippets.

**Output (carry forward to 2.5):**
- A limitations list (for your Introduction and Discussion)
- 3-5 new papers discovered through citations (add to your collection)
- Your total collection is now ~28+ papers

---

### STEP 2.5: Crystallize Research Question

**Goal:** Synthesize everything from 2.1-2.4 into one specific, testable research question and a clear contribution statement. This anchors everything from Step 3 onwards.

**Tool:** ChatGPT, Claude, or Qwen

**Input from Steps 2.1-2.4:** The output files from all previous substeps:
- `step2_1_output.md` — validated gaps + paper collection (from 2.1 and 2.2)
- `step2_3_output.md` — comparison table of methods and metrics
- `step2_4_output.md` — limitations and citation context

**Prompt:**
```
Based on my literature search, here is what I found:
- Gaps that are confirmed open: [paste validated gaps from 2.1, updated in 2.2]
- Related work landscape: [key observations from 2.2 graphs]
- Common metrics and methods: [paste comparison table from 2.3]
- Limitations of existing work: [paste limitations list from 2.4]

My system/tool/approach is: [brief description]

Help me formulate:
1. A specific, testable research question
2. A one-sentence contribution statement ("We are the first to..." or "We provide...")
3. Why this question matters (motivation in 2-3 sentences)
4. How this extends or differs from the closest existing work
```

**Process:** Review the output. The research question must be specific enough to design an experiment around. If too broad, ask the LLM to narrow it. If the LLM produces multiple options, pick the one that (a) matches your strongest gap, (b) you can actually execute with your resources, and (c) has the clearest path to a publishable contribution.

**Output file:** `step2_5_output.md` — research question + contribution statement + motivation.

**Output:**
- One clear research question + contribution statement
- This anchors everything from Step 3 onwards

---

### Step 2 summary

**Data flow:**

| Step | Input | Output | Output file | Papers added |
|------|-------|--------|-------------|-------------|
| 2.1 | 3 gaps + queries from Step 1 | Validated gaps + first papers | `step2_1_output.md` | ~10-15 |
| 2.2 | Top 3-5 papers from 2.1 | Terminology expansion + citation graph papers + reclassified gaps + **tiered collection** + **Zotero library with PDFs** | Update `step2_1_output.md` + `zotero_import_ids.txt` | +10-35 (~25-50 total) |
| 2.3 | "Read in full" tier only (5-8 PDFs from Zotero) | Comparison table + summary of standard practices | `step2_3_output.md` | 0 (extraction, not search) |
| 2.4 | Top 5 papers from 2.1+2.2 | Limitations + new papers | `step2_4_output.md` | +3-5 |
| 2.5 | Everything from 2.1-2.4 | Research question + contribution statement | `step2_5_output.md` | 0 (synthesis) |

**Recommended tools (maximize AI assistance):**

| Tool | Role | AI-powered? | Cost |
|------|------|------------|------|
| Semantic Scholar | Gap validation (2.1) + terminology expansion (2.2) | Partial (TLDRs) | Free, unlimited |
| Consensus | Secondary gap confirmation for strongest gaps (2.1) | Yes | 10 free/mo, then $11.99/mo |
| Inciteful | Citation graphs — find connected papers (2.2) | No | Free, unlimited |
| Zotero + `zotero_auto_import.py` | Batch-import papers by identifier (end of 2.2) | No | Free |
| Elicit | Extract methods/metrics from papers (2.3) | Yes | Free search, limited extraction |
| Scite.ai | Find limitations via citation classification (2.4) | Yes | 7-day trial, then ~$10/mo |
| `step2_4_citation_context.py` | Automated citation context analysis (2.4) | No (API) | Free |
| LLM | Synthesis and research question (2.5) | Yes | Free tiers |

**Free alternatives (if you want $0 cost):**

| Step | Instead of | Use | Trade-off |
|------|-----------|-----|-----------|
| 2.1 | Consensus (secondary) | Skip Consensus, use only Semantic Scholar | You lose the AI-synthesized confirmation; rely entirely on your own TLDR reading |
| 2.2 (import) | Manual magic wand | `zotero_auto_import.py` | None — strictly better for large collections. Requires Zotero running. |
| 2.4 | Scite.ai | `step2_4_citation_context.py` or manual Semantic Scholar | Script is free + automated; manual S2 is free but slower. Neither has Scite's supporting/contrasting labels. |

**Total cost with AI tools: ~$22/mo** (Consensus + Scite after trials)
**Total cost with free alternatives: $0**

**Automation scripts (included in this pipeline):**

| Script | Step | What it does | API needed |
|--------|------|-------------|------------|
| `zotero_auto_import.py` | 2.2 | Creates Zotero collection + imports papers by DOI/arXiv ID | Semantic Scholar (free) |
| `step2_4_citation_context.py` | 2.4 | Fetches citation context, detects limitations/criticism, flags future work | Semantic Scholar (free) |
| `zotero_tag_papers.py` | 3.1 | Auto-tags papers by role and tier in Zotero | Zotero local API (free) |
| `step3_2_gemini_qa.py` | 3.2 | Uploads PDFs, asks research questions, saves grounded answers with citations | Gemini API (free tier) |

**API keys needed:**
- **Semantic Scholar** (free, recommended): https://www.semanticscholar.org/product/api#api-key-form — pass with `--s2-key` or `export S2_API_KEY=your_key`
- **Gemini API** (free): https://aistudio.google.com/apikey — pass with `--api-key` or `export GEMINI_API_KEY=your_key`

---

## VERIFICATION CHECKPOINT 1: Before Moving to Step 3

AI tools do the heavy lifting in Step 2 — finding papers, extracting data, identifying limitations. Before you build on their output, verify at two levels:

**Verify synthesis (Step 2.5 output):** The LLM in Step 2.5 synthesized everything from 2.1-2.4 into a research question. Spot-check:
- Does the research question follow logically from the validated gaps (2.1, updated in 2.2)?
- Are the methods/metrics (from 2.3) accurately described, or did the LLM embellish?
- Are the limitations (from 2.4) correctly attributed to the right papers?
- Did the LLM add theoretical connections that aren't in your source data?

**Read in full (5-8 papers):** Your "read in full" tier from Step 2.2 — papers closest to your gap + those whose methods you'll adapt. For these, you need to know exactly what they did.

**Read abstract/methods (~15-20 papers):** Your "read abstract" tier — context and comparison papers. Skim to confirm claims.

**Skim/cite (rest):** Surveys and tangential papers you cite for broad context.

---

## STEP 3: KNOWLEDGE MANAGEMENT

### STEP 3.1: Organize and Tag Papers — Zotero

**Tool:** https://www.zotero.org/ (100% free, unlimited, with browser extension)

**Input:** Your Zotero library, already populated from the bulk import at the end of Step 2.2 (plus any papers added during Step 2.4).

**Process:** Your papers are already in Zotero with metadata and PDFs from the bulk import. This step is about **organizing**, not importing:

1. **Tag papers by role:** `methods`, `evaluation`, `dataset`, `related-work`, `motivation`
2. **Tag papers by tier:** `read-in-full`, `read-abstract`, `skim-cite` (matching your Step 2.2 tiering)
3. **Verify:** Spot-check that metadata is correct (sometimes DOI resolution gets wrong year or venue). Fix any issues.
4. **Add any stragglers:** Papers from Step 2.4 (citation context) that weren't in the original batch — add them by identifier now.

**Option A — Manual:** Open Zotero, right-click each paper, add tags manually. Straightforward for <20 papers.

**Option B — Automated with `zotero_tag_papers.py`:** The script matches papers by DOI/arXiv ID to the category mappings from Step 2.1 output, then applies role and tier tags via the local API. Run:
```
python3 zotero_tag_papers.py --collection "Your Project Name"
python3 zotero_tag_papers.py --collection "Your Project Name" --dry-run  # preview first
```
Edit the `ID_TO_CATEGORY` and tier lists at the top of the script to match your paper collection. After running, manually verify a few papers in Zotero to confirm tags are correct.

**Why this is essential (not redundant):** Zotero is the only tool that stores citation metadata for export to Word/LaTeX. No other tool replaces it. You'll use it in every writing step.

**Output:** Organized, tagged library. Use later for citation export (Step 6) and quick reference.

### STEP 3.2: Grounded Q&A on Research Papers

**Goal:** Ask specific questions of your top papers and get grounded, cited answers. This cross-checks the abstract-level data from Step 2 against full-text content and extracts precise details (metrics, sample sizes, datasets) needed for experimental design.

**Why this matters:** In Step 2, your data came from abstracts and metadata (via Semantic Scholar, Consensus, etc.). This step uses a different AI working from **full PDFs** to corroborate and deepen that data. If the abstract-level extraction from Step 2.3 disagrees with the full-text answer here, the full-text answer is more reliable. Flag discrepancies.

**Input:** PDFs of the **5-8 papers you read in full** (from your Zotero library) + optionally your comparison table from Step 2.3.

---

**Option A — Automated with Gemini API + `step3_2_gemini_qa.py` (recommended)**

The Gemini API provides the same grounded Q&A as NotebookLM (it's the same underlying model) but is fully programmable. The script uploads your PDFs to a Gemini File Search Store, asks all questions automatically, and saves grounded answers with citations.

**Setup (one-time):**
1. Get a free API key at https://aistudio.google.com/apikey
2. Export it: `export GEMINI_API_KEY=your_key`
3. Requirements: `pip install google-genai`

**Run:**
```
python3 step3_2_gemini_qa.py --pdf-dir /path/to/your/pdfs
python3 step3_2_gemini_qa.py --pdf-dir /path/to/your/pdfs --api-key YOUR_KEY
```

The script uses 13 built-in research questions covering three categories:
1. **Experimental design (6 questions):** metrics, datasets, sample sizes, human evaluation, effect sizes
2. **Gap verification (4 questions):** whether any paper already does what you propose
3. **Writing (3 questions):** motivations, open challenges, state of the art

To use custom questions: `--questions your_questions.txt` (one question per line).

**Cost:** Free tier (Gemini 2.5 Flash) allows ~250 requests/day and 250K tokens/minute. A full run with 15-20 papers and 13 questions uses ~15 requests — you can run it many times per day.

**Where to find your PDFs:** Zotero stores PDFs in its data directory. Find it via Zotero → Edit → Settings → Advanced → Files and Folders → Data Directory Location. PDFs are inside `storage/` subfolders. Alternatively, export your top-tier collection from Zotero: right-click collection → "Export Collection" → choose a format that includes files, or manually copy PDFs to a working directory.

---

**Option B — Manual with NotebookLM (if you prefer a visual interface)**

**Tool:** https://notebooklm.google/ (free with Google account, up to 50 sources per notebook)

1. Create a new notebook and upload your top-tier PDFs
2. Ask the same questions (pre-prepared in `step3_2_notebooklm_questions.md`)
3. Copy-paste answers to `step3_2_output.md`
4. Budget ~30-45 minutes of browser work

NotebookLM cites the source passage for each answer — click through to verify.

---

**Questions to ask (both options use the same questions):**

For experimental design (Step 4):
- "What exact computational metrics did each paper use to evaluate lip synchronization / voice quality?"
- "What human evaluation methods did these papers use? Study design, number of participants?"
- "What datasets did each paper use? How many samples, what types of speech?"
- "What sample sizes were used? Models compared, stimuli per condition, human evaluators?"
- "Did any papers report effect sizes, confidence intervals, or correlation coefficients?"

For gap verification:
- "Do any papers benchmark multiple voice cloning + lip sync systems on the same stimuli?"
- "Do any papers compare quality between emotional and neutral speech conditions?"
- "What do papers say about the limitations of LSE-C/LSE-D metrics?"

For writing (Introduction, Related Work, Discussion):
- "What motivations do papers give for talking head evaluation research?"
- "What open challenges or future work do papers identify?"

**Output file:** `step3_2_output.md` — grounded answers with source citations.

**Output:** Grounded answers with citations to your uploaded papers. Save these — they feed directly into Step 4 (metrics, sample sizes) and Step 6 (writing).

---

## STEP 4: EXPERIMENTAL DESIGN

### STEP 4.1: Define Goal and Hypotheses

**Tool:** ChatGPT, Claude, or Qwen

**Input from previous steps:**
- Research question and contribution statement from `step2_5_output.md`
- Metrics, datasets, sample sizes, and effect sizes from `step3_2_output.md` (Experimental Design answers)
- Validated gaps from `step2_1_output.md`

**Prompt:**
```
My research question is: "[paste research question from step2_5_output.md]"

My contribution statement is: "[paste from step2_5_output.md]"

From my literature review (grounded Q&A on full papers), I found that:

Standard metrics used in the field:
[paste the answers to Q1 (lip sync metrics) and Q2 (audio metrics) from step3_2_output.md]

Typical sample sizes:
[paste the answer to Q5 (sample sizes) from step3_2_output.md]

Effect sizes from literature:
[paste the answer to Q6 (effect sizes/correlations) from step3_2_output.md]

Existing datasets:
[paste the answer to Q4 (datasets) from step3_2_output.md]

Gap verification:
[paste the answers to Q7-Q10 from step3_2_output.md]

Preliminary hypotheses from my literature synthesis:
[paste the "Specific Testable Hypotheses" section from step2_5_output.md]

Help me define:
1. Formal hypotheses (main + secondary), each with:
   - A clear directional prediction
   - The rationale from the literature
   - Which specific finding from my literature review supports this prediction
2. For each hypothesis: what a positive result looks like, what a negative/null result would mean, and whether a null result is still publishable
3. A priority ordering of the hypotheses (which is most novel, which is most important for the contribution)
```

**Output file:** `step4_1_output.md` — formal hypotheses with rationale and expected outcomes.

### STEP 4.2: Design Variables and Conditions

**Tool:** ChatGPT, Claude, or Qwen (same conversation as 4.1)

**Input:** Hypotheses from Step 4.1 + metrics/sample sizes from Step 3.2

**Prompt:**
```
Given the hypotheses I just defined, and using the literature data I provided, help me design the full experiment:

1. Define all independent variables and their levels. For each IV, list the specific tools/conditions to use (choose tools that are open-source, freely available, and cover a range of quality levels).
2. Define all dependent variables. For each DV:
   - Specify how it is measured (which tool, pretrained model, formula)
   - Categorize as: computational (automated) or human (requires participants)
   - For human ratings, specify the scale type (MOS, Likert, 2AFC) and anchors
3. Specify the factorial design (N × M × K conditions). Calculate total conditions and stimuli.
4. Choose within-subjects vs between-subjects design and justify.
5. Describe stimuli construction: source dataset, how many identities, sentences per condition, total generated videos.
6. List confounding variables and how to control each one.
7. Recommend the statistical test (LMM vs ANOVA) and justify.
8. Specify the multiple comparisons correction (Bonferroni vs BH FDR) and justify.
9. Specify effect size measures for each test (eta-squared, Cohen's d, Spearman ρ).
10. Estimate required sample size using specific effect sizes from the literature I provided. State G*Power parameters.
11. Define exclusion criteria for participants/data.
```

**Important:** Do NOT rely on the LLM's sample size estimate as final. Use G\*Power (free: https://www.psychologie.hhu.de/gpower) or equivalent to compute the required N from the expected effect size, alpha, and power. The LLM can help choose the right test family and effect size type, but the computation must come from a dedicated tool.

**Output file:** `step4_2_output.md` — complete experimental design with all variables, conditions, statistical plan, and power analysis parameters.

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

**Output file:** `step4_3_output.md` — complete preregistration draft. File it at https://aspredicted.org/ (free) or https://osf.io/ (free) **before proceeding to Step 5**. A preregistration filed after seeing results is not a preregistration.

### STEP 4.3b: Ethics and Institutional Approval

If your study involves human participants, animal subjects, or sensitive data, submit your experimental design and preregistration to your institution's IRB/ethics board **before collecting data**. Do not proceed to data collection until approval is granted. Record the approval number for inclusion in the Methods section (Step 6.3).

If your study is purely computational with no human subjects, document why ethics review was not required — many journals now require this statement explicitly.

### STEP 4.4: Plan Implementation Steps

**Tool:** ChatGPT, Claude, or Qwen (same conversation as 4.1-4.3)

**Input:** Experimental design from Step 4.2 + preregistration from Step 4.3

**Prompt:**
```
I need to implement this experiment. Here is my experimental design:
[paste the Design Summary Table from step4_2_output.md]

My setup: [brief technical description — e.g., "Linux workstation with GPU, Python 3, all tools will be open-source"]

Break down the implementation into concrete coding tasks organized by phase:
1. Phase 1 — Data Preparation: source dataset download, tool installation, wrapper scripts
2. Phase 2 — Stimulus Generation: voice cloning step, lipsync step, ground truth + attention checks
3. Phase 3 — Computational Evaluation: per-metric scripts, merge into master CSV
4. Phase 4 — Human Evaluation: web interface, pilot study, full study
5. Phase 5 — Statistical Analysis: exclusions, LMM, metric validation, figures/tables

For each task, specify:
- Task ID (for dependency tracking)
- Input files/data
- Output files/data
- Dependencies (which tasks must complete first)
- Estimated effort (hours/days)

Also draw a dependency graph showing which tasks can run in parallel.
```

**Output file:** `step4_4_output.md` — implementation task list with inputs, outputs, and dependencies. Each task becomes a coding prompt for Step 5.

### Step 4 data flow

| Step | Input | Output | Output file |
|------|-------|--------|-------------|
| 4.1 | Research question (2.5) + metrics/datasets (3.2) + gaps (2.1) | Formal hypotheses + expected outcomes | `step4_1_output.md` |
| 4.2 | Hypotheses (4.1) + literature data (3.2) | Full experimental design: IVs, DVs, statistics, power | `step4_2_output.md` |
| 4.3 | Design (4.2) | Preregistration (AsPredicted format) | `step4_3_output.md` |
| 4.3b | Design (4.2) + preregistration (4.3) | IRB approval (if needed) | — |
| 4.4 | Design (4.2) | Implementation task list with dependencies | `step4_4_output.md` |

### CHECKPOINT 2: Review Experimental Design

Before coding, verify the LLM-generated design makes sense:
- Is the statistical test appropriate for your data type and design? Cross-check with what papers in your comparison table (Step 2.3) used.
- Is the sample size justified by G\*Power, not just the LLM's estimate?
- Does the design actually test your hypothesis?
- Are the chosen tools (VC systems, lipsync systems) still available and working?
- If possible, have a colleague or advisor review the design. Catching a flaw here saves weeks of wasted implementation.

---

## STEP 5: CODING + EXECUTION

**Tool:** Claude Code (CLI)

**Input:** Task list from Step 4.4 + experimental design from Step 4.2.

This step has two phases: **planning** (interactive, you review) and **execution** (unattended, fully automated).

### Step 5a: Plan (interactive)

**Setup:** Initialize a Git repository and create a `CLAUDE.md` file in your project root. This file gives Claude Code persistent context about your project — it reads it automatically at the start of every session. Include:

```markdown
# Project: [your project name]

## What this is
[1-2 sentence description of the experiment]

## Key files
- `config.yaml` — experiment configuration
- `step4_2_output.md` — experimental design
- `step4_4_output.md` — implementation task list

## Allowed operations
- Install Python packages with pip
- Clone git repos into tools/repos/
- Download model checkpoints
- Run Python scripts
- Use ffmpeg for media processing
- Read/write files in the experiment directory
```

**Process:** Open Claude Code normally and paste this prompt:

```
Read step4_4_output.md (implementation tasks) and step4_2_output.md (experimental design).
Enter plan mode. Design the full implementation: config files, script structure, tool
wrappers, and execution pipeline. Present the plan for my review.
```

Claude Code will explore the codebase, read your design documents, and produce a detailed implementation plan. **Review the plan carefully** — this is your last checkpoint before unattended execution. Verify:
- The pipeline structure makes sense
- The right tools/models are being used
- The metrics match your preregistration
- The statistical analysis matches your design

Approve the plan when satisfied.

### Step 5b: Execute (unattended)

Once the plan is approved, you want Claude Code to implement everything, run it, and fix any errors — **without stopping to ask you for permission** on every file write, pip install, or script execution.

**The problem:** By default, Claude Code asks for confirmation before running shell commands, writing files, etc. For a complex experiment pipeline that installs dozens of packages, downloads model checkpoints, runs multiple scripts, and fixes compatibility errors along the way, this means hundreds of confirmations over several hours.

**The solution:** Launch Claude Code with the `--dangerously-skip-permissions` flag. This tells it to execute all tool calls without asking — file writes, pip installs, git clones, script runs, everything.

```bash
claude --dangerously-skip-permissions
```

Then paste this prompt:

```
Read the approved implementation plan. Implement everything from scratch: write all scripts
and config files, install all dependencies, download all model checkpoints, then run the
full pipeline end to end. When something fails, diagnose the error, fix it, and re-run.
Keep iterating until all phases complete successfully (data preparation, generation,
metrics computation, statistical analysis). Do not stop to ask me questions — make
reasonable decisions and keep going. When everything is done, print a final summary of
what was generated, any failures, and where to find the results.
```

**What happens:** Claude Code will autonomously:
1. Write all scripts, config files, and tool wrappers
2. Install Python packages (`pip install`)
3. Clone tool repositories (`git clone`)
4. Download model checkpoints (HuggingFace, Google Drive, etc.)
5. Run each pipeline phase in order
6. When something breaks (and it will — version incompatibilities, API changes, missing dependencies), it reads the error, patches the code, and retries
7. Continue until all phases complete

This typically takes 1-4 hours depending on the experiment complexity, model download sizes, and how many compatibility issues arise. You can walk away and come back to check results.

**Common issues Claude Code handles automatically:**
- Python version incompatibilities (e.g., NumPy 2.x removing `np.float`, Python 3.12+ removing `pkg_resources`)
- Library API changes (renamed parameters, moved modules)
- Missing dependencies not listed in requirements files
- Model download failures (retries, switches mirrors)
- Face detection failures on specific frames (logs and continues)
- GPU memory issues (falls back to CPU or reduces batch size)

**Output:** Working code + generated stimuli + metrics CSV + statistical results + figures, all in the experiment directory.

### Checkpoint 3: Verify results

Before proceeding to writing, verify the outputs:
- **Stimuli:** Open a few generated videos from each condition — do they look/sound reasonable?
- **Metrics CSV:** Correct number of rows? No unexpected NaN columns? Values in plausible ranges?
- **ANOVA/stats:** Do significant effects make sense given what you see in the stimuli?
- **Figures:** Do heatmaps and comparison plots show meaningful variation?

If something looks wrong, open a new Claude Code session (with or without `--dangerously-skip-permissions`) and describe what needs fixing.

---

## DO ACTUAL EXPERIMENT (if applicable)

If your experiment is purely computational (e.g., a benchmark), Step 5b already ran it — the stimuli are generated, metrics are computed, and statistical analysis is done. Skip to Step 6.

If your experiment has a **human evaluation component** (e.g., MOS ratings, perceptual studies):

**Pilot first:** Run a small pilot (N=5-10) before the full study. Verify: (1) the evaluation app works as designed, (2) output format matches what analysis scripts expect, (3) results are plausible. Fix issues before running the full experiment.

Then run the full study, collect data, and run the human evaluation analysis scripts from Step 5.

---

## STEP 6: WRITING

**Tools:**
- **Claude Code** — drafts each section grounded in your actual project files
- **Gemini File Search API** — grounded Q&A over your literature PDFs with citation metadata (replaces NotebookLM)
- **Trinka API** — academic-specific grammar and style, trained on millions of peer-reviewed papers (closest Writefull replacement)
- **Vale** + custom academic rules — detects overclaiming, hedging issues, filler/boilerplate (YAML-configurable)
- **CheckMyTex** — unified LaTeX checker combining LanguageTool + aspell + ChkTeX + proselint in one pass
- **MoreThanSentiments** — quantifies boilerplate score per paragraph (flags filler)
- **LanguageTool + proselint + textstat + PassivePy** — general grammar, style, readability, passive voice
- **statcheck + languagecheck** — statistical result verification + scientific LaTeX checks (replaces Penelope.ai)
- **PaperBanana** (pip package) — AI-generated methodology diagrams via Gemini API
- **Semantic Scholar API** — automated paper existence verification

**Principle:** Every section is drafted by Claude Code reading your actual project files — not from the LLM's general knowledge. The grounding sources are the files you already have from Steps 1-5. Claude Code reads them directly, so there is no copy-pasting between tools and no opportunity for information to get distorted in transit. For literature Q&A that requires grounding in the actual PDFs (not just your step outputs), the Gemini File Search API provides retrieval-augmented answers with source metadata.

**Anti-hallucination approach:**
- Methods section: Claude Code reads `config.yaml`, the actual scripts, and `step4_2_output.md` — it describes what the code *actually does*, not what it thinks an experiment should do
- Results section: Claude Code reads `results/all_metrics.csv` and `results/computational_anova.csv` — every number comes directly from the data files
- Introduction/Related Work: Gemini File Search API answers questions grounded in your PDFs (with citation metadata), then Claude Code drafts using those grounded answers + your step2/3 outputs
- Discussion: Claude Code reads its own Results draft + the literature outputs — comparisons are grounded in both
- Verification: `statcheck` recomputes p-values from reported test statistics to catch mismatches; Semantic Scholar API confirms every cited paper exists

**Style principle:** Technical papers should describe what was done, not pad word count. Every sentence should convey information. No "In recent years, X has become increasingly important" filler. No restating things already said. If a paragraph doesn't add new information, delete it.

**How to run:** You can draft all sections in a single Claude Code session. Launch with `--dangerously-skip-permissions` so it can read all files without confirmations. Paste the prompt for each section one at a time (or all at once if you want the full draft in one go).

**Setup before starting:**

1. **BibTeX export** from Zotero:
```bash
# Option A: manual export from Zotero (File > Export Library > BibTeX)
# Option B: automated via pyzotero
python3 -c "
from pyzotero import zotero
zot = zotero.Zotero('YOUR_LIBRARY_ID', 'user', 'YOUR_API_KEY')
items = zot.collection_items('YOUR_COLLECTION_KEY', format='bibtex')
with open('references.bib', 'w') as f:
    f.write(items)
"
```

2. **Gemini File Search store** (grounded literature Q&A):
```python
# run once to create a searchable index of your PDFs
from google import genai
from google.genai import types
import time, glob

client = genai.Client(api_key="YOUR_GEMINI_API_KEY")
store = client.file_search_stores.create(config={'display_name': 'literature'})

for pdf in glob.glob("pdfs/*.pdf"):
    op = client.file_search_stores.upload_to_file_search_store(
        file=pdf, file_search_store_name=store.name,
        config={'display_name': pdf.split('/')[-1]}
    )
    while not op.done:
        time.sleep(2)
        op = client.operations.get(op)
    print(f"Indexed: {pdf}")

print(f"Store name: {store.name}")  # save this for later queries
```

3. **Install writing quality tools:**
```bash
# Core style + grammar stack
pip install language-tool-python proselint textstat PassivePy statcheck paperbanana
pip install MoreThanSentiments   # boilerplate detection
pip install CheckMyTex           # unified LaTeX checker (requires Java for LanguageTool)
python3 -m spacy download en_core_web_sm   # required by PassivePy

# Vale prose linter (with academic rules)
# Linux:
wget -qO- https://github.com/errata-ai/vale/releases/latest/download/vale_Linux_64-bit.tar.gz | tar xz -C ~/.local/bin vale
# macOS: brew install vale

# Create academic rules for Vale:
mkdir -p .vale/styles/Academic
cat > .vale/styles/Academic/Overclaiming.yml << 'YAML'
extends: existence
message: "Overclaiming: '%s'. Consider hedging (e.g., 'suggests', 'indicates')."
level: warning
tokens:
  - clearly shows
  - clearly demonstrates
  - undoubtedly
  - undeniably
  - obviously
  - it is well known
  - it is widely recognized
  - proves that
  - confirms that
YAML
cat > .vale/styles/Academic/Filler.yml << 'YAML'
extends: existence
message: "Filler phrase: '%s'. Can this sentence start with substance instead?"
level: warning
tokens:
  - In recent years
  - It is worth noting that
  - It should be noted that
  - It is important to note
  - As we all know
  - Needless to say
  - It goes without saying
  - In the current study
  - The aim of this paper is
YAML
cat > .vale.ini << 'INI'
StylesPath = .vale/styles
MinAlertLevel = suggestion
[*.tex]
BasedOnStyles = Academic
INI

# Trinka API (academic-specific grammar, closest to Writefull)
# Sign up at https://developer.trinka.ai/ for a free API key ($5 credit)
# Usage: POST https://api.trinka.ai/api/v1/grammar with your text

# For languagecheck: git clone https://github.com/JohannesBuchner/languagecheck
```

Then tell Claude Code to use `\cite{key}` references matching the BibTeX keys.

---

### STEP 6.0: Visualization (before writing)

**Tool:** PaperBanana (pip package) or Claude Code (matplotlib/tikz)

Step 5b already generated results figures (heatmaps, comparisons, interaction plots). For the **methodology figure**, you have two options:

**Option A — PaperBanana** (AI-generated methodology diagram via Gemini API):
```bash
# Install: pip install paperbanana
# Generates a publication-ready methodology figure from a description
paperbanana generate --prompt "Voice cloning and lipsync factorial benchmark pipeline: \
  5 Spanish-speaking actors (2 conditions: neutral/emotional) → 20 source clips (5s, face-cropped 512x512) → \
  4 VC systems (XTTS-v2, kNN-VC, OpenVoice V2, CosyVoice 2) → 80 cloned audios → \
  3 lipsync systems (Wav2Lip, SadTalker, VideoReTalking) → 240 stimulus videos → \
  10 computational metrics (sync: LSE-C/LSE-D/AVSM/AVSU/LMD; visual: FID/SSIM/CPBD; audio: WavLM-sim/Mel-sim/WER) → \
  factorial ANOVA with BH FDR correction" \
  --output figures/fig1_methodology.pdf --style academic
```

**Option B — Claude Code** (matplotlib):
```
Read config.yaml and the experiment scripts (01-05). Generate a methodology diagram
as a publication-ready figure showing the pipeline: source videos → face cropping →
VC systems → lipsync systems → metrics → analysis. Use matplotlib with clean boxes
and arrows. Save as figures/fig1_methodology.pdf and .png.
```

The key is: have all figures ready before drafting so you can reference them.

---

### STEP 6.1: Introduction

**Step A — Ground in literature** (Gemini File Search API):
```python
# Query your PDF index for introduction-relevant context
from google import genai
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

queries = [
    "What are the main practical applications of talking-head generation and voice cloning?",
    "What existing benchmarks evaluate voice cloning or lipsync systems? What datasets and metrics do they use?",
    "Has anyone evaluated voice cloning and lipsync systems together as a combined pipeline?",
]
for q in queries:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=q,
        config={"tools": [{"file_search": {"store": "YOUR_STORE_NAME"}}]}
    )
    print(f"Q: {q}\nA: {response.text}\n")
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
        print(f"  Source: {chunk.retrieved_context.title}")
```
Save the output as `writing/intro_grounding.txt`.

**Step B — Draft** (Claude Code prompt):
```
Read these files:
- step2_1_output.md (validated gaps — categories A-J with ~55 papers)
- step2_5_output.md (research question and contribution statement)
- step2_3_output.md (comparison table of 7 top papers with venues and metrics)
- step3_2_output.md (grounded Q&A with PDF citations)
- writing/intro_grounding.txt (grounded answers from Gemini File Search)
- references.bib (BibTeX keys for citations)

Write an Introduction section in LaTeX (~500-600 words, 4 paragraphs). Follow this exact structure:

PARAGRAPH 1 — WHAT AND WHY: Define talking head generation as combining VC + lipsync.
Name 2-3 applications. Cite 1-2 survey papers.

PARAGRAPH 2 — WHAT EXISTS: Name the specific benchmarks and what they cover.
"THEval [cite] benchmarks 17 lipsync models..." "ClonEval [cite] evaluates 5 VC systems..."
"AV-Deepfake1M++ [cite] combines 5 TTS with 3 lipsync but for detection, not quality."
Get the exact numbers from step2_3_output.md — do not guess.

PARAGRAPH 3 — THE GAP: State precisely what is missing.
"No study has evaluated VC and lipsync systems jointly in a factorial design on the same
stimuli for quality assessment." Then explain WHY this matters with 2-3 numbered reasons:
(1) component interaction, (2) metric biases (cite Zhang and Yaman), (3) practitioner need.

PARAGRAPH 4 — THIS PAPER: "We present the first factorial benchmark of VC×lipsync pipelines,
evaluating N VC systems crossed with M lipsync systems on K source clips from P actors..."
Get N, M, K, P from config.yaml and manifests. End with section preview.

Rules:
- Every factual claim MUST have a \cite{}. Only use keys from references.bib.
- Cross-check paper descriptions against step2_3_output.md and intro_grounding.txt.
  If two sources disagree, flag it and use the PDF-grounded version.
- No filler: no "In recent years", no "It is widely recognized", no "has attracted
  significant attention". Start each paragraph with a concrete statement.
- Do not describe papers you haven't read. Only cite papers from your step2 outputs.
```

**Step C — Quality check** (run after drafting each section):
```bash
# === Quick check: Vale (academic-specific rules) + CheckMyTex (unified LaTeX) ===
vale manuscript.tex                          # overclaiming, filler, custom academic rules
checkmytex manuscript.tex                    # LanguageTool + aspell + ChkTeX + proselint combined

# === Detailed check: individual tools ===
python3 -c "
import language_tool_python, proselint, textstat
import re

with open('manuscript.tex') as f: text = f.read()
body = re.sub(r'\\\\[a-zA-Z]+(\{[^}]*\})*', '', text)  # strip LaTeX
body = re.sub(r'[{}\\\\$%&]', '', body)

# Grammar (LanguageTool)
tool = language_tool_python.LanguageTool('en-US')
matches = tool.check(body)
print(f'=== Grammar: {len(matches)} issues ===')
for m in matches[:10]: print(f'  {m.message}')

# Readability (textstat)
print(f'\n=== Readability: FK Grade {textstat.flesch_kincaid_grade(body)} (target 12-16) ===')

# Style (proselint)
suggestions = proselint.tools.lint(body)
print(f'\n=== Style: {len(suggestions)} issues ===')
for s in suggestions[:10]: print(f'  {s}')

# Boilerplate detection (MoreThanSentiments)
from MoreThanSentiments import boilerplate_score
import nltk; nltk.download('punkt', quiet=True)
paragraphs = [p.strip() for p in body.split('\n\n') if len(p.strip()) > 50]
for i, p in enumerate(paragraphs):
    score = boilerplate_score([p])
    if score.values[0] > 0.5:
        print(f'\n  [BOILERPLATE] Paragraph {i+1} (score={score.values[0]:.2f}): {p[:80]}...')
"

# === Academic-specific check: Trinka API (optional, best quality) ===
python3 -c "
import requests, re
with open('manuscript.tex') as f: text = f.read()
body = re.sub(r'\\\\[a-zA-Z]+(\{[^}]*\})*', '', text)
body = re.sub(r'[{}\\\\$%&]', '', body)
# Split into chunks <500 words for free tier
words = body.split()
for i in range(0, len(words), 400):
    chunk = ' '.join(words[i:i+400])
    r = requests.post('https://api.trinka.ai/api/v1/grammar',
        headers={'Authorization': 'Bearer YOUR_TRINKA_API_KEY', 'Content-Type': 'application/json'},
        json={'text': chunk, 'language': 'en'})
    if r.ok:
        for c in r.json().get('corrections', []):
            print(f'  [{c.get(\"type\")}] {c.get(\"original\")} -> {c.get(\"suggestion\")} ({c.get(\"message\")})')
"
```

---

### STEP 6.2: Related Work

**Step A — Ground in literature** (Gemini File Search API):
```python
from google import genai
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

queries = [
    "What metrics are used to evaluate voice cloning quality? What are the reported baselines?",
    "How do existing lipsync evaluation studies measure visual quality and synchronization?",
    "What are the limitations of existing voice cloning and lipsync benchmarks?",
    "What datasets are used in talking-head generation benchmarks?",
]
for q in queries:
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=q,
        config={"tools": [{"file_search": {"store": "YOUR_STORE_NAME"}}]}
    )
    print(f"Q: {q}\nA: {response.text}\n")
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
        print(f"  Source: {chunk.retrieved_context.title}")
```
Save as `writing/related_work_grounding.txt`.

**Step B — Draft** (Claude Code prompt):
```
Read these files:
- step2_1_output.md (validated gaps + ~55 papers organized in categories A-J)
- step2_3_output.md (comparison table: 7 papers with venue, focus, metrics, datasets)
- step2_4_output.md (citation context: how each top paper has been criticized)
- step3_2_output.md (grounded Q&A with PDF citations)
- writing/related_work_grounding.txt (grounded metric baselines from Gemini File Search)
- references.bib

Write a Related Work section in LaTeX (~800-1000 words). Use exactly 3 subsections that
map to our gap areas:

SUBSECTION 1 — "Lip Synchronization Evaluation": Cover THEval (17 models, 85K videos,
rho=0.870), Zhang ICIP 2024 (LSE-C/D poor correlation, 2AFC), Yaman ECCV 2024
(SyncNet bias), LatentSync and MuseTalk benchmarks. Note the limitation: all use
ground-truth audio, not voice-cloned audio.

SUBSECTION 2 — "Voice Cloning Evaluation": Cover ClonEval (5 systems, neutral+emotional),
RVCBench (criticism of ClonEval from step2_4_output.md), EmoKnob (WER degrades with
emotion). Note: all evaluate VC in isolation, not through a lipsync pipeline.

SUBSECTION 3 — "Combined Pipeline Evaluation": Cover AV-Deepfake1M++ (5 TTS × 3 lipsync
but for detection), Mittal 2020 (73.2% emotion mismatch). End with: "Our work fills
the gap by applying a factorial design for quality assessment."

For each paper, write exactly what they did (not vague summaries): how many models,
what metrics, what dataset, what they found. Get these numbers from step2_3_output.md.
Note limitations from step2_4_output.md (e.g., "RVCBench criticizes ClonEval as
quality-centric under clean settings").

Rules:
- Every claim about a paper MUST cite it and match step2_3 or step3_2 or
  related_work_grounding.txt. If you can't verify a claim, don't make it.
- No generic statements without citations.
- Do not describe papers not in your step2/3 outputs.
```

**Step C — Style check**: Run the same quality check from Step 6.1 (Vale + CheckMyTex + Trinka).

---

### STEP 6.3: Methods

**Prompt for Claude Code** (no Gemini File Search needed — Methods is grounded entirely in project files):

```
Read these files in this order:
1. config.yaml — extract ALL parameters (clip duration, fps, resolution, audio SR, etc.)
2. data/source/manifest.csv — count rows = number of source clips
3. data/vc_output/vc_manifest.csv — count rows = number of VC outputs
4. data/generated/stimulus_manifest.csv — count rows = planned stimuli
5. results/all_metrics.csv — count rows = successful stimuli; check which columns exist
6. tools/vc_systems.py — read HOW each VC system works (text-based vs audio-to-audio)
7. tools/lipsync_systems.py — read HOW each lipsync system works (video vs image input)
8. tools/metrics.py — read HOW each metric is computed (the actual algorithm)
9. tools/face_crop.py — read face cropping parameters
10. 05_run_analysis.py — read statistical test details

Write a Methods section in LaTeX (~1200-1500 words) with exactly 5 subsections:

SUBSECTION 1 — "Source Material": State: N actors (list names), 2 conditions (name them),
N clips per video (state duration, offset, gap — from config.yaml), total = N source clips
(count from manifest.csv). Describe face cropping: model (MediaPipe BlazeFace), confidence
threshold, two-pass algorithm (detect → interpolate → smooth → crop), padding factor,
target resolution. Get EVERY number from config.yaml or face_crop.py.

SUBSECTION 2 — "Voice Cloning Systems": For each of the 4 systems, write 2-3 sentences:
model name/citation, whether it is text-based (needs transcription) or audio-to-audio
(language-agnostic), what Whisper model is used for transcription if applicable, output
sample rate. Get this from vc_systems.py — describe what the CODE does, not what the
paper claims the model can do. End with: "All 4 systems processed all N clips, yielding
M VC outputs (X% success rate)" — get M from vc_manifest.csv.

SUBSECTION 3 — "Lip Synchronization Systems": For each of the 3 active systems: model
name/citation, whether it takes video or still image as input, key parameters. State that
MuseTalk was disabled and why. End with: "N stimuli were successfully generated (X%);
the Y failures were [cause]" — get N from all_metrics.csv, Y = planned minus actual.
Identify the failure cause from the stimulus_manifest.csv.

SUBSECTION 4 — "Evaluation Metrics": List ALL metrics that appear as columns in
all_metrics.csv (not from config, from the actual CSV header). For each metric: one
sentence defining what it measures and how (from metrics.py). Group into sync, visual,
audio. If a metric in config is NOT in the CSV (e.g., FID), do not list it.

SUBSECTION 5 — "Statistical Analysis": From 05_run_analysis.py, describe: what type of
ANOVA, how many factors, how many levels per factor, what correction method, what alpha.
State the total number of tests = metrics × factors. If human eval is planned, describe
the LMM formula.

Rules:
- EVERY number must come from a file you read. If config.yaml says clip_duration: 5,
  write "5-second clips". If manifest.csv has 20 rows, write "20 source clips".
  Do NOT write approximate numbers.
- No interpretation. Methods describes WHAT was done, not WHY.
- If a system was disabled, state the technical reason (from config.yaml comments).
- Describe algorithms as implemented in the code, not as described in the original papers.
  Our LSE-C/D is a cross-correlation proxy, not the full SyncNet — say so.
```

**After drafting** — run the quality check from Step 6.1 (Vale + CheckMyTex). statcheck is not needed for Methods (no reported statistics).

---

### STEP 6.4: Results

**Prompt for Claude Code** (no Gemini File Search needed — Results is 100% grounded in CSV files):

```
Read these files:
1. results/computational_anova.csv — this is the PRIMARY source for all statistics
2. results/all_metrics.csv — for computing condition means and checking counts
3. step4_1_output.md — hypotheses H1-H6, to structure the section

Write a Results section in LaTeX (~800-1000 words). Structure:

SUBSECTION 1 — "Overview": State total planned stimuli (from stimulus_manifest.csv row
count), actual successful (from all_metrics.csv row count), success rate, and what failed.
Then introduce Table 1: "Table 1 presents the ANOVA results for all N metrics across
the three factors."

TABLE 1 — Create a LaTeX table with columns: Metric, F_vc, p_vc, η²_vc, F_ls, p_ls,
η²_ls, F_emo, p_emo, η²_emo. Copy values EXACTLY from computational_anova.csv.
Bold significant values (after FDR correction). This table is the centerpiece of Results.

SUBSECTION 2 — "H1: VC System Main Effect": For each metric where VC is significant,
report exact F(df1,df2), exact p-value, and η². State which metrics were NOT affected.
Highlight the pattern: "VC explains X-Y% of variance in audio metrics but <1% in visual."

SUBSECTION 3 — "H2: Lipsync System Main Effect": Same format, inverse pattern.

SUBSECTION 4 — "H4: Emotion Condition": Report the NULL result with full statistics.
"Emotion had no significant effect on any metric. The largest F was for LMD (F=X, p=Y)."

SUBSECTION 5 — "Cross-Factor Independence": Describe the factorization pattern: VC
affects audio, lipsync affects visuals, with sync metrics (LSE-C/D) sensitive to both.
Note that AVSu showed no sensitivity to any factor.

Reference figures: fig2_heatmaps (Figure 1), fig3_vc_system_comparison (Figure 2),
fig3_lipsync_system_comparison (Figure 3), fig4_emotion_comparison (Figure 4).

Rules:
- EVERY number must come from computational_anova.csv. Copy F, p, η² values verbatim.
- Report p-values exactly: if p=0.001855, write p=.002. If p=0.000000, write p<.001.
  Do NOT write p<.05 — always give the exact value or p<.001.
- Report null results with the same detail as significant results.
- No interpretation — just describe what the numbers show. Save "why" for Discussion.
- If human evaluation data exists, add a subsection for it. If not, add a placeholder.
```

**After drafting — CRITICAL: verify every reported statistic:**
```bash
# Cross-check: extract all F/p/η² from manuscript and compare to CSV
python3 -c "
import re, pandas as pd
with open('manuscript.tex') as f: tex = f.read()
anova = pd.read_csv('results/computational_anova.csv')

# Find all F-statistics in the manuscript
f_vals = re.findall(r'F\([0-9,]+\)\s*=\s*([0-9.]+)', tex)
print(f'Found {len(f_vals)} F-values in manuscript')

# Find all eta-squared values
eta_vals = re.findall(r'eta\^2\s*=\s*([0-9.]+)', tex)
# Also LaTeX format
eta_vals += re.findall(r'\\\\eta\^2\s*=\s*([0-9.]+)', tex)
print(f'Found {len(eta_vals)} eta-squared values in manuscript')

# Compare with CSV
csv_f_vals = []
for _, row in anova.iterrows():
    csv_f_vals.extend([row['F_vc'], row['F_ls'], row['F_emo']])
csv_f_vals = [f'{v:.2f}' for v in csv_f_vals]

for f in f_vals:
    if f not in csv_f_vals:
        print(f'  WARNING: F={f} in manuscript but not in CSV')
print('Cross-check complete.')
"
```
Also run statcheck and the style check from Step 6.1.

---

### STEP 6.5: Discussion

**Step A — Ground comparisons in literature** (Gemini File Search API):
```python
from google import genai
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

queries = [
    "What FID, SSIM, or LSE-C values have been reported for Wav2Lip, SadTalker, and VideoReTalking?",
    "What voice cloning quality metrics (speaker similarity, MOS, WER) have been reported for XTTS, kNN-VC, or OpenVoice?",
    "Do existing studies find that emotional speech degrades voice cloning or lipsync quality?",
    "What are the reported limitations of current talking-head generation benchmarks?",
]
for q in queries:
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=q,
        config={"tools": [{"file_search": {"store": "YOUR_STORE_NAME"}}]}
    )
    print(f"Q: {q}\nA: {response.text}\n")
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
        print(f"  Source: {chunk.retrieved_context.title}")
```
Save as `writing/discussion_grounding.txt`.

**Step B — Draft** (Claude Code prompt):
```
Read these files:
- The Results section you just wrote (manuscript.tex, Results section)
- results/computational_anova.csv (to reference exact numbers in discussion)
- step2_3_output.md (comparison table: what other papers found)
- step2_4_output.md (criticism of each paper from citing works)
- step3_2_output.md (grounded Q&A with PDF citations)
- writing/discussion_grounding.txt (metric baselines from Gemini File Search)
- references.bib

Write a Discussion section in LaTeX (~800-1000 words). Use exactly 5 subsections:

SUBSECTION 1 — "Summary of Findings" (~100 words): State the 3 key results in plain
language: (1) VC dominates audio metrics (η² range), (2) lipsync dominates visual metrics
(η² range), (3) emotion had no effect. State the total significant tests: X/30 after FDR.

SUBSECTION 2 — "Comparison with Prior Work" (~300 words): Make 3-4 SPECIFIC comparisons:
- "AV-Deepfake1M++ [cite] reports detection results by TTS×lipsync combination, implying
   interaction. Our quality metrics suggest the contribution is largely additive."
- "Our finding that LSE-C/D are primarily sensitive to VC (η²=0.40) rather than lipsync
   (η²=0.05) is consistent with Zhang et al. [cite]'s observation that these metrics
   correlate poorly with perceptual lip sync quality."
- "The null emotion effect contrasts with ClonEval [cite]'s finding that emotional speech
   reduces VC quality. Three possible explanations: [give them]."
Get the comparison claims from step2_3_output.md and discussion_grounding.txt.

SUBSECTION 3 — "Limitations" (~150 words): List EVERY limitation honestly:
- Small actor pool (N=5), Spanish only
- MuseTalk excluded (why — from config.yaml)
- SadTalker failures (N/240, non-random)
- High WER across all conditions
- Simplified metric proxies (not full SyncNet/AV-HuBERT)
- Computational-only (no human evaluation yet)

SUBSECTION 4 — "Future Work" (~100 words): Be SPECIFIC:
- Add human evaluation (N=30, 4 MOS dimensions — design already exists)
- Include MuseTalk when mmpose supports Python 3.13+
- Test additional languages beyond Spanish
- Longer clips (>5s) to capture temporal quality degradation
- Full SyncNet/AV-HuBERT implementations instead of proxies

SUBSECTION 5 — "Practical Implications" (~100 words): What should a practitioner choosing
tools take away? State: components can be selected independently at the computational level.

Rules:
- Every comparison with literature MUST cite a paper and match step2_3/step3_2/discussion_grounding.
- Do not spin null results. "Emotion had no effect" means exactly that — discuss why honestly.
- Do not overclaim. "5 Spanish-speaking actors" ≠ "all languages".
- No generic filler like "more research is needed". Every sentence must add information.
```

**Step C — Style check**: Run the quality check from Step 6.1 (Vale + CheckMyTex + Trinka).

---

### STEP 6.6: Abstract

**Prompt for Claude Code** (write LAST — after all other sections are complete):

```
Read the complete manuscript (Introduction, Methods, Results, Discussion, Conclusion).
Read results/computational_anova.csv for exact numbers to include.

Write an abstract (max 250 words, aim for 200) in LaTeX. Follow this exact structure:

SENTENCE 1-2 — BACKGROUND + GAP: "Talking head generation combines VC and lipsync, yet
no benchmark evaluates these jointly in a factorial design."

SENTENCE 3-4 — WHAT WE DID: "We evaluate N VC systems crossed with M lipsync systems
on K clips from P actors in [language], yielding T stimulus videos with Q metrics."
Get N, M, K, P, T, Q from the Methods section.

SENTENCE 5-7 — KEY RESULTS: Report the 2-3 most important findings with EXACT numbers:
"VC system choice dominated audio metrics (WavLM: F=X, η²=Y)" and "lipsync dominated
visual metrics (SSIM: F=X, η²=Y)" and "Emotion had no significant effect."
Copy F and η² values from computational_anova.csv — the exact same values as in Results.

SENTENCE 8 — CONCLUSION: One practical takeaway. "These results indicate that..."

Rules:
- Every number MUST match the Results section exactly. Cross-check.
- No vague language. Not "significant differences" but "F(3,228)=114.14, η²=0.60".
- No filler words. Every word in a 250-word abstract must carry information.
```

**After drafting**: Run the quality check from Step 6.1. Also verify numbers match Results.

---

### STEP 6.6b: Conclusion

**Prompt for Claude Code** (short — often combined with Discussion):

```
Read the Discussion section you wrote and results/computational_anova.csv.

Write a Conclusion section in LaTeX (3-5 sentences, ~100 words). State:
1. What we did (one sentence): "We presented the first factorial benchmark of..."
2. The main finding (one sentence): "Computational metrics reveal..."
3. What's next (one sentence): future work reference (human evaluation, more languages).
4. Availability (one sentence): code/data/stimuli link.

Do not repeat the abstract. Do not introduce new information. This is a wrap-up.
```

---

### STEP 6.7: Factual Verification (automated + manual)

**Part A — Statistical verification with statcheck (~1 min):**

```bash
# statcheck recomputes p-values from reported F/t/chi² statistics
# Catches transposed digits, wrong p-values, and rounding errors
python3 -c "
import statcheck
results = statcheck.checkdir('.')
errors = [r for r in results if r.get('error')]
print(f'Checked {len(results)} reported statistics, found {len(errors)} mismatches')
for e in errors:
    print(f'  MISMATCH: {e}')
"
```

**Part B — Full academic writing quality check (~3 min):**

```bash
# --- B1: Unified LaTeX check (CheckMyTex) ---
# Combines LanguageTool + aspell + ChkTeX + proselint in one pass
checkmytex manuscript.tex

# --- B2: Academic-specific rules (Vale) ---
vale manuscript.tex   # uses .vale/styles/Academic rules: overclaiming, filler, etc.

# --- B3: Trinka API (academic grammar trained on papers) ---
python3 -c "
import requests, re
with open('manuscript.tex') as f: text = f.read()
body = re.sub(r'\\\\[a-zA-Z]+(\{[^}]*\})*', '', text)
body = re.sub(r'[{}\\\\$%&]', '', body)
words = body.split()
print('=== Trinka (academic-specific grammar) ===')
for i in range(0, len(words), 400):
    chunk = ' '.join(words[i:i+400])
    r = requests.post('https://api.trinka.ai/api/v1/grammar',
        headers={'Authorization': 'Bearer YOUR_TRINKA_API_KEY', 'Content-Type': 'application/json'},
        json={'text': chunk, 'language': 'en'})
    if r.ok:
        for c in r.json().get('corrections', []):
            print(f'  [{c.get(\"type\")}] {c.get(\"original\")} -> {c.get(\"suggestion\")}')
"

# --- B4: Detailed metrics ---
python3 -c "
import textstat, re
from MoreThanSentiments import boilerplate_score
from PassivePy import PassivePyAnalyzer

with open('manuscript.tex') as f: text = f.read()
body = re.sub(r'\\\\[a-zA-Z]+(\{[^}]*\})*', '', text)
body = re.sub(r'[{}\\\\$%&]', '', body)

# Readability
fk = textstat.flesch_kincaid_grade(body)
print(f'=== Readability: FK Grade {fk} (target 12-16 for academic) ===')

# Passive voice
analyzer = PassivePyAnalyzer(spacy_model='en_core_web_sm')
df = analyzer.match_text(body, full_passive=True, truncated_passive=True)
passive_pct = len(df) / max(1, body.count('.')) * 100
print(f'=== Passive voice: {passive_pct:.0f}% (target <20%) ===')

# Boilerplate detection
paragraphs = [p.strip() for p in body.split('\n\n') if len(p.strip()) > 50]
for i, p in enumerate(paragraphs):
    score = boilerplate_score([p])
    if score.values[0] > 0.5:
        print(f'  [BOILERPLATE] Paragraph {i+1}: {p[:80]}...')
"

# --- B5: Scientific LaTeX checks ---
python3 languagecheck/languagecheck.py manuscript.tex   # tense consistency, topic sentences, a/an
```

**Part D — Automated cross-check with Claude Code (~5 min):**

After all automated tools have been run, prompt Claude Code:

```
Read the complete manuscript draft and verify:
1. Every number in the Results section — cross-reference against results/all_metrics.csv and results/computational_anova.csv. Flag any mismatch.
2. Every \cite{} reference — check that the BibTeX key exists in references.bib. Flag any missing keys.
3. Every claim about a cited paper — cross-reference against step2_3_output.md and step3_2_output.md. Flag any claim not supported by those files.
4. Figure references — check that every "Figure N" reference matches an actual figure file in figures/.
5. Counts — verify that stated N values (source clips, VC outputs, lipsync videos, total stimuli) match the manifest files.

Output a verification report listing all issues found.
```

**Part E — Automated paper existence check (~2 min):**

```bash
# Verify every cited paper actually exists in Semantic Scholar
python3 -c "
import requests, re, time
with open('references.bib') as f: bib = f.read()
titles = re.findall(r'title\s*=\s*\{(.+?)\}', bib)
for title in titles:
    r = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
                     params={'query': title[:100], 'limit': 1})
    found = r.json().get('total', 0) > 0
    status = 'OK' if found else 'NOT FOUND'
    print(f'[{status}] {title[:80]}')
    time.sleep(1)  # respect rate limits
"
```

**Part F — Human verification (30-60 min):**

This is the one step that cannot be automated. Read through the draft with your actual data open and verify:
1. **Your own results:** Every number in Results matches the CSV. LLMs sometimes round or flip signs when redrafting.
2. **Attribution accuracy:** Spot-check 5-10 "Paper X found Y" claims against the actual PDFs.
3. **Scope of claims:** Does the Discussion overclaim beyond what the data supports?

---

### STEP 6.8: Declarations

Add to the manuscript:
1. **Conflict of Interest statement**
2. **Funding sources**
3. **Author contributions** — use CRediT taxonomy if required (https://credit.niso.org/)
4. **AI Use Disclosure** — list all AI tools used across the pipeline. Be transparent and specific:
   - Claude Code (Anthropic): experiment implementation, code generation, manuscript drafting, factual cross-checking
   - Gemini API (Google): literature Q&A grounding (Step 3.2), File Search API for PDF-grounded answers (Step 6), PaperBanana figure generation
   - Semantic Scholar API: literature discovery (Step 2), paper existence verification (Step 6.7)
   - LanguageTool, proselint, textstat, PassivePy: automated grammar, style, and readability checking
   - statcheck: statistical result verification
   - Check your target journal's specific AI-use policy.

**Output:** Complete manuscript ready for submission.

---

## STEP 7: PRESENTATION

**Tools:**
- **Marp CLI** — Markdown-to-slides renderer with PDF/PPTX/HTML output, KaTeX math, custom CSS themes
- **Claude Code** — writes the Markdown slide content grounded in your project files
- **Playwright + Chromium** — headless browser for PDF export (fallback if Marp's built-in PDF fails)

**Principle:** The presentation is generated from the same data files as the manuscript. Claude Code reads the ANOVA CSV, manifests, and manuscript draft, then writes a Marp Markdown file with a custom CSS theme. The result is a stylish, publication-quality slide deck with all numbers verified against source data.

**Setup:**
```bash
# Install Marp CLI (requires Node.js)
npm install -g @marp-team/marp-cli
# If global install fails (permission denied), use user directory:
mkdir -p ~/.npm-global && npm config set prefix ~/.npm-global
PATH=~/.npm-global/bin:$PATH npm install -g @marp-team/marp-cli

# For PDF export, Marp needs Chrome/Chromium. If not installed:
pip install playwright && python3 -m playwright install chromium
```

**Workflow:**
1. Claude Code writes `presentation/slides.md` (Marp Markdown with inline CSS theme)
2. Compile to HTML: `marp slides.md --html --allow-local-files -o slides.html`
3. Export to PDF via Playwright (if Marp's built-in PDF fails with Firefox):
```python
from playwright.sync_api import sync_playwright
from PIL import Image
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    page.goto(f'file://{os.path.abspath("slides.html")}')
    page.wait_for_timeout(2000)
    total = 25  # adjust to your slide count
    os.makedirs('slide_images', exist_ok=True)
    for i in range(total):
        page.wait_for_timeout(300)
        page.screenshot(path=f'slide_images/slide_{i+1:02d}.png', full_page=False)
        page.keyboard.press('ArrowRight')
    browser.close()

# Combine PNGs into PDF
images = []
for i in range(1, total + 1):
    img = Image.open(f'slide_images/slide_{i:02d}.png').convert('RGB')
    images.append(img)
images[0].save('slides.pdf', save_all=True, append_images=images[1:], resolution=150)
```

---

### STEP 7.1: Generate Presentation

**Prompt for Claude Code:**

```
Read these files:
- manuscript.tex (the full paper draft — for structure and narrative)
- results/computational_anova.csv (exact F, p, η² values for result slides)
- results/all_metrics.csv (for per-system means)
- config.yaml (for design parameters)
- data/source/manifest.csv (source clip count)
- data/generated/stimulus_manifest.csv (total stimuli count)
- step4_1_output.md (hypotheses — for structuring results)
- All figures in figures/ (to embed in slides)

Write a Marp Markdown presentation (presentation/slides.md) with an inline CSS
theme. The presentation should be ~20-25 slides for a 15-20 minute conference talk.

THEME: Dark gradient background (deep blue/purple), red accent for headings,
gold for emphasis, light blue for secondary text. Clean sans-serif font.
Use CSS custom properties for colors. Include styles for: title slide, section
divider slides (bold gradient), two-column layouts, highlight boxes, stat callouts,
and styled tables with colored headers.

SLIDE STRUCTURE:

TITLE SLIDE (1): Paper title, subtitle with language, authors, conference.

SECTION: THE GAP (3 slides)
- Motivation: two-column layout — VC (what it is + benchmarks) | Lipsync (what it is + benchmarks)
  Callout box: "No benchmark evaluates them together"
- What Exists vs What's Missing: table comparing THEval, ClonEval, RVCBench,
  AV-Deepfake1M++, and this work. Bold "Yes" for our factorial column.
- Research Questions: two-column — Hypotheses H1-H6 | Design summary (N×M×K)

SECTION: METHOD (4 slides)
- Source Material: actors, conditions, clip extraction, face cropping
- Voice Cloning Systems: table with system, approach, input type, language
- Lipsync Systems: table with system, input type, method. Note MuseTalk disabled.
  Include success rate (get from manifests).
- Evaluation Metrics: two-column — Sync (5) | Visual (2) + Audio (3)

SECTION: RESULTS (5-6 slides)
- Big Picture: highlight box with the 3-line summary (VC→audio, lipsync→visual,
  emotion→nothing). Summary table with factor, N significant, η² range.
- H1 VC Main Effect: ANOVA table (F, p, η²) for audio metrics + per-system means table
- H2 Lipsync Main Effect: same for visual metrics
- H4 Emotion: the null result with full statistics
- Heatmaps figure (embed fig2_heatmaps.png)
- Per-system comparison figures (embed fig3 PNGs)

SECTION: DISCUSSION (3 slides)
- Key Takeaways: two-column — Independence finding | Metric insights
- Comparison with Literature: table (finding | prior work | our result)
- Limitations & Future Work: two-column — limitations list | next steps with badges

CLOSING SLIDE (1): Thank you, key numbers, contact info.

Rules:
- Every number must come from the CSV files. Copy F, p, η² values verbatim.
- Use \$...\$ for inline math (KaTeX) — Marp supports this natively.
- Embed figures with: ![w:950 center](../figures/filename.png)
- Use <!-- _class: divider --> for section divider slides.
- Use <!-- _class: lead --> for title and closing slides.
- If human evaluation hasn't been done yet, add PLACEHOLDER badges on those elements.
- Keep text minimal on slides — no full sentences, use bullet points and tables.
  If something takes more than 6 bullet points, split into two slides.
```

### STEP 7.2: Compile and Export

```bash
# Step 1: Compile to HTML (always works)
marp slides.md --html --allow-local-files -o slides.html

# Step 2: Try PDF export
marp slides.md --pdf --allow-local-files -o slides.pdf

# If Step 2 fails (Firefox/Puppeteer issues), use Playwright fallback:
python3 export_slides_pdf.py  # the script from the setup section above

# Step 3 (optional): Export to PPTX
marp slides.md --pptx --allow-local-files -o slides.pptx
```

**Output:** `presentation/slides.html` (interactive), `presentation/slides.pdf` (printable), optionally `slides.pptx`.

### STEP 7.3: Post-Processing Validation

After generating slides, run this validation checklist to catch common rendering issues.
This step can be automated with Claude Code or done manually.

**Prompt for Claude Code:**

```
Read each slide screenshot in presentation/slide_images/ (slide_01.png through
slide_NN.png) and verify the following for EVERY slide:

CONTENT CHECKS:
1. All tables are fully visible — no rows or columns cut off at edges
2. All numbers match the source data in results/computational_anova.csv
3. All figure images loaded successfully (no broken image icons)
4. No raw LaTeX visible (e.g., "$\times$" showing as text instead of ×)
5. PLACEHOLDER badges appear only on human evaluation elements

LAYOUT CHECKS:
6. Text does not overflow the slide boundaries
7. Two-column layouts have balanced content (neither column >60% empty)
8. Table headers and all data rows are readable at presentation size
9. Font is not too small to read (minimum ~14px equivalent on 1280×720)
10. Figures are centered and not cropped or distorted

THEME CHECKS:
11. Table backgrounds match dark theme (no white/light table cells)
12. All text has sufficient contrast against the background
13. Color coding is consistent (red=headings, gold=emphasis, blue=secondary)
14. Slide numbers are visible on all non-title/divider slides

For each slide, report: PASS or FAIL with specific issues.
If any slide fails, suggest the exact edit to slides.md that would fix it.

Common fixes:
- Tables cut off → add <style scoped> to reduce font-size on that slide
- Raw LaTeX → replace $\times$ with × (Unicode), $\to$ with →, $\downarrow$ with ↓
- White table backgrounds → verify CSS has !important on table/td background overrides
- Content overflow → split slide into two, or reduce bullet points
```

**Automated validation script** (optional — run after Playwright export):
```python
# validate_slides.py — checks slide count and file sizes
import glob, os
from PIL import Image

slides = sorted(glob.glob('slide_images/slide_*.png'))
print(f"Total slides: {len(slides)}")

for path in slides:
    img = Image.open(path)
    w, h = img.size
    size_kb = os.path.getsize(path) / 1024
    # Very small file = likely blank or broken slide
    status = "WARN: possibly blank" if size_kb < 20 else "OK"
    print(f"  {os.path.basename(path)}: {w}x{h}, {size_kb:.0f} KB — {status}")
```

### Premium Alternative (Optional)

For higher design quality, these paid tools can replace or supplement Marp:

| Tool | API? | Best for | Math support | Cost |
|------|------|----------|-------------|------|
| **SlideSpeak** | REST API | Automated .PPTX generation, academic discount (25% off) | Limited | Pay-per-slide |
| **Gamma** | REST API | KaTeX math, fast generation, free tier available | KaTeX | $8–15/mo |
| **Beautiful.ai** | No API | Best design quality (manual only) | Limited | $12+/mo |
| **python-pptx** | Python lib | Full programmatic PowerPoint control, free | None (manual) | Free |

**Recommended upgrade path:**
1. **Default (free):** Marp CLI + Playwright → HTML + PDF (current pipeline)
2. **Budget premium:** Gamma API — supports KaTeX, $8/mo, API access for automation
3. **Maximum quality:** Generate Marp draft → export to PPTX → polish in Beautiful.ai manually
4. **Full automation:** SlideSpeak API — best .PPTX output, academic discount, REST API

To integrate Gamma API into the pipeline, replace Steps 7.1-7.2 with:
```bash
# Export slides content as structured JSON, then call Gamma API
# Requires GAMMA_API_KEY environment variable
curl -X POST https://api.gamma.app/v1/presentations \
  -H "Authorization: Bearer $GAMMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @slides_content.json
```

**Note:** The free Marp pipeline produces publication-quality slides for conferences. Paid tools are only recommended if you need corporate-level design polish or want editable .PPTX output for collaborators who prefer PowerPoint.

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
STEP 2.1: Semantic Scholar (primary) + Consensus (secondary, 1-2 strongest gaps)
  Input: 3 gaps + keyword queries from Step 1
  -> validated gaps + ~10-15 papers
STEP 2.2: Semantic Scholar (terminology expansion) + Inciteful / Connected Papers / OKMaps (graphs)
  Input: top 3-5 papers from 2.1 -> extract alternative terms -> build citation graphs
  -> +10-35 new papers (~25-50 total), reclassified gaps, tiered collection
  * ZOTERO BULK IMPORT: paste all DOIs/arXiv IDs into magic wand -> metadata + PDFs *
STEP 2.3: Elicit (or manual extraction from PDFs/abstracts)
  Input: "read in full" tier (5-8 papers) from 2.1 + 2.2 (PDFs now in Zotero)
  -> comparison table (methods, metrics, datasets, effect sizes)
STEP 2.4: Scite.ai (or Semantic Scholar free)
  Input: 5 most important papers from 2.1 + 2.2
  -> limitations list + 3-5 new papers
STEP 2.5: LLM
  Input: validated gaps + table + limitations from 2.1-2.4
  -> RESEARCH QUESTION
  |
  * CHECKPOINT 1: Verify synthesis + read 5-8 papers in full *
  |
STEP 3.1: Zotero (free) + zotero_tag_papers.py -> tag + organize papers already imported at end of 2.2

STEP 3.2: Gemini API (free) via step3_2_gemini_qa.py -> upload 5-20 key PDFs -> grounded Q&A with citations
  Alternative: NotebookLM (free, manual browser work)
  |
STEP 4.1: LLM (with 2.5 + 3.2 inputs) -> step4_1_output.md (hypotheses)
STEP 4.2: LLM + G*Power -> step4_2_output.md (experimental design + power analysis)
STEP 4.3: LLM -> step4_3_output.md (preregistration) -> FILE at AsPredicted/OSF before Step 5
STEP 4.3b: Ethics/IRB approval (if human participants)
STEP 4.4: LLM -> step4_4_output.md (implementation task list)
  * CHECKPOINT 2: Review experimental design before coding *
  |
STEP 5a: Claude Code (interactive) -> enter plan mode -> review & approve implementation plan
STEP 5b: Claude Code --dangerously-skip-permissions (unattended) -> implements, runs, fixes everything
  Output: code + stimuli + metrics CSV + ANOVA results + figures
  |
  * CHECKPOINT 3: Spot-check stimuli, verify metrics, review figures *
  * PILOT (N=5-10) -> verify pipeline works (if human eval component) *
  * DO FULL EXPERIMENT (if human eval component) *
  |
STEP 6.0: PaperBanana or Claude Code -> methodology figure
  |
STEP 6.1: Gemini File Search (ground) -> Claude Code (draft) -> Vale+Trinka+CheckMyTex (check) -> Introduction
STEP 6.2: Gemini File Search (ground) -> Claude Code (draft) -> quality check -> Related Work
STEP 6.3: Claude Code (reads config.yaml, scripts, manifests) -> quality check -> Methods
STEP 6.4: Claude Code (reads CSVs) -> statcheck (verify stats) -> quality check -> Results
STEP 6.5: Gemini File Search (ground) -> Claude Code (draft) -> quality check -> Discussion
STEP 6.6: Claude Code (reads all sections) -> quality check -> Abstract
STEP 6.7: statcheck + Trinka + Vale + CheckMyTex + MoreThanSentiments + PassivePy + languagecheck
         + Claude Code (cross-check) + Semantic Scholar API (paper existence) + YOU (final read)
STEP 6.8: Declarations (COI, funding, AI disclosure, author contributions)
  |
STEP 7.1: Claude Code (reads manuscript + CSVs + figures) -> Marp Markdown slides
STEP 7.2: Marp CLI -> HTML + Playwright -> PDF (25 slides, dark gradient theme)
STEP 7.3: Claude Code (screenshot review) -> validate tables, overflow, numbers
  |
STEP 8: Git + OSF -> reproducibility + data availability statement
```

---

## TOOL COST SUMMARY

### All tools used in this pipeline

| Tool | Uses AI? | Role | Used in steps | Automated? |
|------|----------|------|---------------|------------|
| LLM (ChatGPT/Claude/Qwen) | Yes | Gap identification, experiment design | 1, 2.5, 4 | Prompt-based |
| **Semantic Scholar** API | Partial (TLDRs) | Gap validation + citation context + paper existence check | 2.1, 2.2, 2.4, 6.7 | Yes (API) |
| **Consensus** | Yes | Secondary gap confirmation (strongest gaps) | 2.1 | Browser-based |
| **Inciteful** | No (graph algorithms) | Citation network exploration | 2.2 | Browser-based |
| **Elicit** | Yes | Structured data extraction from papers | 2.3 | Browser-based |
| **Scite.ai** | Yes | Citation classification (supporting/contrasting) | 2.4 | Browser-based |
| **Zotero** + pyzotero | No | Store papers + PDFs, manage citations, export BibTeX | 2.2, 3.1, 6 | Yes (API) |
| **Gemini API** (step3_2 + File Search) | Yes (Google Gemini) | Cross-paper Q&A grounded in PDFs, with citation metadata | 3.2, 6.1, 6.2, 6.5 | Yes (API) |
| **Claude Code** (CLI) | Yes (Claude) | Implementation, execution, paper drafting, cross-check verification | 5, 6, 6.7 | Yes (CLI) |
| **Trinka** API | Yes (academic AI) | Academic-specific grammar/style, trained on scientific papers | 6.1-6.7 | Yes (API) |
| **Vale** + academic rules | No (YAML rules) | Overclaiming, filler/boilerplate, hedging detection | 6.1-6.7 | Yes (CLI) |
| **CheckMyTex** | No | Unified LaTeX checker (LanguageTool + aspell + ChkTeX + proselint) | 6.7 | Yes (pip) |
| **LanguageTool + proselint + textstat + PassivePy** | No | Grammar, style, readability, passive voice | 6.1-6.7 | Yes (pip) |
| **MoreThanSentiments** | No | Boilerplate/filler quantification score | 6.7 | Yes (pip) |
| **statcheck** | No | Recomputes p-values from reported test statistics | 6.4, 6.7 | Yes (pip) |
| **languagecheck** | No | Scientific LaTeX checks (tense, topic sentences, a/an) | 6.7 | Yes (Python) |
| **PaperBanana** | Yes (Gemini) | AI-generated methodology diagrams | 6.0 | Yes (pip) |
| **Marp CLI** + Playwright | No | Markdown-to-slides (PDF/PPTX/HTML) with KaTeX math | 7 | Yes (CLI) |
| **SlideSpeak API** *(optional paid)* | Yes | Premium .PPTX generation via REST API (academic discount) | 7 | Yes (API) |
| **Gamma API** *(optional paid)* | Yes | KaTeX-aware slide generation, free tier available | 7 | Yes (API) |
| Git + OSF | No | Reproducibility | 8 | Yes (CLI) |

15 out of 19 core tools are fully automated (API, CLI, or pip — no browser interaction needed). The 4 browser-based tools (Consensus, Inciteful, Elicit, Scite) are only used in Steps 2.1-2.4 for literature discovery; everything from Step 3 onward is automated. Two optional paid tools (SlideSpeak, Gamma) are available as premium alternatives for Step 7.

**Tool replacements from previous version:**
- NotebookLM → **Gemini File Search API** (same Google backend, now automated via API)
- Writefull → **Trinka API** (academic-specific grammar, closest replacement) + **Vale** (custom academic rules for overclaiming/filler) + **LanguageTool + proselint + PassivePy** (general style) + **MoreThanSentiments** (boilerplate quantification)
- PaperBanana → **PaperBanana pip package** (same tool, now automated via CLI/Python)
- Penelope.ai → **statcheck** (recomputes p-values) + **CheckMyTex** (unified LaTeX checking) + **languagecheck** (scientific paper checks)

### Cost

| Configuration | Monthly cost | What you lose |
|---|---|---|
| **Full pipeline** (recommended) | ~$20/mo (Claude Code Pro) | Nothing |
| **Free alternative** | $0/mo | Claude Code free tier has usage limits; Consensus/Scite free tiers are limited |
| **With extras** | ~$42/mo (add Consensus Pro, Scite, Elicit Plus) | Nothing — just more convenience in Steps 2.1-2.4 |
| **With premium slides** | ~$28-35/mo (add Gamma $8 or SlideSpeak) | Nothing — better .PPTX quality in Step 7 |

The main cost is Claude Code (Anthropic Pro subscription for higher usage). Trinka API gives $5 free credit (~25,000 words — enough for several manuscript drafts). All other tools are free: Semantic Scholar API, Gemini API + File Search, Zotero + pyzotero, Vale, CheckMyTex, LanguageTool, proselint, textstat, PassivePy, MoreThanSentiments, statcheck, PaperBanana, Marp CLI, Playwright, Git. Optional paid slide tools (Gamma $8/mo, SlideSpeak pay-per-slide) are only needed if you want PowerPoint-quality design.

### Verification rule — 5 checkpoints

All AI tools are used for **discovery, implementation, and drafting**. You verify at five points:

1. **After Step 1 (gap sanity check):** Quick Google Scholar search per gap to catch LLM-hallucinated gaps. (~5 min)
2. **Checkpoint 1 — After Step 2.5 (synthesis + reading):** Spot-check the LLM's synthesis against raw data from 2.1-2.4, then read 5-8 key papers in full. (~15 min + 2-4 hours)
3. **Checkpoint 2 — After Step 4.4 (design review):** Verify experimental design, power analysis (G*Power), and preregistration before coding. Check that chosen tools are available and working.
4. **Checkpoint 3 — After Step 5b (implementation review):** Spot-check generated stimuli, verify metrics CSV has correct rows/columns, review ANOVA tables and figures for plausibility. (~30 min)
5. **Step 6.7 (factual review):** Go through the complete draft with the 6-item checklist. Verify every number, every attribution, every paper's existence against source PDFs. (~1-3 hours)

6. **Step 7 (presentation review):** Run Step 7.3 validation (Claude Code reads screenshots, checks all tables visible, no overflow, numbers match CSV). Then flip through slides manually, verify figure readability at projected size. (~15 min)

Total human verification: ~5-10 hours across the entire pipeline. Everything else is AI-accelerated.

---

## AUTOMATION LEVEL

This pipeline is designed for **maximum automation** from Step 3 onward:

| Phase | Automation level | Human time needed |
|---|---|---|
| **Steps 1-2** (literature) | Semi-automated: you prompt + search + browse | ~4-6 hours |
| **Steps 3-4** (design) | Prompt-based: paste prompts, review outputs | ~2-3 hours |
| **Step 5** (implementation) | Fully automated (after plan approval) | ~30 min (review plan + check results) |
| **Step 6** (writing) | Mostly automated (Gemini ground → Claude draft → tools verify) | ~2-3 hours (run scripts + paste prompts + final human review) |
| **Step 7** (presentation) | Fully automated (Claude writes Marp Markdown → compile) | ~15 min (one prompt + review slides) |
| **Step 8** (reproducibility) | Manual: Git push, OSF upload | ~30 min |

**Total human effort:** ~8-12 hours spread across the full pipeline, from topic to submission-ready manuscript. The computational work (coding, running experiments, generating figures, drafting) is handled by Claude Code.
