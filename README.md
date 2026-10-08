# redteam-br

[![CI](https://github.com/arthurpenedo/redteam-br/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurpenedo/redteam-br/actions/workflows/ci.yml)
[![Red-teaming](https://github.com/arthurpenedo/redteam-br/actions/workflows/redteam.yml/badge.svg)](https://github.com/arthurpenedo/redteam-br/actions/workflows/redteam.yml)

> Red-teaming de LLMs em português: ataca o assistente virtual de um banco fictício com
> 30 ataques do OWASP Top 10 para LLMs, multiplicados por 6 técnicas de disfarce, e mede
> quanto cada camada de defesa reduz a taxa de sucesso, sem bloquear clientes de verdade.

🚧 Primeira execução contra um modelo aberto em andamento. README completo em breve.

```bash
pip install -e ".[dev]"
redteam-br listar
redteam-br atacar --alvo ollama:qwen2.5:1.5b --defesa nenhuma --saida nenhuma.json
redteam-br relatorio nenhuma.json prompt.json completa.json --html site/index.html
```
