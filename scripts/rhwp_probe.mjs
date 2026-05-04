#!/usr/bin/env node
/** rhwp/@rhwp-core probe helper for SHawn-hwp.
 *
 * This intentionally keeps rhwp as an optional external engine. It loads
 * @rhwp/core from external/rhwp-core by default, emits JSON, and can export SVG
 * pages for visual/layout QA without replacing SHawn-hwp's text-first salvage
 * routes.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(__filename), '..');
const DEFAULT_CORE_DIR = path.join(REPO_ROOT, 'external', 'rhwp-core', 'node_modules', '@rhwp', 'core');

function usage() {
  console.error(`Usage:
  node scripts/rhwp_probe.mjs info --input file.hwp [--json out.json]
  node scripts/rhwp_probe.mjs export-svg --input file.hwp --outdir outdir [--pages 0,1]
  node scripts/rhwp_probe.mjs export-layout --input file.hwp --json out.json [--pages 0,1]

Environment:
  SHAWN_HWP_RHWP_CORE_DIR   Override @rhwp/core package directory
`);
}

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const args = { command };
  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (!token.startsWith('--')) {
      throw new Error(`Unexpected argument: ${token}`);
    }
    const key = token.slice(2).replaceAll('-', '_');
    const value = rest[i + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for ${token}`);
    }
    args[key] = value;
    i += 1;
  }
  return args;
}

function installMeasureTextFallback() {
  globalThis.measureTextWidth = (font, text) => {
    const fontText = String(font || '');
    const match = fontText.match(/(\d+(?:\.\d+)?)px/);
    const fontSize = match ? Number(match[1]) : 16;
    let width = 0;
    for (const ch of String(text || '')) {
      // Korean/CJK glyphs are roughly square; latin/digits narrower.
      width += /[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af\u4e00-\u9fff]/u.test(ch)
        ? fontSize
        : fontSize * 0.55;
    }
    return width;
  };
}

async function loadCore() {
  const coreDir = process.env.SHAWN_HWP_RHWP_CORE_DIR || DEFAULT_CORE_DIR;
  const modulePath = path.join(coreDir, 'rhwp.js');
  const wasmPath = path.join(coreDir, 'rhwp_bg.wasm');
  if (!fs.existsSync(modulePath) || !fs.existsSync(wasmPath)) {
    throw new Error(`@rhwp/core is not installed at ${coreDir}`);
  }
  installMeasureTextFallback();
  const core = await import(pathToFileURL(modulePath).href);
  await core.default({ module_or_path: fs.readFileSync(wasmPath) });
  return { HwpDocument: core.HwpDocument, coreDir, wasmPath };
}

function loadDocument(HwpDocument, inputPath) {
  const data = new Uint8Array(fs.readFileSync(inputPath));
  return new HwpDocument(data);
}

function writeJson(payload, jsonPath) {
  const text = JSON.stringify(payload, null, 2) + '\n';
  if (jsonPath) {
    fs.mkdirSync(path.dirname(path.resolve(jsonPath)), { recursive: true });
    fs.writeFileSync(jsonPath, text, 'utf8');
  } else {
    process.stdout.write(text);
  }
}

function parsePages(pages, pageCount) {
  if (!pages) return Array.from({ length: pageCount }, (_, i) => i);
  return pages.split(',').map((part) => Number(part.trim())).filter(Number.isInteger);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.command || args.help) {
    usage();
    return 2;
  }
  if (!args.input) throw new Error('--input is required');

  const inputPath = path.resolve(args.input);
  const { HwpDocument, coreDir } = await loadCore();
  const doc = loadDocument(HwpDocument, inputPath);
  const pageCount = doc.pageCount();

  if (args.command === 'info') {
    writeJson({
      engine: 'rhwp-core',
      core_dir: coreDir,
      input: inputPath,
      input_size_bytes: fs.statSync(inputPath).size,
      page_count: pageCount,
    }, args.json);
    return 0;
  }

  if (args.command === 'export-svg') {
    if (!args.outdir) throw new Error('--outdir is required for export-svg');
    const outdir = path.resolve(args.outdir);
    fs.mkdirSync(outdir, { recursive: true });
    const pages = parsePages(args.pages, pageCount);
    const outputs = [];
    for (const page of pages) {
      if (page < 0 || page >= pageCount) throw new Error(`Page out of range: ${page}`);
      const svg = doc.renderPageSvg(page);
      const outPath = path.join(outdir, `page-${String(page).padStart(4, '0')}.svg`);
      fs.writeFileSync(outPath, svg, 'utf8');
      outputs.push(outPath);
    }
    writeJson({
      engine: 'rhwp-core',
      core_dir: coreDir,
      input: inputPath,
      page_count: pageCount,
      exported_pages: pages,
      outputs,
    }, args.json);
    return 0;
  }

  if (args.command === 'export-layout') {
    const pages = parsePages(args.pages, pageCount);
    const layouts = [];
    for (const page of pages) {
      if (page < 0 || page >= pageCount) throw new Error(`Page out of range: ${page}`);
      layouts.push({
        page_index: page,
        page_info: JSON.parse(doc.getPageInfo(page)),
        text_layout: JSON.parse(doc.getPageTextLayout(page)),
        render_tree: JSON.parse(doc.getPageRenderTree(page)),
      });
    }
    writeJson({
      engine: 'rhwp-core',
      core_dir: coreDir,
      input: inputPath,
      page_count: pageCount,
      exported_pages: pages,
      pages: layouts,
    }, args.json);
    return 0;
  }

  throw new Error(`Unknown command: ${args.command}`);
}

main().then((code) => process.exitCode = code).catch((err) => {
  console.error(`rhwp_probe error: ${err.message}`);
  process.exitCode = 1;
});
