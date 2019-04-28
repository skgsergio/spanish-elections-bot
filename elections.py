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
AV = SITE_BASE + "/json/AV/CO{cod}.json"

CODES = {
    "congreso": "CO",
    "senado": "SE"
}


names = {
    "places": {
        "names": {},
        "data": {}
    },
    "parties": {
        "names": {},
        "data": {}
    }
}


def loadNomenclator():
    r = requests.get(NOMENCLATOR)

    if r.status_code != 200:
        raise Exception(f"Error dowloading nomenclator. HTTP Status: {r.status_code}")

    r.encoding = "utf-8"
    res = r.json()

    for code in CODES.values():
        names["places"]["names"][code] = {p["n"] for p in res["ambitos"][code.lower()]}
        names["places"]["data"][code] = {p["c"]: (p["n"], res["constantes"]["level"][str(p["l"])]) for p in res["ambitos"][code.lower()]}
        names["parties"][code] = {p["codpar"]: (p["siglas"], p["nombre"]) for p in res["partidos"][code.lower()]["act"]}


def getPlaces(name, election, limit=4):
    if election == "avances":
        election = "congreso"

    if not name:
        pos = ["Total nacional"]

    else:
        pos = difflib.get_close_matches(name, names["places"]["names"][CODES[election]], n=limit)

    return {c: n for c, n in names["places"]["data"][CODES[election]].items() if n[0] in pos}


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


def getAV(code):
    r = requests.get(AV.format(cod=code))
    r.encoding = "utf-8"

    if r.status_code != 200:
        raise Exception(f"Failed getting 'AV' results for '{code}'. HTTP Status: {r.status_code}")

    res = r.json()

    act = []

    for av in res["avans"]:
        if av["mesas"]["meava"] != "0":
            act.append(av["act"])

    return act


loadNomenclator()
