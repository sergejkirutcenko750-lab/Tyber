#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TYBER ID – АСИНХРОННАЯ версия с управлением токеном
Таргет: 0.2–0.25 сек, SSL через certifi, сохранение токена
"""

import asyncio
import aiohttp
import ssl
import certifi
import time
import os
import sys
import logging
import re
from colorama import init, Fore, Style

# ========== Цветной вывод ==========
try:
    init(autoreset=True)
    COLORS = True
except:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''
    COLORS = False

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
║              {Fore.WHITE}{Style.BRIGHT}управление токеном{Style.RESET_ALL}{Fore.BLUE}                       ║
║              {Fore.WHITE}{Style.BRIGHT}таргет 0.2-0.25 сек{Style.RESET_ALL}{Fore.BLUE}                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

# ========== Константы ==========
VK_VERSION = "5.199"
TOKEN_FILE = "vk_token.txt"
TG_TOKEN_FILE = "tg_token.txt"
TG_CHATID_FILE = "tg_chatid.txt"

# Таймауты для скорости 0.2-0.25 сек
CHECK_TIMEOUT = 0.3
CAPTURE_TIMEOUT = 0.4
GROUP_TIMEOUT = 3.0
CAPTCHA_WAIT = 15
MAX_CAPTURE_FAILS = 3

# ========== SSL контекст с certifi ==========
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# ========== Вспомогательные функции ==========
def clean_domain(raw):
    raw = raw.strip().lower()
    raw = raw.replace('@', '').replace('https://vk.com/', '').replace('vk.com/', '')
    return raw

def is_valid_domain(domain):
    return bool(re.match(r'^[a-z0-9_]{3,32}$', domain))

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

# ========== Функция получения токена (с сохранением) ==========
def get_vk_token():
    # Если есть сохранённый токен, предложить использовать его
    token = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding='utf-8') as f:
            token = f.read().strip()
        if token:
            print_info(f"🔑 Найден сохранённый токен: {token[:10]}...")
            use = input("Использовать сохранённый токен? (y/n): ").strip().lower()
            if use == 'y':
                # Проверим, что токен рабочий
                import requests
                try:
                    r = requests.get("https://api.vk.com/method/users.get",
                                     params={'access_token': token, 'v': VK_VERSION}, timeout=5)
                    data = r.json()
                    if 'error' in data:
                        print_error(f"❌ Сохранённый токен недействителен: {data['error']}")
                        token = None
                    else:
                        user_id = data['response'][0]['id']
                        print_success(f"✅ Сохранённый токен работает! ID: {user_id}")
                        return token
                except Exception as e:
                    print_error(f"❌ Ошибка при проверке сохранённого токена: {e}")
                    token = None
            else:
                token = None
        else:
            token = None

    # Если нет сохранённого или не захотели использовать, запрашиваем новый
    print_info("🔑 Получи токен на https://vkhost.github.io (выбери vk.com, поставь галочку groups)")
    new_token = input("Вставь новый токен VK: ").strip()
    # Очистка от возможных невидимых символов
    new_token = new_token.replace('\u200b', '').replace('\ufeff', '')
    # Проверяем токен
    import requests
    try:
        r = requests.get("https://api.vk.com/method/users.get",
                         params={'access_token': new_token, 'v': VK_VERSION}, timeout=5)
        data = r.json()
        if 'error' in data:
            print_error(f"❌ Токен недействителен: {data['error']}")
            return None
        user_id = data['response'][0]['id']
        print_success(f"✅ Новый токен работает! ID: {user_id}")
        # Сохраняем в файл
        with open(TOKEN_FILE, "w", encoding='utf-8') as f:
            f.write(new_token)
        return new_token
    except Exception as e:
        print_error(f"Ошибка проверки нового токена: {e}")
        return None

# ========== Асинхронные функции VK API ==========
async def vk_api_request(session, method, url, token, params=None, data=None, timeout=0.3, retries=2):
    params = params or {}
    params.update({'access_token': token, 'v': VK_VERSION})
    for attempt in range(retries + 1):
        try:
            if method.upper() == 'GET':
                async with session.get(url, params=params, timeout=timeout) as resp:
                    json_data = await resp.json(content_type=None)
            else:
                async with session.post(url, params=params, data=data, timeout=timeout) as resp:
                    json_data = await resp.json(content_type=None)
            if 'error' in json_data:
                code = json_data['error'].get('error_code')
                if code == 6:
                    await asyncio.sleep(0.2)
                    continue
                elif code == 14:
                    return 'captcha'
                else:
                    return {'error_code': code, 'error_msg': json_data['error'].get('error_msg', '')}
            return json_data.get('response')
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            if attempt < retries:
                print_warning(f"⏳ Сетевая ошибка, попытка {attempt+2}...")
                await asyncio.sleep(0.3)
            else:
                return {'error': 'timeout' if isinstance(e, asyncio.TimeoutError) else 'connection_error'}
        except Exception as e:
            return {'error': str(e)}
    return None

async def get_owner_info(session, token, domain):
    resp = await vk_api_request(session, 'GET', 'https://api.vk.com/method/utils.resolveScreenName',
                                 token, params={'screen_name': domain}, timeout=CHECK_TIMEOUT, retries=2)
    if resp is None:
        return None
    if resp == 'captcha':
        return 'captcha'
    if isinstance(resp, dict) and 'error_code' in resp:
        return None
    if isinstance(resp, dict) and 'error' in resp:
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

async def capture_domain(session, token, domain, target_type='profile', group_id=None):
    if target_type == 'profile':
        resp = await vk_api_request(session, 'POST', 'https://api.vk.com/method/account.saveProfileInfo',
                                     token, params={'screen_name': domain}, timeout=CAPTURE_TIMEOUT, retries=2)
    else:
        if not group_id:
            return False, "Нет ID группы"
        try:
            group_id = int(group_id)
        except:
            return False, f"Некорректный ID группы: {group_id}"
        resp = await vk_api_request(session, 'POST', 'https://api.vk.com/method/groups.edit',
                                     token, params={'group_id': group_id, 'screen_name': domain}, timeout=CAPTURE_TIMEOUT, retries=2)
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

async def load_groups(session, token):
    print_info("🔄 Загружаю список групп...")
    params = {
        'access_token': token,
        'v': VK_VERSION,
        'extended': 1,
        'filter': 'admin'
    }
    try:
        async with session.get("https://api.vk.com/method/groups.get", params=params, timeout=GROUP_TIMEOUT) as resp:
            data = await resp.json(content_type=None)
        # Диагностика
        if 'error' in data:
            error_code = data['error'].get('error_code')
            error_msg = data['error'].get('error_msg')
            print_error(f"❌ Ошибка VK API: код {error_code} - {error_msg}")
            return []
        response = data.get('response')
        if not response:
            print_error("❌ Пустой ответ от VK")
            return []
        if isinstance(response, dict):
            items = response.get('items', [])
            if not items:
                print_warning("⚠️ Список групп пуст. Убедись, что ты администратор хотя бы одной группы.")
            else:
                print_success(f"✅ Найдено групп: {len(items)}")
                for i, g in enumerate(items, 1):
                    print(f"  {i}. {g.get('name', 'Без имени')} (id: {g.get('id')})")
            return items
        elif isinstance(response, list):
            print_warning("⚠️ Получен список ID групп без имён")
            return [{'id': gid, 'name': f'Group {gid}'} for gid in response]
        else:
            print_error(f"❌ Неизвестный формат ответа: {response}")
            return []
    except Exception as e:
        print_error(f"❌ Ошибка при загрузке групп: {e}")
        return []

# ========== Telegram функции ==========
async def send_telegram(session, tg_token, chat_id, domain, success=True, old_owner=None,
                        elapsed=0.0, target_desc="profile", requests_count=0, rps=0.0):
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
                f"Requests made: {requests_count}\n"
                f"Check speed: {rps:.2f} req/sec\n"
                f"Event time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        text = (f"⚠️ Capture error\n\n"
                f"Domain: {domain}\n"
                f"Status: ❌ Failed\n"
                f"Reason: {old_owner if isinstance(old_owner, str) else 'unknown'}\n"
                f"Requests made: {requests_count}\n"
                f"Check speed: {rps:.2f} req/sec\n"
                f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        async with session.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                                data={'chat_id': chat_id, 'text': text}, timeout=3) as resp:
            result = await resp.json()
            return result.get('ok', False)
    except:
        return False

# ========== Настройка Telegram ==========
def setup_telegram():
    print_info("\n📱 Настройка Telegram-уведомлений")
    tg_token = None
    if os.path.exists(TG_TOKEN_FILE):
        with open(TG_TOKEN_FILE, "r", encoding='utf-8') as f:
            tg_token = f.read().strip()
        if tg_token:
            use = input(f"Использовать сохранённый токен Telegram? (y/n): ").strip().lower()
            if use != 'y':
                tg_token = None
    if not tg_token:
        print_info("1. Открой @BotFather в Telegram, создай нового бота (/newbot).")
        print_info("2. Скопируй токен (пример: 123456:ABCdef...).")
        tg_token = input("Вставь токен Telegram бота: ").strip()
        import requests
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
        if chat_id:
            use = input(f"Использовать сохранённый chat_id ({chat_id})? (y/n): ").strip().lower()
            if use != 'y':
                chat_id = None
    if not chat_id:
        print_info("\n📨 Как получить chat_id:")
        print_info("1. Напиши своему боту любое сообщение.")
        print_info("2. Открой в браузере:")
        print_info(f"   https://api.telegram.org/bot{tg_token}/getUpdates")
        print_info("3. Найди поле 'chat': {'id': ТВОЙ_ID} (это число).")
        chat_id = input("Вставь свой chat_id: ").strip()
        # Проверим тестовым сообщением
        async def test():
            conn = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
            async with aiohttp.ClientSession(connector=conn) as sess:
                return await send_telegram(sess, tg_token, chat_id, "test", True, None, 0.0, "profile", 0, 0.0)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if loop.run_until_complete(test()):
            with open(TG_CHATID_FILE, "w", encoding='utf-8') as f:
                f.write(chat_id)
            print_success("✅ Chat_id сохранён, тестовое сообщение отправлено.")
            loop.close()
        else:
            print_error("❌ Не удалось отправить тестовое сообщение.")
            return None, None
    return tg_token, chat_id

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

# ========== Главная асинхронная функция ==========
async def main_async():
    print_banner()
    logging.basicConfig(level=logging.WARNING)

    # Telegram настройка
    use_tg = input("\n📱 Включить Telegram-уведомления? (y/n): ").strip().lower()
    tg_token, tg_chatid = None, None
    if use_tg == 'y':
        tg_token, tg_chatid = setup_telegram()
        if tg_token and tg_chatid:
            print_success("✅ Telegram настроен")
        else:
            print_warning("⚠️ Telegram-уведомления отключены")

    # VK токен
    vk_token = get_vk_token()
    if not vk_token:
        print_error("❌ Нет токена VK. Завершение.")
        return

    # Создаём коннектор с SSL и сессию с общим таймаутом
    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Загружаем группы (для выбора цели)
        groups = await load_groups(session, vk_token)
        print_info("\n🎯 Куда захватывать?")
        print("1. На профиль (profile)")
        print("2. На группу (group)")
        choice = input("Выбери (1/2): ").strip()
        target_type = 'profile'
        group_id = None
        if choice == '2':
            if not groups:
                print_error("❌ Нет доступных групп. Завершаю.")
                return
            print("Доступные группы:")
            for i, g in enumerate(groups, 1):
                name = g.get('name', 'Без имени')
                gid = g.get('id')
                print(f"{i}. {name} (id: {gid})")
            try:
                idx = int(input("Номер группы: ")) - 1
                target_type = 'group'
                group_id = groups[idx]['id']
            except:
                print_warning("Неверный выбор, использую профиль.")
                target_type = 'profile'
                group_id = None
        target_desc = "profile" if target_type == 'profile' else f"group {group_id}"

        domains = input_domains()
        if not domains:
            print_error("❌ Нет доменов.")
            return

        if tg_token and tg_chatid:
            print_info("📱 Проверка Telegram-бота...")
            if await send_telegram(session, tg_token, tg_chatid, "test", True, None, 0.0, target_desc, 0, 0.0):
                print_success("✅ Telegram работает, уведомления будут приходить")
            else:
                print_error("❌ Telegram не отвечает, уведомления отключены")
                tg_token, tg_chatid = None, None

        print_success(f"\n✅ Начинаю мониторинг {len(domains)} доменов...")
        print_info(f"Цель: {target_desc}")
        print_info(f"Таймауты: проверка {CHECK_TIMEOUT}с, захват {CAPTURE_TIMEOUT}с")

        request_count = 0
        start_monitor_time = time.time()
        last_owner = {domain: None for domain in domains}
        capture_fails = {domain: 0 for domain in domains}

        try:
            while True:
                cycle_start = time.time()
                for domain in domains:
                    status = await get_owner_info(session, vk_token, domain)
                    request_count += 1

                    if status is None:
                        continue
                    if status == 'captcha':
                        print_error(f"❗ Капча при проверке {domain}, жду {CAPTCHA_WAIT} сек...")
                        await asyncio.sleep(CAPTCHA_WAIT)
                        continue

                    if status is True:
                        old_owner_str = format_owner(last_owner[domain]) if last_owner[domain] else None
                        print_success(f"🔥 {domain} FREE! (previously: {old_owner_str or 'not occupied'})")

                        start_time = time.time()
                        success, msg = await capture_domain(session, vk_token, domain, target_type, group_id)
                        elapsed = time.time() - start_time

                        total_time = time.time() - start_monitor_time
                        rps = request_count / total_time if total_time > 0 else 0

                        if tg_token and tg_chatid:
                            await send_telegram(session, tg_token, tg_chatid, domain, success,
                                                old_owner_str, elapsed, target_desc, request_count, rps)

                        if success:
                            print_success(f"✅ {domain} captured in {elapsed:.3f} sec! Total checks: {request_count} @ {rps:.2f} req/sec")
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
                        last_owner[domain] = status

                elapsed = time.time() - cycle_start
                target = 1 / 20  # 0.05 сек, чтобы удержать ~20 RPS
                if elapsed < target:
                    await asyncio.sleep(target - elapsed)

        except KeyboardInterrupt:
            print_warning("\n⚠️ Stopped by user.")
            input("Press Enter...")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
