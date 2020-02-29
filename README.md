# freelance_bot
Scrapper that looks for intetersting tasks on freelance sites and sends Telegram message when it finds them

## enviroment variables
In order to work you'll need to setup:
* BOT_TOKEN 		(token of your bot, you cang get it from [BotFather](https://t.me/botfather))
* CHAT_ID 			admin's telegram id
* SECRET_TOKEN 		just generate with secrets.token_hex(16)
* DASHBOARD_LOGIN	login for the dashboard login
* DASHBOARD_PASS	pass for the dashboard login

## parameters
You can run with parameter `parser` to run only parser part, `bot` to run only bot part or `dashboard` to run only dashboard part.
When running dashboard you can specify host and port with `-host` and `-port` arguments