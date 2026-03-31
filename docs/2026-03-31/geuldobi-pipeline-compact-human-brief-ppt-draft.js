const path = require("path")

function loadPptxGenJS() {
  const tempRoot = process.env.TEMP || process.env.TMP || ""
  const candidates = [
    process.env.GEULDOBI_PPTXGENJS_PATH,
    tempRoot
      ? path.join(tempRoot, "geuldobi-pptx-runtime", "node_modules", "pptxgenjs")
      : "",
    "pptxgenjs",
  ].filter(Boolean)

  for (const candidate of candidates) {
    try {
      return require(candidate)
    } catch {}
  }

  throw new Error(
    "PptxGenJS를 찾지 못했습니다. `npm install --prefix %TEMP%\\geuldobi-pptx-runtime pptxgenjs@3.12.0` 후 다시 실행해 주세요."
  )
}

const PptxGenJS = loadPptxGenJS()

const OUTPUT_PATH = path.join(
  __dirname,
  "geuldobi-pipeline-compact-human-brief-draft.pptx"
)

const pptx = new PptxGenJS()
pptx.layout = "LAYOUT_WIDE"
pptx.author = "Codex"
pptx.company = "글도비"
pptx.subject = "글도비 파이프라인 컴팩트 브리프 발표 초안"
pptx.title = "글도비 파이프라인 Compact Brief"
pptx.lang = "ko-KR"

const C = {
  paper: "F7F3EB",
  paperAlt: "EEE4D6",
  white: "FFFFFF",
  ink: "17324D",
  muted: "5F6B78",
  line: "D6CCBE",
  navy: "17324D",
  navySoft: "E6EDF4",
  accent: "BA6B2D",
  accentSoft: "F2E3D5",
  green: "2F6B4F",
  greenSoft: "E5F0E8",
  red: "9E4438",
  redSoft: "F5E4DF",
  teal: "2F6E73",
  tealSoft: "E2EFF0",
}

const FONT = {
  body: "Malgun Gothic",
}

function addChrome(slide, title, subtitle, page, total) {
  slide.background = { color: C.paper }
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.24,
    line: { color: C.navy, pt: 0 },
    fill: { color: C.navy },
  })
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 7.18,
    w: 13.333,
    h: 0.32,
    line: { color: C.paperAlt, pt: 0 },
    fill: { color: C.paperAlt },
  })
  slide.addText(title, {
    x: 0.65,
    y: 0.42,
    w: 8.4,
    h: 0.4,
    fontFace: FONT.body,
    fontSize: 24,
    bold: true,
    color: C.ink,
  })
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.65,
      y: 0.9,
      w: 9.2,
      h: 0.24,
      fontFace: FONT.body,
      fontSize: 10.5,
      color: C.muted,
    })
  }
  slide.addText(`${page}/${total}`, {
    x: 12.08,
    y: 0.48,
    w: 0.55,
    h: 0.22,
    fontFace: FONT.body,
    fontSize: 10,
    color: C.muted,
    align: "right",
  })
}

function addPanel(slide, x, y, w, h, fill, line = C.line) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: line, pt: 1.1 },
    fill: { color: fill },
  })
}

function addPanelTitle(slide, title, x, y, w, color = C.ink, size = 12.5) {
  slide.addText(title, {
    x,
    y,
    w,
    h: 0.28,
    fontFace: FONT.body,
    fontSize: size,
    bold: true,
    color,
  })
}

function addBody(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    fontFace: FONT.body,
    fontSize: opts.fontSize || 10.5,
    color: opts.color || C.ink,
    bold: opts.bold || false,
    valign: opts.valign || "top",
    align: opts.align || "left",
    margin: opts.margin || 0.04,
    breakLine: false,
  })
}

