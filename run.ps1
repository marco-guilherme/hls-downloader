# Author: Marco Guilherme
# Date: 02/12/2025

function Main {
    $absolutePathOutput = Join-Path $PSScriptRoot "output"

    .\hls-downloader-virtual-environment\Scripts\activate

    python .\source-code\main.py "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" -o $absolutePathOutput --verbose
    # python .\source-code\main.py "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"

    deactivate
}

Main
