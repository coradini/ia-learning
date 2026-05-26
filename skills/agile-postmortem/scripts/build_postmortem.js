/**
 * build_postmortem.js — gera o Post Mortem em .docx a partir de um JSON de conteúdo,
 * mantendo o PADRÃO VISUAL fixo. Não altere o bloco FORMAT sem intenção: ele é o que
 * garante que todo post mortem saia idêntico ao template aprovado.
 *
 * Uso:
 *   npm install docx        (uma vez, na pasta da skill)
 *   node build_postmortem.js <conteudo.json> <saida.docx>
 *
 * Estrutura do JSON: ver scripts/content.example.json e references/content-schema.md
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, LevelFormat,
  AlignmentType, ExternalHyperlink
} = require("docx");

// ===================== FORMAT — PARÂMETROS VISUAIS (PADRÃO FIXO) =====================
const FORMAT = {
  FONT: "Arial",
  BODY_SIZE: 22,        // meio-pontos (22 = 11pt)
  H1_SIZE: 32,          // 16pt
  H2_SIZE: 26,          // 13pt
  LINE_SPACING: 360,    // 240=simples, 276=1.15, 360=1.5, 480=duplo
  SPACE_AFTER: 160,     // espaço após parágrafo, em twips (240 ≈ 1 linha)
  H1_BEFORE: 240, H1_AFTER: 200,
  H2_BEFORE: 320, H2_AFTER: 160,
  BULLET_L0: "•", BULLET_L1: "◦",
  HINT_COLOR: "808080", // cinza para dicas/itálico ("(apagar)", evidências)
  TIMELINE_GLYPH: "▸",
  PAGE: { width: 12240, height: 15840, margin: 1440 } // US Letter, margens de 1"
};
// ====================================================================================

const contentPath = process.argv[2];
const outPath = process.argv[3] || "post_mortem.docx";
if (!contentPath) { console.error("Uso: node build_postmortem.js <conteudo.json> <saida.docx>"); process.exit(1); }
const C = JSON.parse(fs.readFileSync(contentPath, "utf8"));

// ---------- helpers de runs ----------
function t(text, opts = {}) { return new TextRun({ text: String(text), ...opts }); }
function mailRuns(value) {
  // transforma e-mails em hyperlinks mailto, mantendo o resto como texto
  const s = String(value || "");
  const re = /[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}/g;
  const runs = []; let last = 0, m;
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) runs.push(t(s.slice(last, m.index)));
    runs.push(new ExternalHyperlink({ children: [new TextRun({ text: m[0], style: "Hyperlink" })], link: "mailto:" + m[0] }));
    last = m.index + m[0].length;
  }
  if (last < s.length) runs.push(t(s.slice(last)));
  return runs.length ? runs : [t(s)];
}
function valueRuns(value) {
  const s = String(value || "");
  if (/^https?:\/\//i.test(s.trim())) return [new ExternalHyperlink({ children: [new TextRun({ text: s.trim(), style: "Hyperlink" })], link: s.trim() })];
  if (s.includes("@")) return mailRuns(s);
  return [t(s)];
}

// ---------- helpers de parágrafos ----------
function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(text, { bold: true })] }); }
function h2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(text, { bold: true })] }); }
function para(runs) { return new Paragraph({ children: runs }); }
function hint(text) { return new Paragraph({ children: [t(text, { italics: true, color: FORMAT.HINT_COLOR })] }); }
function bullet(runs, level = 0) { return new Paragraph({ numbering: { reference: "bul", level }, children: runs }); }
function labelVal(label, runs, level = 0) { return bullet([t(label, { bold: true }), ...runs], level); }
function tlRow(hora, texto) {
  const kids = [t(FORMAT.TIMELINE_GLYPH + " ")];
  if (hora) kids.push(t(hora + "  ", { bold: true }));
  kids.push(t("· " + texto));
  return new Paragraph({ spacing: { after: FORMAT.SPACE_AFTER, line: FORMAT.LINE_SPACING }, children: kids });
}
function dayLabel(text) { return new Paragraph({ spacing: { before: FORMAT.SPACE_AFTER, after: FORMAT.SPACE_AFTER, line: FORMAT.LINE_SPACING }, children: [t(text, { bold: true })] }); }

// item pode ser string ou {texto, sub:[...]}
function listItems(arr) {
  const out = [];
  (arr || []).forEach(it => {
    if (typeof it === "string") { out.push(bullet([t(it)])); }
    else { out.push(bullet([t(it.texto || "")])); (it.sub || []).forEach(s => out.push(bullet([t(s)], 1))); }
  });
  return out;
}

const children = [];

// TÍTULO
children.push(h1(C.titulo || "POST MORTEM"));

// CABEÇALHO
const cab = C.cabecalho || {};
const cabFields = [
  ["Apps ou sites afetados: ", cab.appsAfetados],
  ["Data do Incidente: ", cab.dataIncidente],
  ["Janela do impacto para usuário: ", cab.janelaImpacto],
  ["Indisponibilidade do serviço: ", cab.indisponibilidade],
  ["Time Responsável: ", cab.timeResponsavel],
  ["Squad Lead: ", cab.squadLead],
  ["Gestor: ", cab.gestor],
  ["Participantes da análise: ", cab.participantes],
  ["Transcrição da reunião: ", cab.linkTranscricao || C.linkTranscricao],
];
cabFields.forEach(([lab, val]) => { if (val !== undefined && val !== null && val !== "") children.push(labelVal(lab, valueRuns(val))); });

// 1 RESUMO
children.push(h2("1 · RESUMO"));
(C.resumo || []).forEach(p => children.push(para([t(p)])));
if (C.evidenciasResumo) children.push(hint("Evidência: " + C.evidenciasResumo));

// 2 IMPACTOS
children.push(h2("2 · IMPACTOS"));
listItems(C.impactos).forEach(p => children.push(p));

// 3 TIMELINE
children.push(h2("3 · TIMELINE"));
(C.timeline || []).forEach(grp => {
  if (grp.dia) children.push(dayLabel(grp.dia));
  (grp.linhas || []).forEach(l => children.push(tlRow(l.hora, l.texto)));
});

// 4 CAUSA RAIZ
children.push(h2("4 · CAUSA RAIZ"));
listItems(C.causaRaiz).forEach(p => children.push(p));

// 5 AÇÕES DE CONTORNO
children.push(h2("5 · AÇÕES DE CONTORNO"));
listItems(C.acoesContorno).forEach(p => children.push(p));

// 6 LIÇÕES APRENDIDAS
children.push(h2("6 · LIÇÕES APRENDIDAS"));
listItems(C.licoes).forEach(p => children.push(p));

// 7 PLANO DE AÇÃO
children.push(h2("7 · PLANO DE AÇÃO"));
children.push(para([t("O post mortem é considerado concluído quando cada tarefa abaixo possuir um item de backlog (card) associado.")]));
(C.plano || []).forEach(tk => {
  children.push(labelVal("Tarefa: ", [t(tk.tarefa || "")], 0));
  if (tk.descricao) children.push(labelVal("Descrição: ", [t(tk.descricao)], 1));
  if (tk.responsavel) children.push(labelVal("Responsável: ", valueRuns(tk.responsavel), 1));
  if (tk.backlog) children.push(labelVal("Item de backlog: ", valueRuns(tk.backlog), 1));
});

// 8 NOTAS
if (C.notas && C.notas.length) {
  children.push(h2("8 · NOTAS E PONTOS A CONFIRMAR"));
  listItems(C.notas).forEach(p => children.push(p));
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: FORMAT.FONT, size: FORMAT.BODY_SIZE }, paragraph: { spacing: { line: FORMAT.LINE_SPACING, after: FORMAT.SPACE_AFTER } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: FORMAT.H1_SIZE, bold: true, font: FORMAT.FONT },
        paragraph: { spacing: { before: FORMAT.H1_BEFORE, after: FORMAT.H1_AFTER, line: FORMAT.LINE_SPACING }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: FORMAT.H2_SIZE, bold: true, font: FORMAT.FONT },
        paragraph: { spacing: { before: FORMAT.H2_BEFORE, after: FORMAT.H2_AFTER, line: FORMAT.LINE_SPACING }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bul", levels: [
        { level: 0, format: LevelFormat.BULLET, text: FORMAT.BULLET_L0, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: FORMAT.BULLET_L1, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ] },
    ]
  },
  sections: [{
    properties: { page: { size: { width: FORMAT.PAGE.width, height: FORMAT.PAGE.height }, margin: { top: FORMAT.PAGE.margin, right: FORMAT.PAGE.margin, bottom: FORMAT.PAGE.margin, left: FORMAT.PAGE.margin } } },
    children
  }]
});

Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(outPath, buffer); console.log("OK " + outPath + " (" + buffer.length + " bytes)"); });
