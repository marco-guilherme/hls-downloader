'''
    Author: Marco Guilherme
    Date: 05/12/2025
'''

import requests
import subprocess

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import ParseResult
from typing import List

import constants

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

def downloadFileContent(fileURL: ParseResult) -> str:
    with requests.get(fileURL.geturl()) as fileResponse:
        fileResponse.raise_for_status()

        return fileResponse.text

def writeFile(outputPath: Path, filename: str, fileContent: str) -> None:
    with open(Path(outputPath, filename), 'w', encoding="utf-8") as fileOutput:
        fileOutput.write(fileContent)

def filterResponseBySuffix(requestResponse: str, suffix: str) -> List[str]:
    filteredLines: List[str] = []
    lines: List[str] = requestResponse.splitlines()

    for fileLine in lines:
        if(not fileLine.endswith(suffix)):
            continue

        filteredLines.append(fileLine)

    return filteredLines

def downloadAndSaveFile(fileURL: ParseResult, outputPath: Path, outputFilename: str) -> str:
    fileContent: str = downloadFileContent(fileURL)

    writeFile(outputPath, outputFilename, fileContent)

    return fileContent

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
