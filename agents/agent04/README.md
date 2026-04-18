# Agente de Organização de Tarefas com Trello

Este projeto implementa um agente inteligente para gerenciamento de tarefas integrado ao Trello, utilizando o Google ADK para agentes LLM.

## Funcionalidades

- ✅ Adicionar tarefas com nome, descrição e data de vencimento opcional
- 📋 Listar tarefas (todas ou filtradas por status)
- 🔄 Mudar status de tarefas (A Fazer → Em Andamento → Concluído)
- ✏️ Editar tarefas (nome, descrição, data)
- 🗑️ Remover tarefas
- 📅 Gerar contexto temporal (data/hora atual)
- 🔍 Parsing flexível de datas (ex: "amanhã", "em 2 dias")

## Melhorias Implementadas

### Robustez
- Tratamento completo de erros e exceções
- Validação rigorosa de entrada
- Logging detalhado para depuração

### Performance
- Cache inteligente de cliente, board e listas do Trello
- Evita chamadas desnecessárias à API

### Flexibilidade
- Configuração via `config.json` (nomes de board/listas)
- Parsing de datas com `python-dateutil`
- Credenciais via `.env`

### Documentação
- Docstrings completas em todas as funções
- Comentários explicativos no código
- README detalhado
- Testes unitários com pytest

## Instalação

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure as credenciais no `.env`:
   ```
   TRELLO_API_KEY=your_key
   TRELLO_API_SECRET=your_secret
   TRELLO_TOKEN=your_token
   ```

3. Ajuste `config.json` se necessário (nomes padrão do board/listas).

## Uso

Execute o agente:
```python
from agenttaskmanager.agent import root_agent
# O agente iniciará perguntando sobre tarefas do dia
```

## Estrutura do Projeto

```
agents/agent04/
├── agenttaskmanager/
│   ├── __init__.py
│   └── agent.py          # Código principal do agente
├── config.json           # Configuração de board/listas
├── requirements.txt      # Dependências
├── test_agent.py         # Testes unitários
└── README.md             # Esta documentação
```

## Testes

Execute os testes:
```bash
pytest test_agent.py
```

## Logs

Os logs são salvos no console com nível INFO. Para mais detalhes, ajuste o nível em `logging.basicConfig`.

## Contribuição

Para contribuir:
1. Adicione testes para novas funcionalidades
2. Atualize a documentação
3. Siga as melhores práticas de código

## Licença

Este projeto é para fins educacionais.