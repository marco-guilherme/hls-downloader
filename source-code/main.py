'''
    Author: Marco Guilherme
    Date: 02/12/2025
'''

import requests
import re
import os
import subprocess
import argparse

from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import constants

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

def downloadVideoSegments(absolutePathOutput: Path, baseM3U8PlaylistURL: str, videoSegments: List[str], isVerbose: bool) -> None:
    segmentsURL: List[str] = []
    segmentPaths: List[Path] = []
    downloadStart: datetime = None
    downloadEnd: datetime = None
    downloadDuration: timedelta = None

    for videoSegment in videoSegments:
        newURL: str = videoSegment
        filename: str = getFilenameInURL(videoSegment)
        isRelativeURL: bool = not videoSegment.startswith("http")
        segmentPath: Path = Path(absolutePathOutput, filename)

        # 1080p.h264.mp4/seg-60-v1-a1.ts
        if(isRelativeURL):
            newURL = f"{baseM3U8PlaylistURL}{videoSegment}"
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

def downloadAndSaveVideoSegment(segmentURL: str, segmentPath: Path, isVerbose: bool) -> None:
    with requests.get(segmentURL) as fileResponse:
        fileResponse.raise_for_status()

        with open(segmentPath, "wb") as segmentFile:
            segmentFile.write(fileResponse.content)

    if(isVerbose):
        print(f"Downloaded {segmentURL} in {segmentPath}")

def isFFmpegInstalled() -> bool:
    command: List[str] = [
        "ffmpeg",
        "-version"
    ]

    try:
        subprocess.run(
            command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            check = True
        )

        return True

    except Exception:
        return False

def concatenateVideoSegments(absolutePathOutput: Path) -> None:
    if(not isFFmpegInstalled()):
        raise FileNotFoundError("FFmpeg not found in system path")

    command: List[str] = [
        "ffmpeg",
        "-i",
        f".\\{constants.PLAYLIST_FILENAME}",
        "-c",
        "copy",
        f".\\{constants.OUTPUT_FILENAME}"
    ]

    subprocess.run(
        command,
        cwd=absolutePathOutput,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def handleHLS(masterFileURL: str, absolutePathOutput: Path, isVerbose: bool) -> None:
    baseURL: str = getBaseURL(masterFileURL)
    outputFileAbsolutePath: Path = Path(absolutePathOutput, constants.OUTPUT_FILENAME)

    print(f"Master file URL: {masterFileURL}")

    if(isVerbose):
        print(f"Base URL: {baseURL}")

    masterFileResponse: str = downloadAndSaveFile(masterFileURL, absolutePathOutput, constants.MASTER_FILENAME)

    bestVideoQuality: str = findBestVideoQuality(masterFileResponse)

    if(isVerbose):
        print("Best video quality playlist:", bestVideoQuality)

    bestM3U8PlaylistURL: str = getBaseURL(masterFileURL) + bestVideoQuality
    bestM3U8PlaylistParentURL: str = getBaseURL(bestM3U8PlaylistURL)

    if(isVerbose):
        print(f"Best resolution M3U8 playlist URL: {bestM3U8PlaylistURL}")
        print(f"Best resolution M3U8 playlist parent URL (segment base): {bestM3U8PlaylistParentURL}")

    bestM3U8PlaylistResponse: str = downloadAndSaveFile(bestM3U8PlaylistURL, absolutePathOutput, constants.PLAYLIST_FILENAME)

    videoSegments: List[str] = filterResponseBySuffix(bestM3U8PlaylistResponse, ".ts")

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

    concatenateVideoSegments(absolutePathOutput)

    print(f"Video downloaded to {outputFileAbsolutePath}")
    print("Done")

def parseCommandLineArguments() -> argparse.Namespace:
    argumentParser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="HLS downloader"
    )

    argumentParser.add_argument(
        "master_file_url",
        type = str,
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

def getDefaultAbsolutePathOutput() -> Path:
    POSIXTimestampInSeconds: str = str(
        int(
            datetime.now(tz=timezone.utc).timestamp()
        )
    )

    return Path(
        Path.home(),
        "Downloads",
        POSIXTimestampInSeconds
    )

def main() -> None:
    parsedCommandLineArguments: argparse.Namespace = parseCommandLineArguments()

    masterFileURL: str = parsedCommandLineArguments.master_file_url
    absolutePathOutput: Path = getDefaultAbsolutePathOutput()
    isVerbose: bool = parsedCommandLineArguments.verbose

    if(parsedCommandLineArguments.absolute_path_output):
        absolutePathOutput = parsedCommandLineArguments.absolute_path_output

    absolutePathOutput.mkdir(exist_ok=True)

    handleHLS(masterFileURL, absolutePathOutput, isVerbose)

if(__name__ == "__main__"):
    main()
