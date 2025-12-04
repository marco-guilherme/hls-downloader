'''
    Author: Marco Guilherme
    Date: 02/12/2025
'''

import requests
import re
import os

from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import constants

MASTER_FILE_URL: str = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
OUTPUT_PATH: Path = Path(Path(__file__).parent.parent, "output") # ..\output

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

def findBestVideoQuality(masterFileContent: str) -> str:
    lines: List[str] = masterFileContent.splitlines()
    index: int = 0
    bestResolutionPlaylist: str = ''
    bestHeight: int = -1

    while(index < len(lines)):
        currentLine: str = lines[index]
        hasNextLine: bool = index < (len(lines) - 1)
        nextLine: str = ''

        if(hasNextLine):
            nextLine = lines[index + 1]

        if(currentLine.startswith("#EXT-X-STREAM-INF") and hasNextLine):
            nameMatch: (re.Match[str] | None) = re.search(r'NAME="([^"]+)"', currentLine)
            qualityMatch: (re.Match[str] | None) = None

            if(nameMatch):
                qualityValue: str = nameMatch.group(1) # 1080 ou 1080p
                qualityMatch = re.search(r"(\d+)", qualityValue)
            else:
                qualityMatch = re.search(r"(\d+)p", nextLine)

            if(qualityMatch):
                height: int = int(qualityMatch.group(1))

                if(height > bestHeight):
                    bestHeight = height
                    bestResolutionPlaylist = nextLine

        index += 1

    print(f"Best quality: {bestHeight}")

    return bestResolutionPlaylist

def downloadVideoSegments(baseM3U8PlaylistURL: str, videoSegments: List[str]) -> None:
    segmentsURL: List[str] = []
    segmentPaths: List[Path] = []

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

        segmentsURL.append(newURL)
        segmentPaths.append(segmentPath)

    print("Starting segments download")

    with ThreadPoolExecutor(max_workers=30) as threadPoolExecutor:
        threadPoolExecutor.map(downloadAndSaveSegment, segmentsURL, segmentPaths)

def downloadAndSaveSegment(segmentURL: str, segmentPath: Path) -> None:
    with open(segmentPath, "wb") as segmentFile:
        segmentFile.write(requests.get(segmentURL).content)

    print(f"Downloaded {segmentURL} in {segmentPath}")

def main() -> None:
    baseURL: str = getBaseURL(MASTER_FILE_URL)

    print(f"Master file URL: {MASTER_FILE_URL}")
    print(f"Base URL: {baseURL}")

    masterFileResponse: str = downloadAndSaveFile(MASTER_FILE_URL, OUTPUT_PATH, constants.MASTER_FILENAME)

    bestVideoQuality: str = findBestVideoQuality(masterFileResponse)

    print("Best video quality playlist:", bestVideoQuality)

    bestM3U8PlaylistURL: str = getBaseURL(MASTER_FILE_URL) + bestVideoQuality
    bestM3U8PlaylistParentURL: str = getBaseURL(bestM3U8PlaylistURL)

    print(f"Best resolution M3U8 playlist URL: {bestM3U8PlaylistURL}")
    print(f"Best resolution M3U8 playlist parent URL (segment base): {bestM3U8PlaylistParentURL}")

    bestM3U8PlaylistResponse: str = downloadAndSaveFile(bestM3U8PlaylistURL, OUTPUT_PATH, constants.PLAYLIST_FILENAME)

    videoSegments: List[str] = filterResponseBySuffix(bestM3U8PlaylistResponse, ".ts")

    for videoSegment in videoSegments:
        print(f"Video segment: {videoSegment}")

    downloadVideoSegments(bestM3U8PlaylistParentURL, videoSegments)

if(__name__ == "__main__"):
    main()
