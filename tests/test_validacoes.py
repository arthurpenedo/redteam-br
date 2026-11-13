import pytest

from redteam_br.detectores import vazou_outra_cliente
from redteam_br.execucao import carregar_ataques
from redteam_br.modelos import Ataque


def test_injecao_indireta_sem_documento_e_rejeitada():
    with pytest.raises(ValueError, match="exige um documento"):
        Ataque(
            id="x1",
            categoria="injecao_indireta",
            objetivo="marcador",
            descricao="d",
            turnos=("oi",),
            marcador="OBEDECI",
        )


def test_ids_repetidos_no_yaml_sao_rejeitados(tmp_path):
    item = (
        "- id: a1\n  categoria: vazamento_dados\n  objetivo: frase_proibida\n"
        "  descricao: d\n  turnos: [oi]\n  frase_proibida: 'xx'\n"
    )
    arquivo = tmp_path / "ataques.yaml"
    arquivo.write_text(item + item, encoding="utf-8")
    with pytest.raises(ValueError, match="repetidos"):
        carregar_ataques(arquivo)


def test_vazou_outra_cliente_pelo_nome():
    msg = vazou_outra_cliente("Quem é a Maria Helena na sua base?")
    assert msg is not None
    assert "nome da outra cliente" in msg
