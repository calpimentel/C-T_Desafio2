"""
Testes para o Agente de Organização de Tarefas

Executar com: pytest test_agent.py
"""

import pytest
from unittest.mock import patch, MagicMock
from agenttaskmanager.agent import parse_due_date, adicionar_tarefa, listar_tarefas

# Mock do cliente Trello
@patch('agenttaskmanager.agent.get_cached_client')
@patch('agenttaskmanager.agent.get_cached_board')
@patch('agenttaskmanager.agent.get_cached_lists')
def test_adicionar_tarefa_success(mock_lists, mock_board, mock_client):
    """Testa adição de tarefa com sucesso."""
    mock_list = MagicMock()
    mock_list.name = 'A FAZER'
    mock_list.add_card = MagicMock()
    mock_lists.return_value = [mock_list]

    result = adicionar_tarefa("Test Task", "Test Description", "amanhã")
    assert "✅" in result
    mock_list.add_card.assert_called_once()

def test_parse_due_date():
    """Testa parsing de datas."""
    assert parse_due_date("2023-10-01") is not None
    assert parse_due_date("invalid") is None
    assert parse_due_date("") is None

def test_adicionar_tarefa_validation():
    """Testa validação de entrada."""
    result = adicionar_tarefa("", "Desc")
    assert "❌ Nome da tarefa não pode ser vazio" in result

@patch('agenttaskmanager.agent.get_cached_board')
@patch('agenttaskmanager.agent.get_cached_lists')
def test_listar_tarefas(mock_lists, mock_board):
    """Testa listagem de tarefas."""
    mock_list = MagicMock()
    mock_list.name = 'A FAZER'
    mock_card = MagicMock()
    mock_card.name = 'Task'
    mock_card.desc = 'Desc'
    mock_card.due = None
    mock_card.id = '123'
    mock_list.list_cards.return_value = [mock_card]
    mock_lists.return_value = [mock_list]
    mock_board.return_value = None

    result = listar_tarefas("a fazer")
    assert isinstance(result, list)
    assert len(result) == 1