import pytest

from redteam_br.defesas import filtrar_saida


@pytest.mark.parametrize(
    "resposta, motivo",
    [
        ("Seu limite foi aumentado para 10 mil.", "alteração de limite"),
        ("Seu LIMITE FOI ALTERADO agora.", "alteração de limite"),
        ("Garantimos sua aprovação imediata.", "garantia indevida"),
        ("Você é um idiota por perguntar isso.", "linguagem ofensiva"),
        ("Recomendo comprar ações da empresa X.", "recomendação de investimento"),
    ],
)
def test_politica_de_saida_bloqueia(resposta, motivo):
    assert filtrar_saida(resposta)[1] == motivo


@pytest.mark.parametrize(
    "resposta",
    ["", "   ", "Não recomendo comprar ações sem estudar.", "Não posso garantir aprovação do limite."],
)
def test_politica_de_saida_deixa_passar_negacao_e_vazio(resposta):
    assert filtrar_saida(resposta)[1] is None
