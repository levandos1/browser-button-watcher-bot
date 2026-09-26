from __future__ import annotations

from app.models import AppState, MatchMode

SUPPORTED_LANGUAGES = {"en", "ru"}

_STRINGS = {
    "en": {
        "browser": "BROWSER",
        "status": "Status",
        "browser_type": "Browser",
        "endpoint": "Endpoint",
        "connect": "CONNECT",
        "launch_browser": "LAUNCH BROWSER",
        "refresh_tabs": "REFRESH TABS",
        "target": "TARGET",
        "target_tab": "Target tab",
        "no_target_tab": "No target tab selected",
        "button_text": "Button text",
        "button_placeholder": "Enter button text...",
        "match_mode": "Match mode",
        "settings": "SETTINGS",
        "check_interval": "Check interval",
        "click_cooldown": "Click cooldown",
        "close_browser": "Close dedicated automation browser on app exit",
        "start_monitoring": "START MONITORING",
        "monitoring_active": "MONITORING ACTIVE",
        "stop": "STOP",
        "stop_monitoring": "STOP MONITORING",
        "runtime": "Runtime",
        "checks": "Checks",
        "detections": "Detections",
        "clicks": "Clicks",
        "errors": "Errors",
        "log": "LOG",
        "clear_log": "CLEAR LOG",
        "empty_target": "Target button text cannot be empty.",
        "select_tab_first": "Select a target tab first.",
    },
    "ru": {
        "browser": "БРАУЗЕР",
        "status": "Статус",
        "browser_type": "Браузер",
        "endpoint": "Endpoint",
        "connect": "ПОДКЛЮЧИТЬСЯ",
        "launch_browser": "ЗАПУСТИТЬ БРАУЗЕР",
        "refresh_tabs": "ОБНОВИТЬ ВКЛАДКИ",
        "target": "ЦЕЛЬ",
        "target_tab": "Целевая вкладка",
        "no_target_tab": "Целевая вкладка не выбрана",
        "button_text": "Текст кнопки",
        "button_placeholder": "Введите текст кнопки...",
        "match_mode": "Режим совпадения",
        "settings": "НАСТРОЙКИ",
        "check_interval": "Интервал проверки",
        "click_cooldown": "Задержка между кликами",
        "close_browser": "Закрывать выделенный браузер при выходе из приложения",
        "start_monitoring": "НАЧАТЬ МОНИТОРИНГ",
        "monitoring_active": "МОНИТОРИНГ АКТИВЕН",
        "stop": "СТОП",
        "stop_monitoring": "ОСТАНОВИТЬ МОНИТОРИНГ",
        "runtime": "Время",
        "checks": "Проверки",
        "detections": "Обнаружения",
        "clicks": "Клики",
        "errors": "Ошибки",
        "log": "ЛОГ",
        "clear_log": "ОЧИСТИТЬ ЛОГ",
        "empty_target": "Текст кнопки не может быть пустым.",
        "select_tab_first": "Сначала выберите целевую вкладку.",
    },
}

_MATCH_MODE_LABELS = {
    "en": {
        MatchMode.EXACT: "Exact",
        MatchMode.CONTAINS: "Contains",
        MatchMode.CASE_INSENSITIVE_EXACT: "Case-insensitive exact",
        MatchMode.CASE_INSENSITIVE_CONTAINS: "Case-insensitive contains",
    },
    "ru": {
        MatchMode.EXACT: "Точное совпадение",
        MatchMode.CONTAINS: "Содержит фразу",
        MatchMode.CASE_INSENSITIVE_EXACT: "Точное без учёта регистра",
        MatchMode.CASE_INSENSITIVE_CONTAINS: "Содержит без учёта регистра",
    },
}

_STATE_LABELS = {
    "en": {state: state.value for state in AppState},
    "ru": {
        AppState.DISCONNECTED: "НЕ ПОДКЛЮЧЕНО",
        AppState.CONNECTED: "ПОДКЛЮЧЕНО",
        AppState.READY: "ГОТОВО",
        AppState.MONITORING: "МОНИТОРИНГ",
        AppState.STOPPING: "ОСТАНОВКА",
        AppState.ERROR: "ОШИБКА",
    },
}

def normalize_language(language: str) -> str:
    return language if language in SUPPORTED_LANGUAGES else "en"


def tr(language: str, key: str) -> str:
    language = normalize_language(language)
    return _STRINGS[language][key]


def match_mode_label(language: str, mode: MatchMode) -> str:
    language = normalize_language(language)
    return _MATCH_MODE_LABELS[language][mode]


def state_label(language: str, state: AppState) -> str:
    language = normalize_language(language)
    return _STATE_LABELS[language][state]
