# HLS Downloader
Baixador de vídeo HLS.

## Execução

Comando executado na raiz do repositóro para iniciar o programa:
```bash
.\run.ps1
```

## Juntar os segmentos

Comando utilizado para unir os segmentos em um único vídeo MP4:
```bash
ffmpeg -i .\playlist.m3u8 -c copy .\output.mp4
```
