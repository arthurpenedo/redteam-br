"""OllamaAlvo e criar_alvo, com urlopen simulado (sem Ollama)."""

import io
import json

import pytest

from redteam_br import alvo
from redteam_br.alvo import OllamaAlvo, RoteiroAlvo, criar_alvo


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def _ok(texto):
    return Resp(json.dumps({"message": {"content": texto}}).encode())


def test_corpo_da_requisicao_e_deterministico(monkeypatch):
    vistos = {}

    def urlopen(req, timeout):
        vistos["corpo"], vistos["url"], vistos["timeout"] = json.loads(req.data), req.full_url, timeout
        return _ok("Olá!")

    monkeypatch.setattr(alvo.urllib.request, "urlopen", urlopen)
    msgs = [{"role": "user", "content": "oi"}]
    assert OllamaAlvo(modelo="m:1b", seed=7, timeout=9).responder(msgs) == "Olá!"
    assert vistos["url"] == "http://localhost:11434/api/chat" and vistos["timeout"] == 9
    c = vistos["corpo"]
    assert c["model"] == "m:1b" and c["messages"] == msgs and c["stream"] is False
    assert c["options"] == {"temperature": 0, "seed": 7, "num_predict": 160}


def test_tenta_de_novo_depois_de_falha_de_rede(monkeypatch):
    esperas, chamadas = [], []

    def urlopen(req, timeout):
        chamadas.append(1)
        if len(chamadas) < 3:
            raise ConnectionError("Ollama ainda subindo")
        return _ok("pronto")

    monkeypatch.setattr(alvo.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(alvo.time, "sleep", esperas.append)
    assert OllamaAlvo().responder([]) == "pronto"
    assert esperas == [2, 4]  # espera cresce a cada tentativa


def test_desiste_na_terceira_falha(monkeypatch):
    chamadas = []

    def urlopen(req, timeout):
        chamadas.append(1)
        raise TimeoutError("sem resposta")

    monkeypatch.setattr(alvo.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(alvo.time, "sleep", lambda s: None)
    with pytest.raises(TimeoutError):
        OllamaAlvo().responder([])
    assert len(chamadas) == 3


def test_criar_alvo_aceita_com_e_sem_prefixo():
    assert criar_alvo("ollama:qwen2.5:1.5b").nome == "ollama:qwen2.5:1.5b"
    assert criar_alvo("llama3.2:1b").modelo == "llama3.2:1b"


def test_roteiro_alvo_chama_a_funcao():
    a = RoteiroAlvo(lambda msgs: msgs[-1]["content"].upper())
    assert a.responder([{"role": "user", "content": "oi"}]) == "OI"
