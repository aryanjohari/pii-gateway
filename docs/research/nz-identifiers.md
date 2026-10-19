# NZ identifier formats for Phase 3 recognisers

Research, not legal advice. Access date for all sources: 2026-10-19. Feeds `docs/plans/phase-3.md` (not yet written). Companion to `docs/research/nz-privacy-compliance.md`.

## 1. Summary
- **NHI and IRD have published checksums**, so a recogniser can validate, not just pattern-match. Both algorithms are quoted from primary documents below. Phone and postcode have a structure but no checksum. The driver licence checksum is unknown.
- **Presidio 2.2.364 (installed) has no NZ recogniser.** A one-off probe of default behaviour on NZ-shaped text shows misses and mislabels (section 4). It was 11 hand-written strings, an anecdote and not a measurement.
- **Two sources conflict on the NHI new format.** HISO 10046:2026 (the standard, Sept 2026) says new numbers use the new format from 1 July 2026. A Health NZ web page (updated 26 May 2026) says 1 July 2027. The recogniser must accept both formats either way.
- **IRD's valid range changed on 10 Feb 2026** (upper limit 150,000,000 to 200,000,000). The published algorithm spec (v1.3, 2022) still shows the old limit, so copying it verbatim would be a bug.
- **Weakest evidence:** NZTA licence format (search-summary of an NZTA page I could not fetch), and the ComCom phone definitions come from a *draft* determination.

## 2. Frame and scope
- Product: self-hosted redaction gateway (Presidio + spaCy, policy file). Phase 3 adds custom NZ recognisers, scored with the Phase 2 eval harness and a new `eval/dataset_nz.jsonl`.
- Decision supported: which recognisers are feasible, what each can validate, and what the plan must leave as open risk.
- Covered: NHI number, IRD number, NZ driver licence number, NZ phone numbers, NZ postcodes and addresses. Format, checksum, public or not, Presidio coverage.
- Not covered: NZ passport, bank account, NZBN, vehicle plate, Medicare-style or other identifiers; whether any of these *are* "personal information" in law (see the compliance doc); Māori-language or non-English text; how the sources behave for non-NZ users.
- Method note: primary documents were downloaded and read as text where possible. The NZTA website returned a bot-protection challenge to scripted requests; I did not try to bypass it.

## 3. Findings per identifier

### 3.1 NHI number (National Health Index)
Source: HISO 10046:2026 Consumer Health Identity Standard, section 2.1 [S1]; Health NZ upcoming-changes page [S2].

| Item | Finding | Confidence |
|---|---|---|
| Current format | `AAANNNC`: 3 letters, 3 digits, 1 numeric check digit (0-9). Letters exclude `I` and `O`. Upper case. [S1 2.1.2] | High |
| New format | `AAANNAC`: 3 letters, 2 digits, 1 letter, 1 alphabetic check character (A-Y excluding `I`, `O`). [S1 2.1.3] | High |
| Dates | Standard: all *new* numbers use the new format from 1 July 2026; systems should accept it by 1 July 2027. Both formats coexist indefinitely. [S1 2.1.1] | High (standard); see conflict below |
| Check digit, both formats | Letters map to 1-24 using the alphabet without I and O (A=1 ... Z=24); digits keep face value. Multiply the six characters by 7,6,5,4,3,2. Sum. [S1 2.1.4, Table 1] | High |
| Current format check | `check = 11 - (sum mod 11)`; a result of 10 becomes 0; **if `sum mod 11 == 0` the number is invalid**. [S1 2.1.4] | High |
| New format check | `index = 23 - (sum mod 23)`; the check character is the letter at that index in Table 1. [S1 2.1.4] | High |
| Worked examples | `ZAC5361` (current) and `ZBN77VL` (new). A throwaway script reproduces both (check digit 1, check letter L). [S1 Tables 2-3] | High |
| Test numbers | NHI numbers starting with `Z` are reserved as test numbers. Safe basis for synthetic eval data. [S1 2.1.6] | High |
| Public? | Format and algorithm are public (CC BY 4.0 document). Individual numbers are not. The first six characters are arbitrary and bear no relation to the person. [S1] | High |
| Format detection | If the last character is a digit it is current format; if a letter, new format. [S1 2.1.4] | High |

**Conflict:** [S2] (page updated 26 May 2026, read through a page summariser) says implementation 1 July 2027, calls the format `AAANNAX`, and describes a move "from modulus 24 to modulus 23". [S1] is the later, primary standard and says issuing starts 1 July 2026 and uses modulus 23 in the text I read. Plan should follow [S1]. Interpretation: the 2027 date on [S2] is likely the "all systems ready" deadline.

