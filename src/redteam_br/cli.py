"""Linha de comando: atacar, gerar relatório, comparar execuções e listar ataques."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, relatorio
from .alvo import criar_alvo
from .execucao import carregar_ataques, executar, executar_legitimas, gerar_variantes, salvar
from .modelos import CATEGORIAS


def _atacar(args: argparse.Namespace) -> int:
    ataques = carregar_ataques(args.ataques)
    if args.categorias:
        ataques = [a for a in ataques if a.categoria in args.categorias]
    variantes = gerar_variantes(ataques, args.tecnicas)
    if args.limite:
        variantes = variantes[: args.limite]
    alvo = criar_alvo(args.alvo)
    print(f"Alvo: {alvo.nome} · defesa: {args.defesa} · {len(variantes)} variantes de {len(ataques)} ataques")

    def progresso(n: int, total: int, r) -> None:
        marca = "BLOQUEADO" if r.bloqueado_na_entrada else ("SUCESSO" if r.sucesso else "falhou")
        print(f"[{n:>3}/{total}] {r.variante_id:<42} {marca:<9} {r.segundos:>5.1f}s", flush=True)

    resultados = executar(alvo, variantes, args.defesa, progresso)
    legitimas = None if args.sem_legitimas else executar_legitimas(alvo, args.defesa)
    dados = salvar(args.saida, alvo.nome, resultados, legitimas)
    r = dados["resumo"]
    print(f"\nTaxa de sucesso dos ataques: {r['asr']:.0%}")
    for categoria, taxa in r["por_categoria"].items():
        print(f"  {CATEGORIAS[categoria]:<62} {taxa:.0%}")
    if "falsos_positivos" in r:
        fp = r["falsos_positivos"]
        print(f"Falsos positivos: {fp['taxa']:.0%} ({len(fp['bloqueadas'])}/{fp['total']})")
    return 0


def _relatorio(args: argparse.Namespace) -> int:
    execucoes = {}
    for caminho in args.execucoes:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        execucoes[dados["resumo"]["defesa"]] = dados
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.html).write_text(relatorio.gerar(execucoes), encoding="utf-8")
    print(f"Relatório salvo em {args.html}")
    return 0


def _comparar(args: argparse.Namespace) -> int:
    """Falha (código 1) se a execução nova piorar a taxa de sucesso em alguma categoria além da tolerância."""
    base = json.loads(Path(args.base).read_text(encoding="utf-8"))["resumo"]
    nova = json.loads(Path(args.nova).read_text(encoding="utf-8"))["resumo"]
    print(f"ASR geral: {base['asr']:.0%} -> {nova['asr']:.0%}")
    regressoes = []
    for categoria, taxa_nova in nova["por_categoria"].items():
        taxa_base = base["por_categoria"].get(categoria, 0)
        marca = ""
        if taxa_nova - taxa_base > args.tolerancia:
            regressoes.append(categoria)
            marca = "  <- REGRESSÃO"
        print(f"  {CATEGORIAS[categoria]:<62} {taxa_base:.0%} -> {taxa_nova:.0%}{marca}")
    if regressoes:
        print(f"\n{len(regressoes)} categoria(s) pioraram além da tolerância de {args.tolerancia:.0%}.")
        return 1
    print("\nSem regressões.")
    return 0


def _listar(args: argparse.Namespace) -> int:
    for a in carregar_ataques(args.ataques):
        print(f"{a.id:<30} {a.categoria:<18} {a.objetivo:<20} {a.descricao}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="redteam-br", description="Red-teaming de LLMs em português.")
    parser.add_argument("--version", action="version", version=f"redteam-br {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("atacar", help="executa os ataques contra um modelo")
    p.add_argument("--alvo", default="ollama:qwen2.5:1.5b", help="ex.: ollama:qwen2.5:1.5b")
    p.add_argument("--defesa", default="nenhuma", choices=["nenhuma", "prompt", "completa"])
    p.add_argument("--saida", required=True, help="arquivo JSON com os resultados")
    p.add_argument("--tecnicas", nargs="*", help="mutadores a usar (padrão: todos)")
    p.add_argument("--categorias", nargs="*", choices=list(CATEGORIAS))
    p.add_argument("--limite", type=int, help="máximo de variantes (útil para testes rápidos)")
    p.add_argument("--ataques", help="arquivo YAML de ataques (padrão: o embutido)")
    p.add_argument("--sem-legitimas", action="store_true", help="não medir falsos positivos")
    p.set_defaults(func=_atacar)

    p = sub.add_parser("relatorio", help="gera o relatório HTML a partir de uma ou mais execuções")
    p.add_argument("execucoes", nargs="+")
    p.add_argument("--html", required=True)
    p.set_defaults(func=_relatorio)

    p = sub.add_parser("comparar", help="falha se a execução nova regredir em alguma categoria")
    p.add_argument("base")
    p.add_argument("nova")
    p.add_argument("--tolerancia", type=float, default=0.05)
    p.set_defaults(func=_comparar)

    p = sub.add_parser("listar", help="lista os ataques base")
    p.add_argument("--ataques")
    p.set_defaults(func=_listar)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
