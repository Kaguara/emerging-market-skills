# Sources

Citation keys for `published` and `vendor` evidence. Every `source:` of those
tiers in a `rules.yml` must match a `###` heading here, or CI fails.

`field` evidence does not appear in this file — its source is the product and
market named inline in the rule. See [EVIDENCE.md](EVIDENCE.md).

Add a source by appending a `### key` heading with a URL and an access date.
Keys are lowercase kebab-case and stable once published. Paraphrase what you
cite; do not paste source text into a skill.

---

## Vendor documentation

### android-workmanager
Android Developers — WorkManager.
https://developer.android.com/topic/libraries/architecture/workmanager
Accessed 2026-08-17. Cited for deferrable background work that survives process
death and reboot, and for its built-in backoff policy.

### android-app-bundle
Android Developers — Android App Bundles.
https://developer.android.com/guide/app-bundle
Accessed 2026-08-17. Cited for modular delivery: per-device-configuration APK
generation and on-demand feature modules that keep the initial download small.

### android-go
Android Developers — Android (Go edition).
https://developer.android.com/guide/topics/androidgo
Accessed 2026-08-17. Cited for the memory and storage envelope of entry-level
devices, and the platform's own guidance for building within it.

### aws-backoff-jitter
AWS Architecture Blog — Exponential Backoff And Jitter.
https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
Accessed 2026-08-17. Cited for why jitter, not backoff alone, is what prevents
synchronised retry storms.

### mdn-network-information-api
MDN — Network Information API.
https://developer.mozilla.org/en-US/docs/Web/API/Network_Information_API
Accessed 2026-08-17. Cited for `effectiveType` and `saveData`, and for their
limited browser support.

### mdn-save-data
MDN — `Save-Data` HTTP header.
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Save-Data
Accessed 2026-08-17. Cited as an explicit user instruction to reduce data use,
not a hint to weigh against other factors.

### web-vitals
web.dev — Core Web Vitals.
https://web.dev/articles/vitals
Accessed 2026-08-17. Cited for LCP, INP, and CLS definitions and thresholds.
Note that the published thresholds are calibrated against a global device
population, not against tier C specifically.

### grpc
gRPC.
https://grpc.io/
Accessed 2026-08-17. Cited as a lower-overhead alternative to JSON over HTTP
where payload volume justifies the tooling cost.

### icu-message-format
ICU User Guide — Formatting Messages.
https://unicode-org.github.io/icu/userguide/format_parse/messages/
Accessed 2026-08-17. Cited for plural and gender selection, which string
concatenation cannot express correctly in most languages.

### unicode-cldr
Unicode CLDR — Common Locale Data Repository.
https://cldr.unicode.org/
Accessed 2026-08-17. Cited for locale data: number formats, date formats,
plural categories, and script metadata.

### w3c-text-size-translation
W3C Internationalization — Text size in translation.
https://www.w3.org/International/articles/article-text-size
Accessed 2026-08-17. Cited for expansion factors when translating from English,
which are largest on the short strings that UI labels are made of.

---

## Published research and industry reporting

### google-nbu-new-internet-users
Google Developers Blog — Building better products for new internet users.
https://developers.googleblog.com/building-better-products-for-new-internet-users/
Accessed 2026-08-17. Google's Next Billion Users programme. Cited for the
framing that first impressions are decisive for novice internet users, and that
images, icons, and colour carry cultural assumptions that do not travel.

### cgap-transactional-data-mse
CGAP — Leveraging Transactional Data for Micro and Small Enterprise Lending,
March 2024.
https://www.cgap.org/research/publication/leveraging-transactional-data-for-micro-and-small-enterprise-lending
Accessed 2026-08-17. Cited for the finding that transactional data has
predictive power comparable to formal credit history, which is the technical
argument for treating in-product behavioural data as a first-class asset for
users who have no bureau file.

### gsma-m4d-blog
GSMA — Mobile for Development blog.
https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/blog/
Accessed 2026-08-17. Cited for connectivity, affordability, and mobile-money
adoption reporting. Prefer linking the specific post and its publication date
over the blog index when citing a figure.

### tuck-design-emerging-markets
Tuck School of Business at Dartmouth — How to Design for Emerging Markets.
https://tuck.dartmouth.edu/news/articles/how-to-design-for-emerging-markets
Accessed 2026-08-17. Cited for constraint-driven design as a discipline rather
than as feature removal.

### mckinsey-brands-emerging-markets
McKinsey — Building brands in emerging markets.
https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/building-brands-in-emerging-markets
Accessed 2026-08-17. Mostly out of scope for these skills, which are technical.
Cited only where brand and trust have a direct product-surface consequence.

### miden-building-emerging-markets
Miden — Building in Emerging Markets: Hard Lessons, Smarter Strategies for 2025.
https://blog.miden.co/building-in-emerging-markets-hard-lessons--smarter-strategies-for-2025
Accessed 2026-08-17. Practitioner account. Cited as industry commentary rather
than as research; corroborate figures before promoting one to a `critical` rule.

### beyondthebacklog-developing-markets
Beyond the Backlog — Building products for developing markets, March 2026.
https://beyondthebacklog.com/2026/03/18/building-products-for-developing-markets/
Accessed 2026-08-17. Practitioner account, same caveat as above.
