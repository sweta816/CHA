import os
from dotenv import load_dotenv
from openCHA.orchestrator import Orchestrator
from openCHA.planners import PlannerType
from openCHA.datapipes import DatapipeType
from openCHA.response_generators import ResponseGeneratorType
from openCHA.llms import LLMType
from flask import Flask, request, jsonify, render_template_string

load_dotenv()

# LLMType.GROQ use karo — ChatGroq object nahi
orchestrator = Orchestrator.initialize(
    planner_llm=LLMType.GROQ,
    planner_name=PlannerType.TREE_OF_THOUGHT,
    datapipe_name=DatapipeType.MEMORY,
    response_generator_llm=LLMType.GROQ,
    response_generator_name=ResponseGeneratorType.BASE_GENERATOR,
    available_tasks=["nutrition_search","nutrition_info"],
    verbose=False,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

PREFIX = """
You are NutriMate, nutrition guide for Indian college students.
Use Indian foods and measures (katori, glass, handful).
Never diagnose. Say 'may suggest' not 'you have'.
"""

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>NutriMate</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial; background: #f0f4f0; }
.container { max-width: 750px; margin: 30px auto; padding: 20px; }
h1 { color: #2e7d32; margin-bottom: 10px; }
#chat { height: 480px; overflow-y: auto; background: white;
        border: 1px solid #ddd; border-radius: 10px;
        padding: 15px; margin-bottom: 12px; }
.user-msg { text-align: right; margin: 8px 0; }
.user-msg span { background: #2e7d32; color: white;
    padding: 9px 14px; border-radius: 16px 16px 2px 16px;
    display: inline-block; max-width: 75%; white-space: pre-wrap; }
.bot-msg { text-align: left; margin: 8px 0; }
.bot-msg span { background: #e8f5e9; color: #1a1a1a;
    padding: 9px 14px; border-radius: 16px 16px 16px 2px;
    display: inline-block; max-width: 75%; white-space: pre-wrap; }
.input-row { display: flex; gap: 8px; }
#msg { flex: 1; padding: 11px; border: 1px solid #ccc;
       border-radius: 8px; font-size: 15px; }
button { padding: 11px 20px; background: #2e7d32; color: white;
         border: none; border-radius: 8px; cursor: pointer; }
</style></head>
<body>
<div class="container">
    <h1>🥗 NutriMate</h1>
    <p style="color:#666;margin-bottom:15px;">
        OpenCHA + LLaMA 3 via Groq</p>
    <div id="chat"></div>
    <div class="input-row">
        <input id="msg" type="text"
               placeholder="Apna sawaal poochho..."
               onkeypress="if(event.key==='Enter') send()"/>
        <button onclick="send()">Send</button>
    </div>
</div>
<script>
let history = [];
function addMsg(text, who) {
    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.className = who + '-msg';
    const span = document.createElement('span');
    span.innerText = text;
    div.appendChild(span);
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}
async function send() {
    const input = document.getElementById('msg');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    addMsg(msg, 'user');
    const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg, history: history})
    });
    const data = await res.json();
    addMsg(data.response, 'bot');
    history.push([msg, data.response]);
}
window.onload = () => addMsg(
    "Namaste! Main NutriMate hoon.\\n\\nBatao:\\n" +
    "1. Veg/Non-veg/Eggetarian?\\n" +
    "2. Hostel/PG/Home?\\n" +
    "3. Main concern?", 'bot');
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data    = request.json
    user_msg = data['message']
    history  = data['history']

    history_str = ""
    for human, assistant in history:
        history_str += f"User: {human}\nAssistant: {assistant}\n"

    response = orchestrator.run(
        query=user_msg,
        meta=[],
        history=history_str,
        use_history=True,
        response_generator_prefix_prompt=PREFIX
    )

    return jsonify({"response": str(response)})

if __name__ == '__main__':
    print("NutriMate: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)