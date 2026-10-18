# NZ privacy law and pii-gateway: can it become a "reduced compliance" building block?

Research, not legal advice. Access date for all sources: 2026-10-19. Several rules below were confirmed only from search-result summaries or regulator pages, not from the statute text; confidence is marked per row.

## 1. Summary
- NZ has no "sanitize and you're compliant" safe harbour. The Privacy Act 2020 defines personal information as information about an *identifiable individual* and does not define "anonymised" or "de-identified" (secondary source). A redaction tool lowers exposure; it does not remove obligations.
- The strongest fit is **pre-processing before data leaves a business's control**, mainly into generative-AI tools. The Privacy Commissioner (OPC) says not to put personal information into a gen-AI tool unless the provider is confirmed not to retain or disclose it, and names stripping re-identifying data as an option.
- Secondary fits: reducing the size of a breach (IPP 5, notifiable breaches), retention (IPP 9) and overseas-disclosure exposure (IPP 12) by scrubbing logs, analytics and test data.
- Biggest risk to the idea: best-effort NLP misses. Any "compliance" claim would be unsafe without published accuracy numbers.
- Open items needing an expert: the fine for failing to notify a breach, sector codes (health, credit), and whether tokenised data is still "personal information".

## 2. Frame and scope
- Product: self-hosted FastAPI service; policy-file field rules plus Presidio NLP; optional batch from Postgres/CSV/S3. Today it is a library-like service, not a compliance product.
- Question: could it be packaged and coupled into tools (connectors, plugins) that any NZ business can attach to its systems to reduce compliance burden?
- Decision supported: positioning and roadmap.
- Covered: Privacy Act 2020 IPPs, notifiable breaches, IPP 3A (new), IPP 12, OPC AI guidance.
- Not covered: Health Information Privacy Code, Credit Reporting Privacy Code, biometrics code, Māori data sovereignty in depth, sector rules (financial, health), other-jurisdiction law (GDPR/AU Privacy Act) for exporters, existing competitor products.

## 3. Requirements table

| Rule (source + section) | Plain meaning | Applies? | Feature or test it implies | Priority | Confidence |
|---|---|---|---|---|---|
| IPP 5 storage and security (OPC IPP page [S1]; text of s 22 not fetched, the legislation site returned 403) | Keep personal information safe and secure | Yes: the less raw PII held in logs, analytics and test data, the smaller the exposure | Scrub-before-store connectors (log shipper, DB export); policy to never persist raw input (already `write_raw` false in demo policy) | High | Medium (summary only) |
| Notifiable privacy breach, s 114 [S2][S3] | Unauthorised access/loss where serious harm is reasonably believed must be notified to the OPC "as soon as practicable"; OPC expects within 72 hours | Indirect: scrubbed datasets may reduce harm if they leak, but a leak of re-identifiable data is still a breach | Docs: what a leak of *scrubbed* data does and does not mean. No claim of "breach-proof" | Medium | Medium |
| IPP 9 retention [S1] | Do not keep personal information longer than needed | Yes | Retention-oriented outputs (cleaned-only artifacts, TTL on stored artifacts); test that raw is not written under demo policy | Medium | Medium |
| IPP 10/11 use and disclosure [S1] | Use and disclose only for the purpose collected, unless an exception applies | Yes for sharing with analytics and AI vendors | Scrub-by-purpose policies (per-destination policy files) | Medium | Low-medium (not read in full) |
| IPP 12 overseas disclosure [S4, updated June 2021] | Overseas disclosure needs reasonable belief of comparable safeguards. Cloud providers acting as *agent* are generally not a "disclosure", but the exception fails if the provider uses data for its own purposes | Yes: sending text to an offshore LLM API | "Scrub before offshore call" proxy mode; document that scrubbing may take data outside "personal information" only if truly non-identifiable (interpretation) | High | Medium |
| IPP 3A indirect collection, in force 1 May 2026 [S1][S5 secondary] | When collecting personal information from someone other than the individual, take reasonable steps to make them aware | Not directly; it affects businesses that ingest third-party data. Scrubbing does not satisfy notification | None. Avoid implying the tool discharges IPP 3A | Low | Medium (secondary sources) |
| OPC gen-AI expectations, 15 Jun 2023 [S6] | Do not input personal/confidential information into a gen-AI tool unless confirmed it is not retained or disclosed; consider stripping re-identifying information; assess re-identification risk of outputs | Yes: this is the strongest fit | LLM-gateway mode; test showing identifiers are removed before the upstream call; output re-identification check as a roadmap item | High | High for content, medium for currency (2023 page; later guidance exists [S7]) |
| OPC AI guidance on IPPs, Sept 2023 [S7] | Privacy Impact Assessment first; transparency; human review of outputs | Yes, for customers | Ship a short PIA template that includes the gateway as a control | Medium | Medium (search summary only) |
| Definition of personal information; no statutory definition of de-identified [secondary, S8] | Information remains personal if the person is reasonably identifiable, including by combining datasets | Yes: critical for claims | Never use "anonymised"; use "redacted". Tokenize mode needs documentation: is the mapping stored, and by whom | High | Medium (secondary source) |

