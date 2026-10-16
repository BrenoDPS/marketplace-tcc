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
    "cool_stuff": "Cool stuff",
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


def rotulo_cidade(cidade: str | None) -> str | None:
    """O Olist grava a cidade em minusculas e sem acento ("sao jose do rio
    preto"). Capitaliza e deixa conectivos minusculos; acento nao ha de onde
    tirar sem uma base de municipios."""
    if not cidade:
        return cidade
    palavras = cidade.split()
    return " ".join(
        w if i > 0 and w in _CONECTIVOS else w[:1].upper() + w[1:] for i, w in enumerate(palavras)
    )
