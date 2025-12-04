# Author: Marco Guilherme
# Date: 04/12/2025

function Main {
    $outputRelativePath = ".\output"

    Get-ChildItem -Path $outputRelativePath -Recurse -Force | Where-Object {
        $_.Name -ne ".gitkeep"
    } | Remove-Item -Recurse -Force
}

Main
