'''
    Autor: Marco Guilherme
    Data: 02/12/2025
'''

import requests
import re
import os

from typing import List
from pathlib import Path

# Master: ele lista várias versões do mesmo vídeo em diferentes qualidades e resoluções
MASTER_FILE_URL: str = ""
OUTPUT_PATH: Path = Path(r".")
MASTER_FILENAME: str = "master.m3u8"
PLAYLIST_FILENAME: str = "playlist.m3u8"

def downloadFileContent(fileURL: str) -> str:
    with requests.get(fileURL) as fileResponse:
        fileResponse.raise_for_status()

        return fileResponse.text

def writeFile(outputPath: Path, filename: str, fileContent: str) -> None:
    with open(Path(outputPath, filename), 'w', encoding="utf-8") as fileOutput:
        fileOutput.write(fileContent)

def getBaseURL(fullURL: str) -> str:
    return fullURL.rsplit('/', 1)[0] + '/'

def getFilenameInURL(fullURL: str) -> str:
    return fullURL.rsplit('/', 1).pop()

def filterResponseBySuffix(requestResponse: str, suffix: str) -> List[str]:
    filteredLines: List[str] = []
    lines: List[str] = requestResponse.splitlines()

    for fileLine in lines:
        if(not fileLine.endswith(suffix)):
            continue

        filteredLines.append(fileLine)

    return filteredLines

def downloadAndSaveFile(fileURL: str, outputPath: Path, outputFilename: str) -> str:
    fileContent: str = downloadFileContent(fileURL)

    writeFile(outputPath, outputFilename, fileContent)

    return fileContent

# ---------------

def findBestVideoQuality(resolutions: List[str]) -> str:
    if(not len(resolutions)):
        raise Exception("Empty qualities")

    bestResolution: str = ""
    bestHeight: int = -1

    for resolution in resolutions:
        match: (re.Match[str] | None) = re.search(r"(\d+)p", resolution)

        if(not match):
            continue

        height: int = int(match.group(1))

        if(height > bestHeight):
            bestHeight = height
            bestResolution = resolution

    return bestResolution

def downloadVideoSegments(baseM3U8PlaylistURL: str, videoSegments: List[str]) -> None:
    for videoSegment in videoSegments:
        newURL: str = videoSegment
        filename: str = getFilenameInURL(videoSegment)
        isRelativeURL: bool = not videoSegment.startswith("http")
        segmentPath: Path = Path(OUTPUT_PATH, filename)

        # 1080p.h264.mp4/seg-60-v1-a1.ts
        if(isRelativeURL):
            newURL = f"{baseM3U8PlaylistURL}{videoSegment}"
            segmentPath = Path(OUTPUT_PATH, videoSegment)

        os.makedirs(os.path.dirname(segmentPath), exist_ok=True)

        print(f"Downloading {newURL} in {segmentPath}")

        with open(segmentPath, "wb") as segmentFile:
            segmentFile.write(requests.get(newURL).content)

def main() -> None:
    baseURL: str = getBaseURL(MASTER_FILE_URL)

    print(f"Master file URL: {MASTER_FILE_URL}")
    print(f"Base URL: {baseURL}")

    masterFileResponse: str = downloadAndSaveFile(MASTER_FILE_URL, OUTPUT_PATH, MASTER_FILENAME)

    videoQualities: List[str] = filterResponseBySuffix(masterFileResponse, ".m3u8")

    for quality in videoQualities:
        print(f"Quality: {quality}")

    bestVideoQuality: str = findBestVideoQuality(videoQualities)

    print("Best video quality", bestVideoQuality)

    bestM3U8PlaylistURL: str = getBaseURL(MASTER_FILE_URL) + bestVideoQuality

    print(f"Best resolution M3U8 playlist URL: {bestM3U8PlaylistURL}")

    bestM3U8PlaylistResponse: str = downloadAndSaveFile(bestM3U8PlaylistURL, OUTPUT_PATH, PLAYLIST_FILENAME)

    videoSegments: List[str] = filterResponseBySuffix(bestM3U8PlaylistResponse, ".ts")

    for videoSegment in videoSegments:
        print(f"Video segment: {videoSegment}")

    downloadVideoSegments(baseURL, videoSegments)

if(__name__ == "__main__"):
    main()
