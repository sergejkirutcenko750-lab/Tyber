#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
СКРИПТ ДЛЯ ПЕРЕНОСА ДОМЕНА ВКОНТАКТЕ
Токен уже вставлен, сам всё почистит и определит
"""

import vk_api
import time
import sys
import os
import re
from vk_api.exceptions import ApiError

# ТВОЙ ТОКЕН (уже вставлен, бро!)
RAW_TOKEN = "vk1.a.pn29T_dfdVgZJvToe_6BfSybD0QsARa2nbuYqMhQCeqP6VVuFibYNsKv4xRr786BuIMtoupKgMYe1wjBamku6DZgWsiWIlWLZIccUJ1_Sy333rJ0NK3iQlsb8Zn_Ms5mcRwP0ME8-aois8U6S47ZE32OcbAFzeKyI436FAqOD4WsTZxNzThepcg2CKnX-IywH5FjbBpyZywq2xaaMRPyAA"

# Для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_token(token):
    """СУПЕР-ОЧИСТКА токена от любого мусора"""
    if not token:
        return None
    
    # Убираем пробелы и кавычки
    token = token.strip().strip('"').strip("'")
    
    # Если это ссылка, вытаскиваем токен
    if 'access_token=' in token:
        token = token.split('access_token=')[1].split('&')[0]
    
    # Если это полный URL, берем только токен
    if 'vk1.a.' in token:
        # Регулярка для точного выделения токена
        match = re.search(r'(vk1\.[a-zA-Z0-9._-]+)', token)
        if match:
            token = match.group(1)
    
    # Финальная зачистка
    token = re.sub(r'[^a-zA-Z0-9._-]', '', token)
    
    return token

def main():
    # Очистка экрана
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*60)
    print("🎯 VK ДОМЕН СВАПАТЕЛЬ (ПРЕМИУМ ИЗДАНИЕ)")
    print("="*60)
    
    # ЧИСТИМ ТОКЕН
    print("\n🔧 Очищаю токен...")
    VK_TOKEN = clean_token(RAW_TOKEN)
    
    if not VK_TOKEN:
        print("❌ Токен пустой!")
        input("\nНажми Enter для выхода...")
        return
    
    print(f"✅ Токен очищен! Длина: {len(VK_TOKEN)} символов")
    print(f"📌 Начинается с: {VK_TOKEN[:10]}...")
    
    # Подключаемся к ВК
    print("\n🔄 Авторизация в ВКонтакте...")
    
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    
    try:
        vk_session.auth()
        print("✅ Авторизация успешна!")
    except vk_api.AuthError as error_msg:
        print(f"❌ Ошибка авторизации: {error_msg}")
        print("\n💡 Возможные причины:")
        print("1. Токен протух (получи новый на vkhost.github.io)")
        print("2. Не те права (выбирай VK Admin)")
        print("3. Аккаунт заблокирован")
        input("\nНажми Enter для выхода...")
        return
    
    vk = vk_session.get_api()
    
    # Получаем инфу о пользователе
    try:
        user_info = vk.users.get()[0]
        print(f"👤 Авторизован как: {user_info['first_name']} {user_info['last_name']}")
    except Exception as e:
        print(f"❌ Не удалось получить инфу: {e}")
        input("\nНажми Enter для выхода...")
        return
    
    # ГРУЗИМ СООБЩЕСТВА
    print("\n📋 Загружаю твои сообщества...")
    
    try:
        groups = vk.groups.get(extended=1, filter='admin')
        groups_count = groups['count']
        
        if groups_count == 0:
            print("❌ Нет сообществ, где ты админ")
            input("\nНажми Enter для выхода...")
            return
        
        print(f"✅ Найдено сообществ: {groups_count}\n")
        print("📌 СООБЩЕСТВА ПО НОМЕРАМ:\n")
        
        groups_list = []
        for i, group in enumerate(groups['items'], 1):
            group_id = -group['id']
            domain = group.get('screen_name', 'нет домена')
            groups_list.append({
                'index': i,
                'id': group_id,
                'name': group['name'],
                'screen_name': domain
            })
            
            # Красивый вывод
            print(f"{i}. {group['name']}")
            if domain != 'нет домена':
                print(f"   🔗 vk.com/{domain} | ID: {group_id}")
            else:
                print(f"   ⚠️ Нет домена | ID: {group_id}")
            print()
        
        # ВЫБОР СООБЩЕСТВА
        while True:
            try:
                choice = int(input(f"🔢 Выбери номер (1-{groups_count}): "))
                if 1 <= choice <= groups_count:
                    selected = groups_list[choice-1]
                    SOURCE_GROUP_ID = selected['id']
                    DOMAIN_NAME = selected['screen_name']
                    
                    if DOMAIN_NAME == 'нет домена':
                        print("\n❌ У этого сообщества нет домена!")
                        input("\nНажми Enter для выхода...")
                        return
                    
                    print(f"\n✅ Выбрано: {selected['name']}")
                    print(f"📍 Домен: {DOMAIN_NAME}")
                    break
                else:
                    print("❌ Неверный номер")
            except ValueError:
                print("❌ Введи число!")
        
        # ID профиля
        TARGET_USER_ID = vk.users.get()[0]['id']
        print(f"👤 Профиль ID: {TARGET_USER_ID}")
        
        # ПОДТВЕРЖДЕНИЕ
        print("\n⚠️  ВНИМАНИЕ! Операция необратима!")
        confirm = input(f"\n🔴 Перенести домен '{DOMAIN_NAME}'? (да/нет): ")
        if confirm.lower() not in ['да', 'yes', 'y', 'lf', 'д']:
            print("❌ Отмена")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 1: Инфа о группе
        print("\n📦 [1/4] Сохраняю инфу...")
        try:
            group_info = vk.groups.getById(group_id=SOURCE_GROUP_ID)[0]
            old_name = group_info['name']
            print(f"   Старое название: {old_name}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 2: Снимаем домен
        print("\n🔄 [2/4] Снимаю домен с сообщества...")
        try:
            vk.groups.edit(
                group_id=abs(SOURCE_GROUP_ID),
                address=''
            )
            print("   ✅ Домен снят!")
            time.sleep(1)
        except ApiError as e:
            print(f"   ❌ Ошибка: {e}")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 3: Ставим на профиль
        print("\n📌 [3/4] Устанавливаю на профиль...")
        try:
            vk.account.setNameInMenu(name=DOMAIN_NAME)
            print(f"   ✅ Домен '{DOMAIN_NAME}' теперь твой!")
            time.sleep(1)
        except ApiError as e:
            print(f"   ❌ Ошибка: {e}")
            if "already used" in str(e).lower():
                print("   👤 Кто-то успел занять домен!")
            input("\nНажми Enter для выхода...")
            return
        
        # ШАГ 4: Меняем название и постим
        print("\n✏️ [4/4] Оформляю сообщество...")
        try:
            # Меняем название
            vk.groups.edit(
                group_id=abs(SOURCE_GROUP_ID),
                title='ZzZZZZz'
            )
            print("   ✅ Название → ZzZZZZz")
            
            # Постим
            try:
                vk.wall.post(
                    owner_id=SOURCE_GROUP_ID,
                    message='Темыч СВАПАЕТ =3',
                    from_group=1
                )
                print("   ✅ Пост 'Темыч СВАПАЕТ =3' опубликован!")
            except:
                print("   ⚠️ Не удалось опубликовать пост (стена закрыта?)")
                
        except ApiError as e:
            print(f"   ⚠️ Ошибка при оформлении: {e}")
        
        # ФИНАЛ
        print("\n" + "="*60)
        print("🎉 УСПЕХ! ОПЕРАЦИЯ ВЫПОЛНЕНА!")
        print("="*60)
        print(f"✅ Домен '{DOMAIN_NAME}' перенесен на профиль!")
        print("✅ Название сообщества: ZzZZZZz")
        print("✅ Пост: Темыч СВАПАЕТ =3")
        print("="*60)
        
    except ApiError as e:
        print(f"\n❌ Ошибка API: {e}")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    main()
