from dataclasses import dataclass, field
from typing import List, Optional
import random
from database import salvar_partida

@dataclass
class CartaOportunidade:
    titulo: str
    descricao: str
    custo_total: float
    entrada: float
    renda_mensal: float
    tipo: str = "imovel"
    preco_unitario: float = 0.0

@dataclass
class CartaBesteira:
    titulo: str
    valor: float

@dataclass
class CartaMercado:
    titulo: str
    descricao: str
    tipo_alvo: str
    alvo_nome: str
    preco_oferta: float

@dataclass
class CartaPistaRapida:
    titulo: str
    custo: float
    renda_mensal: float
    tipo: str

@dataclass
class Ativo:
    nome: str
    entrada: float
    renda_mensal: float
    tipo: str = "imovel"
    quantidade: int = 1
    preco_compra_unitario: float = 0.0

@dataclass
class Jogador:
    nome: str
    profissao: str
    salario: float
    despesas_fixas: float
    caixa: float
    sonho_titulo: str = ""
    sonho_custo: float = 0.0
    posicao: int = 0
    is_bot: bool = False
    ativos: List[Ativo] = field(default_factory=list)
    emprestimos: float = 0.0
    na_pista_rapida: bool = False
    renda_pista_rapida: float = 0.0
    venceu_jogo: bool = False

    @property
    def renda_passiva(self) -> float:
        return sum(ativo.renda_mensal * (ativo.quantidade if ativo.tipo == 'acao' else 1) for ativo in self.ativos)

    @property
    def juros_emprestimo(self) -> float:
        return self.emprestimos * 0.10

    @property
    def total_despesas(self) -> float:
        if self.na_pista_rapida:
            return 0.0
        return self.despesas_fixas + self.juros_emprestimo

    @property
    def fluxo_de_caixa(self) -> float:
        if self.na_pista_rapida:
            return self.renda_pista_rapida
        return (self.salario + self.renda_passiva) - self.total_despesas

    def saiu_da_corrida(self) -> bool:
        return self.renda_passiva > self.total_despesas

    def serializar(self) -> dict:
        return {
            "nome": self.nome,
            "profissao": self.profissao,
            "salario": self.salario,
            "despesas": self.total_despesas,
            "caixa": self.caixa,
            "renda_passiva": self.renda_passiva,
            "fluxo_de_caixa": self.fluxo_de_caixa,
            "emprestimos": self.emprestimos,
            "juros_emprestimo": self.juros_emprestimo,
            "sonho_titulo": self.sonho_titulo,
            "sonho_custo": self.sonho_custo,
            "posicao": self.posicao,
            "na_pista_rapida": self.na_pista_rapida,
            "saiu_da_corrida": self.saiu_da_corrida(),
            "venceu_jogo": self.venceu_jogo,
            "is_bot": self.is_bot,
            "ativos": [
                {
                    "nome": a.nome,
                    "entrada": a.entrada,
                    "renda": a.renda_mensal,
                    "tipo": a.tipo,
                    "quantidade": a.quantidade,
                    "preco_unitario": a.preco_compra_unitario
                }
                for a in self.ativos
            ]
        }

