import os
from collections import namedtuple

User = namedtuple('User', ['chat_id', 'keywords'])

usr1 = User(os.environ['CHAT_ID'], ['python', 'питон', 'пайтон', 'парс', 'парсер', 'спарсить', 'парсинг', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть', 'analytics', 'аналитикс', 'метрика', 'metrica', 'metrika', 'gtm', 'bi', 'query'])
usr2 = User(os.environ['ADDITIONAL_ID'], ['php', 'пхп', 'js', 'javascript', 'script', 'angular', 'ux', 'ui', 'linux', 'unix', 'worpress', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть'])

users = [usr1, usr2]
