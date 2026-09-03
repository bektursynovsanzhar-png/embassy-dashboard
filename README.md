# Embassy — автоматический дашборд

Живой дашборд с ключевыми показателями (заявки, ПУ, продажи, приход по проектам),
который сам пересобирается при внесении новых данных. Ты как директор просто
держишь одну ссылку в закладках — она всегда показывает актуальные цифры.

## Как это устроено

```
Сотрудники → Google Форма → Google Таблица
                                  │  (Apps Script, авто при каждой отправке формы)
                                  ▼
                        data/daily.csv в этом репозитории
                                  │  (GitHub Actions, авто при обновлении файла)
                                  ▼
                            index.html (дашборд)
                                  │  (GitHub Pages)
                                  ▼
                     https://<username>.github.io/<repo>/
```

## Настройка с нуля (один раз)

### 1. Создать репозиторий
Загрузи все файлы этой папки в новый **публичный** репозиторий на GitHub
(например `embassy-dashboard`).

### 2. Включить GitHub Pages
Settings → Pages → Source: **Deploy from a branch** → Branch: **main** / **(root)** → Save.

### 3. Дать права GitHub Actions на запись
Settings → Actions → General → Workflow permissions →
**Read and write permissions** → Save.
(Иначе автосборка не сможет закоммитить обновлённый `index.html`.)

### 4. Проверить автосборку
Actions → workflow "Build dashboard" → Run workflow (запустить вручную первый раз).
Через минуту в репозитории появится/обновится `index.html`,
и по ссылке `https://<username>.github.io/<repo>/` будет виден дашборд.

### 5. Настроить сбор данных от сотрудников
1. Создай Google Форму с полями (в таком порядке):
   **Дата, Проект, Канал, Заявки, Записей на ПУ, Дошли, Продаж (шт), Приход (тг), Доплаты (тг)**
   - Проект: короткий текст или список (Варламова / Самал / Астана / Онлайн)
   - Канал: оффлайн / онлайн
2. Ответы → **Создать таблицу** (Google Sheets). Переименуй лист в `daily`.
3. В таблице: Расширения → Apps Script → вставь код из `scripts/apps_script_sync.gs`.
4. Там же: File → Project properties → Script properties → добавь:
   - `GITHUB_TOKEN` — токен из GitHub (Settings → Developer settings →
     Personal access tokens → Generate new token → права **repo**)
   - `GITHUB_REPO` — например `bektursynovsanzhar-png/embassy-dashboard`
   - `GITHUB_BRANCH` — `main`
5. Триггеры (значок часов слева) → Add Trigger →
   Function `syncToGitHub`, Event source: **From spreadsheet**, Event type: **On form submit**.

Готово: теперь при каждой отправке формы данные улетают в GitHub,
Actions пересобирает дашборд, и ссылка на Pages всегда показывает свежие цифры.

### 6. Обновить план на новый месяц
Открой `data/plans.csv`, добавь строки на следующий месяц
(месяц, проект, канал, план на месяц) и запушь в репозиторий — дашборд
подхватит план автоматически.

## Структура файлов

- `data/daily.csv` — ежедневные факты (обновляется автоматически из формы)
- `data/plans.csv` — планы по проектам на месяц (редактируется вручную при смене плана)
- `scripts/build_dashboard.py` — генерирует `index.html` из данных
- `scripts/apps_script_sync.gs` — код-мост Google Sheets → GitHub
- `.github/workflows/build.yml` — автозапуск сборки в GitHub Actions

## Дальнейшие улучшения (по желанию)

- Подключить прямой импорт из CRM (amoCRM/Bitrix24) через API вместо части ручного
  ввода — тогда форма нужна будет только для того, чего в CRM нет.
- Добавить блоки СММ, лидов по этапам отказа, воронку ПУ — по тому же принципу,
  что и в `build_dashboard.py` (просто добавляются новые карточки/таблицы,
  генератор уже настроен под этот стиль).
- Настроить уведомление в Telegram/Slack при сильном отклонении от плана.
