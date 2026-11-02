"""Rotulos pt-BR do que o Olist grava como slug: categorias e cidades.

O dataset traz so o slug sem acento (`moveis_decoracao`), e o `.title()` sobre
ele chegava a tela como "Moveis Decoracao". Um mapa por slug, compartilhado
pelas fatias que exibem categoria (Home, detalhe, checkout). Slug fora do mapa
cai no titulo antigo: categoria nova nao quebra a tela, so fica sem acento.
"""

from __future__ import annotations

CATEGORIAS: dict[str, str] = {
    "agro_industria_e_comercio": "Agroindústria e comércio",
    "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos e bebidas",
    "artes": "Artes",
    "artes_e_artesanato": "Artes e artesanato",
    "artigos_de_festas": "Artigos de festa",
    "artigos_de_natal": "Artigos de Natal",
    "audio": "Áudio",
    "automotivo": "Automotivo",
    "bebes": "Bebês",
    "bebidas": "Bebidas",
    "beleza_saude": "Beleza e saúde",
    "brinquedos": "Brinquedos",
    "cama_mesa_banho": "Cama, mesa e banho",
    "casa_conforto": "Casa e conforto",
    "casa_conforto_2": "Casa e conforto",
    "casa_construcao": "Casa e construção",
    "cds_dvds_musicais": "CDs e DVDs musicais",
    "cine_foto": "Cine e foto",
    "climatizacao": "Climatização",
    "consoles_games": "Consoles e games",
    "construcao_ferramentas_construcao": "Ferramentas de construção",
    "construcao_ferramentas_ferramentas": "Ferramentas",
    "construcao_ferramentas_iluminacao": "Iluminação",
    "construcao_ferramentas_jardim": "Ferramentas de jardim",
    "construcao_ferramentas_seguranca": "Segurança",
    "cool_stuff": "Presentes criativos",
    "dvds_blu_ray": "DVDs e Blu-ray",
    "eletrodomesticos": "Eletrodomésticos",
    "eletrodomesticos_2": "Eletrodomésticos",
    "eletronicos": "Eletrônicos",
    "eletroportateis": "Eletroportáteis",
    "esporte_lazer": "Esporte e lazer",
    "fashion_bolsas_e_acessorios": "Bolsas e acessórios",
    "fashion_calcados": "Calçados",
    "fashion_esporte": "Moda esportiva",
    "fashion_roupa_feminina": "Roupa feminina",
    "fashion_roupa_infanto_juvenil": "Roupa infantojuvenil",
    "fashion_roupa_masculina": "Roupa masculina",
    "fashion_underwear_e_moda_praia": "Underwear e moda praia",
    "ferramentas_jardim": "Ferramentas e jardim",
    "flores": "Flores",
    "fraldas_higiene": "Fraldas e higiene",
    "industria_comercio_e_negocios": "Indústria, comércio e negócios",
    "informatica_acessorios": "Informática e acessórios",
    "instrumentos_musicais": "Instrumentos musicais",
    "la_cuisine": "La Cuisine",
    "livros_importados": "Livros importados",
    "livros_interesse_geral": "Livros de interesse geral",
    "livros_tecnicos": "Livros técnicos",
    "malas_acessorios": "Malas e acessórios",
    "market_place": "Marketplace",
    "moveis_colchao_e_estofado": "Colchões e estofados",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Móveis de cozinha, jantar e jardim",
    "moveis_decoracao": "Móveis e decoração",
    "moveis_escritorio": "Móveis de escritório",
    "moveis_quarto": "Móveis de quarto",
    "moveis_sala": "Móveis de sala",
    "musica": "Música",
    "papelaria": "Papelaria",
    "pc_gamer": "PC gamer",
    "pcs": "PCs",
    "perfumaria": "Perfumaria",
    "pet_shop": "Pet shop",
    "portateis_casa_forno_e_cafe": "Fornos e cafeteiras",
    "portateis_cozinha_e_preparadores_de_alimentos": "Portáteis de cozinha",
    "relogios_presentes": "Relógios e presentes",
    "seguros_e_servicos": "Seguros e serviços",
    "sinalizacao_e_seguranca": "Sinalização e segurança",
    "tablets_impressao_imagem": "Tablets, impressão e imagem",
    "telefonia": "Telefonia",
    "telefonia_fixa": "Telefonia fixa",
    "utilidades_domesticas": "Utilidades domésticas",
}


def rotulo_categoria(slug: str) -> str:
    return CATEGORIAS.get(slug) or slug.replace("_", " ").title()


