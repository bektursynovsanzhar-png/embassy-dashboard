/**
 * УСТАНОВИТЬ В ЭТУ ТАБЛИЦУ: "Запись посетителей NEW"
 * (та самая, где листы "ПУ Offline Варламова NEW", "ПУ Offline АСТАНА", "ПУ Offline САМАЛ" и т.д.)
 *
 * Таблица → Расширения → Apps Script → вставить этот код.
 *
 * Что делает:
 * Раз в час (или по кнопке) считает по каждому листу-филиалу:
 *   - сколько строк с "Цель встречи" = "Пробный Урок" стоит на СЕГОДНЯ (колонка "День")
 *   - сколько стоит на ВЧЕРА, и сколько из них отмечено галочкой (колонка A, "дошёл")
 * И коммитит небольшой файл data/pu_live.csv в репозиторий дашборда.
 * Старые даты в файле не затираются — обновляются только сегодня/вчера.
 *
 * НАСТРОЙКА:
 * 1) Впиши в BRANCH_SHEETS точные названия листов (см. ниже — для Онлайн
 *    нужно вписать самому, посмотри точное название вкладки внизу таблицы).
 * 2) Настройки проекта → Свойства скрипта, добавь (те же, что и в основном
 *    дашборде — можно скопировать значения оттуда):
 *      GITHUB_TOKEN, GITHUB_REPO (username/embassy-dashboard), GITHUB_BRANCH (main)
 * 3) Триггеры → Add Trigger → syncPuToGitHub → Time-driven → Hour timer → каждый час
 *    (по кнопке отправки формы здесь не привязать, т.к. это не форма — только по расписанию)
 */

// Сопоставление: точное название листа (вкладки внизу) → название проекта на дашборде.
// Названия должны совпадать 1-в-1 с тем, что в data/plans.csv на дашборде.
const BRANCH_SHEETS = {
  'ПУ Offline Варламова NEW': 'Варламова',
  'ПУ Offline АСТАНА': 'Астана',
  'ПУ Offline САМАЛ': 'Самал',
  'ВПИШИ ТОЧНОЕ НАЗВАНИЕ ЛИСТА ОНЛАЙН': 'Онлайн', // ← замени на реальное название вкладки
};

const COL_ATTENDED = 1; // A — чекбокс "дошёл"
const COL_PURPOSE  = 4; // D — "Цель встречи"
const COL_DATE      = 6; // F — "День"
const PURPOSE_FILTER = 'Пробный Урок'; // считаем только строки с этой целью встречи

function countForDate(sheet, targetDateStr) {
  const data = sheet.getDataRange().getValues();
  let records = 0, attended = 0;
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[COL_PURPOSE - 1] !== PURPOSE_FILTER) continue;
    const cellDate = row[COL_DATE - 1];
    if (!(cellDate instanceof Date)) continue;
    if (Utilities.formatDate(cellDate, 'GMT+6', 'yyyy-MM-dd') !== targetDateStr) continue;
    records++;
    if (row[COL_ATTENDED - 1] === true) attended++;
  }
  return { records, attended };
}

function syncPuToGitHub() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const tz = 'GMT+6';
  const today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  const yesterday = Utilities.formatDate(new Date(Date.now() - 86400000), tz, 'yyyy-MM-dd');

  // Новые/обновлённые значения на сегодня и вчера по каждому филиалу
  const fresh = {}; // key: date+"|"+project -> {records, attended}
  for (const [sheetName, project] of Object.entries(BRANCH_SHEETS)) {
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) { Logger.log('Лист не найден: ' + sheetName); continue; }
    const t = countForDate(sheet, today);
    const y = countForDate(sheet, yesterday);
    fresh[today + '|' + project] = t;
    fresh[yesterday + '|' + project] = y;
  }

  // Подтягиваем текущий файл из GitHub, чтобы не терять историю прошлых дней
  const existingRows = fetchExistingCsv('data/pu_live.csv'); // [[date,project,records,attended], ...]
  const merged = {}; // key -> [date,project,records,attended]
  existingRows.forEach(r => { merged[r[0] + '|' + r[1]] = r; });
  Object.entries(fresh).forEach(([key, val]) => {
    const [date, project] = key.split('|');
    merged[key] = [date, project, val.records, val.attended];
  });

  const header = 'date,project,pu_records,pu_attended';
  const lines = [header];
  Object.values(merged)
    .sort((a, b) => (a[0] + a[1]).localeCompare(b[0] + b[1]))
    .forEach(r => lines.push(r.join(',')));

  commitFileToGithub('data/pu_live.csv', lines.join('\n'), `Обновление ПУ (live): ${new Date().toISOString()}`);
}

function fetchExistingCsv(path) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const repo = props.getProperty('GITHUB_REPO');
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';
  const apiUrl = `https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`;
  try {
    const resp = UrlFetchApp.fetch(apiUrl, { headers: { Authorization: `token ${token}` }, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) return [];
    const content = Utilities.newBlob(Utilities.base64Decode(JSON.parse(resp.getContentText()).content)).getDataAsString();
    const lines = content.split('\n').filter(l => l.trim());
    lines.shift(); // header
    return lines.map(l => l.split(','));
  } catch (e) {
    return [];
  }
}

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
      headers: { Authorization: `token ${token}` }, muteHttpExceptions: true,
    });
    if (getResp.getResponseCode() === 200) sha = JSON.parse(getResp.getContentText()).sha;
  } catch (e) {}

  const payload = { message: commitMessage, content: contentBase64, branch: branch };
  if (sha) payload.sha = sha;

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: 'put', contentType: 'application/json',
    headers: { Authorization: `token ${token}` },
    payload: JSON.stringify(payload), muteHttpExceptions: true,
  });
  Logger.log(putResp.getResponseCode());
  Logger.log(putResp.getContentText());
}
