# Author: Marco Guilherme
# Date: 02/12/2025

function Main {
    .\hls-downloader-virtual-environment\Scripts\activate

    python .\source-code\main.py

    deactivate
}

Main
