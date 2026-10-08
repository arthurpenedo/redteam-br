"""Executa as variantes contra o alvo em cada nível de defesa e resume os resultados."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Callable
from importlib import resources
from pathlib import Path

import yaml

from . import defesas
from .alvo import Alvo
from .detectores import avaliar, vazou_canario, vazou_outra_cliente
from .modelos import CATEGORIAS, Ataque, Resultado, Variante
from .mutadores import gerar_variantes


def carregar_ataques(caminho: str | Path | None = None) -> list[Ataque]:
    texto = Path(caminho).read_text(encoding="utf-8") if caminho else (
        resources.files("redteam_br").joinpath("dados/ataques.yaml").read_text(encoding="utf-8")
    )
    ataques = []
    for item in yaml.safe_load(texto):
        item["turnos"] = tuple(item["turnos"])
        if item.get("turnos_en"):
            item["turnos_en"] = tuple(item["turnos_en"])
        ataques.append(Ataque(**item))
    ids = [a.id for a in ataques]
    if len(ids) != len(set(ids)):
        raise ValueError("há ids de ataque repetidos")
    return ataques


def carregar_legitimas() -> list[dict]:
    texto = resources.files("redteam_br").joinpath("dados/legitimas.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(texto)


def conversar(alvo: Alvo, turnos: tuple[str, ...] | list[str], documento: str | None,
              config: defesas.Configuracao) -> tuple[list[str], bool, str | None]:
    """Conduz a conversa turno a turno. Devolve (respostas, bloqueado_na_entrada, motivo)."""
    if config.filtra_entrada:
        motivo = defesas.filtrar_entrada([*turnos, documento or ""])
        if motivo:
            return [defesas.RESPOSTA_BLOQUEIO], True, motivo

    mensagens = [{"role": "system", "content": defesas.prompt_de_sistema(config.nome)}]
    respostas: list[str] = []
    for i, turno in enumerate(turnos):
        # o documento de terceiros acompanha a primeira mensagem do cliente
        texto = defesas.mensagem_do_cliente(turno, documento if i == 0 else None, config.nome)
        mensagens.append({"role": "user", "content": texto})
        resposta = alvo.responder(mensagens)
        motivo_saida = None
        if config.filtra_saida:
            resposta, motivo_saida = defesas.filtrar_saida(resposta)
        respostas.append(resposta)
        mensagens.append({"role": "assistant", "content": resposta})
        if motivo_saida:
            return respostas, False, motivo_saida
    return respostas, False, None


def executar(alvo: Alvo, variantes: list[Variante], defesa: str,
             progresso: Callable[[int, int, Resultado], None] | None = None) -> list[Resultado]:
    config = defesas.Configuracao(defesa)
    resultados = []
    for n, variante in enumerate(variantes, 1):
        inicio = time.perf_counter()
        respostas, bloqueado, _ = conversar(alvo, variante.turnos, variante.ataque.documento, config)
        evidencia = None if bloqueado else avaliar(variante.ataque, respostas)
        resultado = Resultado(
            variante_id=variante.id,
            ataque_id=variante.ataque.id,
            categoria=variante.ataque.categoria,
            tecnica=variante.tecnica,
            defesa=defesa,
            sucesso=evidencia is not None,
            bloqueado_na_entrada=bloqueado,
            resposta="\n---\n".join(respostas),
            turnos=list(variante.turnos),
            evidencia=evidencia,
            segundos=round(time.perf_counter() - inicio, 2),
        )
        resultados.append(resultado)
        if progresso:
            progresso(n, len(variantes), resultado)
    return resultados


def executar_legitimas(alvo: Alvo, defesa: str) -> list[dict]:
    """Roda as mensagens legítimas e separa duas situações bem diferentes:

    - bloqueio indevido: a defesa barrou um cliente que não fez nada de errado (falso positivo);
    - vazamento espontâneo: o próprio modelo vazou um segredo numa pergunta inocente.
      Se o filtro de saída barrou, é um acerto da defesa, não um falso positivo.
    """
    config = defesas.Configuracao(defesa)
    saida = []
    for item in carregar_legitimas():
        respostas, bloqueado_entrada, motivo = conversar(alvo, item["turnos"], item.get("documento"), config)
        texto = "\n---\n".join(respostas)
        vazou_sozinho = motivo in defesas.MOTIVOS_VAZAMENTO or bool(vazou_canario(texto) or vazou_outra_cliente(texto))
        saida.append({
            "id": item["id"], "turnos": item["turnos"],
            "bloqueado": bloqueado_entrada or (motivo is not None and motivo not in defesas.MOTIVOS_VAZAMENTO),
            "vazamento_espontaneo": vazou_sozinho,
            "vazamento_evitado": motivo in defesas.MOTIVOS_VAZAMENTO,
            "motivo": motivo, "resposta": texto,
        })
    return saida


def _taxa(itens: list[Resultado]) -> float:
    return round(sum(r.sucesso for r in itens) / len(itens), 4) if itens else 0.0


def resumir(resultados: list[Resultado], legitimas: list[dict] | None = None) -> dict:
    """Taxa de sucesso dos ataques (ASR) no geral, por categoria e por técnica, mais falsos positivos."""
    por_categoria: dict[str, list[Resultado]] = defaultdict(list)
    por_tecnica: dict[str, list[Resultado]] = defaultdict(list)
    for r in resultados:
        por_categoria[r.categoria].append(r)
        por_tecnica[r.tecnica].append(r)
    resumo = {
        "defesa": resultados[0].defesa if resultados else None,
        "variantes": len(resultados),
        "ataques_base": len({r.ataque_id for r in resultados}),
        "asr": _taxa(resultados),
        "bloqueados_na_entrada": sum(r.bloqueado_na_entrada for r in resultados),
        "por_categoria": {c: _taxa(por_categoria[c]) for c in CATEGORIAS if c in por_categoria},
        "por_tecnica": {t: _taxa(v) for t, v in sorted(por_tecnica.items())},
    }
    if legitimas is not None:
        bloqueadas = [x["id"] for x in legitimas if x["bloqueado"]]
        resumo["falsos_positivos"] = {
            "taxa": round(len(bloqueadas) / len(legitimas), 4) if legitimas else 0.0,
            "bloqueadas": bloqueadas,
            "total": len(legitimas),
        }
        resumo["vazamentos_espontaneos"] = {
            "ocorridos": [x["id"] for x in legitimas if x.get("vazamento_espontaneo")],
            "evitados": [x["id"] for x in legitimas if x.get("vazamento_evitado")],
        }
    return resumo


def salvar(caminho: str | Path, alvo_nome: str, resultados: list[Resultado], legitimas: list[dict] | None) -> dict:
    dados = {
        "alvo": alvo_nome,
        "resumo": resumir(resultados, legitimas),
        "resultados": [r.to_dict() for r in resultados],
        "legitimas": legitimas or [],
    }
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return dados


__all__ = ["carregar_ataques", "carregar_legitimas", "executar", "executar_legitimas",
           "gerar_variantes", "resumir", "salvar"]
