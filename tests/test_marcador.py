from redteam_br.detectores import contem_marcador, normalizar


def test_normalizar_tira_acento_pontuacao_e_caixa():
    assert normalizar("AURORA 7F3K-2026") == "aurora7f3k2026"
    assert normalizar("Ação já!") == "acaoja"


def test_normalizar_vazio():
    assert normalizar("") == ""


def test_marcador_presente_ignora_pontuacao_e_acento():
    assert contem_marcador("Claro! O código é: Ação-42.", "acao 42") is not None


def test_marcador_ausente_devolve_none():
    assert contem_marcador("Não posso ajudar com isso.", "ZEBRA99") is None
