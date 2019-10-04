import os
import re
from flask import Flask, request
import psycopg2
import telebot
from telebot import *

TOKEN = ''
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


def generaMencion(usuario):
	mencion = ""
	if usuario.username is None:
		nombre = usuario.first_name

		if usuario.last_name is not None:
			nombre += " " + usuario.last_name

		mencion = "[{}](tg://user?id={})".format(nombre, usuario.id)

	else:
		mencion =  "[@{}](tg://user?id={})".format(usuario.username, usuario.id)

	return mencion


def conectar_bd():
	DATABASE_URL = os.environ['DATABASE_URL']
	conn = psycopg2.connect(DATABASE_URL, sslmode='require')
	cursor = conn.cursor()

	return conn, cursor


@bot.message_handler(commands=['start'])
def send_welcome(message):
	cid = message.chat.id

	bot.send_message(cid, "Bienvenido a Llamame+Bot")


@bot.message_handler(commands=['llamame'])
def anadiralabd(message):
	chat = message.chat
	user = message.from_user
	uid = user.id
	mid = message.message_id
	cid = chat.id
	chattpye = chat.type

	if chattpye == "group" or chattpye == "supergroup":
		conn, cursor = conectar_bd()

		cursor.execute("SELECT * FROM pertenece WHERE id={} and cid={}".format(uid, cid))
		row = cursor.fetchone()

		if row is None:
			fn = user.first_name
			ln = user.last_name
			username = user.username

			cursor.execute(f"SELECT * FROM usuario WHERE id={uid}")
			usuario = cursor.fetchone()

			if usuario is None:
				cursor.execute(f"INSERT INTO usuario VALUES ({uid},'{fn}','{ln}','{username}')")

			cursor.execute(f"SELECT * FROM chat WHERE cid={cid}")
			ch = cursor.fetchone()

			if ch is None:
				titulo = chat.title
				cursor.execute(f"INSERT INTO chat VALUES ({cid},'{titulo}')")

			cursor.execute(f"INSERT INTO pertenece VALUES({uid},{cid})")

			bot.send_message(chat_id=cid, text="{} has sido registrado en la base de datos de este grupo con éxito.".format(generaMencion(user)), parse_mode="Markdown")
		else:
			bot.send_message(chat_id=cid, text="{} te registré en la base de datos de este grupo antes.".format(generaMencion(user)), parse_mode="Markdown")

		conn.commit()
		conn.close()
	else:
		bot.send_message(cid, "Esto deberías de ponerlo en el grupo desde donde quieres que te llame.")

	bot.delete_message(cid, mid)


@bot.message_handler(commands=['llamar'])
def llamar(message):
	chat = message.chat
	user = message.from_user
	uid = user.id
	mid = message.message_id
	cid = chat.id
	chattpye = chat.type

	if chattpye == "group" or chattpye == "supergroup":
		entrada = message.text.split()
		entrada = entrada[1::]
		mensaje = "{} os dice: ".format(generaMencion(user))

		for palabra in entrada:
			mensaje += palabra + " "

		conn, cursor = conectar_bd()

		cursor.execute(f"SELECT usuario.id FROM usuario, pertenece WHERE usuario.id=pertenece.id AND pertenece.cid={cid}")
		usuarios = cursor.fetchall()

		conn.commit()
		conn.close()

		if usuarios is None:
			bot.send_message(cid, "No hay nadie en la lista de llamamientos.")
		else:
			menciones = ""
			for usuario in usuarios:
				us = bot.get_chat_member(cid, usuario[0]).user

				menciones += generaMencion(us)

				if usuario != usuarios[len(usuarios)-1]:
					menciones += " - "

		if len(menciones) > 0:
			if len(entrada) > 0:
				bot.send_message(chat_id=cid, text=mensaje + "\n" + menciones, parse_mode="Markdown")
			else:
				bot.send_message(chat_id=cid, text=menciones, parse_mode="Markdown")
		else:
			bot.send_message(chat_id=cid, text="No hay nadie en la lista de llamamientos.", parse_mode="Markdown")

	else:
		bot.send_message(cid, "Eso debes de ponerlo por un grupo.")

	bot.delete_message(cid, mid)



