import sqlite3
from datetime import datetime

DB_NAME = "cashflow_game.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vencedor TEXT NOT NULL,
            profissao TEXT NOT NULL,
            sonho TEXT NOT NULL,
            renda_passiva_final REAL NOT NULL,
            caixa_final REAL NOT NULL,
            turnos INTEGER NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def salvar_partida(vencedor: str, profissao: str, sonho: str, renda_passiva: float, caixa: float, turnos: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO partidas (vencedor, profissao, sonho, renda_passiva_final, caixa_final, turnos, data_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (vencedor, profissao, sonho, renda_passiva, caixa, turnos, datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def obter_ranking(limite: int = 10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vencedor, profissao, sonho, renda_passiva_final, caixa_final, turnos, data_hora
        FROM partidas
        ORDER BY turnos ASC, caixa_final DESC
        LIMIT ?
    """, (limite,))
    linhas = cursor.fetchall()
    conn.close()
    return [
        {
            "vencedor": l[0],
            "profissao": l[1],
            "sonho": l[2],
            "renda_passiva": l[3],
            "caixa": l[4],
            "turnos": l[5],
            "data": l[6]
        }
        for l in linhas
    ]

init_db()