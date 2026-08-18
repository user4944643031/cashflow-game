from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from regras import Jogo
from database import obter_ranking

app = FastAPI()
jogo = Jogo()

class JogadorConfig(BaseModel):
    nome: str
    profissao: str
    sonho: str
    is_bot: bool

class MultiSetupData(BaseModel):
    jogadores: List[JogadorConfig]

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

@app.post("/iniciar_multi")
def iniciar_multi(data: MultiSetupData):
    configs = [j.model_dump() for j in data.jogadores]
    jogo.iniciar_partida(configs)
    return jogo.obter_estado_geral()

@app.post("/jogar_humano")
def jogar_humano():
    return jogo.jogar_turno_humano()

@app.post("/jogar_bot")
def jogar_bot():
    return jogo.executar_turno_bot()

@app.post("/comprar")
def comprar(data: CompraData = CompraData()):
    return jogo.comprar_atual(quantidade=data.quantidade)

@app.post("/pagar_besteira")
def pagar_besteira():
    return jogo.pagar_besteira_atual()

@app.post("/vender_mercado")
def vender_mercado():
    return jogo.vender_ativo_mercado_atual()

@app.post("/passar")
def passar():
    return jogo.passar_atual()

@app.post("/entrar_pista_rapida")
def entrar_pista():
    return jogo.entrar_pista_rapida_atual()

@app.post("/emprestimo")
def pegar_emprestimo():
    return jogo.emprestimo_atual()

@app.post("/quitar_emprestimo")
def quitar_emprestimo():
    return jogo.quitar_emprestimo_atual()