/**
 * ВСТАВИТЬ ЭТОТ КОД В: Google Таблица → Расширения → Apps Script
 *
 * Что делает:
 * 1) Забирает все строки из листа "daily"
 * 2) Собирает CSV в формате data/daily.csv
 * 3) Коммитит файл в GitHub-репозиторий через GitHub API
 *
 * НАСТРОЙКА (один раз):
 * 1) Google Форма с полями (порядок важен!):
 *    Дата, Проект, Канал, Лиды с таргета, Лиды органика, Бюджет потрачено (тг),
 *    Записей на ПУ, Дошли на ПУ, Продаж (шт), Приход (тг), Доплаты (тг)
 * 2) Ответы формы → создать таблицу, переименовать лист в "daily"
 * 3) GitHub: Settings → Developer settings → Personal access tokens →
 *    Generate new token (classic), права "repo"
 * 4) Apps Script → Настройки проекта → Свойства скрипта, добавить:
 *      GITHUB_TOKEN, GITHUB_REPO (username/repo), GITHUB_BRANCH (main)
 * 5) Apps Script → Триггеры → Add Trigger →
 *      syncToGitHub, From spreadsheet, On form submit
 */

function syncToGitHub() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const repo = props.getProperty('GITHUB_REPO');
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';
  const path = 'data/daily.csv';

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('daily');
  const rows = sheet.getDataRange().getValues();

  // Ожидаемые колонки листа (после Timestamp формы):
  // [0]=Timestamp, [1]=Дата, [2]=Проект, [3]=Канал,
  // [4]=Лиды с таргета, [5]=Лиды органика, [6]=Бюджет потрачено,
  // [7]=Записей на ПУ, [8]=Дошли на ПУ, [9]=Продаж, [10]=Приход, [11]=Доплаты
  const header = 'date,project,channel,leads_target,leads_organic,budget_spent,pu_records,pu_attended,sales_count,revenue,doplaty';
  const csvLines = [header];

  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[1]) continue;
    const date = Utilities.formatDate(new Date(r[1]), 'GMT+6', 'yyyy-MM-dd');
    const line = [
      date, r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]
    ].join(',');
    csvLines.push(line);
  }

  const csvContent = csvLines.join('\n');
  const contentBase64 = Utilities.base64Encode(csvContent, Utilities.Charset.UTF_8);
  const apiUrl = `https://api.github.com/repos/${repo}/contents/${path}`;

  let sha = null;
  try {
    const getResp = UrlFetchApp.fetch(`${apiUrl}?ref=${branch}`, {
      headers: { Authorization: `token ${token}` },
      muteHttpExceptions: true,
    });
    if (getResp.getResponseCode() === 200) {
      sha = JSON.parse(getResp.getContentText()).sha;
    }
  } catch (e) {}

  const payload = {
    message: `Обновление данных: ${new Date().toISOString()}`,
    content: contentBase64,
    branch: branch,
  };
  if (sha) payload.sha = sha;

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: 'put',
    contentType: 'application/json',
    headers: { Authorization: `token ${token}` },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  });

  Logger.log(putResp.getResponseCode());
  Logger.log(putResp.getContentText());
}

/**
 * Второй, отдельный синк — для планов (data/plans.csv).
 * Полезно, если план меняешь в отдельной Google Таблице/листе "plans"
 * с колонками: month, project, channel, plan_revenue, plan_leads_target,
 * plan_leads_organic, plan_budget, plan_pu_records, plan_sales_count.
 * Запускать вручную при смене плана (не по триггеру формы).
 */
function syncPlansToGitHub() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const repo = props.getProperty('GITHUB_REPO');
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';
  const path = 'data/plans.csv';

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('plans');
  const rows = sheet.getDataRange().getValues();

  const header = 'month,project,channel,plan_revenue,plan_leads_target,plan_leads_organic,plan_budget,plan_pu_records,plan_sales_count';
  const csvLines = [header];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    csvLines.push(r.slice(0, 9).join(','));
  }
  const csvContent = csvLines.join('\n');
  const contentBase64 = Utilities.base64Encode(csvContent, Utilities.Charset.UTF_8);
  const apiUrl = `https://api.github.com/repos/${repo}/contents/${path}`;

  let sha = null;
  try {
    const getResp = UrlFetchApp.fetch(`${apiUrl}?ref=${branch}`, {
      headers: { Authorization: `token ${token}` },
      muteHttpExceptions: true,
    });
    if (getResp.getResponseCode() === 200) sha = JSON.parse(getResp.getContentText()).sha;
  } catch (e) {}

  const payload = { message: `Обновление плана: ${new Date().toISOString()}`, content: contentBase64, branch: branch };
  if (sha) payload.sha = sha;

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: 'put',
    contentType: 'application/json',
    headers: { Authorization: `token ${token}` },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  });
  Logger.log(putResp.getResponseCode());
  Logger.log(putResp.getContentText());
}
