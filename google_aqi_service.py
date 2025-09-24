# Arquivo: google_aqi_service.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_AQI_API_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"
GOOGLE_AQI_API_URL_HISTORY = "https://airquality.googleapis.com/v1/history:lookup"


def get_historical_air_quality(datetime_obj):

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Erro: Chave de API do Google não encontrada.")
        return None
    
    utc_datetime_str = datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ')

    payload = {
        "dateTime": utc_datetime_str,
        "location": {
            "latitude": -23.536428421966946,
            "longitude": -46.635818385548866
        },
        "extraComputations": [
            "HEALTH_RECOMMENDATIONS",
            "POLLUTANT_ADDITIONAL_INFO"
        ],
        "languageCode": "pt-br"
    }

    try:
        response = requests.post(GOOGLE_AQI_API_URL_HISTORY, params={"key": api_key}, json=payload)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        error_message = f"Erro ao chamar a API de Histórico do Google: {e}"
        print(error_message)
        
        # Loga a resposta detalhada da API do Google para facilitar a depuração
        if e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Resposta da API: {e.response.text}")
            if e.response.status_code == 400:
                error_message = "Requisição inválida. Verifique se a data solicitada está dentro dos últimos 30 dias e se o formato está correto."
            else:
                error_message = f"Erro na API do Google: {e.response.text}"
        return None, error_message
    except Exception as e:
        error_message = f"Ocorreu um erro inesperado: {e}"
        print(error_message)
        return None, error_message