_CONECTIVOS = {"da", "das", "de", "do", "dos", "e"}

# Acento por PALAVRA (D1): o Olist grava "sao jose do rio preto". Sem base de
# municipios, um mapa das palavras que mais aparecem nos nomes de cidade cobre
# a vitrine; palavra fora do mapa segue sem acento, como antes.
# ponytail: mapa manual; uma base do IBGE resolveria todas, se valer o ETL.
_ACENTOS: dict[str, str] = {
    w.replace("á", "a").replace("â", "a").replace("ã", "a").replace("é", "e").replace("ê", "e")
    .replace("í", "i").replace("ó", "o").replace("ô", "o").replace("õ", "o").replace("ú", "u")
    .replace("ç", "c"): w
    for w in (
        "são", "joão", "josé", "luís", "antônio", "sebastião", "simão", "estêvão", "lourenço",
        "gonçalo", "andré", "conceição", "ribeirão", "goiânia", "brasília", "florianópolis",
        "maringá", "uberlândia", "belém", "vitória", "niterói", "petrópolis", "jacareí", "taubaté",
        "itajaí", "jundiaí", "guanhães", "pradópolis", "paraíba", "mauá", "parnaíba", "araçatuba",
        "macaé", "itaúna", "chapecó", "criciúma", "jaraguá", "guarujá", "cubatão", "marília",
        "bragança", "tatuí", "avaré", "jaú", "lençóis", "araçoiaba", "guaçu", "ceará", "piauí",
        "paraná", "amapá", "maranhão", "rondônia", "goiás", "espírito", "teófilo", "poços",
        "divinópolis", "maceió", "macapá", "cuiabá", "várzea", "rondonópolis", "jaboatão",
        "iguaçu", "araucária", "beltrão", "magé", "itaboraí", "maricá", "teresópolis", "união",
        "sertãozinho", "águas", "lindóia", "itajubá", "três", "corações", "unaí", "anápolis",
        "catalão", "araguaína", "mossoró", "jequié", "eunápolis", "valença", "gravataí", "viamão",
        "ijuí", "palhoça", "biguaçu", "balneário", "camboriú", "tubarão", "concórdia", "joaçaba",
        "caçador", "timbó", "xanxerê", "paranavaí", "mourão", "cambé", "rolândia", "ibiporã",
        "telêmaco", "cornélio", "procópio", "guaíra", "ilhéus", "camaçari", "petrolândia",
        "itapetininga", "votuporanga", "assis", "barretos", "osasco", "carapicuíba", "itaquaquecetuba",
        "suzano", "poá", "ferraz", "vasconcelos", "embu", "taboão", "cotia", "santana", "itapevi",
        "jandira", "barueri", "pirapora", "atibaia", "mairiporã", "caieiras", "juquiá", "registro",
        "peruíbe", "itanhaém", "mongaguá", "bertioga", "ubatuba", "caraguatatuba", "ilhabela",
        "jacareí", "pindamonhangaba", "guaratinguetá", "lorena", "cruzeiro", "aparecida",
    )
}


def rotulo_cidade(cidade: str | None) -> str | None:
    """O Olist grava a cidade em minusculas e sem acento ("sao jose do rio
    preto"). Capitaliza, deixa conectivos minusculos e devolve o acento das
    palavras de `_ACENTOS` ("São José do Rio Preto")."""
    if not cidade:
        return cidade
    palavras = [_ACENTOS.get(w, w) for w in cidade.split()]
    return " ".join(
        w if i > 0 and w in _CONECTIVOS else w[:1].upper() + w[1:] for i, w in enumerate(palavras)
    )


def _numero(valor: float, casas: int) -> str:
    texto = f"{valor:.{casas}f}".replace(".", ",")
    return texto[:-2] if texto.endswith(",0") else texto


def descritor_produto(product_id: str, weight_g: float | None, volume_cm3: float | None) -> str:
    """Identidade do produto sem inventar nome: referencia curta do id + peso +
    volume, todos do dataset ("Ref. 4F2A9C · 150 g · 0,9 L")."""
    partes = [f"Ref. {product_id[:6].upper()}"]
    if weight_g:
        partes.append(f"{_numero(weight_g / 1000, 1)} kg" if weight_g >= 1000 else f"{round(weight_g)} g")
    if volume_cm3:
        litros = volume_cm3 / 1000
        partes.append(f"{_numero(litros, 0 if litros >= 10 else 1)} L" if litros >= 1 else f"{round(volume_cm3 / 10) * 10} mL")
    return " · ".join(partes)
