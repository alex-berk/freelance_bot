# freelance_bot
Scrapper that looks for intetersting tasks on freelance sites and sends Telegram message when it finds them

## enviroment variables
In order to work you'll need to setup:
* BOT_TOKEN 		_token of your bot, you can get it from [BotFather](https://t.me/botfather)_
* CHAT_ID 			_admin's telegram id_
* SECRET_TOKEN 		_token for flask encryption. You can generate with secrets.token_hex(16)_
* DASHBOARD_LOGIN	_login for the dashboard login_
* DASHBOARD_PASS	_pass for the dashboard login_

## parameters
You can run with parameter `parser` to run only parser part, `bot` to run only bot part or `dashboard` to run only dashboard part.
When running dashboard you can specify host and port with `-host` and `-port` arguments