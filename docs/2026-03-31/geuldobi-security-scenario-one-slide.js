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
  "geuldobi-security-scenario-one-slide.pptx"
)

const pptx = new PptxGenJS()
pptx.layout = "LAYOUT_WIDE"
pptx.author = "Codex"
pptx.company = "글도비"
pptx.subject = "FE 시나리오별 현재 취약점과 해결 방향"
pptx.title = "Geuldobi Security Scenario One Slide"
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

function addBody(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    fontFace: FONT.body,
    fontSize: opts.fontSize || 10.6,
    bold: opts.bold || false,
    color: opts.color || C.ink,
    align: opts.align || "left",
    valign: opts.valign || "top",
    margin: opts.margin || 0.04,
    breakLine: false,
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
  addBody(slide, label, x + 0.12, y + 0.1, w - 0.24, 0.18, {
    fontSize: 10,
    bold: true,
    color: lineMap[tone],
    align: "center",
    valign: "mid",
  })
}

function addBulletList(slide, items, x, y, w, startY = 0, fontSize = 10.4, gap = 0.54) {
  let offset = startY
  for (const item of items) {
    addBody(slide, "•", x, y + offset, 0.18, 0.18, {
      fontSize,
      bold: true,
      color: C.ink,
      valign: "mid",
      align: "center",
    })
    addBody(slide, item, x + 0.2, y + offset - 0.01, w - 0.2, 0.34, {
      fontSize,
      color: C.ink,
    })
    offset += gap
  }
}

function addSectionCard(slide, title, riskItems, solutionItems, x, tone) {
  const toneLine = {
    accent: C.accent,
    teal: C.teal,
    green: C.green,
    navy: C.navy,
  }[tone]
  const toneFill = {
    accent: C.accentSoft,
    teal: C.tealSoft,
    green: C.greenSoft,
    navy: C.navySoft,
  }[tone]

  addPanel(slide, x, 1.55, 5.9, 4.95, C.white, C.line)
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y: 1.55,
    w: 5.9,
    h: 0.5,
    line: { color: toneLine, pt: 0 },
    fill: { color: toneLine },
  })
  addBody(slide, title, x + 0.18, 1.69, 5.5, 0.2, {
    fontSize: 13,
    bold: true,
    color: C.white,
    align: "center",
    valign: "mid",
  })

  addPanel(slide, x + 0.2, 2.28, 5.5, 1.6, toneFill, toneLine)
  addChip(slide, "현재 취약점", x + 0.36, 2.46, 1.12, "red")
  addBulletList(slide, riskItems, x + 0.38, 2.86, 4.96, 0, 10.2, 0.44)

  addPanel(slide, x + 0.2, 4.14, 5.5, 1.96, C.paper, C.line)
  addChip(slide, "해결 방향", x + 0.36, 4.34, 1.12, "green")
  addBulletList(slide, solutionItems, x + 0.38, 4.74, 4.96, 0, 10.15, 0.44)
}

const slide = pptx.addSlide()
slide.background = { color: C.paper }
slide.addShape(pptx.ShapeType.rect, {
  x: 0,
  y: 0,
  w: 13.333,
  h: 0.26,
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

addBody(slide, "현재 취약점과 해결 방안", 0.68, 0.46, 4.7, 0.32, {
  fontSize: 24,
  bold: true,
  color: C.ink,
})
addBody(
  slide,
  "FE 시나리오별로 보면 취약점의 무게중심이 달라지지만, 공통 핵심은 API/자격증명 관리다",
  0.72,
  0.98,
  7.6,
  0.26,
  { fontSize: 10.8, color: C.muted }
)
addBody(slide, "1/1", 12.02, 0.54, 0.55, 0.2, {
  fontSize: 10,
  color: C.muted,
  align: "right",
})

addSectionCard(
  slide,
  "FE 포기 · 운영 전용 백엔드",
  [
    "주요 리스크는 외부 해킹보다 평문 API 키 저장, 백업본, subprocess env 확산이다.",
    "원고·판정 사유·운영 로그는 계속 필요하므로, 기기/계정 통제가 약하면 그대로 노출된다.",
    "즉 공격면은 줄지만 secret 관리가 약하면 내부 운영형 구조도 안전하지 않다.",
  ],
  [
    "desktop/bridge를 걷어내고 CLI/배치 중심으로 단순화한다.",
    "API key보다 Vertex service account 또는 OS credential store로 전환한다.",
    "운영자 계정 분리, 디스크 암호화, 최소 감사 로그만 유지한다.",
  ],
  0.72,
  "accent"
)

addSectionCard(
  slide,
  "내부 운영용 FE 유지",
  [
    "localhost bridge 무인증, 전역 WebSocket broadcast, prompt/input 노출이 현재 제일 직접적인 취약점이다.",
    "settings.json 평문 키 저장과 .bak 복구본은 로컬 탈취 면을 넓힌다.",
    "결국 FE 자체보다 control plane과 secret 저장 방식이 문제의 중심이다.",
  ],
  [
    "HTTP 대신 로컬 IPC 또는 세션 토큰 기반 bridge로 제한한다.",
    "WebSocket은 run_id 또는 세션 단위로 scope를 분리한다.",
    "API 키 평문 저장을 없애고, FE는 운영 편의 기능만 담당하게 만든다.",
  ],
  6.72,
  "teal"
)

addPanel(slide, 0.92, 6.65, 11.48, 0.34, C.navy, C.navy)
addBody(
  slide,
  "결론: FE를 안 만들면 공격면은 크게 줄지만, 어떤 시나리오든 보안의 중심은 API/자격증명 관리와 실행 권한 통제다.",
  1.12,
  6.74,
  11.08,
  0.14,
  { fontSize: 11.2, bold: true, color: C.white, align: "center", valign: "mid" }
)

async function main() {
  await pptx.writeFile({ fileName: OUTPUT_PATH })
  console.log(`Created: ${OUTPUT_PATH}`)
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
