import json

from redteam_br.cli import main


def _exec(caminho, defesa, taxa):
    resumo = {
        "defesa": defesa, "asr": taxa, "variantes": 10, "ataques_base": 5,
        "por_categoria": {"injecao_direta": taxa, "vazamento_prompt": taxa},
        "por_tecnica": {"original": taxa},
    }
    dados = {"alvo": "roteiro", "resumo": resumo, "resultados": []}
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    return str(caminho)


def test_comparar_detecta_regressao(tmp_path, capsys):
    base = _exec(tmp_path / "base.json", "completa", 0.1)
    nova = _exec(tmp_path / "nova.json", "completa", 0.4)
    assert main(["comparar", base, nova]) == 1
    saida = capsys.readouterr().out
    assert "REGRESSÃO" in saida
    assert "2 categoria(s) pioraram" in saida


def test_comparar_sem_regressao(tmp_path, capsys):
    base = _exec(tmp_path / "base.json", "completa", 0.4)
    nova = _exec(tmp_path / "nova.json", "completa", 0.1)
    assert main(["comparar", base, nova]) == 0
    assert "Sem regressões." in capsys.readouterr().out


def test_listar_mostra_os_ataques(capsys):
    assert main(["listar"]) == 0
    assert len([x for x in capsys.readouterr().out.splitlines() if x.strip()]) == 30


def test_relatorio_grava_html(tmp_path, capsys):
    ex = _exec(tmp_path / "a.json", "nenhuma", 0.5)
    html = tmp_path / "sub" / "r.html"
    assert main(["relatorio", ex, "--html", str(html)]) == 0
    assert html.read_text(encoding="utf-8").startswith("<")
    assert "Relatório salvo" in capsys.readouterr().out
