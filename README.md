# HLS Downloader
Baixador de segmentos HLS e arquivos M3U8.

## Como executar
Os comandos citados abaixo devem ser executados na raiz do repositório.

### Primeira vez
Execute os comandos abaixo para obter o setup do projeto.

1. Crie o ambiente virtual:
```bash
python -m venv .\hls-downloader-virtual-environment
```

2. Ative o ambiente virtual:
```bash
.\hls-downloader-virtual-environment\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r .\requirements.txt
```

#### Scripts PS1
Passo a passo para executar corretamente scripts "PS1" (necessário fazer apenas uma vez).

1. Inicie o PowerShell como administrador;

2. Execute o comando abaixo para alterar a política de execução de scripts:
```bash
Set-ExecutionPolicy RemoteSigned
```

3. Digite `A` (`[A] Sim para Todos`) e pressione Enter;

4. Encontre o caminho do executável do PowerShell (o retorno será algo como `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`):
```bash
where.exe powershell
```

5. Copie o caminho para o diretório pai. Por exemplo:
```
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -> C:\Windows\System32\WindowsPowerShell\v1.0\
```

6. Clique com o botão direito do mouse no arquivo `run.ps1` > `Abrir com` > `Escolher outro aplicativo`;

7. Role para baixo e clique em `Escolha um aplicativo no seu PC`;

8. Cole o caminho copiado na barra de endereço do explorador de arquivos e pressione Enter;

9. Selecione o arquivo `powershell.exe` e clique em `Abrir`;

10. Em `Aplicativo padrão`, selecione `Windows PowerShell` e clique em `Sempre`.

### Execução
Comando utilizado para iniciar o programa após o setup estar concluído:
```bash
.\run.ps1
```

### Atualização de dependências
Ao adicionar/remover/atualizar uma ou mais dependências, execute o comando abaixo na raiz do repositório para atualizar o arquivo de controle correspondente:

```bash
pip freeze > .\requirements.txt
```

## Juntar os segmentos
Comando utilizado para unir os segmentos em um único vídeo MP4:
```bash
ffmpeg -i .\playlist.m3u8 -c copy .\output.mp4
```

## Outros
- Versão do Python: 3.12.5
- Versão do FFmpeg: 7.1-full_build-www.gyan.dev | built with gcc 14.2.0 (Rev1, Built by MSYS2 project)
