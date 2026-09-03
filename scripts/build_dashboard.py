#!/usr/bin/env python3
"""
Собирает интерактивный HTML-дашборд Embassy.
Данные встраиваются в страницу как JSON — фильтр периода и график
работают в браузере без пересборки. Пересборка нужна только когда
в data/daily.csv или data/plans.csv появляются новые строки.
"""
import csv
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DAILY = ROOT / "data" / "daily.csv"
DATA_PLANS = ROOT / "data" / "plans.csv"
OUTPUT = ROOT / "index.html"


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v, default=0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def build():
    daily_rows = read_csv(DATA_DAILY)
    plan_rows = read_csv(DATA_PLANS)
    if not daily_rows:
        raise SystemExit("Нет данных в daily.csv")

    daily = []
    projects_order = []
    for row in daily_rows:
        p = row["project"]
        if p not in projects_order:
            projects_order.append(p)
        daily.append({
            "date": row["date"],
            "project": p,
            "channel": row.get("channel", ""),
            "leads_target": num(row.get("leads_target")),
            "leads_organic": num(row.get("leads_organic")),
            "budget_spent": num(row.get("budget_spent")),
            "pu_records": num(row.get("pu_records")),
            "pu_attended": num(row.get("pu_attended")),
            "sales_count": num(row.get("sales_count")),
            "revenue": num(row.get("revenue")),
            "doplaty": num(row.get("doplaty")),
        })

    plans = {}
    for row in plan_rows:
        p = row["project"]
        if p not in projects_order:
            projects_order.append(p)
        plans.setdefault(row["month"], {})[p] = {
            "revenue": num(row.get("plan_revenue")),
            "leads_target": num(row.get("plan_leads_target")),
            "leads_organic": num(row.get("plan_leads_organic")),
            "budget": num(row.get("plan_budget")),
            "pu_records": num(row.get("plan_pu_records")),
            "sales_count": num(row.get("plan_sales_count")),
        }

    now = datetime.datetime.now()
    payload = {
        "daily": daily,
        "plans": plans,
        "projects": projects_order,
        "generatedAt": now.strftime("%d.%m.%Y %H:%M"),
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Собрано: {OUTPUT} (записей: {len(daily)}, проектов: {len(projects_order)})")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Embassy — Дашборд</title>
<style>
  :root{
    --bg:#eef4fb; --card:#ffffff; --border:#d7e6f5;
    --navy:#173963; --navy-soft:#3a5a80;
    --blue:#2f6fb0; --blue-track:#e3edf7;
    --green:#6fbf5e; --green-dark:#3f8f3a; --green-track:#e2f2df;
    --teal:#3aa0a0; --amber:#e0a63a; --purple:#8a4fe0;
    --gray:#6b7a90; --red:#e2574c;
  }
  *{box-sizing:border-box;}
  body{ margin:0; background:var(--bg); font-family:'Manrope','Inter',-apple-system,BlinkMacSystemFont,sans-serif; color:var(--navy); padding:24px 0 60px; }
  .page{ max-width:1240px; margin:0 auto; padding:0 20px; }
  header.title{ text-align:center; margin-bottom:18px; }
  header.title h1{ font-size:28px; font-weight:800; margin:0 0 6px; color:var(--navy); }
  header.title p{ margin:0; color:var(--gray); font-size:13px; }
  .card{ background:var(--card); border:1px solid var(--border); border-radius:16px; box-shadow:0 2px 10px rgba(23,57,99,0.05); padding:18px 20px; }
  .row{ display:grid; gap:16px; margin-bottom:16px; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); }
  .metric{ text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; }
  .metric .label{ font-size:11.5px; font-weight:800; color:var(--navy-soft); }
  .metric .big{ font-size:19px; font-weight:800; color:var(--navy); }
  .metric .sub{ font-size:10.5px; color:var(--gray); }
  .ring{ position:relative; width:80px; height:80px; border-radius:50%; margin-top:2px; }
  .ring-inner{ position:absolute; inset:7px; background:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; }
  .ring-inner .pct{ font-size:13px; font-weight:800; }
  .ring-caption{ font-size:9.5px; color:var(--gray); }
  table{ width:100%; border-collapse:collapse; font-size:12.5px; }
  th,td{ padding:8px 10px; text-align:left; border-bottom:1px solid var(--border); }
  th{ background:#f2f7fc; color:var(--navy-soft); font-weight:800; font-size:11px; }
  td.num, th.num{ text-align:right; }
  td.pos{ color:var(--green-dark); font-weight:700; }
  td.neg{ color:var(--red); font-weight:700; }

  .filter-bar{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:16px; }
  .filter-btn{ background:#fff; border:1px solid var(--border); color:var(--navy-soft); font-size:12px; font-weight:700; padding:8px 14px; border-radius:10px; cursor:pointer; }
  .filter-btn:hover{ background:#f2f7fc; }
  .filter-btn.active{ background:var(--blue); color:#fff; border-color:var(--blue); }
  .filter-bar input[type=date]{ border:1px solid var(--border); border-radius:8px; padding:7px 10px; font-size:12px; font-family:inherit; color:var(--navy); }
  .filter-bar .apply-btn{ background:var(--navy); color:#fff; border:none; font-size:12px; font-weight:700; padding:8px 14px; border-radius:10px; cursor:pointer; }
  .filter-label{ font-size:11px; color:var(--gray); margin-right:4px; }

  .card-title{ font-size:12px; font-weight:800; color:var(--navy-soft); text-align:center; margin-bottom:10px; }
  .card-title.left{ text-align:left; }
  .chart-legend{ display:flex; justify-content:center; gap:14px; font-size:11px; color:var(--gray); flex-wrap:wrap; margin-top:8px; }
  .chart-legend .dot{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; vertical-align:middle; }
  .updated{ text-align:center; font-size:11px; color:var(--gray); margin-top:20px; }
  .period-caption{ text-align:center; font-size:12.5px; color:var(--navy-soft); font-weight:700; margin-bottom:14px; }
  .section-title{ text-align:center; font-size:16px; font-weight:800; color:#fff; background:linear-gradient(90deg,var(--navy),var(--blue)); padding:10px 18px; border-radius:12px; margin:26px 0 14px; }
  .lag-list{ display:flex; flex-direction:column; gap:10px; }
  .lag-row{ display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-radius:10px; background:#f7fafd; }
  .lag-row .name{ font-weight:700; font-size:13px; color:var(--navy); }
  .lag-row .amount{ font-weight:800; font-size:14px; }
  .lag-row.behind .amount{ color:var(--red); }
  .lag-row.ahead .amount{ color:var(--green-dark); }
</style>
</head>
<body>
<div class="page">
  <header class="title">
    <h1>EMBASSY — ДАШБОРД</h1>
    <p id="generated-at"></p>
  </header>

  <div class="filter-bar">
    <span class="filter-label">Период:</span>
    <button class="filter-btn" data-preset="today">Сегодня</button>
    <button class="filter-btn" data-preset="yesterday">Вчера</button>
    <button class="filter-btn" data-preset="last7">Последние 7 дней</button>
    <button class="filter-btn" data-preset="thisweek">Эта неделя</button>
    <button class="filter-btn active" data-preset="thismonth">Этот месяц</button>
    <button class="filter-btn" data-preset="lastmonth">Прошлый месяц</button>
    <span class="filter-label" style="margin-left:10px;">или свой период:</span>
    <input type="date" id="date-from">
    <span style="color:var(--gray);">—</span>
    <input type="date" id="date-to">
    <button class="apply-btn" id="apply-custom">Показать</button>
  </div>

  <div class="period-caption" id="period-caption"></div>

  <!-- 1. ПРИХОД: ПЛАН/ФАКТ -->
  <div class="row" id="cards-row"></div>

  <div class="card" style="margin-bottom:16px;">
    <div class="card-title">ДИНАМИКА ПРИХОДА ПО ДНЯМ</div>
    <div id="chart-wrap"></div>
    <div class="chart-legend" id="chart-legend"></div>
  </div>

  <!-- 2. ОТСТАВАНИЕ ОТ ПЛАНА -->
  <div class="section-title">ОТСТАВАНИЕ / ОПЕРЕЖЕНИЕ ПЛАНА, ТГ</div>
  <div class="card" style="margin-bottom:16px;">
    <div class="lag-list" id="lag-list"></div>
  </div>

  <!-- 3. ЛИДЫ: ТАРГЕТ/ОРГАНИКА, БЮДЖЕТ, CPL -->
  <div class="section-title">ЛИДЫ, БЮДЖЕТ И ЦЕНА ЗАЯВКИ (CPL)</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <thead>
        <tr>
          <th rowspan="2">Проект</th>
          <th class="num" colspan="2">Лиды таргет</th>
          <th class="num" colspan="2">Лиды органика</th>
          <th class="num" colspan="2">Бюджет, тг</th>
          <th class="num" colspan="2">CPL, тг</th>
        </tr>
        <tr>
          <th class="num">План</th><th class="num">Факт</th>
          <th class="num">План</th><th class="num">Факт</th>
          <th class="num">План</th><th class="num">Факт</th>
          <th class="num">План</th><th class="num">Факт</th>
        </tr>
      </thead>
      <tbody id="leads-table-body"></tbody>
    </table>
  </div>

  <!-- 4. ПРОБНЫЕ УРОКИ: ПЛАН/ФАКТ -->
  <div class="section-title">ПРОБНЫЕ УРОКИ (ПУ): ПЛАН / ФАКТ</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <tr><th>Проект</th><th class="num">План записей</th><th class="num">Факт записей</th><th class="num">% плана</th><th class="num">Дошли</th><th class="num">Доходимость</th></tr>
      <tbody id="pu-table-body"></tbody>
    </table>
  </div>

  <!-- 5. ПРОДАЖИ: ПЛАН/ФАКТ -->
  <div class="section-title">ПРОДАЖИ: ПЛАН / ФАКТ</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <tr><th>Проект</th><th class="num">План, шт</th><th class="num">Факт, шт</th><th class="num">% плана (шт)</th><th class="num">План, тг</th><th class="num">Факт, тг</th><th class="num">% плана (тг)</th></tr>
      <tbody id="sales-table-body"></tbody>
    </table>
  </div>

  <p class="updated">Данные пересобираются автоматически при внесении новых записей. Фильтр периода и график работают прямо в браузере.</p>
</div>

<script id="dashboard-data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
const PROJECT_COLORS = ['#2f6fb0', '#3aa0a0', '#e0a63a', '#6fbf5e', '#8a4fe0', '#e2574c'];
function colorFor(idx){ return PROJECT_COLORS[idx % PROJECT_COLORS.length]; }

document.getElementById('generated-at').textContent = 'Данные обновлены: ' + DATA.generatedAt;

function fmtTg(v){ return Math.round(v).toLocaleString('ru-RU') + ' тг'; }
function fmtInt(v){ return Math.round(v).toLocaleString('ru-RU'); }
function toISO(d){ return d.toISOString().slice(0,10); }
function daysInMonth(y, mIdx){ return new Date(y, mIdx+1, 0).getDate(); }
function monthKey(d){ return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0'); }

function proratedPlan(d, project, metric){
  const mk = monthKey(d);
  const mp = DATA.plans[mk];
  if (!mp || !mp[project]) return 0;
  return (mp[project][metric] || 0) / daysInMonth(d.getFullYear(), d.getMonth());
}

function eachDate(start, end){
  const out = []; let cur = new Date(start);
  while (cur <= end){ out.push(new Date(cur)); cur.setDate(cur.getDate()+1); }
  return out;
}

function renderRange(start, end, label){
  document.getElementById('period-caption').textContent =
    label + ' (' + toISO(start) + ' — ' + toISO(end) + ')';
  const startISO = toISO(start), endISO = toISO(end);
  const filtered = DATA.daily.filter(r => r.date >= startISO && r.date <= endISO);
  const dateList = eachDate(start, end);

  const empty = () => ({leads_target:0, leads_organic:0, budget_spent:0, pu_records:0, pu_attended:0, sales_count:0, revenue:0});
  const agg = {}; DATA.projects.forEach(p => agg[p] = empty());
  filtered.forEach(r => {
    if (!agg[r.project]) agg[r.project] = empty();
    const a = agg[r.project];
    a.leads_target += r.leads_target; a.leads_organic += r.leads_organic;
    a.budget_spent += r.budget_spent; a.pu_records += r.pu_records;
    a.pu_attended += r.pu_attended; a.sales_count += r.sales_count;
    a.revenue += r.revenue + r.doplaty;
  });

  const metrics = ['revenue','leads_target','leads_organic','budget','pu_records','sales_count'];
  const plan = {}; DATA.projects.forEach(p => { plan[p] = {}; metrics.forEach(m => plan[p][m]=0); });
  dateList.forEach(d => DATA.projects.forEach(p => metrics.forEach(m => { plan[p][m] += proratedPlan(d,p,m); })));

  const totalFact = DATA.projects.reduce((s,p)=>s+agg[p].revenue,0);
  const totalPlan = DATA.projects.reduce((s,p)=>s+plan[p].revenue,0);
  const totalPct = totalPlan ? (totalFact/totalPlan*100) : 0;

  // ---- 1. Карточки приход ----
  let cardsHtml = `
    <div class="card metric">
      <div class="label">ОБЩИЙ ПРИХОД</div>
      <div class="big">${fmtTg(totalFact)}</div>
      <div class="sub">План периода: ${fmtTg(totalPlan)}</div>
      <div class="ring" style="background:conic-gradient(var(--amber) 0% ${Math.min(totalPct,100).toFixed(1)}%, var(--blue-track) ${Math.min(totalPct,100).toFixed(1)}% 100%);">
        <div class="ring-inner"><div class="pct" style="color:var(--amber)">${totalPct.toFixed(1)}%</div></div>
      </div>
      <div class="ring-caption">% от плана периода</div>
    </div>`;
  DATA.projects.forEach((p, idx) => {
    const pl = plan[p].revenue, fa = agg[p].revenue;
    const pct = pl ? (fa/pl*100) : 0;
    const color = colorFor(idx);
    cardsHtml += `
    <div class="card metric">
      <div class="label">${p.toUpperCase()}</div>
      <div class="big">${fmtTg(fa)}</div>
      <div class="sub">План периода: ${fmtTg(pl)}</div>
      <div class="ring" style="background:conic-gradient(${color} 0% ${Math.min(pct,100).toFixed(1)}%, var(--blue-track) ${Math.min(pct,100).toFixed(1)}% 100%);">
        <div class="ring-inner"><div class="pct" style="color:${color}">${pct.toFixed(1)}%</div></div>
      </div>
      <div class="ring-caption">% от плана периода</div>
    </div>`;
  });
  document.getElementById('cards-row').innerHTML = cardsHtml;

  renderChart(dateList, filtered);

  // ---- 2. Отставание/опережение в тг ----
  let lagHtml = '';
  const totalDiff = totalFact - totalPlan;
  lagHtml += `<div class="lag-row ${totalDiff<0?'behind':'ahead'}"><span class="name">ИТОГО ПО КОМПАНИИ</span><span class="amount">${totalDiff<0?'−':'+'}${fmtTg(Math.abs(totalDiff))}</span></div>`;
  DATA.projects.forEach(p => {
    const diff = agg[p].revenue - plan[p].revenue;
    lagHtml += `<div class="lag-row ${diff<0?'behind':'ahead'}"><span class="name">${p}</span><span class="amount">${diff<0?'−':'+'}${fmtTg(Math.abs(diff))}</span></div>`;
  });
  document.getElementById('lag-list').innerHTML = lagHtml;

  // ---- 3. Лиды / бюджет / CPL ----
  let leadsRows = '';
  DATA.projects.forEach(p => {
    const a = agg[p], pl = plan[p];
    const cplPlan = pl.leads_target ? (pl.budget/pl.leads_target) : 0;
    const cplFact = a.leads_target ? (a.budget_spent/a.leads_target) : 0;
    leadsRows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(pl.leads_target)}</td><td class="num">${fmtInt(a.leads_target)}</td>
      <td class="num">${fmtInt(pl.leads_organic)}</td><td class="num">${fmtInt(a.leads_organic)}</td>
      <td class="num">${fmtTg(pl.budget)}</td><td class="num">${fmtTg(a.budget_spent)}</td>
      <td class="num">${fmtTg(cplPlan)}</td><td class="num ${cplFact>cplPlan?'neg':'pos'}">${fmtTg(cplFact)}</td>
    </tr>`;
  });
  document.getElementById('leads-table-body').innerHTML = leadsRows;

  // ---- 4. ПУ ----
  let puRows = '';
  DATA.projects.forEach(p => {
    const a = agg[p], pl = plan[p];
    const pct = pl.pu_records ? (a.pu_records/pl.pu_records*100) : 0;
    const doh = a.pu_records ? (a.pu_attended/a.pu_records*100) : 0;
    puRows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(pl.pu_records)}</td>
      <td class="num">${fmtInt(a.pu_records)}</td>
      <td class="num ${pct>=100?'pos':'neg'}">${pct.toFixed(1)}%</td>
      <td class="num">${fmtInt(a.pu_attended)}</td>
      <td class="num">${doh.toFixed(1)}%</td>
    </tr>`;
  });
  document.getElementById('pu-table-body').innerHTML = puRows;

  // ---- 5. Продажи ----
  let salesRows = '';
  DATA.projects.forEach(p => {
    const a = agg[p], pl = plan[p];
    const pctCnt = pl.sales_count ? (a.sales_count/pl.sales_count*100) : 0;
    const pctRev = pl.revenue ? (a.revenue/pl.revenue*100) : 0;
    salesRows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(pl.sales_count)}</td>
      <td class="num">${fmtInt(a.sales_count)}</td>
      <td class="num ${pctCnt>=100?'pos':'neg'}">${pctCnt.toFixed(1)}%</td>
      <td class="num">${fmtTg(pl.revenue)}</td>
      <td class="num">${fmtTg(a.revenue)}</td>
      <td class="num ${pctRev>=100?'pos':'neg'}">${pctRev.toFixed(1)}%</td>
    </tr>`;
  });
  document.getElementById('sales-table-body').innerHTML = salesRows;
}

function renderChart(dateList, filtered){
  const byDateProject = {};
  dateList.forEach(d => { byDateProject[toISO(d)] = {}; });
  filtered.forEach(r => {
    if (!byDateProject[r.date]) byDateProject[r.date] = {};
    byDateProject[r.date][r.project] = (byDateProject[r.date][r.project]||0) + r.revenue + r.doplaty;
  });
  const n = dateList.length;
  const w = Math.max(600, n*46), h = 220;
  const padL=60,padR=10,padT=10,padB=34;
  const plotW=w-padL-padR, plotH=h-padT-padB;
  let maxDayTotal=0;
  dateList.forEach(d => {
    const iso=toISO(d);
    const dayTotal = DATA.projects.reduce((s,p)=> s+(byDateProject[iso][p]||0),0);
    if (dayTotal>maxDayTotal) maxDayTotal=dayTotal;
  });
  if (maxDayTotal===0) maxDayTotal=1;
  const niceMax = maxDayTotal*1.15;
  const barW = Math.min(34, plotW/n*0.6);
  const step = plotW/n;
  let svg = `<svg viewBox="0 0 ${w} ${h}" style="width:100%; height:auto; display:block;">`;
  for (let i=0;i<=4;i++){
    const y = padT+plotH-(plotH*i/4);
    const val = niceMax*i/4;
    svg += `<line x1="${padL}" y1="${y}" x2="${w-padR}" y2="${y}" stroke="#e3edf7" stroke-width="1"/>`;
    svg += `<text x="${padL-8}" y="${y+4}" text-anchor="end" font-size="10" fill="#6b7a90">${Math.round(val/1000)}k</text>`;
  }
  dateList.forEach((d,i) => {
    const iso=toISO(d);
    let yCursor = padT+plotH;
    const x = padL+i*step+(step-barW)/2;
    DATA.projects.forEach((p,pi) => {
      const val = byDateProject[iso][p]||0;
      if (val<=0) return;
      const barH = (val/niceMax)*plotH;
      yCursor -= barH;
      svg += `<rect x="${x.toFixed(1)}" y="${yCursor.toFixed(1)}" width="${barW.toFixed(1)}" height="${barH.toFixed(1)}" fill="${colorFor(pi)}" rx="2"/>`;
    });
    const label = d.getDate()+'.'+String(d.getMonth()+1).padStart(2,'0');
    svg += `<text x="${(x+barW/2).toFixed(1)}" y="${h-padB+16}" text-anchor="middle" font-size="10" fill="#6b7a90">${label}</text>`;
  });
  svg += `</svg>`;
  document.getElementById('chart-wrap').innerHTML = svg;
  let legend = '';
  DATA.projects.forEach((p,idx) => { legend += `<span><span class="dot" style="background:${colorFor(idx)}"></span>${p}</span>`; });
  document.getElementById('chart-legend').innerHTML = legend;
}

function setActiveButton(btn){
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

function applyPreset(preset, btn){
  const today = new Date(); today.setHours(0,0,0,0);
  let start, end, label;
  if (preset==='today'){ start=new Date(today); end=new Date(today); label='Сегодня'; }
  else if (preset==='yesterday'){ start=new Date(today); start.setDate(start.getDate()-1); end=new Date(start); label='Вчера'; }
  else if (preset==='last7'){ end=new Date(today); start=new Date(today); start.setDate(start.getDate()-6); label='Последние 7 дней'; }
  else if (preset==='thisweek'){ const dow=(today.getDay()+6)%7; start=new Date(today); start.setDate(start.getDate()-dow); end=new Date(today); label='Эта неделя'; }
  else if (preset==='thismonth'){ start=new Date(today.getFullYear(), today.getMonth(), 1); end=new Date(today); label='Этот месяц'; }
  else if (preset==='lastmonth'){ start=new Date(today.getFullYear(), today.getMonth()-1, 1); end=new Date(today.getFullYear(), today.getMonth(), 0); label='Прошлый месяц'; }
  setActiveButton(btn);
  document.getElementById('date-from').value = toISO(start);
  document.getElementById('date-to').value = toISO(end);
  renderRange(start, end, label);
}

document.querySelectorAll('.filter-btn').forEach(btn => btn.addEventListener('click', () => applyPreset(btn.dataset.preset, btn)));
document.getElementById('apply-custom').addEventListener('click', () => {
  const from = document.getElementById('date-from').value, to = document.getElementById('date-to').value;
  if (!from || !to) return;
  setActiveButton(null);
  renderRange(new Date(from), new Date(to), 'Свой период');
});

applyPreset('thismonth', document.querySelector('[data-preset="thismonth"]'));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
