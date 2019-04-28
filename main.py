# spanish-elections-bot
# Copyright (C) 2019, Sergio Conde Gomez <skgsergio@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import logging

import elections

import telebot
from telebot import types


logger = telebot.logger
logger.setLevel(logging.INFO)

with open("token.txt") as f:
    bot = telebot.TeleBot(f.readline().strip())

username = bot.get_me().username


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, f"Soy un bot inline, escribe en cualquier chat @{username} y te saldrá un menú.\n\nNo necesito estar en grupo para funcionar.")


@bot.inline_handler(lambda q: True)
def query_text(q):
    try:
        qs = q.query.split(" ")

        if qs[0] not in elections.CODES.keys():
            bot.answer_inline_query(q.id, [
                types.InlineQueryResultArticle(
                    "None",
                    f"Indica la elección: {', '.join(elections.CODES.keys())}",
                    types.InputTextMessageContent(f"No se ha especificado la elección.\n\nDisponibles: {', '.join(elections.CODES.keys())}")
                )
            ])

        else:
            election = qs[0]
            places = elections.getPlaces(" ".join(qs[1:]), election)

            r = []
            for cod, place in places.items():
                res = elections.getResults(cod, election)

                title = f"{place} ({cod})"
                r.append(types.InlineQueryResultArticle(
                    hashlib.sha256(title.encode('utf-8')).hexdigest(),
                    title,
                    resMessage(election, place, res)
                ))

            bot.answer_inline_query(q.id, r)

    except Exception as e:
        logger.error(e)


def resMessage(election, place, res):
    s = f"Resultados <i>{election}</i> en <b>{place}</b> al <i>{res[0]['pcenes']}</i>\n\n"

    s += f"<b>Participación</b>: {res[0]['pvotant']} [<i>{res[0]['dpvotant']}</i>]\n\n"

    s += f"<b>Abstención</b>: {res[0]['pabsten']} [<i>{res[0]['dpabsten']}</i>]\n"
    s += f"<b>Nulos</b>: {res[0]['pvotnul']} [<i>{res[0]['dpvotnul']}</i>]\n"
    s += f"<b>En Blanco</b>: {res[0]['pvotbla']} [<i>{res[0]['dpvotbla']}</i>]\n"

    s += f"\nLas <b>{len(res[1])}</b> candidaturas más votadas:\n"

    for r in res[1]:
        if "nomcan" in r:
            s += f"\n<b>{r['party']}</b> (<i>{r['nomcan']} {r['apecan']}</i>):"
        else:
            s += f"\n<b>{r['party']}</b>:"

        if "carg" in r:
            s += f" {r['carg']} [<i>{r['dcarg']}</i>]"

        if "carg" in r and "vot" in r:
            s += " |"

        if "vot" in r:
            s += f" {r['vot']} ({r['pvot']})"

            if "dvot" in r:
                s += f" [<i>{r['dvot']}</i> (<i>{r['dpvot']}</i>)]"

    return types.InputTextMessageContent(s, parse_mode="HTML")


bot.polling()