@bot.message_handler(commands=['nomellames'])
def nollamar(message):
	chat = message.chat
	user = message.from_user
	uid = user.id
	mid = message.message_id
	cid = chat.id
	chattype = chat.type

	if chattype == "private":
		conn, cursor = conectar_bd()

		cursor.execute(f"SELECT chat.cid, chat.title FROM chat, pertenece WHERE chat.cid=pertenece.cid AND pertenece.id={uid}")
		grupos = cursor.fetchall()

		if len(grupos) > 0:
			menuKeyboard = types.InlineKeyboardMarkup()

			for grupo in grupos:
				menuKeyboard.add(types.InlineKeyboardButton(grupo[1], callback_data=grupo[0]))

			bot.send_message(chat_id=cid, text="Seleccione el grupo desde el que desea no ser llamado.", parse_mode="Markdown", reply_markup=menuKeyboard)

		conn.commit()
		conn.close()
	else:
		bot.send_message(chat_id=cid, text="{} eso me lo tienes que decir por privado".format(generaMencion(user)), parse_mode="Markdown")

	bot.delete_message(cid, mid)


@bot.callback_query_handler(func=lambda call: call.data is not None)
def callback_handlerMenu(call):
	cid = call.message.chat.id
	mid = call.message.message_id
	info = call.data

	conn, cursor = conectar_bd()

	cursor.execute(f"SELECT title FROM chat WHERE cid={info}")
	nombre = cursor.fetchone()
	bot.edit_message_text(chat_id=cid, message_id=mid, text="De acuerdo, no te llamaré en el grupo {}".format(nombre[0]))

	cursor.execute(f"DELETE FROM pertenece WHERE cid={info} AND id={cid}")

	conn.commit()
	conn.close()


@bot.message_handler(commands=['creditos'])
def enviar_creditos(message):
	cid = message.chat.id
	mid = message.message_id
	user = message.from_user

	bot.send_message(chat_id=cid, text="{} este bot existe gracias a: 🦉\n\n-@ManuJNR: programador del bot.\n\n-@IgnasiCR: creador de la primera version del bot en la cual me he basado y he eliminado todos los problemas.".format(generaMencion(user)), parse_mode="Markdown")
	bot.delete_message(cid, mid)


@bot.message_handler(commands=['github'])
def enviar_creditos(message):
	cid = message.chat.id
	mid = message.message_id
	user = message.from_user

	bot.send_message(chat_id=cid, text="{} mi GitHub es [ManuelJNunez](https://github.com/ManuelJNunez)".format(generaMencion(user)), parse_mode="Markdown")
	bot.delete_message(cid, mid)


@bot.message_handler(func=lambda message: True, content_types=['left_chat_member'])
def adios(message):
	cid = message.chat.id
	user = message.left_chat_member
	uid = user.id

	conn, cursor = conectar_bd()

	cursor.execute(f"SELECT * FROM pertenece WHERE id={uid} AND cid={cid}")
	usuario = cursor.fetchone()

	if usuario is not None:
		despedida = "{} ha salido del grupo, lo he eliminado de la lista de llamamientos.".format(generaMencion(user))
		cursor.execute(f"DELETE FROM pertenece WHERE cid={cid} AND id={uid}")
		bot.send_message(chat_id=cid, text=despedida, parse_mode="Markdown")

	conn.commit()
	conn.close()



@bot.message_handler(func=lambda message: True, content_types=['new_chat_members'])
def hola(message):
	cid = message.chat.id
	user = message.new_chat_member

	bot.send_message(chat_id=cid, text="Hola {} si desea ser añadido a la lista de llamamientos de este grupo usa /llamame".format(generaMencion(user)), parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def respuestas(message):
	cid = message.chat.id
	mensaje = message.text.lower()

	if re.search("golfo", mensaje) is not None or re.search("golfito", mensaje):
		bot.send_message(cid, "Buff 🐶")
	if re.search("oki", mensaje) is not None:
		bot.send_message(cid, "Oki, oki.")
	if re.search("python", mensaje) is not None:
		bot.send_photo(cid, "https://i.imgur.com/hdbXhTT.png")


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://llamameplus.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
