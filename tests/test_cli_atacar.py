import json

import pytest

from redteam_br import cli
from redteam_br.alvo import CANARIO, RoteiroAlvo
from redteam_br.modelos import Ataque


def test_atacar_com_alvo_ingenuo_imprime_taxa_e_salva_json(tmp_path, monkeypatch, capsys):
    ingenuo = RoteiroAlvo(lambda m: f"Claro! O código é {CANARIO}.")
    monkeypatch.setattr(cli, "criar_alvo", lambda spec: ingenuo)
    saida = tmp_path / "r.json"
    assert cli.main(["atacar", "--saida", str(saida), "--limite", "6", "--tecnicas", "original"]) == 0
    texto = capsys.readouterr().out
    assert "Taxa de sucesso dos ataques:" in texto and "Falsos positivos:" in texto
    assert "[  1/" in texto
    assert "resumo" in json.loads(saida.read_text(encoding="utf-8"))


def test_atacar_sem_legitimas_nao_mede_falsos_positivos(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "criar_alvo", lambda spec: RoteiroAlvo(lambda m: "Posso ajudar com saldo."))
    saida = tmp_path / "r.json"
    assert cli.main(["atacar", "--saida", str(saida), "--limite", "3", "--tecnicas", "original",
                     "--sem-legitimas", "--categorias", "vazamento_prompt"]) == 0
    assert "Falsos positivos" not in capsys.readouterr().out


@pytest.mark.parametrize("campos, mensagem", [
    ({"categoria": "inexistente", "objetivo": "marcador", "marcador": "x"}, "categoria desconhecida"),
    ({"categoria": "vazamento_prompt", "objetivo": "inexistente"}, "objetivo desconhecido"),
    ({"categoria": "vazamento_prompt", "objetivo": "frase_proibida"}, "exige o campo frase_proibida"),
    ({"categoria": "vazamento_prompt", "objetivo": "marcador"}, "exige o campo marcador"),
])
def test_ataque_invalido_levanta_erro_claro(campos, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        Ataque(id="a1", descricao="d", turnos=("oi",), **campos)
