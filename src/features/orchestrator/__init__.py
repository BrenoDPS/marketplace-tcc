"""Fatia VSA: Orchestrator.

Hoje faz uma coisa: as mutacoes de contrato do modo apresentacao
(`mutacoes.py`, Sprint 16) — o BFF reordena, injeta ou degrada a propria
arvore a pedido, para a §3.3 ser demonstrada ao vivo.

O roteamento por `version` de bloco continua NAO IMPLEMENTADO: todo bloco vale
1, entao nao ha segunda versao para rotear entre. Implementar quando houver
duas versoes vivas do mesmo bloco — antes disso e construir o roteador antes
da estrada.
"""
