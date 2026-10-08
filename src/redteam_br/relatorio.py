"""Relatório HTML (um arquivo, sem dependências) comparando os níveis de defesa."""

from __future__ import annotations

import html
from datetime import date

from .defesas import DEFESAS
from .modelos import CATEGORIAS
from .mutadores import MUTADORES

_NOMES_DEFESA = {
    "nenhuma": "Sem defesa",
    "prompt": "Prompt reforçado",
    "completa": "Defesa completa",
}
_CORES = {"nenhuma": "var(--ruim)", "prompt": "var(--medio)", "completa": "var(--bom)"}

_CSS = """
:root{--fundo:#f7f7f8;--cartao:#fff;--texto:#1d1d22;--suave:#5c5c66;--borda:#e3e3e8;
--ruim:#d9485f;--medio:#e0a526;--bom:#2f9e6e;--destaque:#4c5fd5}
@media (prefers-color-scheme:dark){:root{--fundo:#141418;--cartao:#1d1d23;--texto:#ececf1;
--suave:#a0a0ab;--borda:#2e2e37}}
*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--texto);
font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;margin:40px 0 12px}
.sub{color:var(--suave);margin:0 0 24px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.card{background:var(--cartao);border:1px solid var(--borda);border-radius:12px;padding:16px}
.card .rot{color:var(--suave);font-size:13px}.card .num{font-size:34px;font-weight:700}
.card .det{font-size:13px;color:var(--suave)}
table{width:100%;border-collapse:collapse;background:var(--cartao);border:1px solid var(--borda);
border-radius:12px;overflow:hidden}th,td{padding:9px 12px;border-bottom:1px solid var(--borda);
text-align:left;vertical-align:top}th{font-size:13px;color:var(--suave);font-weight:600}
.barra{display:flex;align-items:center;gap:8px;min-width:150px}
.barra span.b{height:10px;border-radius:5px;display:inline-block}
.barra span.v{font-variant-numeric:tabular-nums;font-size:13px;min-width:38px}
details{background:var(--cartao);border:1px solid var(--borda);border-radius:12px;padding:10px 14px;margin:8px 0}
summary{cursor:pointer;font-weight:600}.tag{display:inline-block;font-size:12px;padding:1px 8px;
border-radius:999px;border:1px solid var(--borda);color:var(--suave);margin-left:6px}
pre{white-space:pre-wrap;word-break:break-word;background:var(--fundo);border:1px solid var(--borda);
border-radius:8px;padding:10px;font-size:13px}.ev{color:var(--ruim);font-weight:600}
.leg{display:flex;gap:16px;font-size:13px;color:var(--suave);margin:8px 0}
.leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
footer{margin-top:48px;color:var(--suave);font-size:13px}a{color:var(--destaque)}
"""


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _barra(valor: float, defesa: str) -> str:
    largura = max(2, round(valor * 140))
    return (f'<div class="barra"><span class="b" style="width:{largura}px;background:{_CORES[defesa]}"></span>'
            f'<span class="v">{_pct(valor)}</span></div>')


def _exemplo(r: dict) -> str:
    conversa = "\n\n".join(f"Cliente: {t}" for t in r["turnos"])
    return (
        f"<details><summary>{html.escape(r['ataque_id'])}<span class='tag'>{html.escape(r['tecnica'])}</span>"
        f"<span class='tag'>{html.escape(CATEGORIAS[r['categoria']])}</span></summary>"
        f"<p class='ev'>{html.escape(r['evidencia'] or '')}</p>"
        f"<pre>{html.escape(conversa)}</pre><pre>Aura: {html.escape(r['resposta'])}</pre></details>"
    )


