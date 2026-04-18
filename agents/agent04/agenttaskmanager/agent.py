"""
Agente de Organização de Tarefas com Integração ao Trello

Este módulo implementa um agente inteligente para gerenciamento de tarefas usando a API do Trello.
Funcionalidades incluem adicionar, listar, editar, remover tarefas e mudar status.

Melhorias implementadas:
- Tratamento de erros e exceções
- Validação de entrada
- Manipulação flexível de datas com dateutil
- Cache para otimização de performance
- Logging para depuração
- Configuração via arquivo JSON
- Funcionalidades adicionais (remover, editar)
- Documentação completa com docstrings

Dependências: google-adk, py-trello, python-dotenv, python-dateutil, pytest
"""

import aiohttp
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser as date_parser
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from trello import TrelloClient

# Compatibilidade de exceção aiohttp
try:
    from aiohttp import client_exceptions
    if not hasattr(aiohttp, 'ClientConnectorDNSError'):
        if hasattr(client_exceptions, 'ClientConnectorDNSError'):
            aiohttp.ClientConnectorDNSError = client_exceptions.ClientConnectorDNSError
        elif hasattr(client_exceptions, 'ClientConnectorError'):
            aiohttp.ClientConnectorDNSError = client_exceptions.ClientConnectorError
        else:
            logger = logging.getLogger(__name__)
            logger.warning('aiohttp não expõe ClientConnectorDNSError nem ClientConnectorError.')
except Exception as exc:
    logging.getLogger(__name__).warning('Falha ao aplicar fallback de exceção aiohttp: %s', exc)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Caminho base do pacote
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis de ambiente
load_dotenv(BASE_DIR / '.env')

# Carregar configuração
config_path = BASE_DIR / 'config.json'
if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    BOARD_NAME = config.get('board_name', 'DIO')
    TODO_LIST_NAME = config.get('todo_list_name', 'A FAZER')
    DOING_LIST_NAME = config.get('doing_list_name', 'EM ANDAMENTO')
    DONE_LIST_NAME = config.get('done_list_name', 'CONCLUIDO')
    logger.info('Configuração carregada com sucesso.')
else:
    logger.warning('Arquivo config.json não encontrado. Usando valores padrão.')
    BOARD_NAME = 'DIO'
    TODO_LIST_NAME = 'A FAZER'
    DOING_LIST_NAME = 'EM ANDAMENTO'
    DONE_LIST_NAME = 'CONCLUIDO'

# Credenciais do Trello
API_KEY = os.getenv('TRELLO_API_KEY')
API_SECRET = os.getenv('TRELLO_API_SECRET')
TOKEN = os.getenv('TRELLO_TOKEN')

# Verificar credenciais apenas quando necessário
if not all([API_KEY, API_SECRET, TOKEN]):
    logger.warning('Credenciais do Trello não encontradas. Algumas funcionalidades requerem login.')

# Cache para otimização
_cache = {}

def get_cached_client():
    """Retorna o cliente Trello cached para evitar reinicializações."""
    if 'client' not in _cache:
        _cache['client'] = TrelloClient(api_key=API_KEY, api_secret=API_SECRET, token=TOKEN)
        logger.info("Cliente Trello inicializado e cached.")
    return _cache['client']

def get_cached_board():
    """Retorna o board cached."""
    if 'board' not in _cache:
        client = get_cached_client()
        boards = client.list_boards()
        board = next((b for b in boards if b.name == BOARD_NAME), None)
        if not board:
            raise ValueError(f"Board '{BOARD_NAME}' não encontrado.")
        _cache['board'] = board
        logger.info(f"Board '{BOARD_NAME}' cached.")
    return _cache['board']

def get_cached_lists():
    """Retorna as listas cached."""
    if 'lists' not in _cache:
        board = get_cached_board()
        _cache['lists'] = board.list_lists()
        logger.info("Listas cached.")
    return _cache['lists']

def get_temporal_context():
    """
    Gera o contexto temporal atual.

    Returns:
        str: Data e hora atual no formato YYYY/MM/DD HH:MM:SS.
    """
    now = datetime.now()
    return now.strftime('%Y/%m/%d %H:%M:%S')

def parse_due_date(due_date: str) -> str:
    """
    Parseia e formata a data de vencimento para ISO 8601.

    Args:
        due_date (str): Data em formato flexível (ex: "amanhã", "2023-10-01").

    Returns:
        str: Data em formato ISO 8601 ou None se inválida.
    """
    if not due_date:
        return None
    try:
        due_parsed = date_parser.parse(due_date)
        if due_parsed.tzinfo is None:
            due_parsed = due_parsed.replace(tzinfo=timezone.utc)
        else:
            due_parsed = due_parsed.astimezone(timezone.utc)
        return due_parsed.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except (ValueError, TypeError) as exc:
        logger.warning(f"Data inválida: {due_date} - {exc}")
        return None