function addChip(slide, label, x, y, w, tone = "navy") {
  const fillMap = {
    navy: C.navySoft,
    accent: C.accentSoft,
    green: C.greenSoft,
    teal: C.tealSoft,
    red: C.redSoft,
  }
  const lineMap = {
    navy: C.navy,
    accent: C.accent,
    green: C.green,
    teal: C.teal,
    red: C.red,
  }
  addPanel(slide, x, y, w, 0.42, fillMap[tone], lineMap[tone])
  addBody(slide, label, x + 0.12, y + 0.09, w - 0.24, 0.2, {
    fontSize: 10,
    bold: true,
    color: lineMap[tone],
    align: "center",
    valign: "mid",
  })
}

function addCallout(slide, text, x, y, w, h, tone = "navy") {
  const fillMap = {
    navy: C.navySoft,
    accent: C.accentSoft,
    green: C.greenSoft,
    teal: C.tealSoft,
    red: C.redSoft,
  }
  const lineMap = {
    navy: C.navy,
    accent: C.accent,
    green: C.green,
    teal: C.teal,
    red: C.red,
  }
  addPanel(slide, x, y, w, h, fillMap[tone], lineMap[tone])
  addBody(slide, text, x + 0.16, y + 0.12, w - 0.32, h - 0.24, {
    fontSize: 11,
    bold: true,
    color: C.ink,
    valign: "mid",
  })
}

function tableCell(text, opts = {}) {
  return {
    text,
    options: {
      fontFace: FONT.body,
      fontSize: opts.fontSize || 9.8,
      color: opts.color || C.ink,
      bold: opts.bold || false,
      align: opts.align || "left",
      valign: opts.valign || "mid",
      fill: opts.fill || C.white,
      margin: opts.margin || 0.06,
      border: { type: "solid", color: C.line, pt: 1 },
    },
  }
}

function headerCell(text, fill = C.navy) {
  return tableCell(text, {
    bold: true,
    color: C.white,
    fill,
    align: "center",
  })
}

function addTable(slide, rows, opts) {
  slide.addTable(rows, {
    x: opts.x,
    y: opts.y,
    w: opts.w,
    h: opts.h,
    colW: opts.colW,
    rowH: opts.rowH,
    fontFace: FONT.body,
    fontSize: opts.fontSize || 9.8,
    color: C.ink,
    border: { type: "solid", color: C.line, pt: 1 },
    margin: 0.06,
    autoFit: false,
  })
}

function addStageCard(slide, stage, asset, gate, failure, x, tone) {
  const fillMap = {
    accent: C.accentSoft,
    teal: C.tealSoft,
    green: C.greenSoft,
    navy: C.navySoft,
  }
  const lineMap = {
    accent: C.accent,
    teal: C.teal,
    green: C.green,
    navy: C.navy,
  }
  addPanel(slide, x, 1.6, 2.82, 4.2, C.white, C.line)
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y: 1.6,
    w: 2.82,
    h: 0.48,
    line: { color: lineMap[tone], pt: 0 },
    fill: { color: lineMap[tone] },
  })
  addBody(slide, stage, x + 0.16, 1.73, 2.5, 0.2, {
    fontSize: 12,
    bold: true,
    color: C.white,
    valign: "mid",
    align: "center",
  })
  addPanelTitle(slide, "핵심 산출", x + 0.18, 2.22, 1.2, lineMap[tone], 10.5)
  addBody(slide, asset, x + 0.18, 2.48, 2.46, 0.76, {
    fontSize: 10.4,
    color: C.ink,
  })
  addPanel(slide, x + 0.16, 3.18, 2.5, 0.78, fillMap[tone], lineMap[tone])
  addPanelTitle(slide, "판정 게이트", x + 0.3, 3.33, 1.2, lineMap[tone], 10.2)
  addBody(slide, gate, x + 0.3, 3.53, 2.18, 0.28, {
    fontSize: 10,
    color: C.ink,
    bold: true,
  })
  addPanelTitle(slide, "실패 시", x + 0.18, 4.24, 1.2, C.red, 10.5)
  addBody(slide, failure, x + 0.18, 4.48, 2.46, 0.92, {
    fontSize: 10.2,
    color: C.ink,
  })
}

