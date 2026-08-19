import uuid
import json
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from regras import Jogo
from database import obter_ranking

app = FastAPI()

class Sala:
    def __init__(self, codigo: str, host_id: str):
        self.codigo = codigo
        self.host_id = host_id
        self.status = "lobby"  # 'lobby' ou 'jogando'
        self.jogadores_lobby: List[dict] = []
        self.jogo: Optional[Jogo] = None
        self.conexoes: Dict[str, WebSocket] = {}
        self.timer_task: Optional[asyncio.Task] = None
        self.bot_task: Optional[asyncio.Task] = None

    def parar_timers(self):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()

    def processar_fluxo_pos_acao(self):
        self.parar_timers()
        if self.status != "jogando" or not self.jogo:
            return

        if any(j.venceu_jogo for j in self.jogo.jogadores):
            return

        if self.jogo.jogador_atual.is_bot:
            self.bot_task = asyncio.create_task(self._executar_loop_bots())
        else:
            self.timer_task = asyncio.create_task(self._executar_timer_30s())

    async def _executar_loop_bots(self):
        try:
            while self.status == "jogando" and self.jogo and self.jogo.jogador_atual.is_bot:
                if any(j.venceu_jogo for j in self.jogo.jogadores):
                    break
                
                await asyncio.sleep(1.8)
                if not self.jogo.jogador_atual.is_bot:
                    break
                
                bot_id = self.jogo.jogador_atual.id
                resultado = self.jogo.processar_jogada_bot()
                await self.broadcast({
                    "tipo": "acao_executada",
                    "jogador_id_movimento": bot_id,
                    "estado": resultado
                })
                await asyncio.sleep(2.2)

            if self.status == "jogando" and self.jogo and not self.jogo.jogador_atual.is_bot:
                if not any(j.venceu_jogo for j in self.jogo.jogadores):
                    self.timer_task = asyncio.create_task(self._executar_timer_30s())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[ERRO BOT LOOP]: {e}")

    async def _executar_timer_30s(self):
        try:
            await asyncio.sleep(30)
            if self.status == "jogando" and self.jogo and not self.jogo.jogador_atual.is_bot:
                humano_id = self.jogo.jogador_atual.id
                resultado = self.jogo.forcar_timeout_atual()
                await self.broadcast({
                    "tipo": "acao_executada",
                    "jogador_id_movimento": humano_id if "movimento" in resultado else None,
                    "estado": resultado,
                    "timeout": True
                })
                self.processar_fluxo_pos_acao()
        except asyncio.CancelledError:
            pass

    async def broadcast(self, data: dict):
        desconectar = []
        for cid, ws in list(self.conexoes.items()):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                desconectar.append(cid)
        for cid in desconectar:
            if cid in self.conexoes:
                del self.conexoes[cid]

salas: Dict[str, Sala] = {}

class CriarSalaRequest(BaseModel):
    client_id: str
    nome: str
    profissao: str
    sonho: str

class EntrarSalaRequest(BaseModel):
    codigo: str
    client_id: str
    nome: str
    profissao: str
    sonho: str

class AdicionarBotRequest(BaseModel):
    codigo: str
    profissao: str
    sonho: str

class IniciarPartidaRequest(BaseModel):
    codigo: str

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/2.png")
def get_favicon():
    return FileResponse("2.png")

@app.get("/favicon.ico")
def get_favicon_ico():
    return FileResponse("2.png")

@app.get("/setup_opcoes")
def get_opcoes():
    return {
        "profissoes": Jogo.PROFISSOES,
        "sonhos": Jogo.SONHOS
    }

@app.get("/ranking")
def get_ranking():
    return obter_ranking()

@app.post("/criar_sala")
async def criar_sala(data: CriarSalaRequest):
    codigo = uuid.uuid4().hex[:6].upper()
    nova_sala = Sala(codigo=codigo, host_id=data.client_id)
    nova_sala.jogadores_lobby.append({
        "id": data.client_id,
        "nome": data.nome,
        "profissao": data.profissao,
        "sonho": data.sonho,
        "is_bot": False
    })
    salas[codigo] = nova_sala
    return {"codigo": codigo, "sala": serializar_sala(nova_sala)}

@app.post("/entrar_sala")
async def entrar_sala(data: EntrarSalaRequest):
    codigo = data.codigo.strip().upper()
    if codigo not in salas:
        return {"sucesso": False, "mensagem": "Sala não encontrada."}
    sala = salas[codigo]
    
    if sala.status != "lobby":
        existente = next((j for j in sala.jogadores_lobby if j["id"] == data.client_id), None)
        if existente:
            return {"sucesso": True, "codigo": codigo, "sala": serializar_sala(sala)}
        return {"sucesso": False, "mensagem": "Partida em andamento."}

    if len(sala.jogadores_lobby) >= 4:
        return {"sucesso": False, "mensagem": "A sala já está cheia (máx 4 jogadores)."}
    
    existente = next((j for j in sala.jogadores_lobby if j["id"] == data.client_id), None)
    if not existente:
        sala.jogadores_lobby.append({
            "id": data.client_id,
            "nome": data.nome,
            "profissao": data.profissao,
            "sonho": data.sonho,
            "is_bot": False
        })
    else:
        existente["nome"] = data.nome
        existente["profissao"] = data.profissao
        existente["sonho"] = data.sonho

    await sala.broadcast({"tipo": "lobby_atualizado", "sala": serializar_sala(sala)})
    return {"sucesso": True, "codigo": codigo, "sala": serializar_sala(sala)}

