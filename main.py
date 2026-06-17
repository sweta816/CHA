import os
from dotenv import load_dotenv
from openCHA.orchestrator import Orchestrator
from openCHA.planners import PlannerType
from openCHA.datapipes import DatapipeType
from openCHA.response_generators import ResponseGeneratorType
from openCHA.llms import LLMType
from flask import Flask, request, jsonify, render_template_string

load_dotenv()

# ── Orchestrator Setup ──────────────────────────────────────────────
orchestrator = Orchestrator.initialize(
    planner_llm=LLMType.GROQ,
    planner_name=PlannerType.ZERO_SHOT_REACT_PLANNER,
    datapipe_name=DatapipeType.MEMORY,
    response_generator_llm=LLMType.GROQ,
    response_generator_name=ResponseGeneratorType.BASE_GENERATOR,
    available_tasks=["nutrition_search", "nutrition_info"],
    verbose=True,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# ── System Prompt ────────────────────────────────────────────────────
PREFIX = """
You are NutriMate, nutrition guide for Bihar polytechnic students.
Use Indian foods and measures (katori, glass, handful).
Never diagnose. Say 'may suggest' not 'you have'.

BUDGET & AFFORDABILITY RULE:
Most students spend less than Rs 2,000/month on food. NEVER suggest:
- Brown rice (costs more than regular rice, not commonly available)
- Quinoa, avocado, kale, oats imported brands
- Any food not typically found in Bihar hostel mess or local bazaar

ALWAYS suggest affordable, traditional foods:
- Regular rice (chawal), not brown rice
- Wheat roti/chapati
- Local dal (chana, moong, masoor, arhar)
- Seasonal local vegetables
- Curd/dahi, eggs (if eggetarian/non-veg)

CRITICAL FORMAT RULE:
If the user asks for a short, exact, or specific answer, give ONLY
that — no extra explanation, no elaboration, no advice. Otherwise
keep the answer brief and to the point.
"""

app = Flask(__name__)

# ── Frontend ──────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NutriMate</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.2/marked.min.js"></script>
<style>
  :root{
    --bg-deep:#16301F;
    --bg-deep-2:#1E3F29;
    --panel:#FBF5E9;
    --mustard:#E2A63B;
    --mustard-dark:#C98A22;
    --brick:#A8472E;
    --leaf:#3C6E47;
    --ink:#2A2118;
    --ink-soft:#6B5F4F;
    --line:#E7DCC4;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;}
  body{
    background:radial-gradient(circle at 20% 0%, var(--bg-deep-2), var(--bg-deep) 60%);
    font-family:'Work Sans',sans-serif;
    color:var(--ink);
    display:flex;
    align-items:center;
    justify-content:center;
    min-height:100vh;
    padding:24px;
  }
  .app{
    width:100%;
    max-width:480px;
    height:min(820px, calc(100vh - 48px));
    background:var(--panel);
    border-radius:28px;
    overflow:hidden;
    display:flex;
    flex-direction:column;
    box-shadow:0 30px 60px -20px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.04);
  }
  .header{
    background:linear-gradient(135deg, var(--mustard) 0%, var(--mustard-dark) 100%);
    padding:20px 22px 18px;
    color:#2A1B05;
    position:relative;
  }
  .header .mark{
    width:38px;height:38px;border-radius:50%;
    background:var(--panel);
    display:flex;align-items:center;justify-content:center;
    font-size:18px;
    margin-bottom:10px;
    box-shadow:0 2px 0 rgba(0,0,0,0.12) inset;
  }
  .header h1{
    font-family:'Fraunces',serif;
    font-weight:600;
    font-size:26px;
    margin:0 0 4px;
    letter-spacing:-0.01em;
  }
  .header p{
    margin:0;
    font-size:13px;
    font-weight:500;
    opacity:0.82;
  }
  .chat{
    flex:1;
    overflow-y:auto;
    padding:20px 18px;
    display:flex;
    flex-direction:column;
    gap:14px;
    background:
      radial-gradient(circle at 100% 0%, rgba(60,110,71,0.06), transparent 40%),
      var(--panel);
  }
  .chat::-webkit-scrollbar{width:6px;}
  .chat::-webkit-scrollbar-thumb{background:var(--line);border-radius:6px;}
  .row{display:flex;}
  .row.user{justify-content:flex-end;}
  .row.bot{justify-content:flex-start;}
  .bubble{
    max-width:82%;
    padding:12px 16px;
    font-size:14.5px;
    line-height:1.5;
    word-wrap:break-word;
  }
  .row.bot .bubble{
    background:#fff;
    border:1px solid var(--line);
    border-radius:4px 18px 18px 18px;
    color:var(--ink);
  }
  .row.user .bubble{
    background:var(--brick);
    color:#fff;
    border-radius:18px 18px 4px 18px;
  }
  .bubble table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13px;}
  .bubble th, .bubble td{border:1px solid var(--line);padding:6px 8px;text-align:left;}
  .bubble th{background:#F4ECD8;font-weight:600;}
  .bubble p{margin:0 0 8px;}
  .bubble p:last-child{margin-bottom:0;}
  .bubble ul, .bubble ol{margin:6px 0 6px 18px; padding:0;}
  .typing{display:flex;gap:4px;padding:14px 16px;}
  .typing span{
    width:6px;height:6px;border-radius:50%;
    background:var(--ink-soft);
    opacity:0.4;
    animation:bounce 1.2s infinite;
  }
  .typing span:nth-child(2){animation-delay:0.15s;}
  .typing span:nth-child(3){animation-delay:0.3s;}
  @keyframes bounce{
    0%,60%,100%{transform:translateY(0);opacity:0.4;}
    30%{transform:translateY(-4px);opacity:1;}
  }
  .chips{display:flex;gap:8px;padding:0 18px 12px;overflow-x:auto;flex-wrap:nowrap;}
  .chips::-webkit-scrollbar{display:none;}
  .chip{
    flex:0 0 auto;
    background:#fff;
    border:1px solid var(--line);
    color:var(--leaf);
    font-size:12.5px;
    font-weight:600;
    padding:8px 14px;
    border-radius:999px;
    cursor:pointer;
    white-space:nowrap;
    transition:background 0.15s, transform 0.1s;
  }
  .chip:hover{background:#F4ECD8;}
  .chip:active{transform:scale(0.96);}
  .chip:focus-visible{outline:2px solid var(--leaf); outline-offset:2px;}
  .inputbar{
    display:flex;
    align-items:center;
    gap:10px;
    padding:14px 16px 18px;
    background:var(--panel);
    border-top:1px solid var(--line);
  }
  .inputbar input{
    flex:1;
    border:1px solid var(--line);
    background:#fff;
    border-radius:999px;
    padding:12px 16px;
    font-size:14.5px;
    font-family:'Work Sans',sans-serif;
    color:var(--ink);
  }
  .inputbar input:focus{
    outline:none;
    border-color:var(--leaf);
    box-shadow:0 0 0 3px rgba(60,110,71,0.15);
  }
  .inputbar input::placeholder{color:#A89B82;}
  .send{
    width:42px;height:42px;
    border-radius:50%;
    background:var(--leaf);
    border:none;
    color:#fff;
    display:flex;align-items:center;justify-content:center;
    cursor:pointer;
    flex-shrink:0;
    transition:background 0.15s, transform 0.1s;
  }
  .send:hover{background:#335E3D;}
  .send:active{transform:scale(0.93);}
  .send:focus-visible{outline:2px solid var(--mustard); outline-offset:2px;}
  .send svg{width:18px;height:18px;}
  @media (max-width:380px){
    .app{border-radius:18px;}
    .header h1{font-size:22px;}
  }
</style>
</head>
<body>

<div class="app">
  <div class="header">
    <div class="mark">&#127806;</div>
    <h1>NutriMate</h1>
    <p>Free nutrition guide &mdash; ICMR-NIN data se grounded</p>
  </div>

  <div class="chips" id="chips">
    <div class="chip" data-q="Aaj dinner mein kya khaayein, budget mein?">Budget dinner ideas</div>
    <div class="chip" data-q="Iron badhane wale sasta khana batao">Iron-rich affordable foods</div>
    <div class="chip" data-q="Sattu mein kitna protein hota hai">Sattu nutrition</div>
    <div class="chip" data-q="Hostel mess mein healthy kaise rahe">Hostel mess tips</div>
  </div>

  <div class="chat" id="chat"></div>

  <div class="inputbar">
    <input type="text" id="msgInput" placeholder="Apna sawaal yahan likho..." autocomplete="off">
    <button class="send" id="sendBtn" aria-label="Send message">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="19" x2="12" y2="5"></line>
        <polyline points="6 11 12 5 18 11"></polyline>
      </svg>
    </button>
  </div>
</div>

<script>
  const chat = document.getElementById('chat');
  const input = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const chips = document.getElementById('chips');
  let history = [];

  function addMessage(role, text, isMarkdown){
    const row = document.createElement('div');
    row.className = 'row ' + role;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if(isMarkdown){
      bubble.innerHTML = marked.parse(text);
    } else {
      bubble.textContent = text;
    }
    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
    return bubble;
  }

  function showTyping(){
    const row = document.createElement('div');
    row.className = 'row bot';
    row.id = 'typingRow';
    row.innerHTML = '<div class="bubble typing"><span></span><span></span><span></span></div>';
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
  }

  function hideTyping(){
    const row = document.getElementById('typingRow');
    if(row) row.remove();
  }

  async function sendMessage(text){
    if(!text.trim()) return;
    addMessage('user', text, false);
    input.value = '';
    showTyping();

    try{
      const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text, history: history})
      });
      const data = await res.json();
      hideTyping();
      const botText = data.response || "Maaf karna, kuch gadbad ho gayi.";
      addMessage('bot', botText, true);
      history.push([text, botText]);
    } catch(err){
      hideTyping();
      addMessage('bot', "Connection error. Server chal raha hai check karo.", false);
    }
  }

  sendBtn.addEventListener('click', () => sendMessage(input.value));
  input.addEventListener('keydown', (e) => {
    if(e.key === 'Enter') sendMessage(input.value);
  });
  chips.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if(chip) sendMessage(chip.dataset.q);
  });
</script>

</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data['message']
    history = data['history']

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