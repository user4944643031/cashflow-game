from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from regras import Jogo
from database import obter_ranking

app = FastAPI()
jogo = Jogo()

class SetupData(BaseModel):
    profissao: str
    sonho: str

class CompraData(BaseModel):
    quantidade: int = 1

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/setup_opcoes")
def get_opcoes():
    return {
        "profissoes": Jogo.PROFISSOES,
        "sonhos": Jogo.SONHOS
    }

@app.get("/ranking")
def get_ranking():
    return obter_ranking()

@app.post("/iniciar")
def iniciar(data: SetupData):
    jogo.iniciar_partida(data.profissao, data.sonho)
    return jogo.obter_estado_geral()

@app.post("/jogar_humano")
def jogar_humano():
    return jogo.jogar_turno_humano()

@app.post("/comprar")
def comprar(data: CompraData = CompraData()):
    return jogo.comprar_humano(quantidade=data.quantidade)

@app.post("/pagar_besteira")
def pagar_besteira():
    return jogo.pagar_besteira_humano()

@app.post("/vender_mercado")
def vender_mercado():
    return jogo.vender_ativo_mercado_humano()

@app.post("/jogar_bot")
def jogar_bot():
    return jogo.executar_turno_bot()

@app.post("/passar")
def passar():
    return jogo.passar_humano()

@app.post("/entrar_pista_rapida")
def entrar_pista():
    return jogo.entrar_pista_rapida_humano()

@app.post("/emprestimo")
def pegar_emprestimo():
    return jogo.emprestimo_humano()

@app.post("/quitar_emprestimo")
def quitar_emprestimo():
    return jogo.quitar_emprestimo_humano()