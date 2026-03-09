#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TYBER ID – захват доменов ВК + Telegram-уведомления (ультраскорость 2 мс)
Версия: английские уведомления, улучшенная стабильность, работа с группами
"""

import requests
import time
import os
import sys
import logging
import re
import subprocess
import importlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== Автоустановка colorama ==========
def install_package(package_name):
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        print(f"⚠️ Библиотека {package_name} не найдена.")
        ans = input(f"Установить {package_name} сейчас? (y/n): ").strip().lower()
        if ans == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"✅ {package_name} установлена.")
                importlib.invalidate_caches()
                return True
            except Exception as e:
                print(f"❌ Ошибка установки: {e}")
                return False
        return False

install_package("colorama")
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS = True
except:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''
    COLORS = False

# ========== Цветной вывод ==========
def print_info(msg): print(f"{Fore.BLUE}{msg}{Style.RESET_ALL}")
def print_success(msg): print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
def print_warning(msg): print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
def print_error(msg): print(f"{Fore.RED}{msg}{Style.RESET_ALL}")

def print_banner():
    banner = f"""
{Fore.BLUE}╔══════════════════════════════════════════════════════════╗
║                                                              ║
║     {Fore.CYAN}████████╗██╗   ██╗██████╗ ███████╗██████╗ {Fore.BLUE}            ║
║     {Fore.CYAN}╚══██╔══╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗{Fore.BLUE}            ║
║        {Fore.CYAN}██║    ╚████╔╝ ██████╔╝█████╗  ██████╔╝{Fore.BLUE}            ║
║        {Fore.CYAN}██║     ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗{Fore.BLUE}            ║
║        {Fore.CYAN}██║      ██║   ██████╔╝███████╗██║  ██║{Fore.BLUE}            ║
║        {Fore.CYAN}╚═╝      ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝{Fore.BLUE}            ║
║                                                              ║
║              {Fore.WHITE}{Style.BRIGHT}ЗАБИРАЕМ АЙДИ{Style.RESET_ALL}{Fore.BLUE}                           ║
║              {Fore.WHITE}{Style.BRIGHT}ультраскорость (2 мс){Style.RESET_ALL}{Fore.BLUE}                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

# ========== Константы ==========
VK_VERSION = "5.199"
TOKEN_FILE = "vk_token.txt"
TG_TOKEN_FILE = "tg_token.txt"
TG_CHATID_FILE = "tg_chatid.txt"

BASE_INTERVAL = 0.002        # 2 мс между циклами
CAPTCHA_WAIT = 15
MAX_CAPTURE_FAILS = 3

# Таймауты увеличены для стабильности
CHECK_TIMEOUT = 1.0          # для проверки домена (было 0.3)
CAPTURE_TIMEOUT = 1.5        # для захвата домена (было 0.3)
GROUP_TIMEOUT = 5.0          # для загрузки групп

# ВСТРОЕННЫЙ ТОКЕН VK (замени на свой, если нужно)
VK_TOKEN = "vk1.a.uL1avUdx3GtZjaIffF96_yu8J-GyNY-lOltKB7qMTVREG4TJ0EdqdAREFYHu__3gIrUP9-R7oBCM-0s2dluESyXgXWfs_ZZdemi-g_bY_pzyWYJXMay8CB9nB67wVjU5qPXgr1jm52QhV2qS3IOq2F7pgh3hdwIMRd1-eV6WDfGjiI-gGDShFFr4Px1cFzw7aSR6oDJNaZJbBl6z2grGuA"

# ========== Вспомогательные функции ==========
def clean_domain(raw):
    raw = raw.strip().lower()
    raw = raw.replace('@', '').replace('https://vk.com/', '').replace('vk.com/', '')
    return raw

def is_valid_domain(domain):
    if not domain or len(domain) < 3 or len(domain) > 32:
        return False
    return bool(re.match(r'^[a-z0-9_]+$', domain))

def format_owner(owner_data):
    if not owner_data:
        return None
    obj_type = owner_data.get('type')
    obj_id = owner_data.get('id')
    if obj_type == 'group':
        return f"club{obj_id}"
    elif obj_type == 'user':
        return f"id{obj_id}"
    elif obj_type == 'application':
        return f"app{obj_id}"
    return None

