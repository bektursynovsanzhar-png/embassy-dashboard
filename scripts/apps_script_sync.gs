/**
 * ВСТАВИТЬ ЭТОТ КОД В: Google Таблица → Расширения → Apps Script
 *
 * Что делает:
 * 1) Забирает все строки из листа "daily" (структура колонок как в data/daily.csv)
 * 2) Собирает CSV
 * 3) Отправляет (коммитит) файл data/daily.csv в GitHub-репозиторий через GitHub API
 *
 * Настройка (один раз):
 * 1) Создай Google Форму с полями:
 *    Дата, Проект, Канал, Заявки, Записей на ПУ, Дошли, Продаж (шт), Приход (тг), Доплаты (тг)
 * 2) Свяжи форму с Google Таблицей (Ответы → создать таблицу), назови лист "daily"
 * 3) В GitHub: Settings → Developer settings → Personal access tokens →
 *    создай токен с правом "repo" (Contents: Read and write)
 * 4) В Apps Script: File → Project properties → Script properties, добавь:
 *      GITHUB_TOKEN = <токен из шага 3>
 *      GITHUB_REPO  = username/embassy-dashboard
 *      GITHUB_BRANCH = main
 * 5) В Apps Script: Триггеры (часы, слева) → Add Trigger →
 *      Function: syncToGitHub, Event source: From spreadsheet, On form submit
 *    (тогда синк идёт сразу после каждой отправки формы)
 */

function syncToGitHub() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const repo = props.getProperty('GITHUB_REPO');       // например "bektursynovsanzhar-png/embassy-dashboard"
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';
  const path = 'data/daily.csv';

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('daily');
  const rows = sheet.getDataRange().getValues();

  // Ожидаемый порядок колонок в листе (поменяй под свою форму при необходимости):
  // [0]=Timestamp (игнор), [1]=Дата, [2]=Проект, [3]=Канал, [4]=Заявки,
  // [5]=Записей на ПУ, [6]=Дошли, [7]=Продаж, [8]=Приход, [9]=Доплаты
  const header = 'date,project,channel,leads,pu_records,pu_attended,sales_count,revenue,doplaty';
  const csvLines = [header];

  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r[1]) continue; // пустая строка
    const date = Utilities.formatDate(new Date(r[1]), 'GMT+6', 'yyyy-MM-dd');
    const line = [date, r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]].join(',');
    csvLines.push(line);
  }

  const csvContent = csvLines.join('\n');
  const contentBase64 = Utilities.base64Encode(csvContent, Utilities.Charset.UTF_8);

  const apiUrl = `https://api.github.com/repos/${repo}/contents/${path}`;

  // Сначала узнаём sha текущего файла (нужно для обновления существующего файла)
  let sha = null;
  try {
    const getResp = UrlFetchApp.fetch(`${apiUrl}?ref=${branch}`, {
      headers: { Authorization: `token ${token}` },
      muteHttpExceptions: true,
    });
    if (getResp.getResponseCode() === 200) {
      sha = JSON.parse(getResp.getContentText()).sha;
    }
  } catch (e) {
    // файла ещё нет — это нормально для первого запуска
  }

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