function addRoleCard(slide, title, body, x, tone) {
  addPanel(slide, x, 4.95, 3.9, 1.45, C.white, C.line)
  addChip(slide, title, x + 0.16, 5.12, 1.25, tone)
  addBody(slide, body, x + 0.16, 5.63, 3.48, 0.54, {
    fontSize: 10.2,
    color: C.ink,
  })
}

function addTierBand(slide, title, body, x, y, w, tone) {
  const fillMap = {
    navy: C.navySoft,
    accent: C.accentSoft,
    green: C.greenSoft,
    teal: C.tealSoft,
  }
  const lineMap = {
    navy: C.navy,
    accent: C.accent,
    green: C.green,
    teal: C.teal,
  }
  addPanel(slide, x, y, w, 0.78, fillMap[tone], lineMap[tone])
  addBody(slide, title, x + 0.16, y + 0.13, 1.2, 0.2, {
    fontSize: 10.2,
    bold: true,
    color: lineMap[tone],
  })
  addBody(slide, body, x + 1.28, y + 0.11, w - 1.44, 0.42, {
    fontSize: 9.8,
    color: C.ink,
  })
}

const total = 8
let slide

slide = pptx.addSlide()
slide.background = { color: C.paper }
slide.addShape(pptx.ShapeType.rect, {
  x: 0,
  y: 0,
  w: 13.333,
  h: 0.32,
  line: { color: C.navy, pt: 0 },
  fill: { color: C.navy },
})
slide.addShape(pptx.ShapeType.rect, {
  x: 8.8,
  y: 0.32,
  w: 4.533,
  h: 7.18,
  line: { color: C.paperAlt, pt: 0 },
  fill: { color: C.paperAlt },
})
slide.addText("글도비 파이프라인\nCompact Brief", {
  x: 0.72,
  y: 0.9,
  w: 6.8,
  h: 1.2,
  fontFace: FONT.body,
  fontSize: 26,
  bold: true,
  color: C.ink,
  breakLine: false,
})
slide.addText("원문 기준: geuldobi-pipeline-compact-human-brief.md", {
  x: 0.78,
  y: 2.15,
  w: 5.8,
  h: 0.24,
  fontFace: FONT.body,
  fontSize: 10.5,
  color: C.muted,
})
addCallout(
  slide,
  "글도비는 Stage 0/2/3/4마다 save-handoff gate를 두는 계층형 파이프라인이며, Stage 4에서는 Writer LLM과 Director LLM을 분리해 원고를 판정한다.",
  0.74,
  2.65,
  7.05,
  1.35,
  "accent"
)
addChip(slide, "Writer LLM / Director LLM 분리", 0.82, 4.3, 2.45, "navy")
addChip(slide, "PASS / PASS_WITH_FIX / REJECT 루프", 3.45, 4.3, 2.8, "green")
addChip(slide, "저장 후 컨텍스트 재주입", 6.46, 4.3, 1.95, "teal")
addPanel(slide, 0.74, 5.0, 7.1, 1.58, C.white, C.line)
addPanelTitle(slide, "이번 발표에서 보여 줄 것", 0.96, 5.18, 2.3, C.ink, 12.5)
addBody(
  slide,
  "1. Stage 0-2-3-4 전체샷\n2. Writer / Python / Director 역할 분리\n3. Stage 4 pass-fix / reject retry 상세 루프\n4. 저장 이후 컨텍스트 계층화와 현재 병목",
  0.96,
  5.5,
  6.5,
  0.9,
  { fontSize: 11 }
)
addPanel(slide, 9.18, 0.86, 3.45, 2.25, C.white, C.line)
addPanelTitle(slide, "핵심 메시지", 9.42, 1.08, 2.3, C.accent, 13)
addBody(
  slide,
  "단순 글쓰기 봇이 아니라,\n설계 자산 -> 생성 -> 심사 -> 저장 -> 재주입이 이어지는 폐루프형 생산 시스템이다.",
  9.42,
  1.48,
  2.85,
  1.2,
  { fontSize: 13, bold: true }
)
addPanel(slide, 9.18, 3.4, 3.45, 2.7, C.navy, C.navy)
addPanelTitle(slide, "한 줄 요약", 9.42, 3.67, 1.8, C.white, 13)
addBody(
  slide,
  "강점은 연속성과 추적 가능성,\n현재 과제는 retry 비용 절감과\n컨텍스트 오염 제어, 인간 선호 품질의 안정화다.",
  9.42,
  4.08,
  2.85,
  1.4,
  { fontSize: 12.5, color: C.white }
)
slide.addText("1/8", {
  x: 12.05,
  y: 0.56,
  w: 0.55,
  h: 0.22,
  fontFace: FONT.body,
  fontSize: 10,
  color: C.muted,
  align: "right",
})

