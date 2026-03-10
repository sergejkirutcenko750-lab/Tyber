#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для переноса домена ВКонтакте с сообщества на профиль.
ВНИМАНИЕ: Использовать только в образовательных целях!
"""

import vk_api
import time
import sys
import os
from vk_api.exceptions import ApiError

# Для Windows: правильное отображение русских букв
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clear_screen():
    """Очистка экрана для Windows и других ОС"""
    os.system('cls' if os.name == 'nt' else 'clear')

def auth_handler():
    """Обработчик двухфакторной аутентификации"""
    key = input("Введите код двухфакторной аутентификации: ")
    remember_device = True
    return key, remember_device

def captcha_handler(captcha):
    """Обработчик капчи"""
    key = input(f"Введите капчу (картинка здесь: {captcha.get_url()}): ")
    return captcha.try_again(key)

def save_token(token):
    """Сохраняет токен в файл для будущих использований"""
    try:
        with open('vk_token.txt', 'w') as f:
            f.write(token)
        print("✅ Токен сохранен в vk_token.txt")
    except:
        pass

def load_token():
    """Загружает сохраненный токен"""
    try:
        with open('vk_token.txt', 'r') as f:
            return f.read().strip()
    except:
        return None

def get_token():
    """Получает токен от пользователя"""
    print("\n" + "="*50)
    print("🔑 ВВОД ТОКЕНА VK")
    print("="*50)
    
    # Пробуем загрузить сохраненный токен
    saved_token = load_token()
    if saved_token:
        use_saved = input(f"\nНайден сохраненный токен. Использовать его? (да/нет): ").lower()
        if use_saved in ['да', 'yes', 'y', 'lf', 'д']:
            return saved_token
    
    print("\n📝 Инструкция:")
    print("1. Зайди на vkhost.github.io")
    print("2. Выбери 'VK Admin' или 'Kate Mobile'")
    print("3. Скопируй токен из адресной строки")
    print("   (параметр access_token=...)\n")
    
    token = input("Вставь свой токен: ").strip()
    
    if not token:
        print("❌ Токен не может быть пустым!")
        return get_token()
    
    # Спрашиваем, сохранить ли токен
    save_choice = input("\nСохранить токен для следующих запусков? (да/нет): ").lower()
    if save_choice in ['да', 'yes', 'y', 'lf', 'д']:
        save_token(token)
    
    return token

def main():
    clear_screen()
    
    print("="*50)
    print("🎯 VK ДОМЕН СВАПАТЕЛЬ by Бро")
    print("="*50)
    print("\n⚠️  Используй на свой страх и риск!")
    print("Слишком частые операции = временный бан\n")
    
    # Получаем токен
    VK_TOKEN = get_token()
    
    if not VK_TOKEN:
        print("❌ Токен не получен. Выход.")
        input("\nНажми Enter для выхода...")
        return
    
    # Авторизация
    vk_session = vk_api.VkApi(
        token=VK_TOKEN,
        captcha_handler=captcha_handler,
        auth_handler=auth_handler
    )
    
    try:
        vk_session.auth()
        print("\n✅ Авторизация успешна!")
    except vk_api.AuthError as error_msg:
        print(f"\n❌ Ошибка авторизации: {error_msg}")
        print("Возможно, токен недействителен или истек.")
        input("\nНажми Enter для выхода...")
        return
    
    vk = vk_session.get_api()
    
    # Проверка прав токена
    try:
        user_info = vk.users.get()[0]
        print(f"👤 Авторизован как: {user_info['first_name']} {user_info['last_name']}")
    except Exception as e:
        print(f"❌ Не удалось получить информацию о пользователе: {e}")
        input("\nНажми Enter для выхода...")
        return
    
    # Показываем список доступных сообществ
    print("\n📋 ЗАГРУЗКА ДОСТУПНЫХ СООБЩЕСТВ...\n")
    
    try:
        groups = vk.groups.get(extended=1, filter='admin')
        groups_count = groups['count']
        
        if groups_count == 0:
            print("❌ У тебя нет сообществ, где ты администратор.")
            input("\nНажми Enter для выхода...")
            return
        
        print(f"✅ Найдено сообществ: {groups_count}\n")
        print("📌 Сообщества по номерам:\n")
        
        # Сохраняем список для выбора
        groups_list = []
        for i, group in enumerate(groups['items'], 1):
            group_id = -group['id']
            groups_list.append({
                'index': i,
                'id': group_id,
                'name': group['name'],
                'screen_name': group.get('screen_name', 'нет домена')
            })
            domain_status = group.get('screen_name', 'нет')
            print(f"{i}. {group['name']}")
            print(f"   📍 Домен: {domain_status} | ID: {group_id}\n")
        
        # Выбор сообщества
        while True:
            try:
                choice = int(input(f"🔢 Выбери номер сообщества (1-{groups_count}): "))
                if 1 <= choice <= groups_count:
                    selected_group = groups_list[choice-1]
                    SOURCE_GROUP_ID = selected_group['id']
                    DOMAIN_NAME = selected_group['screen_name']
                    
                    if DOMAIN_NAME == 'нет домена':
                        print("\n❌ У этого сообщества нет короткого имени для переноса!")
                        input("\nНажми Enter для выхода...")
                        return
                    
                    print(f"\n✅ Выбрано: {selected_group['name']}")
                    print(f"📍 Домен для переноса: {DOMAIN_NAME}")
                    break
                else:
                    print("❌ Неверный номер. Попробуй снова.")
            except ValueError:
                print("❌ Введи число!")
        
        # ID профиля
        TARGET_USER_ID = vk.users.get()[0]['id']
        print(f"👤 Целевой профиль ID: {TARGET_USER_ID}")
        
        # Подтверждение
        print("\n⚠️  ВНИМАНИЕ! Операция необратима!")
        confirm = input(f"\n🔴 Перенести домен '{DOMAIN_NAME}' на профиль? (да/нет): ")
        if confirm.lower() not in ['да', 'yes', 'y', 'lf', 'д']:
            print("❌ Операция отменена.")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 1: Сохраняем информацию сообщества
        print("\n📦 [1/4] Сохраняем информацию о сообществе...")
        try:
            group_info = vk.groups.getById(group_id=SOURCE_GROUP_ID)[0]
            old_name = group_info['name']
            print(f"   Старое название: {old_name}")
        except Exception as e:
            print(f"   ❌ Не удалось получить информацию о сообществе: {e}")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 2: Убираем домен с сообщества
        print("\n🔄 [2/4] Освобождаем домен с сообщества...")
        try:
            vk.groups.edit(
                group_id=abs(SOURCE_GROUP_ID),
                address=''
            )
            print("   ✅ Домен освобожден с сообщества!")
            time.sleep(1)
        except ApiError as e:
            if e.code == 14:
                print("   ⚠️ Требуется капча, обрабатываем...")
                vk.groups.edit(
                    group_id=abs(SOURCE_GROUP_ID),
                    address=''
                )
            else:
                print(f"   ❌ Ошибка: {e}")
                if "access_denied" in str(e).lower():
                    print("   Нет прав на управление этим сообществом!")
                input("\nНажми Enter для выхода...")
                return
        
        # ШАГ 3: Устанавливаем домен на профиль
        print("\n📌 [3/4] Устанавливаем домен на профиль...")
        try:
            vk.account.setNameInMenu(name=DOMAIN_NAME)
            print(f"   ✅ Домен '{DOMAIN_NAME}' успешно установлен на профиль!")
            time.sleep(1)
        except ApiError as e:
            if e.code == 14:
                print("   ⚠️ Требуется капча, обрабатываем...")
                vk.account.setNameInMenu(name=DOMAIN_NAME)
            else:
                print(f"   ❌ Ошибка: {e}")
                if "already used" in str(e).lower() or "already taken" in str(e).lower():
                    print("   👤 Похоже, кто-то успел занять домен!")
                input("\nНажми Enter для выхода...")
                return
        
        # ШАГ 4: Меняем название сообщества и пишем пост
        print("\n✏️ [4/4] Обновляем информацию сообщества...")
        try:
            # Меняем название
            vk.groups.edit(
                group_id=abs(SOURCE_GROUP_ID),
                title='ZzZZZZz'
            )
            print("   ✅ Название сообщества изменено на ZzZZZZz")
            
            # Пытаемся сделать запись
            try:
                vk.wall.post(
                    owner_id=SOURCE_GROUP_ID,
                    message='Темыч СВАПАЕТ =3',
                    from_group=1
                )
                print("   ✅ Запись 'Темыч СВАПАЕТ =3' опубликована!")
            except ApiError as wall_error:
                print(f"   ⚠️ Не удалось опубликовать запись: {wall_error}")
                print("   (Возможно, у сообщества закрыта стена)")
                
        except ApiError as e:
            print(f"   ⚠️ Ошибка при обновлении сообщества: {e}")
        
        # ФИНАЛ
        print("\n" + "="*50)
        print("🎉 ОПЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("="*50)
        print(f"✅ Домен '{DOMAIN_NAME}' перенесен на профиль!")
        print("✅ Название сообщества: ZzZZZZz")
        print("✅ Запись: Темыч СВАПАЕТ =3")
        print("="*50)
        
    except ApiError as e:
        print(f"\n❌ Ошибка API: {e}")
    except Exception as e:
        print(f"\n❌ Неизвестная ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    main()
