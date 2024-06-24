
import openai

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