slide = pptx.addSlide()
addChrome(
  slide,
  "Stage 0-2-3-4 전체샷",
  "모든 스테이지에 저장 전 판정 또는 handoff 차단 지점이 있다",
  2,
  total
)
addStageCard(
  slide,
  "Stage 0",
  "candidate 생성\n기초 자산 정리",
  "review gate / handoff gate",
  "RETRY면 재작성,\nREJECT면 저장 또는 handoff 중단",
  0.68,
  "accent"
)
addStageCard(
  slide,
  "Stage 2",
  "arc generation\nstory arc 설계",
  "finalize gate",
  "PASS_WITH_FIX면 arc patch,\nREJECT면 arc 재생성",
  3.92,
  "teal"
)
addStageCard(
  slide,
  "Stage 3",
  "blueprint generation\nepisode 설계",
  "validate gate",
  "PASS_WITH_FIX면 blueprint patch,\nREJECT면 blueprint 재작성",
  7.16,
  "green"
)
addStageCard(
  slide,
  "Stage 4",
  "manuscript generation\nactual draft 작성",
  "director interview",
  "PASS_WITH_FIX면 local patch loop,\nREJECT면 retry routing",
  10.4,
  "navy"
)
addCallout(
  slide,
  "핵심 포인트: 글도비는 단순 직렬 파이프라인이 아니라, 각 stage마다 판정 게이트와 수정 경로가 붙어 있는 계층형 운영 구조다.",
  0.68,
  6.2,
  12.0,
  0.7,
  "accent"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "Stage 4 Writer-Director 분업",
  "생성과 판정을 분리하고, Python은 사전검증과 라우팅을 맡는다",
  3,
  total
)
const flowBoxes = [
  {
    x: 0.66,
    w: 2.1,
    title: "입력 컨텍스트",
    body: "stored context\nStage 2 arc\nStage 3 blueprint",
    tone: "accent",
  },
  {
    x: 2.95,
    w: 2.16,
    title: "Chief Writer",
    body: "ensemble 3개 후보 생성\n원고 초안 생산",
    tone: "navy",
  },
  {
    x: 5.3,
    w: 2.02,
    title: "Python precheck",
    body: "형식 검증\n사전 라우팅\n최종 reject 권한은 없음",
    tone: "teal",
  },
  {
    x: 7.51,
    w: 2.2,
    title: "Director interview",
    body: "PASS / PASS_WITH_FIX / REJECT\n최종 판정 + 수정 지시",
    tone: "green",
  },
  {
    x: 9.9,
    w: 2.78,
    title: "Persist + next prompt",
    body: "episode_bible / world_state / fact_ledger 저장\n다음 화 prompt 재구성",
    tone: "accent",
  },
]
for (const box of flowBoxes) {
  addPanel(slide, box.x, 1.78, box.w, 1.52, C.white, C.line)
  addChip(slide, box.title, box.x + 0.14, 1.95, box.w - 0.28, box.tone)
  addBody(slide, box.body, box.x + 0.16, 2.48, box.w - 0.32, 0.55, {
    fontSize: 10,
    align: "center",
  })
}
for (const arrowX of [2.78, 5.13, 7.34, 9.74]) {
  slide.addText("→", {
    x: arrowX,
    y: 2.3,
    w: 0.14,
    h: 0.24,
    fontFace: FONT.body,
    fontSize: 18,
    bold: true,
    color: C.muted,
    align: "center",
  })
}
addRoleCard(
  slide,
  "Chief Writer",
  "후보를 만든다. 여러 초안을 병렬 생산해 선택 가능한 원고 집합을 제공한다.",
  0.86,
  "navy"
)
addRoleCard(
  slide,
  "Python runtime",
  "사전 검증, 분기, retry routing을 맡는다. 판단 근거는 전달하지만 최종 품질 판정 주체는 아니다.",
  4.7,
  "teal"
)
addRoleCard(
  slide,
  "Director LLM",
  "최종 인터뷰와 선택, 수정 범위 지시를 맡는다. Director가 reject authority를 가진다.",
  8.54,
  "green"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "Stage 4 상세 루프",
  "PASS_WITH_FIX는 accept branch 내부 patch loop이고, REJECT는 retry routing으로 빠진다",
  4,
  total
)
addChip(slide, "PASS", 0.82, 1.5, 1.18, "green")
addPanel(slide, 0.82, 1.96, 3.6, 1.06, C.white, C.line)
addBody(slide, "accept and persist\n사후 검증까지 통과하면 저장 후보가 된다.", 1.0, 2.22, 3.2, 0.48, {
  fontSize: 11,
  align: "center",
})
addChip(slide, "PASS_WITH_FIX", 4.86, 1.5, 1.9, "accent")
addPanel(slide, 4.86, 1.96, 3.6, 1.06, C.white, C.line)
addBody(slide, "local pass-fix patch loop\naccept branch 안에서 수정하고 Director가 다시 감리한다.", 5.04, 2.15, 3.24, 0.58, {
  fontSize: 10.8,
  align: "center",
})
addChip(slide, "REJECT", 8.92, 1.5, 1.18, "red")
addPanel(slide, 8.92, 1.96, 3.6, 1.06, C.white, C.line)
addBody(slide, "retry routing\n같은 pathology가 반복되면 더 큰 재생성 또는 상위 단계 재작성으로 올라간다.", 9.1, 2.12, 3.22, 0.62, {
  fontSize: 10.6,
  align: "center",
})
addTable(
  slide,
  [
    [headerCell("retry lane"), headerCell("설명", C.teal)],
    [
      tableCell("inplace patch", { bold: true, color: C.teal }),
      tableCell("기존 초안을 유지한 채 명확한 오류 지점만 국소 수정한다."),
    ],
    [
      tableCell("reduced regenerate", { bold: true, color: C.teal }),
      tableCell("일부 장면 또는 논리 블록만 다시 써서 비용을 낮춘다."),
    ],
    [
      tableCell("full regenerate", { bold: true, color: C.teal }),
      tableCell("patch 계약이 무너지면 거의 새 원고처럼 다시 생성한다."),
    ],
    [
      tableCell("blueprint regenerate", { bold: true, color: C.teal }),
      tableCell("원고 레벨에서 수렴하지 않으면 단일 에피소드 blueprint까지 역피드백을 올린다."),
    ],
    [
      tableCell("QR-7 reroute / HIL", { bold: true, color: C.teal }),
      tableCell("동일 pathology가 반복되면 full rewrite reroute 또는 인간 개입 구간으로 escalation된다."),
    ],
  ],
  {
    x: 0.82,
    y: 3.48,
    w: 11.7,
    h: 2.6,
    colW: [2.2, 9.5],
    fontSize: 9.6,
  }
)
addCallout(
  slide,
  "요지: 첫 라운드는 ensemble 3개 후보에서 시작하고, Stage 4 기준 기본 5회 기회가 소진되면 HIL 또는 stop으로 넘어간다.",
  0.82,
  6.28,
  11.7,
  0.62,
  "accent"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "수정 경로는 스테이지마다 다르다",
  "같은 PASS_WITH_FIX라도 stage별 처리 방식과 복구 범위가 다르다",
  5,
  total
)
addTable(
  slide,
  [
    [
      headerCell("Stage"),
      headerCell("Gate", C.accent),
      headerCell("PASS / PASS_WITH_FIX 처리", C.teal),
      headerCell("REJECT 또는 실패 시", C.red),
    ],
    [
      tableCell("Stage 0", { bold: true }),
      tableCell("review gate / handoff gate", { bold: true, align: "center" }),
      tableCell("save-handoff 적합성 review. 통과하지 못하면 저장이나 다음 단계 handoff를 막는다."),
      tableCell("RETRY면 재작성, REJECT면 stop."),
    ],
    [
      tableCell("Stage 2", { bold: true }),
      tableCell("finalize gate", { bold: true, align: "center" }),
      tableCell("PASS_WITH_FIX면 arc patch 후 Director 재감리."),
      tableCell("해결되지 않으면 REJECT로 떨어지고 arc를 다시 잡는다."),
    ],
    [
      tableCell("Stage 3", { bold: true }),
      tableCell("validate gate", { bold: true, align: "center" }),
      tableCell("PASS_WITH_FIX면 blueprint patch. PASS_WITH_WARNING도 존재한다."),
      tableCell("quality gate, dead-NPC precheck에서 다시 REJECT로 내려갈 수 있다."),
    ],
    [
      tableCell("Stage 4", { bold: true }),
      tableCell("director interview", { bold: true, align: "center" }),
      tableCell("PASS_WITH_FIX는 accept branch 내부 local patch loop다."),
      tableCell("REJECT면 retry routing으로 들어가 partial / full / blueprint regenerate가 열린다."),
    ],
  ],
  {
    x: 0.72,
    y: 1.55,
    w: 12.0,
    h: 4.75,
    colW: [1.1, 2.05, 4.3, 4.55],
    fontSize: 9.4,
  }
)
addCallout(
  slide,
  "같은 '수정'이라는 표현을 쓰더라도, 실제로는 stage-local patch부터 full regenerate, blueprint regenerate까지 범위가 다르게 설계되어 있다.",
  0.72,
  6.4,
  12.0,
  0.58,
  "teal"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "저장 이후의 컨텍스트 재주입",
  "PASS된 결과는 다음 화 생성 때 계층형 컨텍스트로 다시 조립된다",
  6,
  total
)
addPanel(slide, 0.74, 1.55, 4.15, 4.9, C.white, C.line)
addPanelTitle(slide, "저장되는 자산", 0.98, 1.8, 1.8, C.accent, 12.5)
addBody(
  slide,
  "episode_bible\nworld_state\nfact_ledger\nstage_attempts / director_selections\nrecent manuscripts / blueprint history\ncurrent arc / current blueprint",
  1.02,
  2.2,
  3.4,
  2.1,
  { fontSize: 11.2, bold: true }
)
addCallout(
  slide,
  "저장으로 끝나지 않는다. 다음 화 Writer prompt의 재료로 다시 투입된다.",
  0.98,
  5.3,
  3.7,
  0.72,
  "accent"
)
addPanel(slide, 5.2, 1.55, 7.38, 4.9, C.white, C.line)
addPanelTitle(slide, "Stage 4 Context Builder", 5.46, 1.8, 2.6, C.teal, 12.5)
addTierBand(slide, "Tier 0", "world_state / fact_ledger", 5.5, 2.18, 6.8, "navy")
addTierBand(slide, "Tier 1", "episode_bible / recent manuscript", 5.5, 3.06, 6.8, "accent")
addTierBand(slide, "Tier 2", "stage_attempts / retry pathology", 5.5, 3.94, 6.8, "teal")
addTierBand(slide, "Tier 3", "current arc / current blueprint", 5.5, 4.82, 6.8, "green")
addCallout(
  slide,
  "장점: 연속성과 추적 가능성이 높아진다.",
  5.5,
  5.86,
  3.25,
  0.56,
  "green"
)
addCallout(
  slide,
  "리스크: 상류 오류나 오염된 컨텍스트가 다음 단계 전체로 전염될 수 있다.",
  8.97,
  5.86,
  3.33,
  0.56,
  "red"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "현재 주요 병목 3가지",
  "운영 관찰상 retry 비용, 계약 정규화, 인간 선호 품질이 핵심 병목이다",
  7,
  total
)
const bottlenecks = [
  {
    x: 0.78,
    tone: "accent",
    title: "최적화 문제",
    body: "Director 기준에 바로 맞는 원고가 나오지 않는 경우가 많다.\nWriter가 여러 차례 재생성해야 해서 비용과 시간이 함께 늘어난다.",
    foot: "문제의 중심: retry cost",
  },
  {
    x: 4.47,
    tone: "teal",
    title: "안정화 문제",
    body: "파이프라인 간 암묵적 계약과 컨텍스트 계층화가 완전히 정규화되지 않았다.\nStage 간 오염이 발생하면 HIL을 쉽게 뺄 수 없다.",
    foot: "문제의 중심: contract normalization",
  },
  {
    x: 8.16,
    tone: "green",
    title: "퀄리티 문제",
    body: "연속성과 정합성을 맞춘 원고라도 사람 기준의 재미, 문체, 흡입력은 별도 문제다.\n연속성 해결과 인간 선호는 자동으로 일치하지 않는다.",
    foot: "문제의 중심: preference quality",
  },
]
for (const item of bottlenecks) {
  addPanel(slide, item.x, 1.72, 3.45, 3.95, C.white, C.line)
  addChip(slide, item.title, item.x + 0.2, 1.98, 1.55, item.tone)
  addBody(slide, item.body, item.x + 0.22, 2.6, 2.98, 1.7, {
    fontSize: 11,
  })
  addCallout(slide, item.foot, item.x + 0.2, 4.78, 3.05, 0.56, item.tone)
}
addCallout(
  slide,
  "발표용 정리: 지금의 핵심 과제는 '더 많이 쓰게 하는 것'이 아니라, retry 비용 절감 + 컨텍스트 오염 제어 + 인간 선호 품질 안정화를 동시에 달성하는 것이다.",
  0.78,
  6.08,
  10.83,
  0.68,
  "accent"
)

