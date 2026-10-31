# Agente de monitorização automatizado

Faz um jornal do dia: recolhe notícias de vários jornais portugueses por RSS, junta a mesma
história contada por jornais diferentes, escolhe as principais de cada secção e junta o tempo
atual (API pública [Open-Meteo](https://open-meteo.com), sem chave).

No fim cria dois ficheiros em `reports/`:

- `jornal_AAAA-MM-DD_HHMMSS.html` — o jornal, com fotografias, que **abre sozinho no browser**;
- `relatorio_AAAA-MM-DD_HHMMSS.md` — o mesmo conteúdo em Markdown.

Sem internet, usa os ficheiros de exemplo em `dados/`.

## Secções e fontes

| Secção | Fontes |
|---|---|
| Portugal | RTP Notícias, Público, Notícias ao Minuto, Observador |
| Mundo | RTP Notícias, Público, Notícias ao Minuto, Observador |
| Economia | RTP Notícias, Público, ECO, Notícias ao Minuto, Observador |
| Desporto | RTP Notícias, Público, Record, Notícias ao Minuto, Observador |
| Cultura | RTP Notícias, Público, Notícias ao Minuto, Observador |
| Ciência e Tecnologia | Público, Notícias ao Minuto, Observador |

Expresso e SIC Notícias não estão incluídos porque recusam pedidos automáticos (erro 403).

**Como são escolhidas as notícias:** só as de hoje; sem opinião nem crónicas; a mesma história em
vários jornais conta como uma só, e as que aparecem em mais jornais sobem para o topo (a primeira é a
manchete). Em caso de empate ganha a mais recente, alternando entre jornais.

## Preparar (só da primeira vez)

No PowerShell, dentro desta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Correr

```powershell
.\.venv\Scripts\python.exe -m agente                  # faz o jornal e abre-o no browser
.\.venv\Scripts\python.exe -m agente --sem-abrir      # faz o jornal sem o abrir
.\.venv\Scripts\python.exe -m agente --fonte local    # simulação com os ficheiros de dados/
.\.venv\Scripts\python.exe -m pytest                  # testes
```

## Site público (GitHub Pages)

O ficheiro `.github/workflows/jornal.yml` faz o jornal todas as manhãs (06:30 UTC) e publica-o no
GitHub Pages, sem os resumos (só títulos, fotografias e links). Para isto funcionar, no GitHub:
**Settings → Pages → Source: GitHub Actions**. Para fazer uma edição já: **Actions → Jornal do dia →
Run workflow**. O GitHub desliga os agendamentos de repositórios sem alterações há 60 dias; para
voltar a ligar, basta carregar em **Enable workflow** no separador Actions.

## Ficheiros

| Ficheiro | O que faz |
|---|---|
| `agente/config.py` | Secções, feeds de cada jornal, locais do tempo, limites dos alertas |
| `agente/noticias.py` | Lê os feeds, tira fotografias e datas, junta histórias repetidas, escolhe as do dia |
| `agente/jornal.py` | Gera o jornal em HTML |
| `agente/relatorio.py` | Gera o Markdown e guarda os ficheiros em `reports/` |
| `agente/fontes.py` | Lê a meteorologia da API ou do ficheiro JSON |
| `agente/analise.py` | Compara a meteorologia com os limites e calcula médias/máximos |
| `agente/__main__.py` | Ponto de entrada e opções da linha de comandos |
| `dados/exemplo.json`, `dados/noticias_exemplo.json` | Dados simulados para o modo local |