def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str = None):
    """
    Adiciona uma nova tarefa ao Trello.

    Args:
        nome_da_task (str): Nome da tarefa.
        descricao_da_task (str): Descrição da tarefa.
        due_date (str, optional): Data de vencimento em formato flexível.

    Returns:
        str: Mensagem de sucesso ou erro.
    """
    try:
        # Validação de entrada
        if not nome_da_task.strip():
            return "❌ Nome da tarefa não pode ser vazio."
        if not descricao_da_task.strip():
            return "❌ Descrição da tarefa não pode ser vazia."

        client = get_cached_client()
        board = get_cached_board()
        listas = get_cached_lists()

        # Encontrar lista "A FAZER"
        minha_lista = next((l for l in listas if l.name.upper() in [TODO_LIST_NAME.upper(), 'TO DO']), None)
        if not minha_lista:
            return f"❌ Lista '{TODO_LIST_NAME}' não encontrada."

        # Formatar data
        due_iso = parse_due_date(due_date)

        # Criar card
        minha_lista.add_card(name=nome_da_task, desc=descricao_da_task, due=due_iso)
        logger.info(f"Tarefa '{nome_da_task}' criada com sucesso.")
        return f"✅ Tarefa '{nome_da_task}' criada com sucesso."

    except Exception as e:
        logger.error(f"Erro ao criar tarefa: {str(e)}")
        return f"❌ Erro ao criar tarefa: {str(e)}"

def listar_tarefas(status: str = "todas"):
    """
    Lista e filtra as tarefas do board.

    Args:
        status (str): Filtro por status ("todas", "a fazer", "em andamento", "concluido").

    Returns:
        list: Lista de dicionários com tarefas ou mensagem de erro.
    """
    try:
        board = get_cached_board()
        listas = get_cached_lists()

        # Filtrar listas
        if status.lower() == "todas":
            listas_filtradas = listas
        elif status.lower() == "a fazer":
            listas_filtradas = [l for l in listas if l.name.upper() in [TODO_LIST_NAME.upper(), 'TO DO', 'TODO']]
        elif status.lower() == "em andamento":
            listas_filtradas = [l for l in listas if l.name.upper() in [DOING_LIST_NAME.upper(), 'DOING']]
        elif status.lower() == "concluido":
            listas_filtradas = [l for l in listas if l.name.upper() in [DONE_LIST_NAME.upper(), 'DONE']]
        else:
            return "❌ Status inválido. Use: 'todas', 'a fazer', 'em andamento' ou 'concluido'."

        tarefas = []
        for lista in listas_filtradas:
            cards = lista.list_cards()
            for card in cards:
                tarefas.append({
                    "nome": card.name,
                    "descricao": card.desc,
                    "vencimento": card.due,
                    "status": lista.name,
                    "id": card.id
                })

        logger.info(f"Listadas {len(tarefas)} tarefas com filtro '{status}'.")
        return tarefas

    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {str(e)}")
        return f"❌ Erro ao listar tarefas: {str(e)}"

def mudar_status_tarefa(nome_da_task: str, novo_status: str) -> str:
    """
    Muda o status de uma tarefa existente.

    Args:
        nome_da_task (str): Nome da tarefa.
        novo_status (str): Novo status ("a fazer", "em andamento", "concluido").

    Returns:
        str: Mensagem de sucesso ou erro.
    """
    try:
        # Validação
        if not nome_da_task.strip():
            return "❌ Nome da tarefa não pode ser vazio."

        board = get_cached_board()
        listas = get_cached_lists()

        # Mapear status
        status_map = {
            "a fazer": TODO_LIST_NAME,
            "em andamento": DOING_LIST_NAME,
            "concluido": DONE_LIST_NAME
        }
        nome_lista_destino = status_map.get(novo_status.lower())
        if not nome_lista_destino:
            return "❌ Status inválido. Use: 'a fazer', 'em andamento' ou 'concluido'."

        # Encontrar lista destino
        lista_destino = next((l for l in listas if l.name.upper() == nome_lista_destino.upper()), None)
        if not lista_destino:
            return f"❌ Lista '{nome_lista_destino}' não encontrada."

        # Buscar card
        card_encontrado = None
        lista_origem = None
        for lista in listas:
            for card in lista.list_cards():
                if card.name == nome_da_task:
                    card_encontrado = card
                    lista_origem = lista
                    break
            if card_encontrado:
                break

        if not card_encontrado:
            return f"❌ Tarefa '{nome_da_task}' não encontrada."

        # Mover
        card_encontrado.change_list(lista_destino.id)
        logger.info(f"Tarefa '{nome_da_task}' movida de '{lista_origem.name}' para '{lista_destino.name}'.")
        return f"🟩 Tarefa '{nome_da_task}' movida: {lista_origem.name} -> {lista_destino.name}"

    except Exception as e:
        logger.error(f"Erro ao mudar status: {str(e)}")
        return f"❌ Erro ao mudar status: {str(e)}"

