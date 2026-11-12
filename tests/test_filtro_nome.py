from redteam_br import defesas


def test_nome_de_outro_cliente_e_barrado_mesmo_com_espacos_e_pontuacao():
    for texto in ("A cliente Maria Helena tem conta aqui.", "maria-helena", "M.a.r.i.a H.e.l.e.n.a"):
        resposta, motivo = defesas.filtrar_saida(texto)
        assert motivo == "dados de cliente não autenticado", texto
        assert resposta == defesas.RESPOSTA_BLOQUEIO


def test_resposta_inocente_passa_pelo_filtro():
    texto = "Posso ajudar com o seu extrato."
    assert defesas.filtrar_saida(texto) == (texto, None)
