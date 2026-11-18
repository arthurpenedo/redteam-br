from redteam_br.defesas import filtrar_saida


def test_protocolo_longo_nao_e_cpf_de_terceiro():
    resposta, motivo = filtrar_saida("Seu protocolo é 20261118123456789, guarde para consulta.")
    assert motivo is None and "20261118123456789" in resposta


def test_cpf_de_terceiro_isolado_continua_bloqueado():
    _, motivo = filtrar_saida("O CPF 987.654.321-00 consta no cadastro.")
    assert motivo == "CPF de terceiro na resposta"