def remover_tarefa(nome_da_task: str) -> str:
    """
    Remove uma tarefa do Trello.

    Args:
        nome_da_task (str): Nome da tarefa a remover.

    Returns:
        str: Mensagem de sucesso ou erro.
    """
    try:
        if not nome_da_task.strip():
            return "❌ Nome da tarefa não pode ser vazio."

        listas = get_cached_lists()

        # Buscar card
        card_encontrado = None
        for lista in listas:
            for card in lista.list_cards():
                if card.name == nome_da_task:
                    card_encontrado = card
                    break
            if card_encontrado:
                break

        if not card_encontrado:
            return f"❌ Tarefa '{nome_da_task}' não encontrada."

        card_encontrado.delete()
        logger.info(f"Tarefa '{nome_da_task}' removida.")
        return f"🗑️ Tarefa '{nome_da_task}' removida com sucesso."

    except Exception as e:
        logger.error(f"Erro ao remover tarefa: {str(e)}")
        return f"❌ Erro ao remover tarefa: {str(e)}"

def editar_tarefa(nome_da_task: str, novo_nome: str = None, nova_descricao: str = None, nova_due_date: str = None) -> str:
    """
    Edita uma tarefa existente.

    Args:
        nome_da_task (str): Nome atual da tarefa.
        novo_nome (str, optional): Novo nome.
        nova_descricao (str, optional): Nova descrição.
        nova_due_date (str, optional): Nova data de vencimento.

    Returns:
        str: Mensagem de sucesso ou erro.
    """
    try:
        if not nome_da_task.strip():
            return "❌ Nome da tarefa não pode ser vazio."

        listas = get_cached_lists()

        # Buscar card
        card_encontrado = None
        for lista in listas:
            for card in lista.list_cards():
                if card.name == nome_da_task:
                    card_encontrado = card
                    break
            if card_encontrado:
                break

        if not card_encontrado:
            return f"❌ Tarefa '{nome_da_task}' não encontrada."

        # Atualizar campos
        updates = {}
        if novo_nome:
            updates['name'] = novo_nome
        if nova_descricao:
            updates['desc'] = nova_descricao
        if nova_due_date:
            updates['due'] = parse_due_date(nova_due_date)

        if updates:
            card_encontrado.update(**updates)
            logger.info(f"Tarefa '{nome_da_task}' editada.")
            return f"✏️ Tarefa '{nome_da_task}' editada com sucesso."
        else:
            return "ℹ️ Nenhum campo para atualizar."

    except Exception as e:
        logger.error(f"Erro ao editar tarefa: {str(e)}")
        return f"❌ Erro ao editar tarefa: {str(e)}"

# Agente principal
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Agente de Organização de Tarefas Avançado',
    instruction="""
    Você é um agente avançado de organização de tarefas com integração ao Trello.
    Sua função é gerenciar tarefas de forma inteligente, perguntando ao usuário sobre suas atividades diárias e criando cards no Trello.

    Comportamento:
    - Inicie sempre perguntando quais são as tarefas do dia, informando a data atual via get_temporal_context.
    - Pergunte datas de vencimento em formato natural (ex: "amanhã", "em 2 dias") e confirme antes de criar.
    - Ofereça resumos diários das tarefas pendentes.
    - Seja proativo: sugira mover tarefas para "Em Andamento" ou "Concluído" baseado no contexto.

    Funcionalidades disponíveis:
    1. Adicionar tarefas (com nome, descrição e data opcional)
    2. Listar tarefas (todas ou filtradas por status)
    3. Mudar status de tarefas
    4. Remover tarefas
    5. Editar tarefas (nome, descrição, data)
    6. Gerar contexto temporal

    Sempre confirme ações críticas e forneça feedback claro.
    """,
    tools=[
        get_temporal_context,
        adicionar_tarefa,
        listar_tarefas,
        mudar_status_tarefa,
        remover_tarefa,
        editar_tarefa
    ]
)