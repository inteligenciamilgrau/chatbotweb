from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import io
import base64
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Adicione uma chave secreta para a sessão

# Inicializar o cliente OpenAI
client = OpenAI()

@app.route('/')
def index():
    session['conversation_history'] = []  # Inicializa o histórico da conversa
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # 1. Capturar o áudio do microfone
    audio_file = request.files['audio']

    # 2. Transcrever o áudio para texto usando Whisper
    audio_data = audio_file.read()
    audio_file.seek(0)  # Reiniciar o ponteiro do arquivo
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.wav", audio_data, "audio/wav")
    )
    text = transcript.text

    # Atualizar o histórico da conversa
    conversation_history = session.get('conversation_history', [])
    conversation_history.append({"role": "user", "content": text})

    # 3. Enviar o histórico da conversa para o ChatGPT e gerar uma resposta
    messages = [{"role": "system", "content": "Você é um assistente útil."}] + conversation_history
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    gpt_response = chat_completion.choices[0].message.content

    # Adicionar a resposta do assistente ao histórico
    conversation_history.append({"role": "assistant", "content": gpt_response})
    session['conversation_history'] = conversation_history

    # 4. Transformar o texto da resposta em áudio usando a API TTS da OpenAI
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=gpt_response
    )

    # 5. Retornar o áudio para tocar no cliente
    audio_base64 = base64.b64encode(audio_response.content).decode()

    return jsonify({
        'text': text,
        'response': gpt_response,
        'audio': audio_base64
    })

if __name__ == '__main__':
    app.run(debug=True)