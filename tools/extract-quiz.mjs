/**
 * 从 docs/10-测试题与答案.md 与 docs/11-面试速查表.md 抽取结构化题库，
 * 输出 site/quiz-bank.json，供练习站使用。
 *
 * 用法（在 tools 目录下）：
 *   node extract-quiz.mjs
 *
 * 抽取内容：
 *   - 第一关 判断对错（20 题）
 *   - 第二关 说出输出（25 题，Python 代码，用 `# N` 注释分隔）
 *   - 面试速查表里的高频问答
 */

import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '..');
const docsDir = path.join(ROOT, 'docs');
const outDir = path.join(ROOT, 'site');

const md10 = fs.readFileSync(path.join(docsDir, '10-测试题与答案.md'), 'utf8');
const md11 = fs.readFileSync(path.join(docsDir, '11-面试速查表.md'), 'utf8');

const bank = { stage1: [], stage2: [], interview: [] };

/** 取 [startRe, endRe) 之间的片段 */
function section(text, startRe, endRe) {
  const s = text.search(startRe);
  if (s < 0) return '';
  const rest = text.slice(s);
  const e = rest.slice(1).search(endRe);
  return e < 0 ? rest : rest.slice(0, e + 1);
}

/**
 * 按 | 切分表格行，保留被转义的 \| 。
 * 返回去掉首尾空字段后的单元格数组；不是表格行返回 null。
 */
function cells(line) {
  const t = line.trim();
  if (!t.startsWith('|')) return null;
  const parts = t
    .replace(/\\\|/g, '\u0000')   // 保护被转义的竖线
    .split('|')
    .map((s) => s.replace(/\u0000/g, '|').trim());
  // 首尾各有一个空串（因为行以 | 开头结尾）
  if (parts.length >= 2 && parts[0] === '') parts.shift();
  if (parts.length >= 1 && parts[parts.length - 1] === '') parts.pop();
  return parts;
}

/* ───────────── 第一关：判断对错 ───────────── */
const s1 = section(md10, /## 第一关 · 概念快问快答/, /\n## 第二关 · 说出输出/);
const s1ans = section(md10, /## 第一关答案/, /\n## 第二关答案/);

const q1 = {};
for (const line of s1.split('\n')) {
  const m = line.match(/^(\d+)\.\s+(.*)$/);
  if (m) q1[Number(m[1])] = m[2].trim();
}

const a1 = {};
for (const line of s1ans.split('\n')) {
  const c = cells(line);
  if (!c || c.length < 4) continue;
  const no = Number(c[0]);
  if (!Number.isInteger(no)) continue;
  const ans = c[1].replace(/\*/g, '').trim();   // **对** → 对
  if (ans !== '对' && ans !== '错') continue;
  a1[no] = { answer: ans === '对', why: c[2], from: c[3] };
}

for (const n of Object.keys(q1).map(Number).sort((a, b) => a - b)) {
  const a = a1[n];
  bank.stage1.push({
    id: `s1-${n}`,
    no: n,
    q: q1[n],
    answer: a ? a.answer : null,
    why: a ? a.why : '',
    from: a ? a.from : '',
  });
}

/* ───────────── 第二关：说出输出 ───────────── */
const s2 = section(md10, /## 第二关 · 说出输出/, /\n## 第三关 · 改错/);
const s2ans = section(md10, /## 第二关答案/, /\n## 第三关答案/);

// 题面：代码块里 `# N` 单独一行作为分隔（Python 注释）
const codeLines = {};
const codeBlock = s2.match(/```(?:python|py)\n([\s\S]*?)```/);
if (codeBlock) {
  let cur = null;
  for (const line of codeBlock[1].split('\n')) {
    const m = line.match(/^#\s*(\d+)\s*$/);
    if (m) {
      cur = Number(m[1]);
      codeLines[cur] = [];
      continue;
    }
    if (cur !== null) codeLines[cur].push(line);
  }
}

// 答案表：| # | 输出 | 关键点 |
const a2 = {};
for (const line of s2ans.split('\n')) {
  const c = cells(line);
  if (!c || c.length < 3) continue;
  const no = Number(c[0]);
  if (!Number.isInteger(no)) continue;
  a2[no] = { out: c[1], note: c[2] };
}

const q2nos = Object.keys(codeLines).map(Number).sort((a, b) => a - b);
for (const n of q2nos) {
  const a = a2[n];
  // 去掉题目代码首尾的空行
  const code = (codeLines[n] || []).join('\n').replace(/^\n+|\n+$/g, '');
  bank.stage2.push({
    id: `s2-${n}`,
    no: n,
    code,
    out: a ? a.out : '',
    note: a ? a.note : '',
  });
}

/* ───────────── 面试题（11 章） ───────────── */
const qMarks = [];
const reQ = /\*\*Q(\d+)[:：]\s*([\s\S]*?)\*\*/g;
let mq;
while ((mq = reQ.exec(md11)) !== null) {
  const t = mq[2].trim();
  if (t.endsWith('?') || t.endsWith('？')) {
    qMarks.push({ no: Number(mq[1]), q: t, start: mq.index, end: reQ.lastIndex });
  }
}
for (let i = 0; i < qMarks.length; i++) {
  const cur = qMarks[i];
  const next = qMarks[i + 1];
  let body = md11.slice(cur.end, next ? next.start : cur.end + 2000);
  body = body.split(/\n###\s/)[0].trim();
  if (body.length < 10) continue;
  bank.interview.push({
    id: `iv-${cur.no}-${i}`,
    no: cur.no,
    q: cur.q,
    a: body.slice(0, 1600),
  });
}

/* ───────────── 输出 ───────────── */
fs.mkdirSync(outDir, { recursive: true });
const out = path.join(outDir, 'quiz-bank.json');
fs.writeFileSync(out, JSON.stringify(bank, null, 2), 'utf8');

console.log('第一关（判断）    ', bank.stage1.length, '题');
console.log('第二关（说输出）  ', bank.stage2.length, '题');
console.log('面试题            ', bank.interview.length, '题');

const miss1 = bank.stage1.filter((x) => x.answer === null);
const miss2 = bank.stage2.filter((x) => !x.out);
const miss1why = bank.stage1.filter((x) => !x.why);
let problems = 0;
if (bank.stage1.length !== 20) { console.log('⚠ 第一关题数应为 20，实际', bank.stage1.length); problems++; }
if (bank.stage2.length !== 25) { console.log('⚠ 第二关题数应为 25，实际', bank.stage2.length); problems++; }
if (miss1.length) { console.log('⚠ 缺答案的第一关题号:', miss1.map((x) => x.no).join(',')); problems++; }
if (miss2.length) { console.log('⚠ 缺输出的第二关题号:', miss2.map((x) => x.no).join(',')); problems++; }
if (miss1why.length) { console.log('⚠ 缺解析的第一关题号:', miss1why.map((x) => x.no).join(',')); problems++; }
if (bank.interview.length < 30) { console.log('⚠ 面试题少于 30 道，检查 11 章格式'); problems++; }

// 答案分布合理性（避免全是"对"）
const yes = bank.stage1.filter((x) => x.answer === true).length;
console.log('第一关答案分布    ', yes, '对 /', bank.stage1.length - yes, '错');
if (yes === 0 || yes === bank.stage1.length) { console.log('⚠ 第一关答案一边倒，可能解析错了'); problems++; }

console.log(problems === 0 ? '\n✅ 题库抽取正常' : `\n❌ 存在 ${problems} 个问题`);
console.log('写入 ->', path.relative(ROOT, out));
if (problems) process.exitCode = 1;
