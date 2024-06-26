
import openai
import requests

# Setup API key and initialize OpenAI
def setup_openai_api():
    openai.api_key = 'your-openai-api-key'

# Function to get response from ChatGPT
def get_chatgpt_response(prompt):
    setup_openai_api()
    response = openai.Completion.create(
        engine="text-davinci-003",  # Specify the model engine
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()


def sumarizar_texto(api_key, texto):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-3.5-turbo",  # Certifique-se de que este é o modelo de chat correto disponível
        "messages": [{"role": "assistant", "content": "Faça um resumo sobre como funciona a Rescisão contratual:" + texto }],
        "max_tokens": 350,
        "temperature": 0.7
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code != 200:
        print("Erro na requisição:", response.status_code)
        print("Mensagem de erro:", response.text)
    
    response.raise_for_status()
    return response.json()
