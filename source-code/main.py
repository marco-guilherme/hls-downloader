'''
    Author: Marco Guilherme
    Date: 02/12/2025
'''

import requests
import re
import os
import argparse

from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import ParseResult

import constants

from utilities import url_utilities
from helpers import helpers

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

def downloadVideoSegments(absolutePathOutput: Path,
                          baseM3U8PlaylistURL: ParseResult,
                          videoSegments: List[str],
                          isVerbose: bool) -> None:
    segmentsURL: List[ParseResult] = []
    segmentPaths: List[Path] = []
    downloadStart: datetime = None
    downloadEnd: datetime = None
    downloadDuration: timedelta = None

    for videoSegment in videoSegments:
        newURL: ParseResult = url_utilities.parseURL(videoSegment)
        filename: str = url_utilities.getFilenameInURL(newURL)
        isRelativeURL: bool = not newURL.scheme.startswith("http")
        segmentPath: Path = Path(absolutePathOutput, filename)

        # 1080p.h264.mp4/seg-60-v1-a1.ts
        if(isRelativeURL):
            newURL = url_utilities.concatenateURL(baseM3U8PlaylistURL, videoSegment)
            segmentPath = Path(absolutePathOutput, videoSegment)

            os.makedirs(os.path.dirname(segmentPath), exist_ok=True)

            segmentsURL.append(newURL)
            segmentPaths.append(segmentPath)

    print("Starting segments download")

    downloadStart = datetime.now()

    with ThreadPoolExecutor(max_workers=30) as threadPoolExecutor:
        threadPoolExecutor.map(
            downloadAndSaveVideoSegment,
            segmentsURL,
            segmentPaths,
            [isVerbose] * len(segmentsURL)
        )

    downloadEnd = datetime.now()
    downloadDuration = downloadEnd - downloadStart

    print(f"Download elapsed time (seconds): {downloadDuration.total_seconds()}")

def downloadAndSaveVideoSegment(segmentURL: ParseResult, segmentPath: Path, isVerbose: bool) -> None:
    with requests.get(segmentURL.geturl()) as fileResponse:
        fileResponse.raise_for_status()

        with open(segmentPath, "wb") as segmentFile:
            segmentFile.write(fileResponse.content)

    if(isVerbose):
        print(f"Downloaded {segmentURL.geturl()} in {segmentPath}")

def handleHLS(masterFileURL: ParseResult, absolutePathOutput: Path, isVerbose: bool) -> None:
    baseURL: ParseResult = url_utilities.getBaseURL(masterFileURL)
    outputFileAbsolutePath: Path = Path(absolutePathOutput, constants.OUTPUT_FILENAME)

    print(f"Master file URL: {masterFileURL.geturl()}")

    if(isVerbose):
        print(f"Base URL: {baseURL.geturl()}")

    masterFileResponse: str = helpers.downloadAndSaveFile(
        masterFileURL,
        absolutePathOutput,
        constants.MASTER_FILENAME
    )

    bestVideoQuality: str = findBestVideoQuality(masterFileResponse)

    if(isVerbose):
        print("Best video quality playlist:", bestVideoQuality)

    bestM3U8PlaylistURL: ParseResult = url_utilities.concatenateURL(baseURL, bestVideoQuality)
    bestM3U8PlaylistParentURL: ParseResult = url_utilities.getBaseURL(bestM3U8PlaylistURL)

    if(isVerbose):
        print(f"Best resolution M3U8 playlist URL: {bestM3U8PlaylistURL.geturl()}")
        print(f"Best resolution M3U8 playlist parent URL (segment base): {bestM3U8PlaylistParentURL.geturl()}")

    bestM3U8PlaylistResponse: str = helpers.downloadAndSaveFile(bestM3U8PlaylistURL, absolutePathOutput, constants.PLAYLIST_FILENAME)

    videoSegments: List[str] = helpers.filterResponseBySuffix(bestM3U8PlaylistResponse, ".ts")

    if(isVerbose):
        for videoSegment in videoSegments:
            print(f"Video segment: {videoSegment}")

    downloadVideoSegments(
        absolutePathOutput,
        bestM3U8PlaylistParentURL,
        videoSegments,
        isVerbose
    )

    print("Concatenating segments of the video...")

    helpers.concatenateVideoSegments(absolutePathOutput)

    print(f"Video downloaded to {outputFileAbsolutePath}")
    print("Done")

def downloadUsingPlaylist(M3U8PlaylistURL: ParseResult, absolutePathOutput: Path, isVerbose: bool) -> None:
    originURL: ParseResult = url_utilities.getOriginURL(M3U8PlaylistURL)
    bestM3U8PlaylistResponse: str = helpers.downloadAndSaveFile(M3U8PlaylistURL, absolutePathOutput, constants.PLAYLIST_FILENAME)
    outputFileAbsolutePath: Path = Path(absolutePathOutput, constants.OUTPUT_FILENAME)

    print(f"Origin URL: {originURL.geturl()}")

    videoSegments: List[str] = helpers.filterResponseBySuffix(bestM3U8PlaylistResponse, ".ts")

    if(isVerbose):
        for videoSegment in videoSegments:
            print(f"Video segment: {videoSegment}")

    downloadVideoSegments(
        absolutePathOutput,
        originURL,
        videoSegments,
        isVerbose
    )

    print("Concatenating segments of the video...")

    helpers.concatenateVideoSegments(absolutePathOutput, isVerbose)

    print(f"Video downloaded to {outputFileAbsolutePath}")
    print("Done")

def parseCommandLineArguments() -> argparse.Namespace:
    argumentParser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="HLS downloader"
    )

    argumentParser.add_argument(
        "master_file_url",
        type = url_utilities.parseURL,
        help = "Master file URL (M3U8)"
    )

    argumentParser.add_argument(
        "-o",
        "--absolute_path_output",
        type = Path,
        help = "Absolute path to the directory where the downloaded file will be stored"
    )

    argumentParser.add_argument(
        "-v",
        "--verbose",
        action = "store_true",
        help = "Enable verbose output"
    )

    return argumentParser.parse_args()

def main() -> None:
    parsedCommandLineArguments: argparse.Namespace = parseCommandLineArguments()

    masterFileURL: ParseResult = parsedCommandLineArguments.master_file_url
    absolutePathOutput: Path = helpers.getDefaultAbsolutePathOutput()
    isVerbose: bool = parsedCommandLineArguments.verbose

    if(parsedCommandLineArguments.absolute_path_output):
        absolutePathOutput = parsedCommandLineArguments.absolute_path_output

    absolutePathOutput.mkdir(exist_ok=True)

    # handleHLS(masterFileURL, absolutePathOutput, isVerbose)

    M3U8PlaylistURL: ParseResult = masterFileURL

    downloadUsingPlaylist(M3U8PlaylistURL, absolutePathOutput, isVerbose)

if(__name__ == "__main__"):
    main()
