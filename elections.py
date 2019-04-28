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

import difflib

import requests


SITE_BASE = "https://www.resultados.eleccionesgenerales19.es"
NOMENCLATOR = SITE_BASE + "/assets/nomenclator.json"
RESULTS = SITE_BASE + "/json/{t}/{t}{cod}.json"

CODES = {
    "congreso": "CO",
    "senado": "SE"
}


names = {
    "places": {},
    "parties": {}
}


def loadNomenclator():
    r = requests.get(NOMENCLATOR)

    if r.status_code != 200:
        raise Exception(f"Error dowloading nomenclator. HTTP Status: {r.status_code}")

    r.encoding = "utf-8"
    res = r.json()

    for code in CODES.values():
        names["places"][code] = {p["c"]: p["n"] for p in res["ambitos"][code.lower()]}
        names["parties"][code] = {p["codpar"]: (p["siglas"], p["nombre"]) for p in res["partidos"][code.lower()]["act"]}


def getPlaces(name, election, limit=4):
    if not name:
        name = "Total nacional"

    pos = difflib.get_close_matches(name, names["places"][CODES[election]].values(), n=limit)

    return {c: n for c, n in names["places"][CODES[election]].items() if n in pos}


def sortResults(r):
    return int(r["carg"]) if "carg" in r else int(r["vot"])


def getResults(code, election, limit=5):
    r = requests.get(RESULTS.format(t=CODES[election], cod=code))
    r.encoding = "utf-8"

    if r.status_code != 200:
        raise Exception(f"Failed getting '{election}' results for '{code}'. HTTP Status: {r.status_code}")

    res = r.json()

    act = []

    if "partotabla" in res:
        for ra in res["partotabla"]:
            if ra["act"]["codpar"] != "0000":
                rs = {
                    "party": names["parties"][CODES[election]][ra["act"]["codpar"]][0],
                    **ra["act"]
                }

                act.append(rs)

    elif "cantotabla" in res:
        limit *= 2
        for ra in res["cantotabla"]:
            if ra["codpar"] != "0000":
                rs = {
                    "party": names["parties"][CODES[election]][ra["codpar"]][0],
                    **ra
                }

                act.append(rs)

    act.sort(key=sortResults)

    return (res["totales"]["act"], act[:limit])


loadNomenclator()