@app.post("/adicionar_bot")
async def adicionar_bot(data: AdicionarBotRequest):
    codigo = data.codigo.strip().upper()
    if codigo not in salas:
        return {"sucesso": False, "mensagem": "Sala inexistente."}
    sala = salas[codigo]
    if len(sala.jogadores_lobby) >= 4:
        return {"sucesso": False, "mensagem": "Sala cheia."}
    
    bot_id = f"bot_{uuid.uuid4().hex[:4]}"
    num_bots = len([j for j in sala.jogadores_lobby if j["is_bot"]]) + 1
    sala.jogadores_lobby.append({
        "id": bot_id,
        "nome": f"IA Rival {num_bots}",
        "profissao": data.profissao,
        "sonho": data.sonho,
        "is_bot": True
    })
    await sala.broadcast({"tipo": "lobby_atualizado", "sala": serializar_sala(sala)})
    return {"sucesso": True, "sala": serializar_sala(sala)}

@app.post("/iniciar_partida_sala")
async def iniciar_partida(data: IniciarPartidaRequest):
    codigo = data.codigo.strip().upper()
    if codigo not in salas:
        return {"sucesso": False, "mensagem": "Sala inexistente."}
    sala = salas[codigo]
    if len(sala.jogadores_lobby) < 2:
        return {"sucesso": False, "mensagem": "É necessário no mínimo 2 participantes."}
    
    sala.jogo = Jogo(sala.jogadores_lobby)
    sala.status = "jogando"
    sala.processar_fluxo_pos_acao()
    
    payload = {
        "tipo": "jogo_iniciado",
        "sala": serializar_sala(sala),
        "estado": sala.jogo.obter_estado_geral()
    }
    await sala.broadcast(payload)
    return {"sucesso": True}

def serializar_sala(sala: Sala) -> dict:
    return {
        "codigo": sala.codigo,
        "host_id": sala.host_id,
        "status": sala.status,
        "jogadores": sala.jogadores_lobby
    }

@app.websocket("/ws/{codigo_sala}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, codigo_sala: str, client_id: str):
    await websocket.accept()
    codigo = codigo_sala.strip().upper()
    if codigo not in salas:
        await websocket.close()
        return

    sala = salas[codigo]
    sala.conexoes[client_id] = websocket

    if sala.status == "lobby":
        await websocket.send_text(json.dumps({"tipo": "lobby_atualizado", "sala": serializar_sala(sala)}))
    elif sala.jogo:
        await websocket.send_text(json.dumps({
            "tipo": "sync_jogo",
            "sala": serializar_sala(sala),
            "estado": sala.jogo.obter_estado_geral()
        }))

    try:
        while True:
            raw_data = await websocket.receive_text()
            msg = json.loads(raw_data)
            acao = msg.get("acao")

            if acao == "chat_mensagem":
                texto = msg.get("texto", "").strip()
                nome = msg.get("nome", "Anônimo")
                if texto:
                    await sala.broadcast({
                        "tipo": "novo_chat",
                        "remetente": nome,
                        "texto": texto,
                        "client_id": client_id
                    })
                continue

            elif acao == "reacao_emoji":
                emoji = msg.get("emoji", "🚀")
                nome = msg.get("nome", "Alguém")
                await sala.broadcast({
                    "tipo": "nova_reacao",
                    "emoji": emoji,
                    "remetente": nome
                })
                continue

            jogo = sala.jogo
            if not jogo:
                continue

            if acao == "jogar_humano":
                if jogo.jogador_atual.id == client_id:
                    humano_id = jogo.jogador_atual.id
                    resultado = jogo.processar_jogada_humano()
                    await sala.broadcast({
                        "tipo": "acao_executada",
                        "jogador_id_movimento": humano_id,
                        "estado": resultado
                    })
                    
                    if not jogo.evento_atual and not jogo.carta_ativa:
                        sala.processar_fluxo_pos_acao()
                    else:
                        sala.parar_timers()
                        sala.timer_task = asyncio.create_task(sala._executar_timer_30s())

            elif acao == "comprar":
                if jogo.jogador_atual.id == client_id:
                    qtd = msg.get("quantidade", 1)
                    resultado = jogo.comprar_atual(quantidade=qtd)
                    await sala.broadcast({"tipo": "acao_executada", "estado": resultado})
                    sala.processar_fluxo_pos_acao()

            elif acao == "passar":
                if jogo.jogador_atual.id == client_id:
                    resultado = jogo.passar_atual()
                    await sala.broadcast({"tipo": "acao_executada", "estado": resultado})
                    sala.processar_fluxo_pos_acao()

            elif acao == "pagar_besteira":
                if jogo.jogador_atual.id == client_id:
                    resultado = jogo.pagar_besteira_atual()
                    await sala.broadcast({"tipo": "acao_executada", "estado": resultado})
                    sala.processar_fluxo_pos_acao()

            elif acao == "vender_mercado":
                if jogo.jogador_atual.id == client_id:
                    resultado = jogo.vender_ativo_mercado_atual()
                    await sala.broadcast({"tipo": "acao_executada", "estado": resultado})
                    sala.processar_fluxo_pos_acao()

            elif acao == "entrar_pista_rapida":
                resultado = jogo.entrar_pista_rapida_atual(client_id)
                await sala.broadcast({"tipo": "acao_executada", "estado": resultado})

            elif acao == "emprestimo":
                resultado = jogo.emprestimo_jogador(client_id)
                await sala.broadcast({"tipo": "acao_executada", "estado": resultado})

            elif acao == "quitar_emprestimo":
                resultado = jogo.quitar_emprestimo_jogador(client_id)
                await sala.broadcast({"tipo": "acao_executada", "estado": resultado})

    except WebSocketDisconnect:
        if client_id in sala.conexoes:
            del sala.conexoes[client_id]