### 3.2 IRD number
Sources: Inland Revenue PIE File Upload Specification v1.3, 21 March 2022, Appendix 5.1 [S3]; IRD news, "Increase to IRD number validation upper limit", 10 Feb 2026 [S4]; IRD "IRD numbers" page, updated 5 Oct 2025 [S5].

| Item | Finding | Confidence |
|---|---|---|
| Format | 8 or 9 digits: a 7- or 8-digit base plus a trailing check digit. [S3] [S4] says length "will remain 9 digits". | High (algorithm); medium on how 8-digit numbers appear today |
| Range | [S3]: invalid if < 10,000,000 or > 150,000,000. **[S4]: upper limit raised to 200,000,000 from 10 Feb 2026.** | High |
| Algorithm | Drop check digit; left-pad base to 8 digits. Weights 3,2,7,6,5,4,3,2; sum; `rem = sum mod 11`; check = 0 if rem is 0, else 11 - rem. If the check is 10, redo with secondary weights 7,4,3,2,5,2,7,6; if it is 10 again the number is invalid. Compare with the supplied last digit. [S3 5.1] | High |
| Worked examples | `49091850`, `35901981`, `49098576` (needs secondary weights), `136410132` valid; `136410133` invalid; `9125568` fails the range. I re-implemented the algorithm in a throwaway script and all six examples give the documented result. [S3] | High |
| Public? | The algorithm is public in a developer spec PDF. The IRD validation service page does not publish it [S6]. Individual numbers are not public. | High |
| Display form | [S3] writes the range as `10-000-000`, so hyphenated grouping appears in IRD's own text. How people actually type IRD numbers (spaces, dashes) is unconfirmed. | Low |

### 3.3 NZ driver licence number
Source: NZTA "Your driver licence explained" [S7], seen only as a search-result summary; the page itself was blocked. NZTA form DL1 (06/26) [S8] was read but does not state the format.

| Item | Finding | Confidence |
|---|---|---|
| Format | 8 characters: 2 letters then 6 digits (example given as `AB123456`). Issued at first application and stays the same for life. | Medium-high (search summary of a primary page, plus the repo owner checked their own physical licence on 2026-10-19: 2 letters + 6 digits; one card, not a citable source) |
| Version number | A separate "version number" changes each time a card is issued. Format not found. | Medium that it exists; format unknown |
| Checksum | Not found in any source read. | Unknown |
| Public? | Format is on a public page. Individual numbers are not. | Medium |

### 3.4 NZ phone numbers
Source: Commerce Commission, Network Terms for Local and Mobile Number Portability, Attachment C, **draft determination, public version, file dated 9 Oct 2026**, Definitions [S9]. The ComCom LMNP overview page [S10] states no formats.

| Item | Finding | Confidence |
|---|---|---|
| Local number | 8 digits: area code + `NXXXXXX`; area code is 3, 4, 6, 7 or 9; `N` is 2-9 (excluding "50AB"). [S9] | Medium (draft; portability scope) |
| Mobile number | `02N` + `XXXXXX[XX]`; `N` is 0, 1, 2, 5, 7, 8 or 9, plus other cellular ranges allocated or recognised by the Numbering Administration Deed (NAD). [S9] | Medium (draft; list can grow) |
| Inter-network form | Written without the leading 0, e.g. `99124200` (geographic) and `274567890` (non-geographic). [S9 para 82] | Medium |
| Checksum | None. | High (none stated) |
| Public? | Number ranges are public. Individual subscriber numbers are personal data. | High |
| Not covered by [S9] | Freephone and premium ranges (0800, 0508, 0900), emergency and short codes, the `+64` country code, written layouts (spaces, brackets). The NAD (`nad.org.nz`) is the authority and was not fetched. | Unknown |

### 3.5 NZ postcodes and addresses
Source: NZ Post "How postcodes work" [S11]; NZ Post "Standards & guides" [S12]. Neither carries a date.

| Item | Finding | Confidence |
|---|---|---|
| Postcode | 4 digits. A leading zero must be kept. No spaces or separators. Digit meaning: 1st = sorting line (north to south), 2nd-3rd = sort area and delivery type, 4th = box lobby, rural round or urban area. [S11] | High |
| Postcode checksum | None. | High (none stated) |
| Address layout | Order: receiver, delivery address, suburb, town/city + postcode. Urban: street number, street, suburb. Rural: "RD" + number. PO Box and Private Bag need a postcode and are not combined with street addresses. [S12] | Medium (summary of page; the 950KB Address Standards PDF it links to was not read) |
| Public? | Yes. NZ Post offers a public Address & Postcode Finder. A postcode alone is a coarse area, not an identifier. | High |
| AS/NZS 4819:2011 | Named as the NZ rural and urban addressing standard in an ISO TC211 conformance page found by search. Not read; the NZ Post page does not cite it. | Unknown |

