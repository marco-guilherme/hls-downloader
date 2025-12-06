'''
    Author: Marco Guilherme
    Date: 04/12/2025
'''

from urllib.parse import urlparse, urljoin, ParseResult

from pathlib import PurePosixPath

def parseURL(fileURL: str) -> ParseResult:
    parsedURL: ParseResult = urlparse(fileURL)
    # isURLInvalid: bool = (not parsedURL.scheme) or (not parsedURL.netloc)

    # if(isURLInvalid):
    #     raise ValueError(f"Invalid URL: {fileURL}")

    return parsedURL

def getBaseURL(fullURL: ParseResult) -> ParseResult:
    basePath: str = str(PurePosixPath(fullURL.path).parent) + '/'
    baseURL: str = f"{fullURL.scheme}://{fullURL.netloc}{basePath}"

    return parseURL(baseURL)

def getFilenameInURL(fullURL: ParseResult) -> str:
    return PurePosixPath(fullURL.path).name

def concatenateURL(baseURL: ParseResult, stringToAppend: str) -> ParseResult:
    newURL: str = urljoin(baseURL.geturl(), stringToAppend)

    return parseURL(newURL)

def getOriginURL(siteURL: ParseResult) -> ParseResult:
    originURL: str = f"{siteURL.scheme}://{siteURL.netloc}"

    return parseURL(originURL)