## 4. Product implications
**Could be built (ordered by fit):**
1. **LLM egress proxy**: OpenAI/Anthropic-compatible endpoint that sanitises prompts before forwarding. This matches the OPC's gen-AI guidance most directly and is the easiest to explain.
2. **Log and analytics scrubbers**: a log-pipeline filter and DB-export job (partly exists).
3. **Per-purpose policy packs**: NZ-specific entity recognisers (NHI number, IRD number, NZ driver licence, NZ phone and address formats) are not in Presidio by default (interpretation: I did not verify the Presidio recogniser list, so confirm before claiming). This is the clearest differentiator for NZ.
4. **Evidence outputs**: a per-request entity-count summary (exists) and a report a business can attach to its PIA.

**Claims to avoid:** "compliant", "anonymised", "guarantees", "removes Privacy Act obligations", "breach-proof".
**Wording to use:** "helps reduce exposure to", "supports your privacy controls", "redacts best-effort; not a substitute for a Privacy Impact Assessment".

**Honest limit:** compliance burden is mostly organisational (privacy officer, notices, access requests, breach process). A technical gateway touches IPP 5, 9, 11 and 12 at best and does nothing for IPPs 1–4, 6–8 or access and correction requests.

## 5. Unknowns and open questions
1. What is the maximum fine for failing to notify a notifiable breach under the Privacy Act 2020 (not confirmed; the statute fetch failed)?
2. Is text with names, emails and NZ identifiers replaced by placeholders still "personal information" when the business can link it back via other records (relevant to IPP 11 and 12 exposure)?
3. If the gateway tokenises values and keeps a mapping, does the mapping holder become an agent holding personal information (s 11)?
4. Does the Health Information Privacy Code 2020 (or its current version) change rules for scrubbing clinical text before sending it to an LLM?
5. Has OPC issued guidance after September 2023 on gen-AI or biometrics that supersedes the 2023 pages used here?
6. Do NZ government agencies (the most likely buyers of a self-hosted tool) have procurement or Government Chief Digital Officer AI rules that would apply?
7. Does IPP 3A change anything for businesses that scrape or ingest third-party text and then scrub it?
8. Who are existing NZ/AU competitors (data-loss-prevention and AI-gateway vendors), and what do they claim?

## 6. Sources (all accessed 2026-10-19)
- [S1] OPC, "Privacy Principles" (13 IPPs; IPP 3A note), https://www.privacy.org.nz/privacy-principles/ (primary; page date not shown).
- [S2] OPC, "What is a notifiable privacy breach?", https://www.privacy.org.nz/resources-and-learning/knowledge-base/view/536/ (primary; page date not shown).
- [S3] Privacy Act 2020, s 114 (referenced via search; the statute page was not fetched), https://mail.nzlii.org/nz/legis/consol_act/pa2020108/s114.html (secondary mirror; not read directly).
- [S4] OPC, "Disclosing personal information outside New Zealand", https://www.privacy.org.nz/disclosing-personal-information-outside-new-zealand/ (primary; updated June 2021).
- [S5] Bell Gully, "Preparing for IPP 3A: new requirements effective 1 May 2026", https://www.bellgully.com/insights/preparing-for-ipp-3a-new-requirements-effective-1-may-2026/ (secondary; found via search, not fetched; Privacy Amendment Act 2025 royal assent 24 Sept 2025 per search summary).
- [S6] OPC, "Generative artificial intelligence", https://www.privacy.org.nz/resources-and-learning/a-z-topics/ai/generative-artificial-intelligence/ (primary; dated 15 Jun 2023).
- [S7] OPC, "AI and the Information Privacy Principles" (Sept 2023), https://www.privacy.org.nz/assets/New-order/Resources-/Publications/Guidance-resources/AI-Guidance-Resources-/AI-and-the-Information-Privacy-Principles.pdf (primary; located via search, not fetched).
- [S8] Sprintlaw NZ, "De-identified Data in New Zealand", https://sprintlaw.co.nz/articles/de-identified-data-in-new-zealand-when-privacy-law-still-applies/ (secondary; used only to locate the concept).
- Failed fetches: OPC AI media release URL (404), OPC breach notification page (404), legislation.govt.nz IPP text (403), nzlii s 118 (DNS error).