class Jogo:
    PROFISSOES = [
        {"nome": "Zelador", "salario": 1600.0, "despesas": 950.0, "caixa": 650.0},
        {"nome": "Técnico de TI", "salario": 3500.0, "despesas": 2100.0, "caixa": 1400.0},
        {"nome": "Advogado", "salario": 7500.0, "despesas": 4800.0, "caixa": 2700.0},
        {"nome": "Médico", "salario": 13000.0, "despesas": 9200.0, "caixa": 3800.0}
    ]

    SONHOS = [
        {"titulo": "Ilha Privativa no Caribe", "custo": 350000.0},
        {"titulo": "Viagem Espacial Orbital", "custo": 250000.0},
        {"titulo": "Mansão com Heliponto", "custo": 300000.0},
        {"titulo": "Fundação Beneficente Global", "custo": 200000.0}
    ]

    def __init__(self):
        self.tabuleiro_ratos = [
            {"id": 0, "tipo": "Payday"}, {"id": 1, "tipo": "Oportunidade"},
            {"id": 2, "tipo": "Besteira"}, {"id": 3, "tipo": "Oportunidade"},
            {"id": 4, "tipo": "Mercado"}, {"id": 5, "tipo": "Payday"},
            {"id": 6, "tipo": "Oportunidade"}, {"id": 7, "tipo": "Besteira"},
            {"id": 8, "tipo": "Oportunidade"}, {"id": 9, "tipo": "Mercado"},
            {"id": 10, "tipo": "Besteira"}, {"id": 11, "tipo": "Oportunidade"}
        ]

        self.tabuleiro_rapido = [
            {"id": 0, "tipo": "Cashflow Day"}, {"id": 1, "tipo": "Negócio Rápido"},
            {"id": 2, "tipo": "Sonho"}, {"id": 3, "tipo": "Negócio Rápido"},
            {"id": 4, "tipo": "Cashflow Day"}, {"id": 5, "tipo": "Negócio Rápido"},
            {"id": 6, "tipo": "Sonho"}, {"id": 7, "tipo": "Negócio Rápido"}
        ]

        self.baralho_oportunidades = [
            CartaOportunidade("Casa 2 Quartos", "Imóvel financiado com aluguel mensal fixo.", 60000, 1000, 300, tipo="imovel"),
            CartaOportunidade("Apartamento Studio", "Ótima localização para locação por temporada.", 90000, 1500, 450, tipo="imovel"),
            CartaOportunidade("Lavanderia Self-Service", "Negócio operando com equipe própria.", 10000, 3000, 950, tipo="imovel"),
            CartaOportunidade("Ações OK4U", "Ações de tecnologia cotadas a preço promocional de R$ 10 cada.", 0, 1000, 0, tipo="acao", preco_unitario=10.0),
            CartaOportunidade("Ações MYT4", "Ações farmacêuticas em oferta por R$ 20 cada (pagam dividendos).", 0, 1000, 50, tipo="acao", preco_unitario=20.0)
        ]

        self.baralho_mercado = [
            CartaMercado("Comprador de Apartamento Studio", "Investidor procura Studios e paga R$ 4.000 por unidade!", "imovel", "Apartamento Studio", 4000.0),
            CartaMercado("Comprador de Casa 2 Quartos", "Fundo imobiliário oferece R$ 3.000 pela entrada da Casa 2 Quartos!", "imovel", "Casa 2 Quartos", 3000.0),
            CartaMercado("Boom nas Ações OK4U", "As ações da OK4U dispararam para R$ 40 cada! Venda suas cotas com alto lucro.", "acao", "Ações OK4U", 40.0),
            CartaMercado("Alta nas Ações MYT4", "Ações MYT4 subiram para R$ 50 cada! Excelente janela para realizar lucros.", "acao", "Ações MYT4", 50.0)
        ]

        self.baralho_besteiras = [
            CartaBesteira("Smartphone Top de Linha", 1200),
            CartaBesteira("Jantar de Luxo e Comemoração", 450),
            CartaBesteira("Conserto Urgente do Veículo", 800),
            CartaBesteira("Cafeteira Expresso Importada", 500)
        ]

        self.baralho_rapido_negocios = [
            CartaPistaRapida("Franquia de Fast Food", 100000, 10000, 'negocio'),
            CartaPistaRapida("Shopping Center Regional", 350000, 30000, 'negocio'),
            CartaPistaRapida("Parque Solar de Energia", 200000, 18000, 'negocio'),
            CartaPistaRapida("Rede de Farmácias", 150000, 14000, 'negocio')
        ]

        self.jogador_humano: Optional[Jogador] = None
        self.jogador_bot: Optional[Jogador] = None
        self.carta_ativa = None
        self.turno_atual: str = "humano"
        self.partida_iniciada: bool = False
        self.total_turnos: int = 0

    def iniciar_partida(self, profissao_nome: str, sonho_titulo: str):
        prof_h = next((p for p in self.PROFISSOES if p["nome"] == profissao_nome), self.PROFISSOES[1])
        sonho_h = next((s for s in self.SONHOS if s["titulo"] == sonho_titulo), self.SONHOS[0])
        self.jogador_humano = Jogador(
            nome="Você (Humano)", profissao=prof_h["nome"], salario=prof_h["salario"],
            despesas_fixas=prof_h["despesas"], caixa=prof_h["caixa"],
            sonho_titulo=sonho_h["titulo"], sonho_custo=sonho_h["custo"], is_bot=False
        )

        profs_bot = [p for p in self.PROFISSOES if p["nome"] != prof_h["nome"]]
        prof_b = random.choice(profs_bot)
        sonhos_bot = [s for s in self.SONHOS if s["titulo"] != sonho_h["titulo"]]
        sonho_b = random.choice(sonhos_bot)
        self.jogador_bot = Jogador(
            nome="IA Rival", profissao=prof_b["nome"], salario=prof_b["salario"],
            despesas_fixas=prof_b["despesas"], caixa=prof_b["caixa"],
            sonho_titulo=sonho_b["titulo"], sonho_custo=sonho_b["custo"], is_bot=True
        )

        self.turno_atual = "humano"
        self.partida_iniciada = True
        self.carta_ativa = None
        self.total_turnos = 0

    def obter_estado_geral(self) -> dict:
        return {
            "partida_iniciada": self.partida_iniciada,
            "turno_atual": self.turno_atual,
            "total_turnos": self.total_turnos,
            "humano": self.jogador_humano.serializar() if self.jogador_humano else None,
            "bot": self.jogador_bot.serializar() if self.jogador_bot else None
        }

    def mover_jogador(self, jogador: Jogador) -> dict:
        tabuleiro = self.tabuleiro_rapido if jogador.na_pista_rapida else self.tabuleiro_ratos
        dado = random.randint(1, 6)
        pos_anterior = jogador.posicao
        nova_pos = (pos_anterior + dado) % len(tabuleiro)

        passou_payday = (pos_anterior + dado) >= len(tabuleiro) or nova_pos == 0
        if passou_payday:
            jogador.caixa += jogador.fluxo_de_caixa

        jogador.posicao = nova_pos
        casa_atual = tabuleiro[nova_pos]["tipo"]
        return {"dado": dado, "nova_pos": nova_pos, "casa_atual": casa_atual, "passou_payday": passou_payday}

    def jogar_turno_humano(self) -> dict:
        self.total_turnos += 1
        j = self.jogador_humano
        mov = self.mover_jogador(j)
        self.carta_ativa = None
        evento = {}

        if not j.na_pista_rapida:
            if mov["casa_atual"] == "Oportunidade":
                self.carta_ativa = random.choice(self.baralho_oportunidades)
                evento = {
                    "tipo": "oportunidade", "subtipo": self.carta_ativa.tipo,
                    "titulo": self.carta_ativa.titulo, "descricao": self.carta_ativa.descricao,
                    "entrada": self.carta_ativa.entrada, "renda": self.carta_ativa.renda_mensal,
                    "preco_unitario": self.carta_ativa.preco_unitario
                }
            elif mov["casa_atual"] == "Mercado":
                self.carta_ativa = random.choice(self.baralho_mercado)
                possui_ativo = any(a.nome == self.carta_ativa.alvo_nome for a in j.ativos)
                evento = {
                    "tipo": "mercado", "titulo": self.carta_ativa.titulo,
                    "descricao": self.carta_ativa.descricao, "alvo_nome": self.carta_ativa.alvo_nome,
                    "preco_oferta": self.carta_ativa.preco_oferta, "possui_ativo": possui_ativo
                }
                if not possui_ativo:
                    self.turno_atual = "bot"
            elif mov["casa_atual"] == "Besteira":
                self.carta_ativa = random.choice(self.baralho_besteiras)
                evento = {"tipo": "besteira", "titulo": self.carta_ativa.titulo, "valor": self.carta_ativa.valor}
            elif mov["casa_atual"] == "Payday":
                self.turno_atual = "bot"
        else:
            if mov["casa_atual"] == "Negócio Rápido":
                self.carta_ativa = random.choice(self.baralho_rapido_negocios)
                evento = {"tipo": "pista_negocio", "titulo": self.carta_ativa.titulo, "custo": self.carta_ativa.custo, "renda": self.carta_ativa.renda_mensal}
            elif mov["casa_atual"] == "Sonho":
                self.carta_ativa = CartaPistaRapida(j.sonho_titulo, j.sonho_custo, 0, 'sonho')
                evento = {"tipo": "sonho", "titulo": j.sonho_titulo, "custo": j.sonho_custo}
            else:
                self.turno_atual = "bot"

        estado = self.obter_estado_geral()
        estado.update({"movimento": mov, "evento": evento})
        return estado

    def pagar_besteira_humano(self) -> dict:
        j = self.jogador_humano
        if not self.carta_ativa or not isinstance(self.carta_ativa, CartaBesteira):
            return {"sucesso": False, "mensagem": "Nenhuma despesa ativa."}

        valor = self.carta_ativa.valor
        titulo = self.carta_ativa.titulo

        if j.caixa < valor:
            falta = valor - j.caixa
            emp = (int(falta // 1000) + 1) * 1000
            j.caixa += emp
            j.emprestimos += emp

        j.caixa -= valor
        self.carta_ativa = None
        self.turno_atual = "bot"

        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": f"💸 Você pagou R$ {valor:.2f} por: {titulo}."})
        return estado

    def vender_ativo_mercado_humano(self) -> dict:
        j = self.jogador_humano
        if not self.carta_ativa or not isinstance(self.carta_ativa, CartaMercado):
            return {"sucesso": False, "mensagem": "Nenhuma oferta ativa."}

        alvo = next((a for a in j.ativos if a.nome == self.carta_ativa.alvo_nome), None)
        if not alvo:
            return {"sucesso": False, "mensagem": "Você não possui este ativo."}

        if alvo.tipo == "acao":
            valor_total = alvo.quantidade * self.carta_ativa.preco_oferta
            j.caixa += valor_total
            j.ativos.remove(alvo)
            msg = f"Você vendeu {alvo.quantidade} cotas de {alvo.nome} por R$ {valor_total:.2f}!"
        else:
            valor_total = self.carta_ativa.preco_oferta
            j.caixa += valor_total
            j.ativos.remove(alvo)
            msg = f"Você vendeu {alvo.nome} por R$ {valor_total:.2f}!"

        self.carta_ativa = None
        self.turno_atual = "bot"
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": msg})
        return estado

    def comprar_humano(self, quantidade: int = 1) -> dict:
        j = self.jogador_humano
        if not self.carta_ativa:
            return {"sucesso": False, "mensagem": "Nenhuma carta ativa."}

        if isinstance(self.carta_ativa, CartaOportunidade):
            if self.carta_ativa.tipo == "acao":
                custo_total = self.carta_ativa.preco_unitario * quantidade
                if j.caixa < custo_total:
                    return {"sucesso": False, "mensagem": f"Caixa insuficiente para comprar {quantidade} ações!"}
                
                j.caixa -= custo_total
                ativo_existente = next((a for a in j.ativos if a.nome == self.carta_ativa.titulo), None)
                if ativo_existente:
                    ativo_existente.quantidade += quantidade
                else:
                    j.ativos.append(Ativo(
                        nome=self.carta_ativa.titulo, entrada=custo_total, renda_mensal=self.carta_ativa.renda_mensal,
                        tipo="acao", quantidade=quantidade, preco_compra_unitario=self.carta_ativa.preco_unitario
                    ))
                msg = f"Você comprou {quantidade} cotas de {self.carta_ativa.titulo}!"
            else:
                if j.caixa < self.carta_ativa.entrada:
                    return {"sucesso": False, "mensagem": "Caixa insuficiente para a entrada!"}
                j.caixa -= self.carta_ativa.entrada
                j.ativos.append(Ativo(self.carta_ativa.titulo, self.carta_ativa.entrada, self.carta_ativa.renda_mensal, tipo="imovel"))
                msg = f"Você comprou: {self.carta_ativa.titulo}!"

        elif isinstance(self.carta_ativa, CartaPistaRapida):
            if j.caixa < self.carta_ativa.custo:
                return {"sucesso": False, "mensagem": "Caixa insuficiente!"}
            j.caixa -= self.carta_ativa.custo
            if self.carta_ativa.tipo == 'negocio':
                j.renda_pista_rapida += self.carta_ativa.renda_mensal
            elif self.carta_ativa.tipo == 'sonho':
                j.venceu_jogo = True
                salvar_partida(j.nome, j.profissao, j.sonho_titulo, j.renda_passiva, j.caixa, self.total_turnos)
            msg = f"Você adquiriu: {self.carta_ativa.titulo}!"

        self.carta_ativa = None
        self.turno_atual = "bot"
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": msg})
        return estado

    def passar_humano(self) -> dict:
        self.carta_ativa = None
        self.turno_atual = "bot"
        return self.obter_estado_geral()

    def executar_turno_bot(self) -> dict:
        b = self.jogador_bot
        
        # IA entra na Pista Rápida assim que puder
        if b.saiu_da_corrida() and not b.na_pista_rapida:
            b.na_pista_rapida = True
            b.posicao = 0
            b.renda_pista_rapida = b.renda_passiva * 10
            b.caixa += b.renda_pista_rapida

        mov = self.mover_jogador(b)
        trilha_nome = "Pista Rápida" if b.na_pista_rapida else "Corrida dos Ratos"
        log_bot = f"🤖 IA tirou {mov['dado']} na {trilha_nome} e parou em <strong>{mov['casa_atual']}</strong>."

        if not b.na_pista_rapida:
            if mov["casa_atual"] == "Oportunidade":
                carta = random.choice(self.baralho_oportunidades)
                if carta.tipo == "acao":
                    qtd = 100
                    custo = carta.preco_unitario * qtd
                    if b.caixa >= custo and carta.preco_unitario <= 20:
                        b.caixa -= custo
                        b.ativos.append(Ativo(carta.titulo, custo, carta.renda_mensal, tipo="acao", quantidade=qtd, preco_compra_unitario=carta.preco_unitario))
                        log_bot += f" Comprou {qtd} ações de {carta.titulo}."
                else:
                    roi = carta.renda_mensal / carta.entrada
                    if roi >= 0.12 and b.caixa >= carta.entrada:
                        b.caixa -= carta.entrada
                        b.ativos.append(Ativo(carta.titulo, carta.entrada, carta.renda_mensal, tipo="imovel"))
                        log_bot += f" Comprou '{carta.titulo}' (+R$ {carta.renda_mensal:.0f}/mês)."
            elif mov["casa_atual"] == "Mercado":
                acao = next((a for a in b.ativos if a.tipo == "acao"), None)
                if acao:
                    ganho = acao.quantidade * 40.0
                    b.caixa += ganho
                    b.ativos.remove(acao)
                    log_bot += f" Vendeu ações no mercado por R$ {ganho:.0f}!"
            elif mov["casa_atual"] == "Besteira":
                besteira = random.choice(self.baralho_besteiras)
                if b.caixa < besteira.valor:
                    falta = besteira.valor - b.caixa
                    emp = (int(falta // 1000) + 1) * 1000
                    b.caixa += emp
                    b.emprestimos += emp
                b.caixa -= besteira.valor
                log_bot += f" Gastou com {besteira.titulo} (-R$ {besteira.valor:.0f})."
        else:
            if mov["casa_atual"] == "Negócio Rápido":
                carta = random.choice(self.baralho_rapido_negocios)
                if b.caixa >= carta.custo:
                    b.caixa -= carta.custo
                    b.renda_pista_rapida += carta.renda_mensal
                    log_bot += f" Adquiriu grande negócio: {carta.titulo}!"
            elif mov["casa_atual"] == "Sonho":
                if b.caixa >= b.sonho_custo:
                    b.caixa -= b.sonho_custo
                    b.venceu_jogo = True
                    salvar_partida(b.nome, b.profissao, b.sonho_titulo, b.renda_passiva, b.caixa, self.total_turnos)
                    log_bot += f" 👑 A IA COMPROU O SONHO DELA ({b.sonho_titulo}) E VENCEU!"

        self.turno_atual = "humano"
        estado = self.obter_estado_geral()
        estado.update({"movimento": mov, "log_bot": log_bot})
        return estado

    def entrar_pista_rapida_humano(self) -> dict:
        j = self.jogador_humano
        j.na_pista_rapida = True
        j.posicao = 0
        j.renda_pista_rapida = j.renda_passiva * 10
        j.caixa += j.renda_pista_rapida
        return self.obter_estado_geral()

    def emprestimo_humano(self) -> dict:
        j = self.jogador_humano
        j.caixa += 1000.0
        j.emprestimos += 1000.0
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": "Empréstimo de R$ 1.000 concedido."})
        return estado

    def quitar_emprestimo_humano(self) -> dict:
        j = self.jogador_humano
        if j.emprestimos < 1000.0:
            return {"sucesso": False, "mensagem": "Sem dívidas para quitar."}
        if j.caixa < 1000.0:
            return {"sucesso": False, "mensagem": "Caixa insuficiente para quitar."}
        j.caixa -= 1000.0
        j.emprestimos -= 1000.0
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": "R$ 1.000 de dívida quitada!"})
        return estado