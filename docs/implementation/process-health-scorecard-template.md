# Process Health Scorecard Template

Use this template when summarizing the operational health of a survey/execution queue or migration topic.

---

# <topic> Process Health Scorecard

Date: YYYY-MM-DD
Status: draft | active | final
Scope: `<topic or queue>`

## 1. Executive Read
- overall color: green | amber | red
- why:

## 2. Dimensions

| Dimension | Status | Evidence | Notes |
| --- | --- | --- | --- |
| governance alignment | green | `<doc>` | `<note>` |
| queue integrity | amber | `<validator>` | `<note>` |
| canonical/mirror sync | green | `<validator>` | `<note>` |
| evidence freshness | amber | `<manifest>` | `<note>` |
| side-effect coverage | green | `<survey>` | `<note>` |
| exception debt | amber | `<exception>` | `<note>` |
| closure readiness | green | `<closure plan>` | `<note>` |

## 3. Immediate Actions
- `<action>`
- `<action>`

---

Before final save:
- complete the document 3-pass audit
- reference real evidence, not impressions only
