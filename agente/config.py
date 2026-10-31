"""
config.py — tudo o que se pode querer mudar sem mexer no resto do código.
"""

from pathlib import Path

# Pasta raiz do projeto (a pasta acima de "agente/").
RAIZ = Path(__file__).resolve().parent.parent

# Onde os relatórios em Markdown são guardados.
PASTA_REPORTS = RAIZ / "reports"

# Ficheiro usado no modo "local" (simulação, sem internet).
FICHEIRO_EXEMPLO = RAIZ / "dados" / "exemplo.json"

# API pública e gratuita, sem chave: https://open-meteo.com
URL_API = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SEGUNDOS = 10

# Locais a monitorizar: nome, latitude, longitude.
LOCAIS = [
    {"nome": "Figueira da Foz", "latitude": 40.15, "longitude": -8.86},
    {"nome": "Coimbra", "latitude": 40.21, "longitude": -8.43},
    {"nome": "Lisboa", "latitude": 38.72, "longitude": -9.14},
    {"nome": "Porto", "latitude": 41.15, "longitude": -8.61},
]

# Secções do jornal, pela ordem em que aparecem.
# "maximo" é quantas notícias mostrar (a primeira é a manchete).
SECOES = {
    "nacional": {"titulo": "Portugal", "emoji": "🇵🇹", "maximo": 8},
    "internacional": {"titulo": "Mundo", "emoji": "🌍", "maximo": 8},
    "economia": {"titulo": "Economia", "emoji": "💶", "maximo": 5},
    "desporto": {"titulo": "Desporto", "emoji": "⚽", "maximo": 5},
    "cultura": {"titulo": "Cultura", "emoji": "🎭", "maximo": 5},
    "tecnologia": {"titulo": "Ciência e Tecnologia", "emoji": "💡", "maximo": 5},
}

# Feeds RSS por secção: (nome da fonte, URL). Todos testados a 31/10/2026.
# Expresso e SIC Notícias ficaram de fora: bloqueiam pedidos automáticos (erro 403).
FEEDS_NOTICIAS = {
    "nacional": [
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/pais"),
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/politica"),
        ("Público", "https://feeds.feedburner.com/PublicoSociedade"),
        ("Público", "https://feeds.feedburner.com/PublicoPolitica"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/pais"),
    ],
    "internacional": [
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/mundo"),
        ("Público", "https://feeds.feedburner.com/PublicoMundo"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/mundo"),
    ],
    "economia": [
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/economia"),
        ("Público", "https://feeds.feedburner.com/PublicoEconomia"),
        ("ECO", "https://eco.sapo.pt/feed/"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/economia"),
    ],
    "desporto": [
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/desporto"),
        ("Público", "https://feeds.feedburner.com/PublicoDesporto"),
        ("Record", "https://www.record.pt/rss"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/desporto"),
    ],
    "cultura": [
        ("RTP Notícias", "https://www.rtp.pt/noticias/rss/cultura"),
        ("Público", "https://feeds.feedburner.com/PublicoCultura"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/cultura"),
    ],
    "tecnologia": [
        ("Público", "https://feeds.feedburner.com/PublicoTecnologia"),
        ("Notícias ao Minuto", "https://www.noticiasaominuto.com/rss/tech"),
    ],
}

# Feeds que misturam tudo num só: cada notícia vai para a secção da primeira
# categoria que aparecer aqui. Notícias sem nenhuma destas categorias ficam de fora.
FEEDS_POR_CATEGORIA = [
    (
        "Observador",
        "https://observador.pt/feed/",
        {
            "País": "nacional", "Sociedade": "nacional", "Política": "nacional",
            "Mundo": "internacional", "Europa": "internacional",
            "Economia": "economia", "Empresas": "economia",
            "Desporto": "desporto", "Futebol": "desporto",
            "Cultura": "cultura",
            "Ciência": "tecnologia", "Tecnologia": "tecnologia",
        },
    ),
]

# Partes do link ou categorias que indicam opinião/crónica (não entram no jornal).
SINAIS_OPINIAO = ["/opiniao/", "/cronica/", "/cronicas/", "/opinion/", "Opinião", "Crónica", "Crónicas"]

# Identifica o agente perante os sites dos jornais.
USER_AGENT = "agente-monitoramento/1.0 (leitor de RSS pessoal)"

# Quantos feeds ler ao mesmo tempo.
FEEDS_EM_PARALELO = 8

# Notícias simuladas para o modo "local".
FICHEIRO_NOTICIAS_EXEMPLO = RAIZ / "dados" / "noticias_exemplo.json"

# Fuso horário usado para decidir o que é "notícia do dia" e mostrar as horas.
FUSO_HORARIO = "Europe/Lisbon"

# Limites que geram alertas no relatório.
LIMITES = {
    "temperatura_max": 35.0,  # °C
    "temperatura_min": 2.0,  # °C
    "vento_max": 50.0,  # km/h
    "humidade_max": 95.0,  # %
}