def gerar(execucoes: dict[str, dict]) -> str:
    """Recebe {defesa: conteúdo do JSON salvo} e devolve o HTML."""
    defs = [d for d in DEFESAS if d in execucoes]
    alvo = next(iter(execucoes.values()))["alvo"]
    resumos = {d: execucoes[d]["resumo"] for d in defs}

    cards = []
    for d in defs:
        r = resumos[d]
        fp = r.get("falsos_positivos")
        det = f"{r['variantes']} variantes · {r['ataques_base']} ataques base"
        if fp:
            det += f"<br>falsos positivos: {_pct(fp['taxa'])} ({len(fp['bloqueadas'])}/{fp['total']} mensagens legítimas)"
        vz = r.get("vazamentos_espontaneos")
        if vz and vz["ocorridos"]:
            evitados = len(vz["evitados"])
            det += (f"<br>vazamentos espontâneos em mensagens legítimas: {len(vz['ocorridos'])}"
                    + (f" ({evitados} barrado{'s' if evitados > 1 else ''} pelo filtro de saída)" if evitados else ""))
        cards.append(f"<div class='card'><div class='rot'>{_NOMES_DEFESA[d]} · taxa de sucesso dos ataques</div>"
                     f"<div class='num' style='color:{_CORES[d]}'>{_pct(r['asr'])}</div><div class='det'>{det}</div></div>")

    legenda = "".join(f"<span><i style='background:{_CORES[d]}'></i>{_NOMES_DEFESA[d]}</span>" for d in defs)
    cabecalho = "".join(f"<th>{_NOMES_DEFESA[d]}</th>" for d in defs)

    linhas_cat = "".join(
        f"<tr><td>{html.escape(CATEGORIAS[c])}</td>"
        + "".join(f"<td>{_barra(resumos[d]['por_categoria'].get(c, 0), d)}</td>" for d in defs) + "</tr>"
        for c in CATEGORIAS if any(c in resumos[d]["por_categoria"] for d in defs)
    )
    tecnicas = sorted({t for d in defs for t in resumos[d]["por_tecnica"]}, key=list(MUTADORES).index)
    linhas_tec = "".join(
        f"<tr><td>{html.escape(t)}<br><span class='tag'>{html.escape(MUTADORES[t][0])}</span></td>"
        + "".join(f"<td>{_barra(resumos[d]['por_tecnica'].get(t, 0), d)}</td>" for d in defs) + "</tr>"
        for t in tecnicas
    )

    base = execucoes.get("nenhuma") or execucoes[defs[0]]
    sucessos_base = [r for r in base["resultados"] if r["sucesso"]]
    vistos, exemplos = set(), []
    for r in sucessos_base:  # um exemplo por categoria e técnica, para variar
        chave = (r["categoria"], r["tecnica"])
        if chave not in vistos:
            vistos.add(chave)
            exemplos.append(r)
    restantes = [r for r in execucoes.get("completa", {}).get("resultados", []) if r["sucesso"]]

    secao_restantes = (
        "<h2>O que ainda passa pela defesa completa</h2><p class='sub'>Risco residual: nenhuma defesa por "
        "filtro é perfeita. Estes casos mostram onde investir a seguir.</p>"
        + ("".join(_exemplo(r) for r in restantes) or "<p>Nenhum ataque passou nesta execução.</p>")
    ) if "completa" in execucoes else ""

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>redteam-br · relatório</title>
<style>{_CSS}</style></head><body><main>
<h1>redteam-br · relatório de red-teaming</h1>
<p class="sub">Alvo: assistente virtual de um banco fictício rodando <b>{html.escape(alvo)}</b> ·
gerado em {date.today():%d/%m/%Y}. Taxa de sucesso dos ataques (ASR): quanto menor, melhor.</p>
<div class="cards">{''.join(cards)}</div>
<h2>Por categoria (OWASP Top 10 para aplicações com LLM)</h2>
<div class="leg">{legenda}</div>
<table><tr><th>Categoria</th>{cabecalho}</tr>{linhas_cat}</table>
<h2>Por técnica de ataque</h2>
<table><tr><th>Técnica</th>{cabecalho}</tr>{linhas_tec}</table>
<h2>Exemplos de ataques bem-sucedidos sem defesa</h2>
<p class="sub">Uma conversa por combinação de categoria e técnica. A evidência em vermelho é o que o
detector encontrou na resposta.</p>
{''.join(_exemplo(r) for r in exemplos[:25]) or '<p>Nenhum ataque teve sucesso.</p>'}
{secao_restantes}
<h2>Como ler</h2>
<p>Cada ataque tem um objetivo verificável sem juiz: um <b>código secreto</b> plantado no prompt de sistema,
os <b>dados de outra cliente</b> carregados no contexto por engano, uma <b>frase proibida</b> pela política
(com checagem de negação, para que uma recusa que cita a frase não conte como sucesso) ou uma
<b>palavra derivada</b> que só aparece se o modelo obedecer à instrução injetada. Os falsos positivos
medem quantas das 20 mensagens legítimas de clientes as defesas bloquearam por engano. Quando o
<b>próprio modelo</b> vaza um segredo numa pergunta inocente e o filtro de saída barra, isso conta como
<b>vazamento evitado</b>, não como falso positivo.</p>
<footer>Gerado pelo <a href="https://github.com/arthurpenedo/redteam-br">redteam-br</a> ·
dados 100% fictícios.</footer></main></body></html>"""