slide = pptx.addSlide()
addChrome(
  slide,
  "발표용 결론",
  "구조적 강점과 현재 과제를 한 장에 닫는다",
  8,
  total
)
addPanel(slide, 0.78, 1.58, 5.15, 4.95, C.white, C.line)
addPanelTitle(slide, "이 시스템이 실제로 하는 일", 1.02, 1.84, 2.55, C.accent, 12.5)
addBody(
  slide,
  "설계 자산 -> Writer 생성 -> Director 판정 -> 저장 -> 컨텍스트 재주입\n\n강점\n- 연속성 유지\n- 추적 가능성\n- stage별 수정 경로 분리\n\n현재 핵심 과제\n- retry 비용 절감\n- 컨텍스트 오염 제어\n- 인간 선호 품질 안정화",
  1.02,
  2.22,
  4.35,
  3.85,
  { fontSize: 11.3 }
)
addPanel(slide, 6.24, 1.58, 6.28, 2.45, C.navy, C.navy)
addPanelTitle(slide, "Closing Line", 6.54, 1.94, 1.6, C.white, 13)
addBody(
  slide,
  "글도비는 '원고를 한 번 뽑는 도구'가 아니라,\n판정과 재주입까지 포함한 폐루프형 서사 생산 시스템이다.",
  6.54,
  2.42,
  5.68,
  1.05,
  { fontSize: 15, color: C.white, bold: true }
)
addPanel(slide, 6.24, 4.28, 6.28, 2.25, C.white, C.line)
addPanelTitle(slide, "질의응답 포인트", 6.54, 4.56, 2.1, C.teal, 12.5)
addBody(
  slide,
  "1. 왜 Writer와 Director를 분리했는가\n2. 왜 저장 후 재주입 구조가 필요한가\n3. 현재 병목을 줄이면 무엇이 가장 먼저 개선되는가",
  6.54,
  4.94,
  5.4,
  1.1,
  { fontSize: 11.5 }
)

async function main() {
  await pptx.writeFile({ fileName: OUTPUT_PATH })
  console.log(`Created: ${OUTPUT_PATH}`)
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
