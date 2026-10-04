"""Fatia VSA: Green Logistics (ODS 12).

Distancia geodesica via Haversine sobre centroides de CEP (mediana de lat/lng
por prefixo, derivados no ETL). CO2e por cadeia de transporte desde a Sprint 9
(ver `co2.py`: circuidade, ultima milha de van, transferencia de caminhao, com
as fontes). Selo "verde" para entregas com d_km < 100.
"""
