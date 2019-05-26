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
LINK = SITE_BASE + "/{section}/{i}/es"
TOTAL_NAME = "Total nacional"

CODES = {
    "congreso": "CO",
    "senado": "SE"
}

CODES_NOMENCLATOR = {
    "CO": "co",
    "SE": "se"
}

SECTIONS = {
    "avances": "Avances",
    "congreso": "Congreso",
    "senado": "Senado"
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
        names["places"]["names"][code] = {p["n"] for p in res["ambitos"][CODES_NOMENCLATOR[code]]}
        names["places"]["data"][code] = {p["c"]: {"name": p["n"], "level": res["constantes"]["level"][str(p["l"])], "i": p["i"]} for p in res["ambitos"][CODES_NOMENCLATOR[code]]}
        names["parties"][code] = {p["codpar"]: (p["siglas"], p["nombre"]) for p in res["partidos"][CODES_NOMENCLATOR[code]]["act"]}


def getLink(section, i):
    return LINK.format(section=SECTIONS[section], i=i)


def getPlaces(name, section, limit=4):
    if section == "avances":
        section = CODES.keys()[0]

    if not name:
        pos = [TOTAL_NAME]

    else:
        pos = difflib.get_close_matches(name, names["places"]["names"][CODES[section]], n=limit)

    return {c: d for c, d in names["places"]["data"][CODES[section]].items() if d["name"] in pos}


def sortResults(r):
    return int(r["carg"]) if "carg" in r else int(r["vot"])


def getResults(code, section, limit=8):
    r = requests.get(RESULTS.format(t=CODES[section], cod=code))
    r.encoding = "utf-8"

    if r.status_code != 200:
        raise Exception(f"Failed getting '{section}' results for '{code}'. HTTP Status: {r.status_code}")

    res = r.json()

    act = []

    if "partotabla" in res:
        for ra in res["partotabla"]:
            if ra["act"]["codpar"] != "0000":
                rs = {
                    "party": names["parties"][CODES[section]][ra["act"]["codpar"]][0],
                    **ra["act"]
                }

                act.append(rs)

    elif "cantotabla" in res:
        for ra in res["cantotabla"]:
            if ra["codpar"] != "0000":
                rs = {
                    "party": names["parties"][CODES[section]][ra["codpar"]][0],
                    **ra
                }

                act.append(rs)

    act.sort(key=sortResults, reverse=True)

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
