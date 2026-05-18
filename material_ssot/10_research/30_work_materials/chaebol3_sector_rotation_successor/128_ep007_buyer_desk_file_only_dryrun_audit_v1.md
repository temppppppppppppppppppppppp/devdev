# EP007 Buyer Desk File-Only Dry Run Audit v1

Date: 2026-05-17
Status: adversarial audit complete
Target: `127_ep007_buyer_desk_file_only_dryrun_sample_v1.md`
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157

## 0. Verdict

`PASS_WITH_WATCH_FOR_STATUS_UPDATE`

The file-only EP007 dry run is usable as Firefly-side research evidence.

It does not authorize:

- B11-B20;
- TR70;
- BI;
- Firefly DB/project mutation;
- `manuscript save`;
- production manuscript save;
- production S4 prompt change.

## 1. Hard Checks

| Check | Verdict | Evidence |
|---|---|---|
| file-only status | PASS | `draft_not_db_saved`, boundary explicit. |
| uses `116` buyer-desk surface | PASS | Sample box, phone, return ledger, parent calls, shelf risk, trial quantity. |
| real buyer desk objects | PASS | Phone, return ledger, memo, front shelf, sample box. |
| asks for less than victory | PASS | 60 becomes 30; front display is refused before it becomes fake reward. |
| buyer protects practical cost | PASS | Return calls, school complaints, delivery penalty, next-month quantity. |
| visible objection remains | PASS | `앞 진열 없음`, `반품 3`, `학교 전화 직접 응대`. |
| ending object/access | PASS | Box stays beside phone/ledger, not front display. |
| next gate from object | PASS | School goods shipment/public-use trial. |
| DB/project safety | PASS | No Firefly command or save. |

## 2. Style / AI-Smell Audit

### What Works

- The buyer looks at the label and ledger before the shoe.
- Doyun does not ask for admiration.
- The buyer's first meaningful act is not approval but quantity cut and objection-writing.
- The final object position is clear.

### Watch

The last two lines are neat:

- `두 글자는 앞 진열대로 가지 못했다.`
- `대신 전화기 옆에 남았다.`

They are acceptable because they point to physical placement, but this exact two-line contrast should not become a repeated closure template.

If patching, prefer ending one beat earlier:

- `상자 옆면만 돌려 라벨이 보이게 했다.`
- `해문`

But patch is not required for this research proof.

### Minor Dialogue Watch

Some Doyun responses are very clean:

- `꺼내시면 거절하실 겁니다.`
- `그 조건으로 들어가면 이 상자가 오늘 나갑니다.`

They work in this short sample. In longer S4, add one practical interruption or buyer-side half sentence so the negotiation does not feel like a diagram.

## 3. Combined Result

Now three surfaces have passed controlled context smoke after audit:

- `118/121`: finance/file-room, paper-heavy surface.
- `122/124`: product-hand, tactile surface.
- `127/128`: buyer desk, commercial outside-actor surface.

This is stronger than the earlier isolated canaries because the same compact packet `116` now survives across document, product, and buyer-room textures.

The recurring failure mode is also clear:

S4-like prose tends to add a final line explaining why the object matters. The fix is consistent: remove the explanation and leave the object/objection in place.

## 4. Decision

Next unit:

`Update SSOT and issue #157. Then choose between Firefly temp-project dry run design or upstream material-pack formalization.`

Recommendation:

Do not run B11-B20 yet.

Do not mutate Firefly DB yet.

The best next step is a small integration design: define how `116`-style compact handoffs should enter Firefly's S4 Writer Context fields without exposing research labels.

Stoplines remain:

- no B11-B20;
- no TR70;
- no BI;
- no Firefly DB/project mutation;
- no production manuscript save.
