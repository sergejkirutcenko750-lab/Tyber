import requests

VK_VERSION = "5.199"
token = input("Вставь токен VK: ").strip()

r = requests.get("https://api.vk.com/method/users.get", params={'access_token': token, 'v': VK_VERSION})
data = r.json()
print("Ответ от ВК:")
print(data)
input("Нажми Enter...")
