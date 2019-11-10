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


CACHE_TIME = 30


logger = telebot.logger
logger.setLevel(logging.INFO)

with open("token.txt") as f:
    bot = telebot.TeleBot(f.readline().strip())

username = bot.get_me().username

logger.info(f"Bot: @{username}")


@bot.message_handler(commands=["start", "help"])
def i_am_inline(m):
    bot.reply_to(m, f"Soy un bot inline, escribe en cualquier chat @{username} y te saldrá un menú.\n\nNo necesito estar en grupo para funcionar.")


@bot.message_handler(content_types=["new_chat_members"])
def i_dont_like_groups(m):
    try:
        logger.info(f"Leaving: {m.chat.title} ({m.chat.id})")
        bot.leave_chat(m.chat.id)

    except Exception as e:
        logger.error(e)


@bot.inline_handler(lambda q: True)
def query_elections(q):
    try:
        qs = q.query.split(" ")
        section = qs[0]
        query = " ".join(qs[1:])

        if section not in elections.CODES.keys() and section != "avances":
            bot.answer_inline_query(q.id, [
                types.InlineQueryResultArticle(
                    "None",
                    "Escribe que dato quieres consultar:",
                    types.InputTextMessageContent(f"No has especificado el dato a consultar: {', '.join(elections.CODES.keys())}, avances"),
                    description=f"{', '.join(elections.CODES.keys())}, avances"
                )
            ])

        elif section == "avances":
            places = elections.getPlaces(query, section)

            logger.info(f"[{q.from_user.id}][{q.from_user.first_name} {q.from_user.last_name} @{q.from_user.username}]: {section} {query} - Results: {[p['name'] for p in places.values()]}")

            r = []
            for cod, place in places.items():
                res = elections.getAV(cod)

                title = f"{place['name']} ({cod})"
                r.append(types.InlineQueryResultArticle(
                    hashlib.sha256(section.encode("utf-8") + title.encode("utf-8")).hexdigest(),
                    title,
                    format_av(place, res),
                    description=f"{place['level']}"
                ))

            bot.answer_inline_query(q.id, r, cache_time=CACHE_TIME)

        else:
            places = elections.getPlaces(query, section)

            logger.info(f"[{q.from_user.id}][{q.from_user.first_name} {q.from_user.last_name} @{q.from_user.username}]: {section} {query} - Results: {[p['name'] for p in places.values()]}")

            r = []
            for cod, place in places.items():
                res = elections.getResults(cod, section)

                title = f"{place['name']} ({cod})"
                r.append(types.InlineQueryResultArticle(
                    hashlib.sha256(section.encode("utf-8") + title.encode("utf-8")).hexdigest(),
                    title,
                    format_res(section, place, res),
                    description=f"{place['level']}"
                ))

            bot.answer_inline_query(q.id, r, cache_time=CACHE_TIME)

    except Exception as e:
        logger.error(e)


def format_res(section, place, res):
    s = f"Resultados <i>{section}</i> en <b>{place['name']}</b> (<i>{place['level']}</i>) al <b>{res[0]['pcenes']}</b> escrutado\n\n"

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

    s += f"\n\n<a href=\"{elections.getLink(section, place['i'])}\">Ver datos</a>"

    return types.InputTextMessageContent(s, parse_mode="HTML")


def format_av(place, res):
    s = f"Avances de participación en <b>{place['name']}</b>\n"

    if res:
        for r in res:
            s += f"\n• {r['vava']} ({r['pvava']}) [<i>{r['dvava']}</i> (<i>{r['dpvava']}</i>)]"
    else:
        s += f"\n• Aún no hay avances de participación"

    return types.InputTextMessageContent(s, parse_mode="HTML")


bot.polling()
