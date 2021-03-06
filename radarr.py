#!/usr/bin/env python3

import json
import logging

import requests

import commons as commons
from config import config

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logging.getLogger("tadarr")

config = config["radarr"]

addMovieNeededFields = ["tmdbId", "year", "title", "titleSlug", "images"]


def search(title):
    parameters = {"term": title}
    req = requests.get(commons.generateApiQuery("radarr", "movie/lookup", parameters))
    parsed_json = json.loads(req.text)

    if req.status_code == 200 and parsed_json:
        return parsed_json
    else:
        return False


def giveTitles(parsed_json):
    data = []
    for movie in parsed_json:
        if all(
            x in movie for x in ["title", "overview", "remotePoster", "year", "tmdbId"]
        ):
            data.append(
                {
                    "title": movie["title"],
                    "overview": movie["overview"],
                    "poster": movie["remotePoster"],
                    "year": movie["year"],
                    "id": movie["tmdbId"],
                }
            )
    return data


def inLibrary(tmdbId):
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "movie", parameters))
    parsed_json = json.loads(req.text)
    return next((True for movie in parsed_json if movie["tmdbId"] == tmdbId), False)


def addToLibrary(tmdbId, path):
    parameters = {"tmdbId": str(tmdbId)}
    req = requests.get(
        commons.generateApiQuery("radarr", "movie/lookup/tmdb", parameters)
    )
    parsed_json = json.loads(req.text)
    data = json.dumps(buildData(parsed_json, path))
    add = requests.post(commons.generateApiQuery("radarr", "movie"), data=data, headers={'Content-Type': 'application/json'})
    parsed_json = json.loads(add.text)
    if add.status_code == 201:
        return parsed_json["id"]
    else:
        return False

def manualImport(path, id):
    data = json.dumps(buildImportData(path, id))
    print(data)
    add = requests.post(commons.generateApiQuery("radarr", "command"), data=data, headers={'Content-Type': 'application/json'})
    print(add.text)
    if add.status_code == 201:
        return True
    else:
        return False


def buildImportData(path, id):
    data = {
        "name": "ManualImport",
        "importMode": "move",
        "files": [{
            "path":path,
            "movieId": id,
            "quality":{"quality":{"id":0,"name":"Unknown","source":"unknown","resolution":0,"modifier":"none"},"revision":{"version":1,"real":0}},
            "languages":[{"id":1,"name":"English","nameLower":"english"}]
            }]
        }
    return data

def buildData(json, path):
    built_data = {
        "qualityProfileId": config["qualityProfileId"],
        "minimumAvailability": "announced",
        "rootFolderPath": path,  # config["rootFolder"],
        "addOptions": {"searchForMovie": False},
    }

    for key in addMovieNeededFields:
        built_data[key] = json[key]
    return built_data


def getRootFolders():
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "Rootfolder", parameters))
    parsed_json = json.loads(req.text)
    logger.debug(f"Found Radarr paths: {parsed_json}")
    return parsed_json
