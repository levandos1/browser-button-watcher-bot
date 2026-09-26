# ButtonWatcher

A Windows desktop app that monitors one selected Chrome / Edge / Opera / Yandex Browser / Chromium tab and automatically clicks a visible enabled button when its text matches a phrase you specify.

ButtonWatcher works through Playwright and Chrome DevTools Protocol (CDP). It clicks inside the browser page and never moves your physical mouse cursor, so you can keep using the computer normally.

> Русская инструкция находится ниже: [Перейти к русской версии](#русский)

## English

### What it does

ButtonWatcher can:

- connect to a Chromium-based browser through local CDP;
- show the browser tabs and let you choose exactly one target tab;
- search the main document and iframes for interactive elements;
- match button text using several comparison modes;
- click matching elements without moving the Windows mouse cursor;
- keep monitoring continuously and click the same visible button again after the configured cooldown;
- keep the UI responsive while monitoring in a background worker;
- switch the interface between English and Russian; the choice is saved in the existing app config;
- save settings and logs under `%LOCALAPPDATA%\ButtonWatcher`.

### Requirements

- Windows 10 or Windows 11
- Google Chrome, Microsoft Edge, Opera, Yandex Browser, or Chromium
- Python 3.12+ only if you want to run from source

For normal use of the compiled `ButtonWatcher.exe`, Python is not required.

### Quick start

The easiest way to use the app is:

1. Run `ButtonWatcher.exe` or start the app from source.
2. Choose **Chrome, Edge, Opera, Yandex Browser, or Chromium** in the Browser dropdown.
3. Click **LAUNCH BROWSER**.
4. In the launched browser, open the page you want to monitor.
5. Click **REFRESH TABS** if the new tab is not shown yet.
6. Select the target tab.
7. Enter the button text, for example `start`.
8. Choose a **Match mode**.
9. Set **Check interval** and **Click cooldown**.
10. Click **START MONITORING**.
11. Leave the app running. You can keep using your mouse and keyboard normally.

While monitoring is active, the interface is visually dimmed and the START / STOP controls are highlighted so the active state is easy to see.

### Match modes

- **Exact** — the button text must match exactly.
- **Contains** — the button text may contain the entered phrase.
- **Case-insensitive exact** — exact match without case sensitivity.
- **Case-insensitive contains** — partial match without case sensitivity.

Example: if the target phrase is `confirm`, case-insensitive contains will also match `Please Confirm now`.

### Check interval and Click cooldown

**Check interval** controls how often the selected page is scanned for the target button.

**Click cooldown** is the minimum delay before the same still-visible matching button can be clicked again.

For example, with a `300 ms` check interval and a `3 sec` cooldown, ButtonWatcher checks the page several times per second but will not click the same continuously visible target more often than approximately once every three seconds.

### Browser connection

The default endpoint is:

```text
http://127.0.0.1:9222
```

#### Recommended: LAUNCH BROWSER

Choose a browser first, then click **LAUNCH BROWSER**. ButtonWatcher finds that browser's executable, starts a separate automation profile with remote debugging enabled, connects to it, and loads its tabs.

This is the most reliable method because a normal browser process started without remote debugging cannot be attached retroactively through CDP.

#### Connect to a browser started manually

Start Chrome with remote debugging enabled, for example:

```bat
chrome.exe --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="%LOCALAPPDATA%\ButtonWatcher\manual-profile"
```

Then click **CONNECT**.

ButtonWatcher first tries the endpoint shown in the UI and then scans common local debugging ports plus `DevToolsActivePort`. Only localhost endpoints are accepted.

### Run from source

```bat
cd /d E:\browser-button-watcher-bot
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

### Build a standalone EXE

Run:

```bat
build.bat
```

The script installs/updates dependencies inside `.venv`, generates the application icon, cleans old build output, and creates a single windowed executable with PyInstaller.

Output:

```text
dist\ButtonWatcher.exe
```

### Tests

Run unit tests:

```bat
.venv\Scripts\python.exe -m pytest -q
```

Run the Chrome/CDP integration smoke test:

```bat
set PYTHONPATH=.
.venv\Scripts\python.exe tests\integration_smoke.py
```

The integration fixture checks visible/hidden/disabled elements, iframe detection, browser-level clicking, repeated clicks after cooldown, and CDP endpoint discovery.

### Where settings and logs are stored

```text
%LOCALAPPDATA%\ButtonWatcher\
├── config.json
├── logs\
├── browser-profile\              # Chrome
├── browser-profile-edge\         # Edge
├── browser-profile-opera\        # Opera
├── browser-profile-yandex\       # Yandex
└── browser-profile-chromium\     # Chromium
```

### Troubleshooting

**The app does not see my already-open Chrome**  
Chrome must have been started with remote debugging enabled. A normal already-running Chrome cannot expose its existing tabs to Playwright/CDP retroactively. Use **LAUNCH BROWSER** or start a separate Chrome profile with a debugging port.

**The target button is not detected**  
Check the selected tab, the entered phrase, the selected Match mode, and whether the control is a real DOM interactive element. Closed Shadow DOM and canvas-only controls are not generally detectable.

**The button is clicked only once**  
Current versions keep monitoring continuously. If the matching button remains visible, it becomes eligible again after the configured Click cooldown.

**The browser click fails**  
The page may replace, cover, disable, or otherwise change the element between detection and click. The error is logged and monitoring continues.

### Project structure

- `app/` — configuration, constants, models and application state
- `browser/` — CDP connection, element detection and clicking
- `workers/` — background asyncio / QThread monitoring worker
- `ui/` — PySide6 interface, styles and custom widgets
- `services/` — logging
- `tests/` — unit and integration tests
- `tools/` — build-time utilities such as icon generation
- `button_watcher.spec` — PyInstaller configuration
- `build.bat` — reproducible Windows build script

---

## Русский

### Что делает программа

ButtonWatcher — Windows-приложение, которое следит за одной выбранной вкладкой Chrome / Edge / Opera / Yandex Browser / Chromium и автоматически нажимает видимую активную кнопку, если её текст совпадает с указанной вами фразой.

Клик выполняется через Playwright непосредственно внутри страницы браузера. Физический курсор мыши Windows не двигается, поэтому во время мониторинга можно продолжать нормально пользоваться компьютером.

### Основные возможности

- подключение к Chromium-браузеру через локальный CDP;
- выбор конкретной вкладки для мониторинга;
- поиск кнопок и других интерактивных DOM-элементов в основной странице и iframe;
- несколько режимов сравнения текста;
- клик внутри браузера без использования системного курсора;
- постоянный мониторинг и повторные клики по той же видимой кнопке после cooldown;
- фоновая работа без зависания интерфейса;
- переключение интерфейса между английским и русским; выбранный язык сохраняется в существующем конфиге приложения;
- сохранение настроек и логов в `%LOCALAPPDATA%\ButtonWatcher`;
- сборка в один `.exe` через PyInstaller.

### Требования

- Windows 10 или Windows 11
- установленный Google Chrome, Microsoft Edge, Opera, Yandex Browser или Chromium
- Python 3.12+ нужен только для запуска из исходников

Для запуска готового `ButtonWatcher.exe` Python на компьютере не требуется.

### Быстрый запуск

1. Запустите `ButtonWatcher.exe`.
2. Выберите **Chrome, Edge, Opera, Yandex Browser или Chromium** в поле браузера.
3. Нажмите **LAUNCH BROWSER**.
4. В открывшемся браузере перейдите на страницу, которую нужно отслеживать.
5. Если вкладка ещё не появилась в программе, нажмите **REFRESH TABS**.
6. Выберите нужную вкладку.
7. Введите текст кнопки, например `Я тут`.
8. Выберите **Match mode**.
9. Настройте **Check interval** и **Click cooldown**.
10. Нажмите **START MONITORING**.
11. Оставьте приложение работать и продолжайте пользоваться компьютером как обычно.

Во время мониторинга остальные панели интерфейса затемняются, а START / STOP визуально выделяются.

### Что такое Match mode

- **Exact** — текст кнопки должен совпасть полностью.
- **Contains** — введённая фраза должна содержаться в тексте кнопки.
- **Case-insensitive exact** — полное совпадение без учёта регистра.
- **Case-insensitive contains** — частичное совпадение без учёта регистра.

Например, если указать `confirm`, режим Case-insensitive contains найдёт и кнопку `Please Confirm now`.

### Check interval и Click cooldown

**Check interval** — как часто программа проверяет выбранную вкладку на наличие нужной кнопки.

**Click cooldown** — минимальная пауза перед повторным кликом по той же кнопке, если она всё ещё остаётся видимой.

Например, при `300 ms` и `3 sec` программа будет проверять страницу несколько раз в секунду, но повторно нажмёт постоянно видимую кнопку примерно не раньше чем через три секунды.

### Подключение браузера

Стандартный адрес CDP:

```text
http://127.0.0.1:9222
```

#### Рекомендуемый вариант: LAUNCH BROWSER

Сначала выберите браузер, затем нажмите **LAUNCH BROWSER**. Программа найдёт выбранный Chrome / Edge / Opera / Yandex Browser / Chromium, запустит отдельный профиль с включённым remote debugging, подключится к нему и покажет список вкладок.

Это самый надёжный способ.

#### Подключение к браузеру, запущенному вручную

Chrome нужно заранее запустить с remote debugging:

```bat
chrome.exe --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="%LOCALAPPDATA%\ButtonWatcher\manual-profile"
```

После запуска браузера нажмите **CONNECT**.

ButtonWatcher сначала проверяет endpoint, указанный в интерфейсе, а затем ищет локальные debugging endpoints на распространённых портах и через `DevToolsActivePort`. Подключения разрешены только к localhost.

Обычный Chrome, который уже был запущен без remote debugging, нельзя подключить к Playwright/CDP задним числом. В таком случае используйте **LAUNCH BROWSER**.

### Запуск из исходников

```bat
cd /d E:\browser-button-watcher-bot
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

### Сборка одного EXE

```bat
build.bat
```

Готовый файл появится здесь:

```text
dist\ButtonWatcher.exe
```

### Тесты

```bat
.venv\Scripts\python.exe -m pytest -q
```

Интеграционный тест Chrome/CDP:

```bat
set PYTHONPATH=.
.venv\Scripts\python.exe tests\integration_smoke.py
```

### Где хранятся настройки и логи

```text
%LOCALAPPDATA%\ButtonWatcher\
├── config.json
├── logs\
└── browser-profile\
```

### Если что-то не работает

**Программа не видит уже открытый Chrome**  
Chrome должен быть запущен с включённым remote debugging. К обычному уже запущенному Chrome без debugging подключиться задним числом нельзя. Используйте **LAUNCH BROWSER**.

**Кнопка не находится**  
Проверьте выбранную вкладку, введённый текст, Match mode и то, является ли элемент настоящим DOM-элементом. Закрытый Shadow DOM и canvas-кнопки обычно недоступны для такого поиска.

**Кнопка нажалась только один раз**  
Текущая версия продолжает мониторинг постоянно. Если кнопка остаётся видимой, она снова станет доступна для клика после Click cooldown.

**Клик завершился ошибкой**  
Страница могла заменить, перекрыть или отключить элемент между обнаружением и кликом. Ошибка записывается в лог, а мониторинг продолжается.

### Структура проекта

- `app/` — конфигурация, модели и состояние приложения
- `browser/` — CDP, обнаружение элементов и клики
- `workers/` — фоновый поток и asyncio-мониторинг
- `ui/` — интерфейс PySide6, стили и виджеты
- `services/` — логирование
- `tests/` — unit- и integration-тесты
- `tools/` — служебные утилиты сборки
- `button_watcher.spec` — конфигурация PyInstaller
- `build.bat` — сборка Windows-версии
