#!/usr/bin/env python3
"""
Собирает интерактивный HTML-дашборд Embassy.
Все данные встраиваются в страницу как JSON — фильтры, графики и расчёты
работают в браузере без пересборки. Пересборка нужна только когда
в data/*.csv появляются новые строки.
"""
import csv
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DAILY = ROOT / "data" / "daily.csv"
DATA_PLANS = ROOT / "data" / "plans.csv"
DATA_SMM = ROOT / "data" / "smm.csv"
OUTPUT = ROOT / "index.html"


def read_csv(path):
    if not path.exists():
        return []
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
    smm_rows = read_csv(DATA_SMM)
    pu_live_rows = read_csv(ROOT / "data" / "pu_live.csv")
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
            "reject_nontarget": num(row.get("reject_nontarget")),
            "reject_accidental": num(row.get("reject_accidental")),
            "reject_no_number": num(row.get("reject_no_number")),
            "pu_records": num(row.get("pu_records")),
            "pu_attended": num(row.get("pu_attended")),
            "sales_target": num(row.get("sales_target")),
            "sales_organic": num(row.get("sales_organic")),
            "revenue_target": num(row.get("revenue_target")),
            "revenue_organic": num(row.get("revenue_organic")),
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

    smm = [{
        "date": row["date"],
        "views": num(row.get("views")),
        "new_followers": num(row.get("new_followers")),
        "reach": num(row.get("reach")),
        "engagement": num(row.get("engagement")),
    } for row in smm_rows]

    pu_live = [{
        "date": row["date"],
        "project": row["project"],
        "pu_records": num(row.get("pu_records")),
        "pu_attended": num(row.get("pu_attended")),
    } for row in pu_live_rows]

    now = datetime.datetime.now()
    payload = {
        "daily": daily,
        "plans": plans,
        "smm": smm,
        "puLive": pu_live,
        "projects": projects_order,
        "generatedAt": now.strftime("%d.%m.%Y %H:%M"),
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Собрано: {OUTPUT} (записей: {len(daily)}, проектов: {len(projects_order)}, SMM: {len(smm)})")


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
  .card.alert{ border:2px solid var(--red); background:#fff8f7; }
  .row{ display:grid; gap:16px; margin-bottom:16px; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); }

  .hero-grid{ display:grid; grid-template-columns: 1.15fr 2fr; gap:16px; margin-bottom:16px; align-items:stretch; }
  #total-card-wrap{ display:flex; }
  #total-card-wrap > .card{ flex:1; }
  .hero-projects{ display:grid; grid-template-columns: repeat(2, 1fr); gap:16px; }
  .card-hero{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; }
  .card-hero .label{ font-size:13px; font-weight:800; color:var(--navy-soft); letter-spacing:0.5px; }
  .card-hero .big{ font-size:34px; font-weight:800; color:var(--navy); }
  .card-hero .sub{ font-size:12px; color:var(--gray); }
  .card-hero .ring{ width:128px; height:128px; margin-top:4px; }
  .card-hero .ring-inner{ inset:11px; }
  .card-hero .ring-inner .pct{ font-size:20px; }
  .card-hero .ring-caption{ font-size:11px; }
  .card-hero .card-lag{ font-size:13px; padding:5px 14px; }
  .card-hero .card-delta{ font-size:12px; }
  @media (max-width: 720px){
    .hero-grid{ grid-template-columns: 1fr; }
    .hero-projects{ grid-template-columns: repeat(2, 1fr); }
  }
  .row-2{ grid-template-columns: repeat(auto-fit, minmax(340px,1fr)); }
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
  .chart-legend{ display:flex; justify-content:center; gap:14px; font-size:11px; color:var(--gray); flex-wrap:wrap; margin-top:8px; }
  .chart-legend .dot{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; vertical-align:middle; }
  .updated{ text-align:center; font-size:11px; color:var(--gray); margin-top:20px; }
  .period-caption{ text-align:center; font-size:12.5px; color:var(--navy-soft); font-weight:700; margin-bottom:14px; }
  .section-title{ text-align:center; font-size:16px; font-weight:800; color:#fff; background:linear-gradient(90deg,var(--navy),var(--blue)); padding:10px 18px; border-radius:12px; margin:26px 0 14px; }
  .section-hint{ text-align:center; font-size:11px; color:var(--gray); margin:-10px 0 14px; }

  .card-lag{ font-size:11.5px; font-weight:800; margin-top:2px; padding:3px 10px; border-radius:8px; }
  .card-lag.behind{ color:var(--red); background:#fbe2df; }
  .card-lag.ahead{ color:var(--green-dark); background:var(--green-track); }
  .card-delta{ font-size:10.5px; font-weight:700; margin-top:2px; }
  .card-delta.up{ color:var(--green-dark); }
  .card-delta.down{ color:var(--red); }

  .funnel{ display:flex; flex-direction:column; gap:10px; }
  .funnel-row{ display:flex; align-items:center; gap:10px; }
  .funnel-row .flabel{ width:130px; font-size:11.5px; font-weight:700; color:var(--navy-soft); flex-shrink:0; }
  .funnel-track{ flex:1; background:var(--blue-track); border-radius:7px; height:24px; position:relative; overflow:hidden; }
  .funnel-fill{ height:100%; border-radius:7px; display:flex; align-items:center; justify-content:flex-end; padding-right:8px; color:#fff; font-size:11px; font-weight:800; }
  .funnel-conv{ width:70px; text-align:right; font-size:11px; color:var(--gray); font-weight:700; }
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

  <!-- ПРИХОД: план/факт/отставание/сравнение с прошлым периодом -->
  <div class="hero-grid">
    <div id="total-card-wrap"></div>
    <div class="hero-projects" id="cards-row"></div>
  </div>

  <!-- ПРОГНОЗ НА КОНЕЦ МЕСЯЦА (не зависит от фильтра) -->
  <div class="section-title">ПРОГНОЗ НА КОНЕЦ МЕСЯЦА</div>
  <div class="section-hint" id="forecast-hint"></div>
  <div class="row" id="forecast-row"></div>

  <div class="card" style="margin-bottom:16px;">
    <div class="card-title">ДИНАМИКА ПРИХОДА ПО ДНЯМ</div>
    <div id="chart-wrap"></div>
    <div class="chart-legend" id="chart-legend"></div>
  </div>

  <!-- ЗАПИСИ НА ПУ: СЕГОДНЯ / ВЧЕРА (живые данные из таблицы записи) -->
  <div class="section-title">ЗАПИСИ НА ПУ — СЕГОДНЯ</div>
  <div class="hero-grid">
    <div id="pu-today-total"></div>
    <div class="hero-projects" id="pu-today-row"></div>
  </div>

  <div class="section-title">ЗАПИСИ НА ПУ ЗА ПЕРИОД (ЖИВЫЕ ДАННЫЕ)</div>
  <div class="section-hint">Меняется вместе с фильтром периода наверху страницы</div>
  <div class="hero-grid">
    <div id="pu-period-total"></div>
    <div class="hero-projects" id="pu-period-row"></div>
  </div>

  <!-- ВОРОНКА -->
  <div class="section-title">ВОРОНКА: ЗАЯВКИ → ПУ → ДОШЛИ → ПРОДАЖИ</div>
  <div class="card" style="margin-bottom:16px;">
    <div class="funnel" id="funnel"></div>
  </div>

  <!-- ЛИДЫ / БЮДЖЕТ / CPL -->
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

  <div class="row row-2">
    <div class="card">
      <div class="card-title">ДИНАМИКА CPL ПО ДНЯМ</div>
      <div id="cpl-chart-wrap"></div>
    </div>
    <div class="card">
      <div class="card-title">ДИНАМИКА СРЕДНЕГО ЧЕКА ПО ДНЯМ</div>
      <div id="check-chart-wrap"></div>
    </div>
  </div>

  <!-- НЕКАЧЕСТВЕННЫЙ ТРАФИК -->
  <div class="section-title">НЕКАЧЕСТВЕННЫЙ ТРАФИК</div>
  <div class="section-hint">Лиды, ушедшие в отказ день в день</div>
  <div class="row" id="reject-total-row" style="margin-bottom:16px;"></div>
  <div class="row row-2">
    <div class="card">
      <div class="card-title">РАЗБИВКА ПО ПРИЧИНАМ</div>
      <table>
        <tr><th>Причина</th><th class="num">Кол-во</th><th class="num">% от заявок</th></tr>
        <tbody id="rejects-table-body"></tbody>
      </table>
    </div>
    <div class="card">
      <div class="card-title">ДОЛЯ ОТ ЗАЯВОК</div>
      <div id="rejects-bars"></div>
    </div>
  </div>

  <!-- ПРОДАЖИ ПО ИСТОЧНИКАМ -->
  <div class="section-title">ПРОДАЖИ ПО ИСТОЧНИКАМ: ТАРГЕТ vs ОРГАНИКА</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <tr><th>Источник</th><th class="num">Продаж, шт</th><th class="num">Сумма, тг</th><th class="num">Средний чек</th><th class="num">Доля продаж</th></tr>
      <tbody id="source-table-body"></tbody>
    </table>
  </div>

  <!-- ПУ -->
  <div class="section-title">ПРОБНЫЕ УРОКИ (ПУ): ПЛАН / ФАКТ</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <tr><th>Проект</th><th class="num">План записей</th><th class="num">Факт записей</th><th class="num">% плана</th><th class="num">Дошли</th><th class="num">Доходимость</th></tr>
      <tbody id="pu-table-body"></tbody>
    </table>
  </div>

  <!-- ПРОДАЖИ ПЛАН/ФАКТ -->
  <div class="section-title">ПРОДАЖИ: ПЛАН / ФАКТ</div>
  <div class="card" style="margin-bottom:16px;">
    <table>
      <tr><th>Проект</th><th class="num">План, шт</th><th class="num">Факт, шт</th><th class="num">% плана (шт)</th><th class="num">План, тг</th><th class="num">Факт, тг</th><th class="num">% плана (тг)</th></tr>
      <tbody id="sales-table-body"></tbody>
    </table>
  </div>

  <!-- СММ -->
  <div class="section-title" id="smm-title" style="display:none;">СММ / INSTAGRAM</div>
  <div class="row" id="smm-row"></div>

  <p class="updated">Данные пересобираются автоматически при внесении новых записей. Фильтр периода и графики работают прямо в браузере.</p>
</div>

<script id="dashboard-data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
const PROJECT_COLORS = ['#2f6fb0', '#3aa0a0', '#e0a63a', '#6fbf5e', '#8a4fe0', '#e2574c'];
function colorFor(idx){ return PROJECT_COLORS[idx % PROJECT_COLORS.length]; }
const ALERT_THRESHOLD = 50; // % от плана, ниже которого подсвечиваем карточку

document.getElementById('generated-at').textContent = 'Данные обновлены: ' + DATA.generatedAt;

function fmtTg(v){ return Math.round(v).toLocaleString('ru-RU') + ' тг'; }
function fmtInt(v){ return Math.round(v).toLocaleString('ru-RU'); }
function toISO(d){
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}
function daysInMonth(y, mIdx){ return new Date(y, mIdx+1, 0).getDate(); }
function monthKey(d){ return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0'); }
function addDays(d, n){ const r = new Date(d); r.setDate(r.getDate()+n); return r; }

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

function emptyAgg(){
  return {leads_target:0, leads_organic:0, budget_spent:0,
    reject_nontarget:0, reject_accidental:0, reject_no_number:0,
    pu_records:0, pu_attended:0,
    sales_target:0, sales_organic:0, revenue_target:0, revenue_organic:0, doplaty:0};
}

function aggregate(rows, projects){
  const agg = {}; projects.forEach(p => agg[p]=emptyAgg());
  rows.forEach(r => {
    if (!agg[r.project]) agg[r.project]=emptyAgg();
    const a = agg[r.project];
    a.leads_target+=r.leads_target; a.leads_organic+=r.leads_organic; a.budget_spent+=r.budget_spent;
    a.reject_nontarget+=r.reject_nontarget; a.reject_accidental+=r.reject_accidental;
    a.reject_no_number+=r.reject_no_number;
    a.pu_records+=r.pu_records; a.pu_attended+=r.pu_attended;
    a.sales_target+=r.sales_target; a.sales_organic+=r.sales_organic;
    a.revenue_target+=r.revenue_target; a.revenue_organic+=r.revenue_organic; a.doplaty+=r.doplaty;
  });
  return agg;
}
function aggRevenue(a){ return a.revenue_target + a.revenue_organic + a.doplaty; }
function aggSales(a){ return a.sales_target + a.sales_organic; }
function aggLeads(a){ return a.leads_target + a.leads_organic; }
function aggRejects(a){ return a.reject_nontarget+a.reject_accidental+a.reject_no_number; }

function planSum(dateList, projects, metric){
  const plan = {}; projects.forEach(p=>plan[p]=0);
  dateList.forEach(d => projects.forEach(p => { plan[p]+=proratedPlan(d,p,metric); }));
  return plan;
}

// =================== ОСНОВНОЙ РЕНДЕР (зависит от фильтра) ===================
function renderRange(start, end, label){
  document.getElementById('period-caption').textContent =
    label + ' (' + toISO(start) + ' — ' + toISO(end) + ')';
  const startISO = toISO(start), endISO = toISO(end);
  const filtered = DATA.daily.filter(r => r.date >= startISO && r.date <= endISO);
  const dateList = eachDate(start, end);
  const agg = aggregate(filtered, DATA.projects);
  const planRevenue = planSum(dateList, DATA.projects, 'revenue');

  // ---- предыдущий период той же длины (для сравнения) ----
  const periodLen = dateList.length;
  const prevEnd = addDays(start, -1);
  const prevStart = addDays(prevEnd, -(periodLen-1));
  const prevFiltered = DATA.daily.filter(r => r.date >= toISO(prevStart) && r.date <= toISO(prevEnd));
  const prevAgg = aggregate(prevFiltered, DATA.projects);

  const totalFact = DATA.projects.reduce((s,p)=>s+aggRevenue(agg[p]),0);
  const totalPlan = DATA.projects.reduce((s,p)=>s+planRevenue[p],0);
  const totalPct = totalPlan ? (totalFact/totalPlan*100) : 0;
  const totalPrev = DATA.projects.reduce((s,p)=>s+aggRevenue(prevAgg[p]),0);
  const totalDeltaPct = totalPrev ? ((totalFact-totalPrev)/totalPrev*100) : null;

  // ---- Карточки ----
  function deltaBadge(deltaPct){
    if (deltaPct === null) return '';
    const up = deltaPct >= 0;
    return `<div class="card-delta ${up?'up':'down'}">${up?'▲':'▼'} ${Math.abs(deltaPct).toFixed(1)}% к пред. периоду</div>`;
  }

  let totalCardHtml = `
    <div class="card metric card-hero ${totalPct<ALERT_THRESHOLD?'alert':''}">
      <div class="label">ОБЩИЙ ПРИХОД</div>
      <div class="big">${fmtTg(totalFact)}</div>
      <div class="sub">План периода: ${fmtTg(totalPlan)}</div>
      <div class="ring" style="background:conic-gradient(var(--amber) 0% ${Math.min(totalPct,100).toFixed(1)}%, var(--blue-track) ${Math.min(totalPct,100).toFixed(1)}% 100%);">
        <div class="ring-inner"><div class="pct" style="color:var(--amber)">${totalPct.toFixed(1)}%</div></div>
      </div>
      <div class="ring-caption">% от плана периода</div>
      <div class="card-lag ${(totalFact-totalPlan)<0?'behind':'ahead'}">${(totalFact-totalPlan)<0?'−':'+'}${fmtTg(Math.abs(totalFact-totalPlan))} ${(totalFact-totalPlan)<0?'от плана':'к плану'}</div>
      ${deltaBadge(totalDeltaPct)}
    </div>`;
  document.getElementById('total-card-wrap').innerHTML = totalCardHtml;

  let cardsHtml = '';
  DATA.projects.forEach((p, idx) => {
    const pl = planRevenue[p], fa = aggRevenue(agg[p]);
    const pct = pl ? (fa/pl*100) : 0;
    const diff = fa - pl;
    const prevFa = aggRevenue(prevAgg[p]);
    const deltaPct = prevFa ? ((fa-prevFa)/prevFa*100) : null;
    const color = colorFor(idx);
    cardsHtml += `
    <div class="card metric ${pct<ALERT_THRESHOLD?'alert':''}">
      <div class="label">${p.toUpperCase()}</div>
      <div class="big">${fmtTg(fa)}</div>
      <div class="sub">План периода: ${fmtTg(pl)}</div>
      <div class="ring" style="background:conic-gradient(${color} 0% ${Math.min(pct,100).toFixed(1)}%, var(--blue-track) ${Math.min(pct,100).toFixed(1)}% 100%);">
        <div class="ring-inner"><div class="pct" style="color:${color}">${pct.toFixed(1)}%</div></div>
      </div>
      <div class="ring-caption">% от плана периода</div>
      <div class="card-lag ${diff<0?'behind':'ahead'}">${diff<0?'−':'+'}${fmtTg(Math.abs(diff))} ${diff<0?'от плана':'к плану'}</div>
      ${deltaBadge(deltaPct)}
    </div>`;
  });
  document.getElementById('cards-row').innerHTML = cardsHtml;

  renderChart(dateList, filtered);
  renderFunnel(agg);
  renderLeadsTable(agg, planRevenue, dateList);
  renderCplChart(dateList, filtered);
  renderCheckChart(dateList, filtered);
  renderRejects(agg);
  renderSourceTable(agg);
  renderPuTable(agg, dateList);
  renderSalesTable(agg, planRevenue, dateList);
  renderSmm(startISO, endISO);
  renderPuPeriod(startISO, endISO, label);
}

// ---- Воронка ----
function renderFunnel(agg){
  let leads=0, records=0, attended=0, sales=0;
  DATA.projects.forEach(p => {
    const a = agg[p];
    leads += aggLeads(a); records += a.pu_records; attended += a.pu_attended; sales += aggSales(a);
  });
  const steps = [
    {label:'Заявки', val:leads, color:'var(--purple)'},
    {label:'Записи на ПУ', val:records, color:'var(--blue)'},
    {label:'Дошли', val:attended, color:'var(--teal)'},
    {label:'Продажи', val:sales, color:'var(--green-dark)'},
  ];
  const maxVal = steps[0].val || 1;
  let html = '';
  steps.forEach((s, i) => {
    const width = (s.val/maxVal*100).toFixed(1);
    const conv = i===0 ? '' : (steps[i-1].val ? (s.val/steps[i-1].val*100).toFixed(1)+'%' : '—');
    html += `<div class="funnel-row">
      <div class="flabel">${s.label}</div>
      <div class="funnel-track"><div class="funnel-fill" style="width:${width}%; background:${s.color};">${fmtInt(s.val)}</div></div>
      <div class="funnel-conv">${conv}</div>
    </div>`;
  });
  document.getElementById('funnel').innerHTML = html;
}

// ---- Лиды/бюджет/CPL таблица ----
function renderLeadsTable(agg, planRevenue, dateList){
  const planLT = planSum(dateList, DATA.projects, 'leads_target');
  const planLO = planSum(dateList, DATA.projects, 'leads_organic');
  const planB = planSum(dateList, DATA.projects, 'budget');
  let rows = '';
  DATA.projects.forEach(p => {
    const a = agg[p];
    const cplPlan = planLT[p] ? (planB[p]/planLT[p]) : 0;
    const cplFact = a.leads_target ? (a.budget_spent/a.leads_target) : 0;
    rows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(planLT[p])}</td><td class="num">${fmtInt(a.leads_target)}</td>
      <td class="num">${fmtInt(planLO[p])}</td><td class="num">${fmtInt(a.leads_organic)}</td>
      <td class="num">${fmtTg(planB[p])}</td><td class="num">${fmtTg(a.budget_spent)}</td>
      <td class="num">${fmtTg(cplPlan)}</td><td class="num ${cplFact>cplPlan?'neg':'pos'}">${fmtTg(cplFact)}</td>
    </tr>`;
  });
  document.getElementById('leads-table-body').innerHTML = rows;
}

// ---- Тренд CPL ----
function lineChart(dateList, values, color, unit){
  const n = dateList.length;
  const w = Math.max(500, n*50), h = 160;
  const padL=54,padR=10,padT=10,padB=30;
  const plotW=w-padL-padR, plotH=h-padT-padB;
  const maxV = Math.max(...values, 1) * 1.2;
  const pts = values.map((v,i) => {
    const x = padL + (n<=1?plotW/2:i*(plotW/(n-1)));
    const y = padT + plotH - (v/maxV)*plotH;
    return [x,y];
  });
  let svg = `<svg viewBox="0 0 ${w} ${h}" style="width:100%; height:auto; display:block;">`;
  for (let i=0;i<=3;i++){
    const y = padT+plotH-(plotH*i/3);
    const val = maxV*i/3;
    svg += `<line x1="${padL}" y1="${y}" x2="${w-padR}" y2="${y}" stroke="#e3edf7" stroke-width="1"/>`;
    svg += `<text x="${padL-8}" y="${y+4}" text-anchor="end" font-size="9" fill="#6b7a90">${Math.round(val)}${unit||''}</text>`;
  }
  const poly = pts.map(p=>p.join(',')).join(' ');
  svg += `<polyline points="${poly}" fill="none" stroke="${color}" stroke-width="2.2"/>`;
  pts.forEach(([x,y],i) => { svg += `<circle cx="${x}" cy="${y}" r="3" fill="${color}"/>`; });
  dateList.forEach((d,i) => {
    if (n>14 && i%2!==0) return;
    const label = d.getDate()+'.'+String(d.getMonth()+1).padStart(2,'0');
    svg += `<text x="${pts[i][0]}" y="${h-padB+16}" text-anchor="middle" font-size="9" fill="#6b7a90">${label}</text>`;
  });
  svg += `</svg>`;
  return svg;
}

function renderCplChart(dateList, filtered){
  const byDate = {};
  dateList.forEach(d => byDate[toISO(d)] = {budget:0, leads:0});
  filtered.forEach(r => {
    const b = byDate[r.date]; if (!b) return;
    b.budget += r.budget_spent; b.leads += r.leads_target;
  });
  const values = dateList.map(d => {
    const b = byDate[toISO(d)];
    return b.leads ? b.budget/b.leads : 0;
  });
  document.getElementById('cpl-chart-wrap').innerHTML = lineChart(dateList, values, 'var(--red)', '');
}

function renderCheckChart(dateList, filtered){
  const byDate = {};
  dateList.forEach(d => byDate[toISO(d)] = {revenue:0, sales:0});
  filtered.forEach(r => {
    const b = byDate[r.date]; if (!b) return;
    b.revenue += r.revenue_target + r.revenue_organic; b.sales += r.sales_target + r.sales_organic;
  });
  const values = dateList.map(d => {
    const b = byDate[toISO(d)];
    return b.sales ? b.revenue/b.sales : 0;
  });
  document.getElementById('check-chart-wrap').innerHTML = lineChart(dateList, values, 'var(--teal)', '');
}

// ---- Некачественный трафик ----
function renderRejects(agg){
  let nontarget=0, accidental=0, noNumber=0, leads=0;
  DATA.projects.forEach(p => {
    const a = agg[p];
    nontarget+=a.reject_nontarget; accidental+=a.reject_accidental; noNumber+=a.reject_no_number;
    leads += aggLeads(a);
  });
  const totalRejects = nontarget+accidental+noNumber;
  const totalPct = leads ? (totalRejects/leads*100) : 0;

  document.getElementById('reject-total-row').innerHTML = `
    <div class="card metric ${totalPct>40?'alert':''}">
      <div class="label">НЕКАЧЕСТВЕННЫЙ ТРАФИК ЗА ПЕРИОД</div>
      <div class="big">${fmtInt(totalRejects)}</div>
      <div class="sub">${totalPct.toFixed(1)}% от ${fmtInt(leads)} заявок</div>
    </div>`;

  const items = [
    ['Непрофильный лид', nontarget],
    ['Не оставлял заявку', accidental],
    ['Нет номера телефона', noNumber],
  ];
  let rows = '';
  let barsHtml = '<div class="bars" style="display:flex;flex-direction:column;gap:12px;">';
  items.forEach(([name,val]) => {
    const pct = leads ? (val/leads*100) : 0;
    rows += `<tr><td>${name}</td><td class="num">${fmtInt(val)}</td><td class="num">${pct.toFixed(1)}%</td></tr>`;
    barsHtml += `<div><div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:4px;color:var(--navy-soft);font-weight:700;"><span>${name}</span><span>${pct.toFixed(1)}%</span></div>
      <div style="height:12px;background:var(--blue-track);border-radius:7px;overflow:hidden;"><div style="height:100%;width:${Math.min(pct,100).toFixed(1)}%;background:var(--red);border-radius:7px;"></div></div></div>`;
  });
  rows += `<tr style="font-weight:800;background:#f7fafd;"><td>Итого</td><td class="num">${fmtInt(totalRejects)}</td><td class="num">${totalPct.toFixed(1)}%</td></tr>`;
  barsHtml += '</div>';
  document.getElementById('rejects-table-body').innerHTML = rows;
  document.getElementById('rejects-bars').innerHTML = barsHtml;
}

// ---- Продажи по источникам ----
function renderSourceTable(agg){
  let targetCnt=0, targetRev=0, organicCnt=0, organicRev=0;
  DATA.projects.forEach(p => {
    const a = agg[p];
    targetCnt+=a.sales_target; targetRev+=a.revenue_target;
    organicCnt+=a.sales_organic; organicRev+=a.revenue_organic;
  });
  const totalCnt = targetCnt+organicCnt;
  const rows = [
    ['Таргет', targetCnt, targetRev],
    ['Органика', organicCnt, organicRev],
  ];
  let html = '';
  rows.forEach(([name,cnt,rev]) => {
    const avgCheck = cnt ? rev/cnt : 0;
    const share = totalCnt ? (cnt/totalCnt*100) : 0;
    html += `<tr><td>${name}</td><td class="num">${fmtInt(cnt)}</td><td class="num">${fmtTg(rev)}</td><td class="num">${fmtTg(avgCheck)}</td><td class="num">${share.toFixed(1)}%</td></tr>`;
  });
  html += `<tr style="font-weight:800;background:#f7fafd;"><td>Итого</td><td class="num">${fmtInt(totalCnt)}</td><td class="num">${fmtTg(targetRev+organicRev)}</td><td class="num">${fmtTg(totalCnt?(targetRev+organicRev)/totalCnt:0)}</td><td class="num">100%</td></tr>`;
  document.getElementById('source-table-body').innerHTML = html;
}

// ---- ПУ таблица ----
function renderPuTable(agg, dateList){
  const planPU = planSum(dateList, DATA.projects, 'pu_records');
  let rows = '';
  DATA.projects.forEach(p => {
    const a = agg[p];
    const pct = planPU[p] ? (a.pu_records/planPU[p]*100) : 0;
    const doh = a.pu_records ? (a.pu_attended/a.pu_records*100) : 0;
    rows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(planPU[p])}</td>
      <td class="num">${fmtInt(a.pu_records)}</td>
      <td class="num ${pct>=100?'pos':'neg'}">${pct.toFixed(1)}%</td>
      <td class="num">${fmtInt(a.pu_attended)}</td>
      <td class="num">${doh.toFixed(1)}%</td>
    </tr>`;
  });
  document.getElementById('pu-table-body').innerHTML = rows;
}

// ---- Продажи план/факт ----
function renderSalesTable(agg, planRevenue, dateList){
  const planSC = planSum(dateList, DATA.projects, 'sales_count');
  let rows = '';
  DATA.projects.forEach(p => {
    const a = agg[p];
    const factCnt = aggSales(a), factRev = aggRevenue(a);
    const pctCnt = planSC[p] ? (factCnt/planSC[p]*100) : 0;
    const pctRev = planRevenue[p] ? (factRev/planRevenue[p]*100) : 0;
    rows += `<tr>
      <td>${p}</td>
      <td class="num">${fmtInt(planSC[p])}</td>
      <td class="num">${fmtInt(factCnt)}</td>
      <td class="num ${pctCnt>=100?'pos':'neg'}">${pctCnt.toFixed(1)}%</td>
      <td class="num">${fmtTg(planRevenue[p])}</td>
      <td class="num">${fmtTg(factRev)}</td>
      <td class="num ${pctRev>=100?'pos':'neg'}">${pctRev.toFixed(1)}%</td>
    </tr>`;
  });
  document.getElementById('sales-table-body').innerHTML = rows;
}

// ---- СММ ----
function renderSmm(startISO, endISO){
  if (!DATA.smm || DATA.smm.length===0){
    document.getElementById('smm-title').style.display='none';
    document.getElementById('smm-row').innerHTML='';
    return;
  }
  document.getElementById('smm-title').style.display='block';
  const filtered = DATA.smm.filter(r => r.date>=startISO && r.date<=endISO);
  const sum = (key) => filtered.reduce((s,r)=>s+r[key],0);
  const cards = [
    ['ПРОСМОТРЫ', sum('views'), ''],
    ['НОВЫЕ ПОДПИСЧИКИ', sum('new_followers'), ''],
    ['ОХВАЧЕННЫЕ АККАУНТЫ', sum('reach'), ''],
    ['ВЗАИМОДЕЙСТВИЯ', sum('engagement'), ''],
  ];
  let html = '';
  cards.forEach(([label,val]) => {
    html += `<div class="card metric">
      <div class="label">${label}</div>
      <div class="big">${fmtInt(val)}</div>
      <div class="sub">за выбранный период</div>
    </div>`;
  });
  document.getElementById('smm-row').innerHTML = html;
}

// =================== ПРОГНОЗ (не зависит от фильтра, всегда текущий месяц) ===================
function renderForecast(){
  const today = new Date(); today.setHours(0,0,0,0);
  const mk = monthKey(today);
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
  const daysPassed = Math.floor((today-monthStart)/86400000)+1;
  const totalDaysInMonth = daysInMonth(today.getFullYear(), today.getMonth());

  const monthRows = DATA.daily.filter(r => r.date.slice(0,7)===mk);
  const agg = aggregate(monthRows, DATA.projects);

  document.getElementById('forecast-hint').textContent =
    `На основе темпа первых ${daysPassed} дн. из ${totalDaysInMonth} в месяце ${mk}`;

  const planMonth = {}; DATA.projects.forEach(p => planMonth[p] = (DATA.plans[mk] && DATA.plans[mk][p]) ? DATA.plans[mk][p].revenue : 0);

  let html = '';
  let totalForecast=0, totalPlan=0, totalFactSoFar=0;
  DATA.projects.forEach((p, idx) => {
    const factSoFar = aggRevenue(agg[p]);
    const runRate = daysPassed ? factSoFar/daysPassed : 0;
    const forecast = runRate*totalDaysInMonth;
    const plan = planMonth[p];
    const pct = plan ? (forecast/plan*100) : 0;
    totalForecast += forecast; totalPlan += plan; totalFactSoFar += factSoFar;
    const color = colorFor(idx);
    html += `<div class="card metric ${pct<ALERT_THRESHOLD?'alert':''}">
      <div class="label">${p.toUpperCase()}</div>
      <div class="big">${fmtTg(forecast)}</div>
      <div class="sub">Факт сейчас: ${fmtTg(factSoFar)} · План: ${fmtTg(plan)}</div>
      <div class="card-lag ${pct<100?'behind':'ahead'}">${pct.toFixed(0)}% от плана к концу месяца</div>
    </div>`;
  });
  const totalPct = totalPlan ? (totalForecast/totalPlan*100) : 0;
  html = `<div class="card metric ${totalPct<ALERT_THRESHOLD?'alert':''}">
      <div class="label">ВСЕГО ПО КОМПАНИИ</div>
      <div class="big">${fmtTg(totalForecast)}</div>
      <div class="sub">Факт сейчас: ${fmtTg(totalFactSoFar)} · План: ${fmtTg(totalPlan)}</div>
      <div class="card-lag ${totalPct<100?'behind':'ahead'}">${totalPct.toFixed(0)}% от плана к концу месяца</div>
    </div>` + html;
  document.getElementById('forecast-row').innerHTML = html;
}

// =================== ГРАФИК ПРИХОДА ПО ДНЯМ ===================
function fmtAxisTg(v){
  if (v >= 1000000){
    const m = v/1000000;
    const mStr = Number.isInteger(m) ? String(m) : m.toFixed(1).replace('.', ',');
    return mStr + ' млн';
  }
  if (v === 0) return '0';
  return Math.round(v/1000) + ' тыс.';
}

function renderChart(dateList, filtered){
  const byDateProject = {};
  dateList.forEach(d => { byDateProject[toISO(d)] = {}; });
  filtered.forEach(r => {
    if (!byDateProject[r.date]) byDateProject[r.date] = {};
    byDateProject[r.date][r.project] = (byDateProject[r.date][r.project]||0) + r.revenue_target + r.revenue_organic + r.doplaty;
  });
  const n = dateList.length;
  const w = Math.max(600, n*46), h = 220;
  const padL=64,padR=10,padT=10,padB=34;
  const plotW=w-padL-padR, plotH=h-padT-padB;
  let maxDayTotal=0;
  dateList.forEach(d => {
    const iso=toISO(d);
    const dayTotal = DATA.projects.reduce((s,p)=> s+(byDateProject[iso][p]||0),0);
    if (dayTotal>maxDayTotal) maxDayTotal=dayTotal;
  });
  // Фиксированная сетка шагом 500 тыс., минимум до 5 млн, дальше расширяется тем же шагом
  const GRID_STEP = 500000;
  const MIN_TOP = 5000000;
  const topValue = Math.max(MIN_TOP, Math.ceil((maxDayTotal*1.05) / GRID_STEP) * GRID_STEP);
  const gridCount = topValue / GRID_STEP;

  const barW = Math.min(34, plotW/n*0.6);
  const step = plotW/n;
  let svg = `<svg viewBox="0 0 ${w} ${h}" style="width:100%; height:auto; display:block;">`;
  for (let i=0;i<=gridCount;i++){
    const val = i*GRID_STEP;
    const y = padT+plotH-(plotH*val/topValue);
    svg += `<line x1="${padL}" y1="${y}" x2="${w-padR}" y2="${y}" stroke="#e3edf7" stroke-width="1"/>`;
    svg += `<text x="${padL-8}" y="${y+4}" text-anchor="end" font-size="10" fill="#6b7a90">${fmtAxisTg(val)}</text>`;
  }
  dateList.forEach((d,i) => {
    const iso=toISO(d);
    let yCursor = padT+plotH;
    const x = padL+i*step+(step-barW)/2;
    DATA.projects.forEach((p,pi) => {
      const val = byDateProject[iso][p]||0;
      if (val<=0) return;
      const barH = (val/topValue)*plotH;
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

// =================== ФИЛЬТРЫ ===================
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

// =================== ЗАПИСИ НА ПУ: СЕГОДНЯ / ВЧЕРА (живые данные) ===================
function heroBlockHtml(title, sub, byProject, alertBelow){
  let totalVal = 0, totalOf = 0;
  DATA.projects.forEach(p => { totalVal += (byProject[p] ? byProject[p].main : 0); totalOf += (byProject[p] ? byProject[p].of : 0); });
  const totalPct = totalOf ? (totalVal/totalOf*100) : null;
  const heroAlert = (alertBelow!=null && totalOf>0 && totalVal/totalOf*100 < alertBelow) ? 'alert' : '';
  let html = `<div class="card metric card-hero ${heroAlert}">
    <div class="label">${title}</div>
    <div class="big">${fmtInt(totalVal)}</div>
    <div class="sub">${sub(totalVal, totalOf, totalPct)}</div>
  </div>`;
  let cardsHtml = '';
  DATA.projects.forEach((p, idx) => {
    const d = byProject[p] || {main:0, of:0};
    const pct = d.of ? (d.main/d.of*100) : null;
    const alert = (alertBelow!=null && d.of>0 && pct < alertBelow) ? 'alert' : '';
    cardsHtml += `<div class="card metric ${alert}">
      <div class="label">${p.toUpperCase()}</div>
      <div class="big">${fmtInt(d.main)}</div>
      <div class="sub">${sub(d.main, d.of, pct)}</div>
    </div>`;
  });
  return {total: html, cards: cardsHtml};
}

function renderPuToday(){
  const puLive = DATA.puLive || [];
  const today = new Date(); today.setHours(0,0,0,0);
  const todayISO = toISO(today);
  const todayDisp = today.getDate()+'.'+String(today.getMonth()+1).padStart(2,'0');

  const byProjectToday = {};
  DATA.projects.forEach(p => { byProjectToday[p] = {main:0, of:0}; });
  puLive.forEach(r => {
    if (r.date === todayISO){
      if (!byProjectToday[r.project]) byProjectToday[r.project] = {main:0,of:0};
      byProjectToday[r.project].main = r.pu_records; byProjectToday[r.project].of = 0;
    }
  });

  const todayBlocks = heroBlockHtml('ЗАПИСЕЙ НА СЕГОДНЯ', ()=>`Записей на ${todayDisp}`, byProjectToday, null);
  document.getElementById('pu-today-total').innerHTML = todayBlocks.total;
  document.getElementById('pu-today-row').innerHTML = todayBlocks.cards;
}

// Вызывается из renderRange() при каждой смене фильтра периода —
// суммирует записи/дошли из pu_live.csv за выбранный диапазон дат.
function renderPuPeriod(startISO, endISO, label){
  const puLive = DATA.puLive || [];
  const filtered = puLive.filter(r => r.date >= startISO && r.date <= endISO);

  const byProject = {};
  DATA.projects.forEach(p => { byProject[p] = {main:0, of:0}; });
  filtered.forEach(r => {
    if (!byProject[r.project]) byProject[r.project] = {main:0, of:0};
    byProject[r.project].main += r.pu_attended;
    byProject[r.project].of += r.pu_records;
  });

  const blocks = heroBlockHtml(
    'ДОШЛИ ЗА ПЕРИОД',
    (v,of,pct)=> of ? `${fmtInt(v)} из ${fmtInt(of)} записей (${pct.toFixed(0)}%)` : 'Записей не было',
    byProject, 50
  );
  document.getElementById('pu-period-total').innerHTML = blocks.total;
  document.getElementById('pu-period-row').innerHTML = blocks.cards;
}

renderPuToday();
renderForecast();
applyPreset('thismonth', document.querySelector('[data-preset="thismonth"]'));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
