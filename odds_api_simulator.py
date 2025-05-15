# Módulo Simulador de Coleta de Dados de Odds via API
# Nome do arquivo: odds_api_simulator.py

import random
import time

# Casas de apostas simuladas que nossa "API" cobriria
CASAS_DE_APOSTAS_SIMULADAS = [
    {"id": "casa_alpha", "nome": "AlphaBet"},
    {"id": "casa_beta", "nome": "BetaWin"},
    {"id": "casa_gamma", "nome": "GammaSpins"},
    {"id": "casa_delta", "nome": "DeltaOdds"}
]

# Eventos esportivos simulados
EVENTOS_ESPORTIVOS_SIMULADOS = [
    {
        "id_evento": "evt_fut_001",
        "esporte": "Futebol",
        "liga": "Campeonato Brasileiro Série A",
        "descricao": "Corinthians vs Palmeiras",
        "data_hora": "2025-05-20T19:00:00Z",
        "resultados_possiveis": ["Corinthians Vence", "Empate", "Palmeiras Vence"],
        "tipo_mercado": "3-vias"
    },
    {
        "id_evento": "evt_fut_002",
        "esporte": "Futebol",
        "liga": "Champions League - Final",
        "descricao": "Real Madrid vs Manchester City",
        "data_hora": "2025-05-28T20:00:00Z",
        "resultados_possiveis": ["Real Madrid Vence", "Empate", "Manchester City Vence"],
        "tipo_mercado": "3-vias"
    },
    {
        "id_evento": "evt_bas_001",
        "esporte": "Basquete",
        "liga": "NBA - Playoffs",
        "descricao": "Los Angeles Lakers vs Golden State Warriors",
        "data_hora": "2025-05-22T21:30:00Z",
        "resultados_possiveis": ["Lakers Vence", "Warriors Vence"],
        "tipo_mercado": "2-vias"
    },
    {
        "id_evento": "evt_ten_001",
        "esporte": "Tênis",
        "liga": "Roland Garros - Masculino Final",
        "descricao": "Jogador A vs Jogador B",
        "data_hora": "2025-06-08T14:00:00Z",
        "resultados_possiveis": ["Jogador A Vence", "Jogador B Vence"],
        "tipo_mercado": "2-vias"
    }
]

def gerar_odd_aleatoria(base=1.5, variacao=1.0):
    """Gera uma odd decimal aleatória com alguma variação."""
    return round(random.uniform(base, base + variacao), 2)

def fetch_live_odds_simulated(evento_id=None):
    """
    Simula a busca de odds ao vivo de múltiplas casas de apostas para eventos específicos ou todos.
    Retorna uma lista de dicionários, cada um representando as odds de uma casa para um evento.
    """
    dados_odds_reais = []
    eventos_para_buscar = EVENTOS_ESPORTIVOS_SIMULADOS
    if evento_id:
        eventos_para_buscar = [e for e in EVENTOS_ESPORTIVOS_SIMULADOS if e["id_evento"] == evento_id]

    if not eventos_para_buscar:
        return {"erro": "Evento não encontrado"}

    for evento in eventos_para_buscar:
        odds_evento_por_casa = {
            "id_evento": evento["id_evento"],
            "descricao_evento": evento["descricao"],
            "esporte": evento["esporte"],
            "liga": evento["liga"],
            "timestamp_consulta": time.time(),
            "odds_por_casa": []
        }

        for casa in random.sample(CASAS_DE_APOSTAS_SIMULADAS, k=random.randint(2, len(CASAS_DE_APOSTAS_SIMULADAS))): # Simula que nem todas as casas cobrem todos os eventos ou estão disponíveis
            odds_para_resultados = {}
            if evento["tipo_mercado"] == "3-vias":
                odds_para_resultados[evento["resultados_possiveis"][0]] = gerar_odd_aleatoria(1.8, 1.5) # Casa
                odds_para_resultados[evento["resultados_possiveis"][1]] = gerar_odd_aleatoria(2.8, 1.0) # Empate
                odds_para_resultados[evento["resultados_possiveis"][2]] = gerar_odd_aleatoria(2.0, 1.8) # Fora
            elif evento["tipo_mercado"] == "2-vias":
                odds_para_resultados[evento["resultados_possiveis"][0]] = gerar_odd_aleatoria(1.5, 0.8)
                odds_para_resultados[evento["resultados_possiveis"][1]] = gerar_odd_aleatoria(1.6, 0.9)
            
            # Adiciona uma pequena chance de uma odd ser muito boa para simular arbitragem
            if random.random() < 0.1: # 10% de chance de uma odd ser "especial"
                resultado_especial = random.choice(list(odds_para_resultados.keys()))
                odds_para_resultados[resultado_especial] = round(odds_para_resultados[resultado_especial] + random.uniform(0.5, 1.5), 2)

            odds_evento_por_casa["odds_por_casa"].append({
                "id_casa": casa["id"],
                "nome_casa": casa["nome"],
                "odds": odds_para_resultados
            })
        dados_odds_reais.append(odds_evento_por_casa)
    
    # Simula uma pequena latência de API
    time.sleep(random.uniform(0.1, 0.5))
    
    return dados_odds_reais

if __name__ == "__main__":
    print("--- Simulando busca de odds para todos os eventos ---")
    odds_todos_eventos = fetch_live_odds_simulated()
    for evento_data in odds_todos_eventos:
        print(f"\nEvento: {evento_data['descricao_evento']} ({evento_data['id_evento']})")
        for casa_odds in evento_data["odds_por_casa"]:
            print(f"  Casa: {casa_odds['nome_casa']}")
            for resultado, odd in casa_odds["odds"].items():
                print(f"    {resultado}: {odd}")

    print("\n--- Simulando busca de odds para um evento específico (evt_fut_001) ---")
    odds_evento_unico = fetch_live_odds_simulated(evento_id="evt_fut_001")
    if isinstance(odds_evento_unico, list):
        for evento_data in odds_evento_unico: # Deveria ser apenas um
            print(f"\nEvento: {evento_data['descricao_evento']} ({evento_data['id_evento']})")
            for casa_odds in evento_data["odds_por_casa"]:
                print(f"  Casa: {casa_odds['nome_casa']}")
                for resultado, odd in casa_odds["odds"].items():
                    print(f"    {resultado}: {odd}")
    else:
        print(odds_evento_unico) # Imprime erro se houver
