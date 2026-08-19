from dataclasses import dataclass, field
from typing import List, Optional, Dict
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
    descricao: str = ""

@dataclass
class CartaMercado:
    titulo: str
    descricao: str
    tipo_alvo: str
    alvo_nome: str
    preco_oferta: float
    fator_multiplicador: float = 1.0

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
    id: str
    nome: str
    profissao: str
    salario: float
    despesas_fixas: float
    caixa: float
    sonho_titulo: str
    sonho_custo: float
    is_bot: bool
    cor: str
    icone: str
    posicao: int = 0
    ativos: List[Ativo] = field(default_factory=list)
    emprestimos: float = 0.0
    na_pista_rapida: bool = False
    renda_pista_rapida: float = 0.0
    venceu_jogo: bool = False
    turnos_sem_besteira: int = 0

    @property
    def renda_passiva(self) -> float:
        total = 0.0
        for a in self.ativos:
            if a.tipo in ["acao", "cripto"]:
                total += a.renda_mensal * a.quantidade
            else:
                total += a.renda_mensal
        return total

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
            "id": self.id,
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
            "cor": self.cor,
            "icone": self.icone,
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

    CORES_ICONES = [
        {"cor": "#facc15", "icone": "🐭"},
        {"cor": "#38bdf8", "icone": "🤖"},
        {"cor": "#4ade80", "icone": "🐱"},
        {"cor": "#c084fc", "icone": "🦊"}
    ]

    def __init__(self, configs_jogadores: List[dict]):
        # Tabuleiro Oficial Equilibrado: 3 Besteiras (2, 7, 10), 2 Mercados (4, 9), 2 Paydays (0, 5), 5 Oportunidades
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
            CartaOportunidade("Lavanderia Self-Service", "Negócio automatizado com alta margem de lucro.", 12000, 3000, 950, tipo="imovel"),
            CartaOportunidade("Franquia de Cafeteria", "Loja em galeria comercial com fluxo contínuo.", 25000, 5000, 1200, tipo="imovel"),
            CartaOportunidade("Startup de IA", "Participação com distribuição mensal de lucros.", 15000, 4000, 1400, tipo="imovel"),
            CartaOportunidade("Kitnet Universitária", "Aluguel estável para estudantes.", 35000, 1200, 350, tipo="imovel"),
            CartaOportunidade("Ações OK4U", "Ações de tecnologia com grande potencial de valorização.", 0, 1000, 0, tipo="acao", preco_unitario=10.0),
            CartaOportunidade("Ações MYT4", "Biotecnologia farmacêutica com dividendos mensais.", 0, 1000, 1.0, tipo="acao", preco_unitario=20.0),
            CartaOportunidade("Fundo Imob FII11", "Cotas de galpões logísticos com proventos mensais.", 0, 1000, 2.5, tipo="acao", preco_unitario=50.0),
            CartaOportunidade("Criptoativo BTC-Node", "Cotas digitais para operações no mercado.", 0, 500, 0, tipo="cripto", preco_unitario=25.0)
        ]

        self.baralho_mercado = [
            CartaMercado("Boom em Studios", "Fundo Imobiliário adquire Studios com valorização recorde!", "imovel", "Apartamento Studio", 4800.0),
            CartaMercado("Comprador de Casa 2 Quartos", "Investidor particular oferece proposta excelente pela sua casa!", "imovel", "Casa 2 Quartos", 3500.0),
            CartaMercado("Aquisição de Lavanderia", "Rede multinacional quer comprar sua lavanderia!", "imovel", "Lavanderia Self-Service", 8000.0),
            CartaMercado("Compra de Startup de IA", "Grupo de tecnologia compra sua cota de Startup por valor multiplicado!", "imovel", "Startup de IA", 12000.0),
            CartaMercado("Comprador de Kitnet", "Investidor local compra sua Kitnet Universitária à vista!", "imovel", "Kitnet Universitária", 3800.0),
            CartaMercado("Expansão de Cafeterias", "Rede de franquias adquire sua cafeteria!", "imovel", "Franquia de Cafeteria", 14000.0),
            CartaMercado("Rally das Ações OK4U", "As ações OK4U subiram para R$ 40,00 por cota! Momento ideal para venda.", "acao", "Ações OK4U", 40.0),
            CartaMercado("Alta Histórica MYT4", "As ações de Biotecnologia MYT4 dispararam para R$ 50,00 por cota!", "acao", "Ações MYT4", 50.0),
            CartaMercado("Valorização do FII11", "Os Fundos Imobiliários FII11 valorizaram para R$ 85,00 por cota!", "acao", "Fundo Imob FII11", 85.0),
            CartaMercado("Explosão do BTC-Node", "O Criptoativo BTC-Node disparou para R$ 75,00 por cota!", "cripto", "Criptoativo BTC-Node", 75.0)
        ]

        self.baralho_besteiras = [
            CartaBesteira("Smartphone Top de Linha", 1200, "Lançamento imperdível com novas tecnologias."),
            CartaBesteira("Jantar de Luxo e Comemoração", 450, "Festa em restaurante sofisticado."),
            CartaBesteira("Conserto Urgente do Veículo", 850, "Troca emergencial de pneus e amortecedores."),
            CartaBesteira("Cafeteira Expresso Importada", 600, "Novo aparelho de conveniência pessoal."),
            CartaBesteira("Imposto Inesperado / Multa", 700, "Cobrança tributária de regularização."),
            CartaBesteira("Viagem de Fim de Semana", 950, "Passagens de última hora.")
        ]

        self.baralho_rapido_negocios = [
            CartaPistaRapida("Franquia de Fast Food", 100000, 10000, 'negocio'),
            CartaPistaRapida("Shopping Center Regional", 350000, 30000, 'negocio'),
            CartaPistaRapida("Parque Solar de Energia", 200000, 18000, 'negocio'),
            CartaPistaRapida("Rede de Farmácias", 150000, 14000, 'negocio'),
            CartaPistaRapida("Concessionária de Veículos", 280000, 25000, 'negocio'),
            CartaPistaRapida("Complexo de Clínicas Médicas", 400000, 38000, 'negocio')
        ]

        self.jogadores: List[Jogador] = []
        for i, cfg in enumerate(configs_jogadores):
            prof = next((p for p in self.PROFISSOES if p["nome"] == cfg["profissao"]), self.PROFISSOES[0])
            sonho = next((s for s in self.SONHOS if s["titulo"] == cfg["sonho"]), self.SONHOS[0])
            visual = self.CORES_ICONES[i % len(self.CORES_ICONES)]
            
            self.jogadores.append(Jogador(
                id=str(cfg.get("id", i)),
                nome=cfg.get("nome", f"Jogador {i+1}"),
                profissao=prof["nome"],
                salario=prof["salario"],
                despesas_fixas=prof["despesas"],
                caixa=prof["caixa"],
                sonho_titulo=sonho["titulo"],
                sonho_custo=sonho["custo"],
                is_bot=cfg.get("is_bot", False),
                cor=visual["cor"],
                icone=visual["icone"]
            ))

        self.indice_atual: int = 0
        self.carta_ativa = None
        self.total_turnos: int = 0
        self.evento_atual: Optional[dict] = None

    @property
    def jogador_atual(self) -> Jogador:
        return self.jogadores[self.indice_atual]

    @property
    def vencedor(self) -> Optional[Jogador]:
        return next((j for j in self.jogadores if j.venceu_jogo), None)

    def avancar_turno(self):
        if self.vencedor:
            return
        self.carta_ativa = None
        self.evento_atual = None
        self.indice_atual = (self.indice_atual + 1) % len(self.jogadores)

    def obter_estado_geral(self) -> dict:
        v = self.vencedor
        return {
            "indice_atual": self.indice_atual,
            "total_turnos": self.total_turnos,
            "jogador_atual_id": self.jogador_atual.id,
            "is_bot_atual": self.jogador_atual.is_bot,
            "evento_atual": self.evento_atual,
            "jogo_finalizado": (v is not None),
            "vencedor": v.serializar() if v else None,
            "jogadores": [j.serializar() for j in self.jogadores]
        }

    def mover_jogador(self, jogador: Jogador) -> dict:
        tabuleiro = self.tabuleiro_rapido if jogador.na_pista_rapida else self.tabuleiro_ratos
        dado = random.randint(1, 6)

        pos_anterior = jogador.posicao
        tam = len(tabuleiro)

        posicoes_percorridas = [(pos_anterior + step) % tam for step in range(1, dado + 1)]
        nova_pos = posicoes_percorridas[-1]

        paydays_passados = sum(1 for p in posicoes_percorridas if tabuleiro[p]["tipo"] in ["Payday", "Cashflow Day"])

        if paydays_passados > 0:
            jogador.caixa += (jogador.fluxo_de_caixa * paydays_passados)

        jogador.posicao = nova_pos
        casa_atual = tabuleiro[nova_pos]["tipo"]

        return {
            "dado": dado,
            "nova_pos": nova_pos,
            "casa_atual": casa_atual,
            "passou_payday": (paydays_passados > 0),
            "qtd_paydays": paydays_passados
        }

    def processar_jogada_humano(self) -> dict:
        if self.vencedor:
            return self.obter_estado_geral()

        j = self.jogador_atual
        self.total_turnos += 1
        mov = self.mover_jogador(j)
        self.carta_ativa = None
        self.evento_atual = None
        evento = {}

        if not j.na_pista_rapida:
            if mov["casa_atual"] == "Oportunidade":
                self.carta_ativa = random.choice(self.baralho_oportunidades)
                evento = {
                    "tipo": "oportunidade",
                    "subtipo": self.carta_ativa.tipo,
                    "titulo": self.carta_ativa.titulo,
                    "descricao": self.carta_ativa.descricao,
                    "entrada": self.carta_ativa.entrada,
                    "renda": self.carta_ativa.renda_mensal,
                    "preco_unitario": self.carta_ativa.preco_unitario
                }
                self.evento_atual = evento

            elif mov["casa_atual"] == "Mercado":
                # Prioriza ofertas para ativos que o jogador possui
                nomes_meus_ativos = [a.nome for a in j.ativos]
                cartas_compativeis = [c for c in self.baralho_mercado if c.alvo_nome in nomes_meus_ativos]
                
                if cartas_compativeis and random.random() < 0.85:
                    self.carta_ativa = random.choice(cartas_compativeis)
                else:
                    self.carta_ativa = random.choice(self.baralho_mercado)

                possui_ativo = any(a.nome == self.carta_ativa.alvo_nome for a in j.ativos)
                ativo_obj = next((a for a in j.ativos if a.nome == self.carta_ativa.alvo_nome), None)

                valor_total = 0.0
                qtd_cotas = 0
                if possui_ativo and ativo_obj:
                    if ativo_obj.tipo in ["acao", "cripto"]:
                        valor_total = ativo_obj.quantidade * self.carta_ativa.preco_oferta
                        qtd_cotas = ativo_obj.quantidade
                    else:
                        valor_total = self.carta_ativa.preco_oferta
                        qtd_cotas = 1

                evento = {
                    "tipo": "mercado",
                    "titulo": self.carta_ativa.titulo,
                    "descricao": self.carta_ativa.descricao,
                    "alvo_nome": self.carta_ativa.alvo_nome,
                    "preco_oferta": self.carta_ativa.preco_oferta,
                    "possui_ativo": possui_ativo,
                    "valor_total_venda": valor_total,
                    "qtd_cotas": qtd_cotas,
                    "subtipo": ativo_obj.tipo if ativo_obj else "imovel"
                }
                self.evento_atual = evento

            elif mov["casa_atual"] == "Besteira":
                self.carta_ativa = random.choice(self.baralho_besteiras)
                evento = {
                    "tipo": "besteira",
                    "titulo": self.carta_ativa.titulo,
                    "descricao": self.carta_ativa.descricao,
                    "valor": self.carta_ativa.valor
                }
                self.evento_atual = evento

            elif mov["casa_atual"] == "Payday":
                self.avancar_turno()

        else:
            if mov["casa_atual"] == "Negócio Rápido":
                self.carta_ativa = random.choice(self.baralho_rapido_negocios)
                evento = {
                    "tipo": "pista_negocio",
                    "titulo": self.carta_ativa.titulo,
                    "custo": self.carta_ativa.custo,
                    "renda": self.carta_ativa.renda_mensal
                }
                self.evento_atual = evento
            elif mov["casa_atual"] == "Sonho":
                self.carta_ativa = CartaPistaRapida(j.sonho_titulo, j.sonho_custo, 0, 'sonho')
                evento = {
                    "tipo": "sonho",
                    "titulo": j.sonho_titulo,
                    "custo": j.sonho_custo
                }
                self.evento_atual = evento
            else:
                self.avancar_turno()

        estado = self.obter_estado_geral()
        estado.update({"movimento": mov, "evento": evento})
        return estado

    def processar_jogada_bot(self) -> dict:
        if self.vencedor:
            return self.obter_estado_geral()

        b = self.jogador_atual
        self.total_turnos += 1

        if b.saiu_da_corrida() and not b.na_pista_rapida:
            b.na_pista_rapida = True
            b.posicao = 0
            b.renda_pista_rapida = max(b.renda_passiva * 10, 50000.0)
            b.caixa += b.renda_pista_rapida

        mov = self.mover_jogador(b)
        trilha_nome = "Pista Rápida" if b.na_pista_rapida else "Corrida dos Ratos"
        log_bot = f"{b.icone} {b.nome} tirou {mov['dado']} e parou em <strong>{mov['casa_atual']}</strong> ({trilha_nome})."

        if not b.na_pista_rapida:
            if mov["casa_atual"] == "Oportunidade":
                carta = random.choice(self.baralho_oportunidades)
                if carta.tipo in ["acao", "cripto"]:
                    max_cotas = int(b.caixa // carta.preco_unitario) if carta.preco_unitario > 0 else 0
                    qtd = min(20, max_cotas)
                    custo = carta.preco_unitario * qtd
                    if qtd > 0:
                        b.caixa -= custo
                        b.ativos.append(Ativo(
                            nome=carta.titulo,
                            entrada=custo,
                            renda_mensal=carta.renda_mensal,
                            tipo=carta.tipo,
                            quantidade=qtd,
                            preco_compra_unitario=carta.preco_unitario
                        ))
                        log_bot += f" Comprou {qtd} cotas de {carta.titulo}."
                else:
                    if b.caixa >= carta.entrada:
                        b.caixa -= carta.entrada
                        b.ativos.append(Ativo(
                            nome=carta.titulo,
                            entrada=carta.entrada,
                            renda_mensal=carta.renda_mensal,
                            tipo="imovel"
                        ))
                        log_bot += f" Comprou '{carta.titulo}' (+R$ {carta.renda_mensal:.0f}/mês)."

            elif mov["casa_atual"] == "Mercado":
                nomes_ativos = [a.nome for a in b.ativos]
                cartas_compativeis = [c for c in self.baralho_mercado if c.alvo_nome in nomes_ativos]
                if cartas_compativeis:
                    carta = random.choice(cartas_compativeis)
                    alvo = next((a for a in b.ativos if a.nome == carta.alvo_nome), None)
                    if alvo:
                        if alvo.tipo in ["acao", "cripto"]:
                            ganho = alvo.quantidade * carta.preco_oferta
                            b.caixa += ganho
                            b.ativos.remove(alvo)
                            log_bot += f" Vendeu {alvo.quantidade}x {alvo.nome} no Mercado por R$ {ganho:.2f}!"
                        else:
                            ganho = carta.preco_oferta
                            b.caixa += ganho
                            b.ativos.remove(alvo)
                            log_bot += f" Vendeu {alvo.nome} no Mercado por R$ {ganho:.2f}!"
                else:
                    log_bot += " Mercado sem ofertas compatíveis com a carteira."

            elif mov["casa_atual"] == "Besteira":
                besteira = random.choice(self.baralho_besteiras)
                if b.caixa < besteira.valor:
                    falta = besteira.valor - b.caixa
                    emp = min((int(falta // 1000) + 1) * 1000, int(10000.0 - b.emprestimos))
                    if emp > 0:
                        b.caixa += emp
                        b.emprestimos += emp
                b.caixa -= besteira.valor
                log_bot += f" Teve imprevisto: {besteira.titulo} (-R$ {besteira.valor:.0f})."

            self.avancar_turno()

        else:
            if mov["casa_atual"] == "Negócio Rápido":
                carta = random.choice(self.baralho_rapido_negocios)
                if b.caixa >= carta.custo:
                    b.caixa -= carta.custo
                    b.renda_pista_rapida += carta.renda_mensal
                    log_bot += f" Adquiriu {carta.titulo}!"
                self.avancar_turno()
            elif mov["casa_atual"] == "Sonho":
                if b.caixa >= b.sonho_custo:
                    b.caixa -= b.sonho_custo
                    b.venceu_jogo = True
                    salvar_partida(b.nome, b.profissao, b.sonho_titulo, b.renda_passiva, b.caixa, self.total_turnos)
                    log_bot += f" 👑 {b.nome} COMPROU O SONHO ({b.sonho_titulo}) E VENCEU O JOGO!"
                else:
                    self.avancar_turno()
            else:
                self.avancar_turno()

        estado = self.obter_estado_geral()
        estado.update({"movimento": mov, "log_bot": log_bot})
        return estado

    def forcar_timeout_atual(self) -> dict:
        if self.vencedor:
            return self.obter_estado_geral()

        j = self.jogador_atual
        if self.evento_atual or self.carta_ativa:
            if isinstance(self.carta_ativa, CartaBesteira):
                return self.pagar_besteira_atual()
            else:
                return self.passar_atual()

        mov = self.mover_jogador(j)
        self.total_turnos += 1
        log_msg = f"⏱️ Tempo de {j.nome} esgotou! Jogou automaticamente: tirou {mov['dado']} ({mov['casa_atual']})."

        if not j.na_pista_rapida and mov["casa_atual"] == "Besteira":
            besteira = random.choice(self.baralho_besteiras)
            if j.caixa < besteira.valor:
                falta = besteira.valor - j.caixa
                emp = min((int(falta // 1000) + 1) * 1000, int(10000.0 - j.emprestimos))
                if emp > 0:
                    j.caixa += emp
                    j.emprestimos += emp
            j.caixa -= besteira.valor
            log_msg += f" Pagou despesa de R$ {besteira.valor:.2f}."

        self.avancar_turno()
        estado = self.obter_estado_geral()
        estado.update({"movimento": mov, "mensagem": log_msg, "timeout": True})
        return estado

    def comprar_atual(self, quantidade: int = 1) -> dict:
        j = self.jogador_atual
        if not self.carta_ativa:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Nenhuma carta ativa."})
            return estado

        if isinstance(self.carta_ativa, CartaOportunidade):
            if self.carta_ativa.tipo in ["acao", "cripto"]:
                custo_total = self.carta_ativa.preco_unitario * quantidade
                if j.caixa < custo_total:
                    estado = self.obter_estado_geral()
                    estado.update({"sucesso": False, "mensagem": f"Caixa insuficiente para comprar {quantidade} cotas (Custo: R$ {custo_total:.2f})!"})
                    return estado
                
                j.caixa -= custo_total
                ativo_existente = next((a for a in j.ativos if a.nome == self.carta_ativa.titulo), None)
                if ativo_existente:
                    ativo_existente.quantidade += quantidade
                    ativo_existente.entrada += custo_total
                else:
                    j.ativos.append(Ativo(
                        nome=self.carta_ativa.titulo,
                        entrada=custo_total,
                        renda_mensal=self.carta_ativa.renda_mensal,
                        tipo=self.carta_ativa.tipo,
                        quantidade=quantidade,
                        preco_compra_unitario=self.carta_ativa.preco_unitario
                    ))
                msg = f"{j.nome} comprou {quantidade} cotas de {self.carta_ativa.titulo} por R$ {custo_total:.2f}!"
            else:
                if j.caixa < self.carta_ativa.entrada:
                    estado = self.obter_estado_geral()
                    estado.update({"sucesso": False, "mensagem": f"Caixa insuficiente para a entrada de R$ {self.carta_ativa.entrada:.2f}!"})
                    return estado
                
                j.caixa -= self.carta_ativa.entrada
                j.ativos.append(Ativo(
                    nome=self.carta_ativa.titulo,
                    entrada=self.carta_ativa.entrada,
                    renda_mensal=self.carta_ativa.renda_mensal,
                    tipo="imovel"
                ))
                msg = f"{j.nome} investiu em: {self.carta_ativa.titulo} (+R$ {self.carta_ativa.renda_mensal:.2f}/mês)!"
            self.avancar_turno()

        elif isinstance(self.carta_ativa, CartaPistaRapida):
            if j.caixa < self.carta_ativa.custo:
                estado = self.obter_estado_geral()
                estado.update({"sucesso": False, "mensagem": f"Caixa insuficiente para adquirir {self.carta_ativa.titulo}!"})
                return estado
            
            j.caixa -= self.carta_ativa.custo
            if self.carta_ativa.tipo == 'negocio':
                j.renda_pista_rapida += self.carta_ativa.renda_mensal
                msg = f"{j.nome} adquiriu: {self.carta_ativa.titulo}!"
                self.avancar_turno()
            elif self.carta_ativa.tipo == 'sonho':
                j.venceu_jogo = True
                salvar_partida(j.nome, j.profissao, j.sonho_titulo, j.renda_passiva, j.caixa, self.total_turnos)
                msg = f"👑 {j.nome} COMPROU O SONHO '{j.sonho_titulo}' E VENCEU O JOGO!"

        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": msg})
        return estado

    def pagar_besteira_atual(self) -> dict:
        j = self.jogador_atual
        if not self.carta_ativa or not isinstance(self.carta_ativa, CartaBesteira):
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Nenhuma despesa ativa."})
            return estado

        valor = self.carta_ativa.valor
        titulo = self.carta_ativa.titulo

        if j.caixa < valor:
            falta = valor - j.caixa
            emp = min((int(falta // 1000) + 1) * 1000, int(10000.0 - j.emprestimos))
            if emp > 0:
                j.caixa += emp
                j.emprestimos += emp

        j.caixa -= valor
        self.avancar_turno()

        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": f"💸 {j.nome} pagou R$ {valor:.2f} por: {titulo}."})
        return estado

    def vender_ativo_mercado_atual(self) -> dict:
        j = self.jogador_atual
        if not self.carta_ativa or not isinstance(self.carta_ativa, CartaMercado):
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Nenhuma oferta ativa."})
            return estado

        alvo = next((a for a in j.ativos if a.nome == self.carta_ativa.alvo_nome), None)
        if not alvo:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Você não possui este ativo."})
            return estado

        if alvo.tipo in ["acao", "cripto"]:
            valor_total = alvo.quantidade * self.carta_ativa.preco_oferta
            j.caixa += valor_total
            j.ativos.remove(alvo)
            msg = f"{j.nome} vendeu {alvo.quantidade} cotas de {alvo.nome} por R$ {valor_total:.2f}!"
        else:
            valor_total = self.carta_ativa.preco_oferta
            j.caixa += valor_total
            j.ativos.remove(alvo)
            msg = f"{j.nome} vendeu {alvo.nome} por R$ {valor_total:.2f}!"

        self.avancar_turno()
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": msg})
        return estado

    def passar_atual(self) -> dict:
        self.avancar_turno()
        return self.obter_estado_geral()

    def entrar_pista_rapida_atual(self, jogador_id: str) -> dict:
        j = next((p for p in self.jogadores if p.id == jogador_id), None)
        if j and j.saiu_da_corrida():
            j.na_pista_rapida = True
            j.posicao = 0
            j.renda_pista_rapida = max(j.renda_passiva * 10, 50000.0)
            j.caixa += j.renda_pista_rapida
        return self.obter_estado_geral()

    def emprestimo_jogador(self, jogador_id: str) -> dict:
        j = next((p for p in self.jogadores if p.id == jogador_id), None)
        if not j:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Jogador não encontrado."})
            return estado
        if j.emprestimos + 1000.0 > 10000.0:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Limite máximo de empréstimo atingido (Máx: R$ 10.000,00)!"})
            return estado

        j.caixa += 1000.0
        j.emprestimos += 1000.0
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": f"Empréstimo de R$ 1.000 concedido (Total: R$ {j.emprestimos:.2f})."})
        return estado

    def quitar_emprestimo_jogador(self, jogador_id: str) -> dict:
        j = next((p for p in self.jogadores if p.id == jogador_id), None)
        if not j:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Jogador não encontrado."})
            return estado
        if j.emprestimos < 1000.0:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Sem dívidas para quitar."})
            return estado
        if j.caixa < 1000.0:
            estado = self.obter_estado_geral()
            estado.update({"sucesso": False, "mensagem": "Caixa insuficiente para quitar."})
            return estado
        
        j.caixa -= 1000.0
        j.emprestimos -= 1000.0
        estado = self.obter_estado_geral()
        estado.update({"sucesso": True, "mensagem": "R$ 1.000 de dívida quitada!"})
        return estado