# ========== Telegram функции (английский текст) ==========
def setup_telegram():
    print_info("\n📱 Настройка Telegram-уведомлений")
    tg_token = None
    if os.path.exists(TG_TOKEN_FILE):
        with open(TG_TOKEN_FILE, "r", encoding='utf-8') as f:
            tg_token = f.read().strip()
        if input("Использовать сохранённый токен Telegram? (y/n): ").strip().lower() != 'y':
            tg_token = None
    if not tg_token:
        print_info("1. Открой @BotFather в Telegram, создай нового бота (/newbot).")
        print_info("2. Скопируй токен (пример: 123456:ABCdef...).")
        tg_token = input("Вставь токен Telegram бота: ").strip()
        try:
            r = requests.get(f"https://api.telegram.org/bot{tg_token}/getMe", timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get('ok'):
                with open(TG_TOKEN_FILE, "w", encoding='utf-8') as f:
                    f.write(tg_token)
                print_success("✅ Токен сохранён.")
            else:
                print_error(f"❌ Токен недействителен: {data}")
                return None, None
        except Exception as e:
            print_error(f"❌ Ошибка проверки токена: {e}")
            return None, None
    chat_id = None
    if os.path.exists(TG_CHATID_FILE):
        with open(TG_CHATID_FILE, "r", encoding='utf-8') as f:
            chat_id = f.read().strip()
        if input(f"Использовать сохранённый chat_id ({chat_id})? (y/n): ").strip().lower() != 'y':
            chat_id = None
    if not chat_id:
        print_info("\n📨 Как получить chat_id:")
        print_info("1. Напиши своему боту любое сообщение.")
        print_info("2. Открой в браузере:")
        print_info(f"   https://api.telegram.org/bot{tg_token}/getUpdates")
        print_info("3. Найди поле 'chat': {'id': ТВОЙ_ID} (это число).")
        chat_id = input("Вставь свой chat_id: ").strip()
        if send_telegram(tg_token, chat_id, "test", True, None, 0.0, "profile"):
            with open(TG_CHATID_FILE, "w", encoding='utf-8') as f:
                f.write(chat_id)
            print_success("✅ Chat_id сохранён, тестовое сообщение отправлено.")
        else:
            print_error("❌ Не удалось отправить тестовое сообщение.")
            return None, None
    return tg_token, chat_id

def send_telegram(tg_token, chat_id, domain, success=True, old_owner=None, elapsed=0.0, target_desc="profile"):
    if not tg_token or not chat_id:
        return False
    if success:
        if old_owner:
            swap_info = f"Moved from: {old_owner} → {target_desc}"
        else:
            swap_info = f"Moved from: None → {target_desc}"
        text = (f"Domain Supplied!\n\n"
                f"Domain: {domain}\n"
                f"{swap_info}\n"
                f"Status: Cut down\n"
                f"Capture time: {elapsed:.3f} sec.\n"
                f"Event time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        text = (f"⚠️ Capture error\n\n"
                f"Domain: {domain}\n"
                f"Status: ❌ Failed\n"
                f"Reason: {old_owner if isinstance(old_owner, str) else 'unknown'}\n"
                f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        r = requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                          data={'chat_id': chat_id, 'text': text}, timeout=5)
        r.raise_for_status()
        result = r.json()
        if result.get('ok'):
            print_success("📨 Уведомление отправлено в Telegram")
            return True
        else:
            print_error(f"❌ Telegram API вернул ошибку: {result}")
            return False
    except Exception as e:
        print_error(f"❌ Ошибка отправки в Telegram: {e}")
        return False

# ========== VK монитор с улучшенной стабильностью ==========
class VKMonitor:
    def __init__(self, token):
        self.token = token
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,                          # разрешаем повторные попытки (до 2)
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=0.5,
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'keep-alive'
        })

    def _api_request(self, method, url, params=None, data=None, timeout=1.0):
        params = params or {}
        params.update({'access_token': self.token, 'v': VK_VERSION})
        try:
            if method.upper() == 'GET':
                resp = self.session.get(url, params=params, timeout=timeout)
            else:
                resp = self.session.post(url, params=params, data=data, timeout=timeout)
            resp.raise_for_status()
            json_data = resp.json()
            if 'error' in json_data:
                code = json_data['error'].get('error_code')
                msg = json_data['error'].get('error_msg', '')
                if code == 6:
                    time.sleep(0.1)
                    return None
                elif code == 14:
                    return 'captcha'
                else:
                    return {'error_code': code, 'error_msg': msg}
            return json_data.get('response')
        except requests.exceptions.Timeout:
            return {'error': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': 'connection_error'}
        except Exception as e:
            return {'error': str(e)}

    def get_owner_info(self, domain, retries=2):
        for attempt in range(retries):
            resp = self._api_request('GET', 'https://api.vk.com/method/utils.resolveScreenName',
                                     params={'screen_name': domain}, timeout=CHECK_TIMEOUT)
            if resp is None:
                return None
            if resp == 'captcha':
                return 'captcha'
            if isinstance(resp, dict) and 'error_code' in resp:
                print_error(f"Ошибка API при проверке {domain}: код {resp['error_code']} - {resp['error_msg']}")
                return None
            if isinstance(resp, dict) and 'error' in resp:
                if resp['error'] in ('timeout', 'connection_error') and attempt < retries - 1:
                    print_warning(f"⏳ Сетевая ошибка при проверке {domain}, повтор {attempt+2}...")
                    time.sleep(0.5)
                    continue
                print_error(f"Сетевая ошибка при проверке {domain}: {resp['error']}")
                return None
            if isinstance(resp, dict) and 'type' in resp:
                owner_type = resp['type']
                owner_id = None
                if owner_type == 'group':
                    owner_id = resp.get('group_id')
                elif owner_type == 'user':
                    owner_id = resp.get('user_id')
                elif owner_type == 'application':
                    owner_id = resp.get('app_id')
                return {'type': owner_type, 'id': owner_id}
            return True
        return None

    def capture_domain(self, domain, target_type='profile', group_id=None):
        if target_type == 'profile':
            resp = self._api_request('POST', 'https://api.vk.com/method/account.saveProfileInfo',
                                     params={'screen_name': domain}, timeout=CAPTURE_TIMEOUT)
        else:
            if not group_id:
                return False, "Нет ID группы"
            try:
                group_id = int(group_id)
            except:
                return False, f"Некорректный ID группы: {group_id}"
            resp = self._api_request('POST', 'https://api.vk.com/method/groups.edit',
                                     params={'group_id': group_id, 'screen_name': domain}, timeout=CAPTURE_TIMEOUT)
        if resp is None:
            return False, "Нет ответа от API"
        if resp == 'captcha':
            return False, "Капча"
        if isinstance(resp, dict):
            if 'error_code' in resp:
                return False, f"Ошибка API {resp['error_code']}: {resp['error_msg']}"
            if 'error' in resp:
                return False, f"Сетевая ошибка: {resp['error']}"
        if resp == 1 or (isinstance(resp, dict) and resp.get('response') == 1):
            return True, "Захвачен"
        return False, f"Неизвестный ответ: {resp}"

    def load_groups(self):
        print_info("🔄 Загружаю список групп...")
        params = {
            'access_token': self.token,
            'v': VK_VERSION,
            'extended': 1,
            'filter': 'admin'
        }
        try:
            resp = self.session.get("https://api.vk.com/method/groups.get", params=params, timeout=GROUP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                error_code = data['error'].get('error_code')
                error_msg = data['error'].get('error_msg')
                print_error(f"Ошибка VK API при загрузке групп: код {error_code} - {error_msg}")
                return []
            response = data.get('response')
            if isinstance(response, dict):
                items = response.get('items', [])
                print_success(f"✅ Загружено групп: {len(items)}")
                return items
            elif isinstance(response, list):
                print_warning("⚠️ Получен список ID групп (без имён). Возможно, токен не имеет прав extended.")
                return [{'id': gid, 'name': f'Group {gid}'} for gid in response]
            else:
                print_error(f"Неизвестный формат ответа: {response}")
                return []
        except Exception as e:
            print_error(f"Ошибка при загрузке групп: {e}")
            return []

# ========== Ввод данных (токен VK больше не запрашивается) ==========
def get_vk_token():
    # Используем встроенный токен
    global VK_TOKEN
    # Проверяем токен
    try:
        r = requests.get("https://api.vk.com/method/users.get",
                         params={'access_token': VK_TOKEN, 'v': VK_VERSION}, timeout=5)
        data = r.json()
        if 'error' in data:
            print_error(f"❌ Встроенный токен недействителен: {data['error']}")
            # Если не сработал, пробуем загрузить из файла (если есть)
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r", encoding='utf-8') as f:
                    token = f.read().strip()
                r2 = requests.get("https://api.vk.com/method/users.get",
                                   params={'access_token': token, 'v': VK_VERSION}, timeout=5)
                data2 = r2.json()
                if 'error' in data2:
                    print_error("❌ Токен из файла тоже недействителен.")
                    return None
                user_id = data2['response'][0]['id']
                print_success(f"✅ Токен из файла работает! ID: {user_id}")
                return token
            return None
        user_id = data['response'][0]['id']
        print_success(f"✅ Встроенный токен работает! ID: {user_id}")
        # Сохраняем токен в файл для будущих запусков
        with open(TOKEN_FILE, "w", encoding='utf-8') as f:
            f.write(VK_TOKEN)
        return VK_TOKEN
    except Exception as e:
        print_error(f"Ошибка проверки токена: {e}")
        return None

def input_domains():
    print_info("\n📝 Введи домены для мониторинга (каждый с новой строки, пустая = конец):")
    domains = []
    while True:
        line = input().strip()
        if not line:
            break
        domains.append(line)
    valid = []
    for raw in domains:
        d = clean_domain(raw)
        if is_valid_domain(d):
            valid.append(d)
        else:
            print_warning(f"Домен '{raw}' недопустим, пропущен.")
    return valid

def choose_target(monitor):
    print_info("\n🎯 Куда захватывать?")
    print("1. На профиль (profile)")
    print("2. На группу (group)")
    choice = input("Выбери (1/2): ").strip()
    if choice == '2':
        groups = monitor.load_groups()
        if not groups:
            print_error("Нет доступных групп (или ошибка загрузки).")
            return 'profile', None
        print("Доступные группы:")
        for i, g in enumerate(groups, 1):
            name = g.get('name', 'Без имени')
            gid = g.get('id')
            print(f"{i}. {name} (id: {gid})")
        try:
            idx = int(input("Номер группы: ")) - 1
            return 'group', groups[idx]['id']
        except:
            print_warning("Неверный выбор, использую профиль.")
            return 'profile', None
    return 'profile', None

# ========== Главная ==========
def main():
    print_banner()
    print_warning("⚠️ Ультраскорость: интервал 2 мс. Высокий риск бана токена!")
    logging.basicConfig(level=logging.WARNING)

    use_tg = input("\n📱 Включить Telegram-уведомления? (y/n): ").strip().lower()
    tg_token, tg_chatid = None, None
    if use_tg == 'y':
        tg_token, tg_chatid = setup_telegram()
        if tg_token and tg_chatid:
            print_success("✅ Telegram настроен")
        else:
            print_warning("⚠️ Telegram-уведомления отключены")

    vk_token = get_vk_token()
    if not vk_token:
        print_error("❌ Нет токена VK. Завершение.")
        input("Нажми Enter...")
        return

    monitor = VKMonitor(vk_token)
    target_type, group_id = choose_target(monitor)
    target_desc = "profile" if target_type == 'profile' else f"group {group_id}"

    domains = input_domains()
    if not domains:
        print_error("❌ Нет доменов.")
        input("Нажми Enter...")
        return

    if tg_token and tg_chatid:
        print_info("📱 Проверка Telegram-бота...")
        if send_telegram(tg_token, tg_chatid, "test", True, None, 0.0, target_desc):
            print_success("✅ Telegram работает, уведомления будут приходить")
        else:
            print_error("❌ Telegram не отвечает, уведомления отключены")
            tg_token, tg_chatid = None, None

    print_success(f"\n✅ Начинаю мониторинг {len(domains)} доменов...")
    print_info(f"Цель: {target_desc}")
    print_info(f"Интервал проверки: {BASE_INTERVAL*1000:.1f} мс")

    last_owner = {domain: None for domain in domains}
    capture_fails = {domain: 0 for domain in domains}

    try:
        while True:
            for domain in domains:
                status = monitor.get_owner_info(domain)
                if status is None:
                    continue
                if status == 'captcha':
                    print_error(f"❗ Капча при проверке {domain}, жду {CAPTCHA_WAIT} сек...")
                    time.sleep(CAPTCHA_WAIT)
                    continue

                if status is True:
                    old_owner_str = format_owner(last_owner[domain]) if last_owner[domain] else None
                    print_success(f"🔥 {domain} FREE! (previously: {old_owner_str or 'not occupied'})")

                    start_time = time.time()
                    success, msg = monitor.capture_domain(domain, target_type, group_id)
                    elapsed = time.time() - start_time

                    if tg_token and tg_chatid:
                        send_telegram(tg_token, tg_chatid, domain, success,
                                      old_owner_str, elapsed, target_desc)

                    if success:
                        print_success(f"✅ {domain} captured in {elapsed:.3f} sec!")
                        input("\n🎉 Press Enter to exit...")
                        return
                    else:
                        print_error(f"❌ Failed to capture {domain} in {elapsed:.3f} sec: {msg}")
                        capture_fails[domain] += 1
                        if capture_fails[domain] >= MAX_CAPTURE_FAILS:
                            print_error(f"Error limit for {domain}, exiting.")
                            input("Press Enter...")
                            return
                else:
                    # Домен занят – обновляем информацию о владельце
                    last_owner[domain] = status

            time.sleep(BASE_INTERVAL)

    except KeyboardInterrupt:
        print_warning("\n⚠️ Stopped by user.")
        input("Press Enter...")

if __name__ == "__main__":
    main()