## 4. What Presidio already covers
Checked on the installed `presidio-analyzer 2.2.364`, using the repo's own `AnalyzerEngine()` construction (`src/pii_gateway/main.py:34`).

- **Default English registry:** CREDIT_CARD, CRYPTO, DATE_TIME, EMAIL_ADDRESS, IBAN_CODE, IP_ADDRESS, LOCATION/PERSON/NRP (spaCy), MAC_ADDRESS, MEDICAL_LICENSE, PHONE_NUMBER, UK_NHS, URL, US_BANK_NUMBER, US_DRIVER_LICENSE, US_ITIN, US_PASSPORT, US_SSN.
- **Country modules shipped:** australia, canada, finland, germany, india, italy, korea, nigeria, philippines, poland, singapore, south_africa, spain, sweden, thai, turkey, uk, us. **No NZ module**, and no "new zealand", `nz_` or NHI string anywhere in the package.
- `PhoneRecognizer` default regions are `US, GB, DE, FR, IL, IN, CA, BR`. NZ is not among them. The repo does not override this.

Probe results (default engine, all entity types, synthetic strings; values for NHI and IRD are the spec's own examples; sample size 11, anecdote only):

| Input | Default Presidio output |
|---|---|
| `ZAC5361`, `ZBN77VL` (NHI) | nothing |
| `49-091-850` (IRD) | nothing |
| `136410132` (IRD) | US_SSN, US_PASSPORT, US_BANK_NUMBER at 0.05, US_DRIVER_LICENSE at 0.01 (wrong types, very low scores) |
| `AB123456` (licence-shaped) | US_DRIVER_LICENSE at 0.65 (wrong type) |
| `021 123 4567` (mobile) | UK_NHS 1.0, DATE_TIME 0.85, PHONE_NUMBER 0.4 |
| `+64 21 123 4567` | PHONE_NUMBER 0.4 |
| `09 912 4200`, `(03) 366 1234 ext 2` | PHONE_NUMBER 0.75 |
| `12 Queen Street, Auckland 1010` | LOCATION (street, city), `1010` as DATE_TIME |
| `0612`, `8110` (postcodes alone) | nothing |

Reading (interpretation): NHI, IRD, licence and postcode are uncovered or mislabelled. NZ phones are partly covered but with low scores, and a mobile is also flagged UK_NHS because both are 10 digits. That matters for Phase 3: the entity list in a policy decides which of these false labels reach the output. The demo policy requests only EMAIL_ADDRESS, PERSON and PHONE_NUMBER, so UK_NHS would not be requested there. The Phase 2 eval has 24 PHONE_NUMBER labels and (by design) no NZ content, so its 1.00 recall says nothing about NZ phones.

## 5. Product implications
- **Validate where a checksum exists.** NHI (both formats) and IRD can use the published algorithm to cut false positives sharply. Phone and postcode cannot; they will rely on pattern plus context words.
- **Recogniser design inputs (for the plan, not decided here):** NHI must accept both formats and the `I`/`O` exclusion. IRD range must use 10,000,000 to 200,000,000, not the 2022 value. A bare 4-digit postcode and a bare 9-digit number are highly ambiguous without context words.
- **Eval data:** NHI examples can use the reserved `Z` prefix. IRD examples can reuse the spec's worked numbers or compute fresh valid ones. Check IRD's terms before copying many spec numbers; they are examples, but I did not check the licence.
- **Claims to avoid:** "detects all NZ identifiers", "validated against the NHI database" (we only check the checksum), "compliant", "anonymised". A valid checksum means a number is well formed, not that it is issued to anyone.
- **Wording to use:** "best-effort detection of NHI, IRD and NZ phone formats; checksum-validated where the issuer publishes one; measured on a small synthetic set".

## 6. Unknowns and open questions
1. NZTA: what exactly does the live "Your driver licence explained" page say about licence number and version number format? (Blocked to scripted fetch; needs a manual read or an NZTA contact.)
2. Does any NZ licence number have a check character or a structure inside the six digits?
3. Has IRD published an updated validation spec after 10 Feb 2026 (range 200,000,000 and anything else)? Only the 2022 PIE spec and the news item were read.
4. How are IRD numbers written by users in practice (spaces, dashes, 8 versus 9 digits with a leading zero)? IRD's own text uses `10-000-000`; no input-format guidance found.
5. What is the issuing date reality for the new NHI format: 1 July 2026 (standard) or 1 July 2027 (web page)? Ask Health NZ (`integration@health.govt.nz` is the contact on [S2]), or accept both as the plan already must.
6. For the new NHI format, how is `sum mod 23 == 0` handled? The text gives `23 - 0 = 23`, which Table 1 maps to `Y`. The old format explicitly calls remainder 0 invalid; the new text is silent. Interpretation only.
7. Is the ComCom draft determination's phone definition final, and what do the NAD number plan documents say about 0800, 0508, 0900 and `+64` written forms?
8. What do NZ Post's Address Standards PDF and AS/NZS 4819:2011 require for rural, PO Box and unit addresses, and is that useful for a rule-based address recogniser beyond spaCy LOCATION?
9. Legal (for an expert): is a checksum-valid NHI or IRD number alone "personal information" under the Privacy Act, and does the Health Information Privacy Code add duties for NHI in text sent to an LLM? (Carries over from compliance doc unknown 4.)

## 7. Sources (all accessed 2026-10-19)
- [S1] Health New Zealand | Te Whatu Ora, *HISO 10046:2026 Consumer Health Identity Standard*, published September 2026, sections 2.1.1-2.1.6. https://static.info.content.health.nz/docs/HISO/HISO%2010046%20Consumer%20Health%20Identity%20Standard.pdf (primary; downloaded and read as text). Listing page, last updated 21 May 2026: https://www.healthnz.govt.nz/health-professionals/guidance-standards/topic/data-and-standards/health-information-standards/approved-health-information-standards/health-identity-standards
- [S2] Health NZ, "Upcoming changes to the NHI", page last updated 26 May 2026. https://www.healthnz.govt.nz/health-professionals/guidance-standards/topic/health-identity/national-health-index-nhi/upcoming-changes-to-the-nhi (primary; read through a page summariser, so lower confidence than [S1]).
- [S3] Inland Revenue, *PIE File Upload Specification V1.3*, 21 March 2022, Appendix 5.1. https://www.ird.govt.nz/-/media/project/ir/home/documents/digital-service-providers/pie-returns-file-upload-specification-v11/pie-returns-file-upload-specification-v13.pdf (primary; downloaded and read as text; superseded in part by [S4]).
- [S4] Inland Revenue, "Increase to IRD number validation upper limit", 10 Feb 2026. https://www.ird.govt.nz/updates/news-folder/2026/increase-to-ird-number-validation-upper-limit (primary; read through a page summariser).
- [S5] Inland Revenue, "IRD numbers", updated 5 Oct 2025. https://www.ird.govt.nz/managing-my-tax/ird-numbers (primary; states no format).
- [S6] Inland Revenue, "IRD number validation service", updated 6 Nov 2024. https://www.ird.govt.nz/digital-service-providers/services-catalogue/customer-and-account/ird-number-validation (primary; states no format).
- [S7] NZTA, "Your driver licence explained". https://www.nzta.govt.nz/driver-licences/getting-a-licence/your-driver-licence-explained (primary; **not read**: fetch returned empty or a bot challenge. The format claim is from a search-result summary).
- [S8] NZTA, *DL1 Application for new, reissue or renewal of driver licence*, 06/26. https://www.nzta.govt.nz/assets/resources/application-for-driver-licence-dl1/docs/dl1.pdf (primary; read as text; no format stated).
- [S9] Commerce Commission, *Network Terms for Local and Mobile Number Portability in New Zealand*, Attachment C to the Designated Multinetwork Determination, draft, public version (file name dated 9 October 2026). https://www.comcom.govt.nz/assets/Documents/2026-review-of-local-and-mobile-number-portability-services-determination/2026-Review-of-LMNP-determination-Attachment-C-Network-Terms-9-October-2026.pdf (primary; downloaded and read as text; **draft**).
- [S10] Commerce Commission, "Local and mobile number portability". https://www.comcom.govt.nz/regulated-industries/telecommunications/regulated-services/copper-services/local-and-mobile-number-portability/ (primary; no formats; last updated 2 Dec 2021).
- [S11] NZ Post, "How postcodes work". https://www.nzpost.co.nz/personal/sending-in-nz/postcodes (primary; undated; read through a page summariser).
- [S12] NZ Post, "Standards & guides". https://www.nzpost.co.nz/personal/sending-within-nz/how-to-address-mail/standards-guides (primary; undated; read through a page summariser; linked Address Standards PDF not read).
- Local checks: `presidio-analyzer 2.2.364` installed in the repo `.venv` (registry listing, package search, `PhoneRecognizer` default regions); probe script kept outside the repo.
- Secondary or search-only, used to locate primary sources and not relied on: Wikipedia "NHI Number" (gave `LLLNNLX` and 1 July 2026, which partly conflicts with [S2]); python-stdnum and other IRD validators; phone-guide sites; ISO TC211 addressing conformance page (mentions AS/NZS 4819).
- Failed or blocked fetches: Health NZ and NZTA old `tewhatuora.govt.nz` URLs (301 to `healthnz.govt.nz`); the consultation PDF for the 2024 NHI change (consultation withdrawn); NZTA pages (bot challenge).
