/**
 * build_template.js — gera o template em branco do post mortem (com [preencher]).
 * Uso: node build_template.js [saida.docx]   (default: Post_Mortem_TEMPLATE.docx)
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, LevelFormat,
  AlignmentType
} = require("docx");

const OUT_PATH = process.argv[2] || "Post_Mortem_TEMPLATE.docx";

// ===== PARÂMETROS DE ESPAÇAMENTO =====
// LINE_SPACING: 240 = simples, 276 = 1.15, 360 = 1.5, 480 = duplo.
// SPACE_AFTER: espaço após cada parágrafo, em twips (240 ≈ 1 linha).
const LINE_SPACING = 360;
const SPACE_AFTER = 160;

const FILL = "[preencher]";

function t(text, opts = {}) { return new TextRun({ text, ...opts }); }
function bullet(children, level = 0) { return new Paragraph({ numbering: { reference: "bul", level }, children }); }
function labelVal(label, valueRuns, level = 0) { return bullet([t(label, { bold: true }), ...valueRuns], level); }
function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(text, { bold: true })] }); }
function h2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(text, { bold: true })] }); }
function p(children, opts = {}) { return new Paragraph({ children, ...opts }); }
function sub(text) { return new Paragraph({ spacing: { before: SPACE_AFTER, after: SPACE_AFTER, line: LINE_SPACING }, children: [t(text, { bold: true })] }); }
// pergunta-chave (guia): itálico cinza, prefixada com (apagar)
function q(text) { return bullet([t("(apagar) " + text, { italics: true, color: "808080" })]); }
function tlRow() {
  return new Paragraph({ spacing: { after: SPACE_AFTER, line: LINE_SPACING },
    children: [t("▸ "), t("[hh:mm]  ", { bold: true }), t("· " + FILL)] });
}

const children = [];

// TITLE
children.push(h1("POST MORTEM — [PREENCHER: TÍTULO BREVE DO INCIDENTE]"));

// HEADER
// Apps ou sites afetados: só os nomes, em sub-bullets indentados.
children.push(bullet([t("Apps ou sites afetados:", { bold: true })]));
children.push(bullet([t(FILL + " — nome do app/sistema")], 1));
children.push(bullet([t(FILL)], 1));
children.push(labelVal("Data do Incidente: ", [t(FILL)]));
children.push(labelVal("Janela do impacto para usuário: ", [t(FILL)]));
children.push(labelVal("Indisponibilidade do serviço: ", [t(FILL)]));
children.push(labelVal("Time Responsável: ", [t(FILL)]));
children.push(labelVal("Squad Lead: ", [t(FILL)]));
children.push(labelVal("Gestor: ", [t(FILL)]));
children.push(labelVal("Participantes da análise: ", [t(FILL)]));
children.push(labelVal("Transcrição da reunião: ", [t(FILL)]));

// 1 RESUMO
children.push(h2("1 · RESUMO"));
children.push(p([t(FILL + " — descreva, em poucos parágrafos, o que aconteceu, o gatilho, a causa, o impacto e como foi contido.")]));
children.push(p([t("Evidência: " + FILL, { italics: true, color: "808080" })]));

// 2 IMPACTOS
children.push(h2("2 · IMPACTOS"));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)], 1));
children.push(bullet([t(FILL)]));

// 3 TIMELINE  (sessões por dia, para incidentes com mais de um dia)
children.push(h2("3 · TIMELINE"));
children.push(sub("Dia 1 — [dd/mm]"));
for (let i = 0; i < 3; i++) children.push(tlRow());
children.push(sub("Dia 2 — [dd/mm]"));
for (let i = 0; i < 3; i++) children.push(tlRow());

// 4 CAUSA RAIZ
children.push(h2("4 · CAUSA RAIZ"));
children.push(q("Qual foi o gatilho imediato e qual a causa raiz por trás dele? (são coisas distintas)"));
children.push(q("Por que as proteções existentes não contiveram o problema? O que permitiu que ele escalasse?"));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));

// 5 ACOES DE CONTORNO
children.push(h2("5 · AÇÕES DE CONTORNO"));
children.push(q("O que foi feito para restabelecer o serviço, e em que ordem?"));
children.push(q("A medida adotada é temporária ou definitiva? Deixa alguma brecha/risco em aberto?"));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));

// 6 LICOES APRENDIDAS
children.push(h2("6 · LIÇÕES APRENDIDAS"));
children.push(q("O que teria detectado ou evitado o problema mais cedo (alerta, monitoramento, runbook)?"));
children.push(q("O que precisa mudar — processo, arquitetura ou responsabilidade — para não se repetir?"));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));

// 7 PLANO DE ACAO
children.push(h2("7 · PLANO DE AÇÃO"));
children.push(p([t("O post mortem é considerado concluído quando cada tarefa abaixo possuir um item de backlog (card) associado.")]));
function taskBlock() {
  children.push(labelVal("Tarefa: ", [t(FILL)], 0));
  children.push(labelVal("Descrição: ", [t(FILL)], 1));
  children.push(labelVal("Responsável: ", [t(FILL)], 1));
  children.push(labelVal("Item de backlog: ", [t(FILL)], 1));
}
for (let i = 0; i < 3; i++) taskBlock();

// 8 NOTAS
children.push(h2("8 · NOTAS E PONTOS A CONFIRMAR"));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));
children.push(bullet([t(FILL)]));

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 }, paragraph: { spacing: { line: LINE_SPACING, after: SPACE_AFTER } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 200, line: LINE_SPACING }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 320, after: 160, line: LINE_SPACING }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bul", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ] },
    ]
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(OUT_PATH, buffer);
  console.log("OK " + OUT_PATH + " (" + buffer.length + " bytes)");
});
