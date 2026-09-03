/**
 * ВСТАВИТЬ ЭТОТ КОД В: Google Таблица → Расширения → Apps Script
 *
 * Функция syncToGitHub()  — коммитит лист "daily" в data/daily.csv
 * Функция syncPlansToGitHub() — коммитит лист "plans" в data/plans.csv
 * Функция syncSmmToGitHub()   — коммитит лист "smm" в data/smm.csv (опционально)
 *
 * НАСТРОЙКА (один раз):
 * 1) Google Форма с полями, порядок важен:
 *    Дата, Проект, Канал,
 *    Лиды с таргета, Лиды органика, Бюджет потрачено (тг),
 *    Отказ: вне рабочее время, Отказ: без номера, Отказ: недозвон, Отказ: непрофильный,
 *    Записей на ПУ, Дошли на ПУ,
 *    Продаж с таргета (шт), Продаж с органики (шт),
 *    Приход с таргета (тг), Приход с органики (тг), Доплаты (тг)
 * 2) Ответы формы → создать таблицу, переименовать лист в "daily"
 * 3) GitHub: Settings → Developer settings → Personal access tokens →
 *    Generate new token (classic), права "repo"
 * 4) Apps Script → Настройки проекта → Свойства скрипта:
 *      GITHUB_TOKEN, GITHUB_REPO (username/repo), GITHUB_BRANCH (main)
 * 5) Apps Script → Триггеры → Add Trigger →
 *      syncToGitHub, From spreadsheet, On form submit
 */

function commitFileToGithub(path, csvContent, commitMessage) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const repo = props.getProperty('GITHUB_REPO');
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';
  const apiUrl = `https://api.github.com/repos/${repo}/contents/${path}`;
  const contentBase64 = Utilities.base64Encode(csvContent, Utilities.Charset.UTF_8);

  let sha = null;
  try {
    const getResp = UrlFetchApp.fetch(`${apiUrl}?ref=${branch}`, {
      headers: { Authorization: `token ${token}` },
      muteHttpExceptions: true,
    });
    if (getResp.getResponseCode() === 200) sha = JSON.parse(getResp.getContentText()).sha;
  } catch (e) {}

  const payload = { message: commitMessage, content: contentBase64, branch: branch };
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

function syncToGitHub() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('daily');
  const rows = sheet.getDataRange().getValues();

  // Колонки листа после Timestamp формы (индексы):
  // [1]=Дата [2]=Проект [3]=Канал
  // [4]=Лиды таргет [5]=Лиды органика [6]=Бюджет
  // [7]=Откaз вне часов [8]=Отказ без номера [9]=Отказ недозвон [10]=Отказ непрофильный
  // [11]=Записей ПУ [12]=Дошли ПУ
  // [13]=Продаж таргет [14]=Продаж органика
  // [15]=Приход таргет [16]=Приход органика [17]=Доплаты
  const header = 'date,project,channel,leads_target,leads_organic,budget_spent,' +
    'reject_offhours,reject_no_number,reject_no_answer,reject_nontarget,' +
    'pu_records,pu_attended,sales_target,sales_organic,revenue_target,revenue_organic,doplaty';
  const csvLines = [header];

  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[1]) continue;
    const date = Utilities.formatDate(new Date(r[1]), 'GMT+6', 'yyyy-MM-dd');
    const line = [date, r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10],
      r[11], r[12], r[13], r[14], r[15], r[16], r[17]].join(',');
    csvLines.push(line);
  }
  commitFileToGithub('data/daily.csv', csvLines.join('\n'), `Обновление данных: ${new Date().toISOString()}`);
}

/**
 * Лист "plans" (ведёшь отдельно, обновляешь вручную при смене плана):
 * колонки: month, project, channel, plan_revenue, plan_leads_target,
 * plan_leads_organic, plan_budget, plan_pu_records, plan_sales_count
 */
function syncPlansToGitHub() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('plans');
  const rows = sheet.getDataRange().getValues();
  const header = 'month,project,channel,plan_revenue,plan_leads_target,plan_leads_organic,plan_budget,plan_pu_records,plan_sales_count';
  const csvLines = [header];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    csvLines.push(r.slice(0, 9).join(','));
  }
  commitFileToGithub('data/plans.csv', csvLines.join('\n'), `Обновление плана: ${new Date().toISOString()}`);
}

/**
 * Лист "smm" (опционально, если хочешь видеть блок СММ на дашборде):
 * колонки: date, views, new_followers, reach, engagement
 */
function syncSmmToGitHub() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('smm');
  const rows = sheet.getDataRange().getValues();
  const header = 'date,views,new_followers,reach,engagement';
  const csvLines = [header];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    const date = Utilities.formatDate(new Date(r[0]), 'GMT+6', 'yyyy-MM-dd');
    csvLines.push([date, r[1], r[2], r[3], r[4]].join(','));
  }
  commitFileToGithub('data/smm.csv', csvLines.join('\n'), `Обновление SMM: ${new Date().toISOString()}`);
}
