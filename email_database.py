#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager


class EmailDatabase:
    def __init__(self, db_path: str = "emails.db"):
        """Inicializa o banco de dados de emails com conexão persistente"""
        self.db_path = db_path
        self._conn = None
        self._prepared_statements = {}
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna uma conexão persistente com o banco"""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA cache_size = 10000")
            self._conn.execute("PRAGMA temp_store = MEMORY")
        return self._conn

    def _get_prepared_statement(self, name: str, sql: str) -> sqlite3.Cursor:
        """Retorna um prepared statement reutilizável"""
        if name not in self._prepared_statements:
            conn = self._get_connection()
            self._prepared_statements[name] = conn.prepare(sql)
        return self._prepared_statements[name]

    @contextmanager
    def _transaction(self):
        """Context manager para transações"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def init_database(self):
        """Inicializa o banco de dados criando as tabelas"""
        try:
            with open('database_schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()

            with self._transaction() as conn:
                conn.executescript(schema)
        except FileNotFoundError:
            raise FileNotFoundError("Arquivo database_schema.sql não encontrado")

    def adicionar_usuario(self, nome: str, email: str) -> int:
        """Adiciona um novo usuário ao banco de dados"""
        sql = "INSERT INTO usuarios (nome, email) VALUES (?, ?)"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (nome, email))
            return cursor.lastrowid

    def adicionar_email(self, remetente: str, destinatario: str, assunto: str, 
                       corpo: str = "", categoria_id: Optional[int] = None) -> int:
        """Adiciona um novo email ao banco de dados"""
        sql = """INSERT INTO emails (remetente, destinatario, assunto, corpo, categoria_id)
                 VALUES (?, ?, ?, ?, ?)"""
        with self._transaction() as conn:
            cursor = conn.execute(sql, (remetente, destinatario, assunto, corpo, categoria_id))
            return cursor.lastrowid

    def buscar_emails(self, destinatario: Optional[str] = None, 
                     categoria_id: Optional[int] = None, 
                     lido: Optional[bool] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """Busca emails com filtros opcionais"""
        conditions = ["1=1"]
        params = []

        if destinatario:
            conditions.append("e.destinatario = ?")
            params.append(destinatario)
        if categoria_id:
            conditions.append("e.categoria_id = ?")
            params.append(categoria_id)
        if lido is not None:
            conditions.append("e.lido = ?")
            params.append(1 if lido else 0)
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT e.*, c.nome as categoria_nome 
            FROM emails e 
            LEFT JOIN categorias c ON e.categoria_id = c.id 
            WHERE {where_clause}
            ORDER BY e.data_envio DESC 
            LIMIT ?
        """
        params.append(limit)
        conn = self._get_connection()
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def marcar_como_lido(self, email_id: int) -> bool:
        """Marca um email como lido"""
        sql = "UPDATE emails SET lido = 1 WHERE id = ?"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (email_id,))
            return cursor.rowcount > 0

    def marcar_importante(self, email_id: int, importante: bool = True) -> bool:
        """Marca um email como importante ou não"""
        sql = "UPDATE emails SET importante = ? WHERE id = ?"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (1 if importante else 0, email_id))
            return cursor.rowcount > 0

    def arquivar_email(self, email_id: int) -> bool:
        """Arquiva um email"""
        sql = "UPDATE emails SET arquivado = 1 WHERE id = ?"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (email_id,))
            return cursor.rowcount > 0

    def obter_categorias(self) -> List[Dict[str, Any]]:
        """Retorna todas as categorias"""
        sql = "SELECT * FROM categorias ORDER BY nome"
        conn = self._get_connection()
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def adicionar_categoria(self, nome: str, descricao: str = "", cor: str = "#007bff") -> int:
        """Adiciona uma nova categoria"""
        sql = "INSERT INTO categorias (nome, descricao, cor) VALUES (?, ?, ?)"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (nome, descricao, cor))
            return cursor.lastrowid

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        conn = self._get_connection()
        with self._transaction() as conn:
            total_emails = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
            nao_lidos = conn.execute("SELECT COUNT(*) FROM emails WHERE lido = 0").fetchone()[0]
            importantes = conn.execute("SELECT COUNT(*) FROM emails WHERE importante = 1").fetchone()[0]
            cursor = conn.execute("""
                SELECT c.nome, COUNT(e.id) as total
                FROM categorias c
                LEFT JOIN emails e ON c.id = e.categoria_id
                GROUP BY c.id, c.nome
                ORDER BY total DESC
            """)
            por_categoria = dict(cursor.fetchall())

            return {
                'total_emails': total_emails,
                'nao_lidos': nao_lidos,
                'importantes': importantes,
                'por_categoria': por_categoria
            }

    def deletar_email(self, email_id: int) -> bool:
        """Deleta um email do banco de dados"""
        sql = "DELETE FROM emails WHERE id = ?"
        with self._transaction() as conn:
            cursor = conn.execute(sql, (email_id,))
            return cursor.rowcount > 0

    def buscar_emails_por_texto(self, texto: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca emails por texto no assunto ou corpo"""
        sql = """
            SELECT e.*, c.nome as categoria_nome 
            FROM emails e 
            LEFT JOIN categorias c ON e.categoria_id = c.id 
            WHERE e.assunto LIKE ? OR e.corpo LIKE ?
            ORDER BY e.data_envio DESC 
            LIMIT ?
        """
        search_term = f"%{texto}%"
        conn = self._get_connection()
        cursor = conn.execute(sql, (search_term, search_term, limit))
        return [dict(row) for row in cursor.fetchall()]

    def obter_emails_nao_lidos(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna emails não lidos"""
        return self.buscar_emails(lido=False, limit=limit)

    def obter_emails_importantes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna emails marcados como importantes"""
        sql = """
            SELECT e.*, c.nome as categoria_nome 
            FROM emails e 
            LEFT JOIN categorias c ON e.categoria_id = c.id 
            WHERE e.importante = 1
            ORDER BY e.data_envio DESC 
            LIMIT ?
        """
        conn = self._get_connection()
        cursor = conn.execute(sql, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def limpar_emails_antigos(self, dias: int = 365) -> int:
        """Remove emails mais antigos que o número de dias especificado"""
        sql = "DELETE FROM emails WHERE data_envio < datetime('now', '-{} days')".format(dias)
        with self._transaction() as conn:
            cursor = conn.execute(sql)
            return cursor.rowcount
    
    def fechar_conexao(self):
        """Fecha a conexão com o banco de dados"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.fechar_conexao()


def main():
    """Função principal para demonstração do uso"""
    with EmailDatabase() as db:
        print("=== Banco de Dados de Emails")
        print("\n1. Adicionando emails de exemplo...")
                user_id = db.adicionar_usuario("João Silva", "joao@exemplo.com")
        
	emails_exemplo = [
            ("contato@empresa.com", "joao@exemplo.com", "Bem-vindo à nossa empresa!", 
             "Olá João, seja bem-vindo ao nosso time...", 1),
            ("amigo@email.com", "joao@exemplo.com", "Fim de semana", 
             "Oi João, vamos sair no fim de semana?", 2),
            ("promo@loja.com", "joao@exemplo.com", "Oferta especial!", 
             "Aproveite nossas ofertas especiais...", 5),
            ("newsletter@tech.com", "joao@exemplo.com", "Novidades da semana", 
             "Confira as últimas novidades em tecnologia...", 6)
        ]
        
        for remetente, destinatario, assunto, corpo, categoria_id in emails_exemplo:
            db.adicionar_email(remetente, destinatario, assunto, corpo, categoria_id)
        
        print("\n2. Estatísticas do banco de dados:")
        stats = db.obter_estatisticas()
        print(f"Total de emails: {stats['total_emails']}")
        print(f"Emails não lidos: {stats['nao_lidos']}")
        print(f"Emails importantes: {stats['importantes']}")
        
        print("\n3. Emails por categoria:")
        for categoria, total in stats['por_categoria'].items():
            print(f"  {categoria}: {total}")
        
        print("\n4. Emails recentes:")
        emails = db.buscar_emails(limit=5)
        for email in emails:
            status = "📧" if email['lido'] else "📬"
            print(f"{status} {email['assunto']} - {email['remetente']}")
        
        print("\n5. Busca por 'empresa':")
        resultados = db.buscar_emails_por_texto("empresa", limit=3)
        for email in resultados:
            print(f"  {email['assunto']} - {email['remetente']}")
        
        print("\n✅ Sucesso!")


if __name__ == "__main__":
    main() 
