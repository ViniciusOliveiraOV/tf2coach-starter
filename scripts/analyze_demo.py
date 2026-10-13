#!/usr/bin/env python3
"""Gera um relatório individual a partir do JSON de tf-demo-parser."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


class AnalysisError(ValueError):
    """Dados ausentes, inválidos ou identidade do jogador ambígua."""


def _as_id(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    return str(value)


def _select_player(parsed: dict, steam_id: str | None) -> tuple[set[str], str]:
    users = parsed.get("users")
    if not isinstance(users, dict):
        raise AnalysisError("O JSON não contém um objeto users válido.")

    records = []
    for key, user in users.items():
        if not isinstance(user, dict):
            continue
        user_id = _as_id(user.get("userId", key))
        if user_id is None:
            continue
        records.append((user_id, user))

    if steam_id is not None:
        matches = [(uid, user) for uid, user in records if user.get("steamId") == steam_id]
        if not matches:
            raise AnalysisError("SteamID não encontrado em users nesta demo.")
        return {uid for uid, _ in matches}, "SteamID informado explicitamente"

    header = parsed.get("header")
    nick = header.get("nick") if isinstance(header, dict) else None
    if not isinstance(nick, str) or not nick:
        raise AnalysisError("O cabeçalho não identifica o POV; informe --steam-id.")
    pov_matches = [(uid, user) for uid, user in records if user.get("name") == nick]
    steam_ids = {user.get("steamId") for _, user in pov_matches if user.get("steamId")}

    if len(steam_ids) == 1 and all(user.get("steamId") for _, user in pov_matches):
        pov_steam_id = next(iter(steam_ids))
        return {
            uid for uid, user in records if user.get("steamId") == pov_steam_id
        }, "POV do cabeçalho, correspondência única"
    if len(pov_matches) == 1:
        return {pov_matches[0][0]}, "POV do cabeçalho, correspondência única"
    raise AnalysisError(
        "Não foi possível identificar o POV sem ambiguidade; informe --steam-id."
    )


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def build_analysis(parsed: dict, steam_id: str | None = None) -> dict:
    """Calcula somente contagens deriváveis dos eventos do JSON."""
    if not isinstance(parsed, dict):
        raise AnalysisError("A raiz do JSON precisa ser um objeto.")
    player_ids, selection = _select_player(parsed, steam_id)

    deaths = parsed.get("deaths")
    if deaths is not None and not isinstance(deaths, list):
        raise AnalysisError("O campo deaths existe, mas não é uma lista.")

    metrics = None
    weapon_counts: Counter[str] = Counter()
    event_ticks: list[int] = []
    player_events = None if deaths is None else []
    if deaths is not None:
        kills = player_deaths = assists = self_eliminations = 0
        for event in deaths:
            if not isinstance(event, dict):
                continue
            killer = _as_id(event.get("killer"))
            victim = _as_id(event.get("victim"))
            assister = _as_id(event.get("assister"))
            is_self_elimination = killer is not None and killer == victim
            roles = []
            report_event = {}

            if victim in player_ids:
                player_deaths += 1
                roles.append("morte")
            if assister in player_ids and victim is not None:
                assists += 1
                roles.append("assist")
            if killer in player_ids and victim is not None:
                if is_self_elimination:
                    self_eliminations += 1
                    roles.append("autoeliminação")
                else:
                    kills += 1
                    roles.append("eliminação atribuída")
                    weapon = event.get("weapon")
                    if isinstance(weapon, str) and weapon:
                        weapon_counts[weapon] += 1
                        report_event["weapon"] = weapon

            if roles:
                tick = event.get("tick")
                if isinstance(tick, int) and not isinstance(tick, bool):
                    event_ticks.append(tick)
                    report_event["tick"] = tick
                else:
                    report_event["tick"] = None
                report_event["roles"] = roles
                player_events.append(report_event)

        player_events.sort(
            key=lambda item: (
                item["tick"] is None,
                item["tick"] if item["tick"] is not None else 0,
            )
        )

        metrics = {
            "kills": kills,
            "deaths": player_deaths,
            "assists": assists,
            "self_eliminations": self_eliminations,
        }

    event_window = None
    if event_ticks:
        event_window = {"first_tick": min(event_ticks), "last_tick": max(event_ticks)}
        start_tick = parsed.get("startTick")
        interval = _number(parsed.get("intervalPerTick"))
        if (
            isinstance(start_tick, int)
            and not isinstance(start_tick, bool)
            and interval is not None
            and interval > 0
            and event_window["first_tick"] >= start_tick
        ):
            event_window["start_seconds"] = round(
                (event_window["first_tick"] - start_tick) * interval, 3
            )
            event_window["end_seconds"] = round(
                (event_window["last_tick"] - start_tick) * interval, 3
            )

    header = parsed.get("header") if isinstance(parsed.get("header"), dict) else {}
    rounds = parsed.get("rounds")
    if rounds is not None and not isinstance(rounds, list):
        raise AnalysisError("O campo rounds existe, mas não é uma lista.")

    round_summary = None
    if rounds is not None:
        round_summary = []
        for round_record in rounds:
            if not isinstance(round_record, dict):
                continue
            round_item = {}
            winner = round_record.get("winner")
            length = _number(round_record.get("length"))
            if isinstance(winner, str):
                round_item["winner"] = winner
            if length is not None:
                round_item["length_seconds"] = length
            round_summary.append(round_item)

    return {
        "selection": selection,
        "map": header.get("map") if isinstance(header.get("map"), str) else None,
        "duration_seconds": _number(header.get("duration")),
        "ticks": header.get("ticks") if isinstance(header.get("ticks"), int) else None,
        "metrics": metrics,
        "weapon_counts": dict(sorted(weapon_counts.items())),
        "events": player_events,
        "event_window": event_window,
        "rounds": round_summary,
    }


def _inline(value: str) -> str:
    return "`" + value.replace("`", "&#96;").replace("\n", " ") + "`"


def render_report(analysis: dict) -> str:
    """Renderiza um relatório sem nicks, SteamIDs, servidor ou chat."""
    lines = ["# Análise individual da partida", "", "## Seleção do jogador", ""]
    lines.append(f"- Identificação: {analysis['selection']}.")
    lines.extend(["", "## Contexto da demo", ""])
    if analysis["map"] is not None:
        lines.append(f"- Mapa: {_inline(analysis['map'])}.")
    if analysis["duration_seconds"] is not None:
        lines.append(f"- Duração no cabeçalho: {analysis['duration_seconds']:.2f} s.")
    if analysis["ticks"] is not None:
        lines.append(f"- Ticks no cabeçalho: {analysis['ticks']}.")

    lines.extend(["", "## Métricas individuais", ""])
    metrics = analysis["metrics"]
    if metrics is None:
        lines.append("Eventos `deaths` ausentes; métricas individuais não calculadas.")
    else:
        lines.extend([
            "Contagens atribuídas ao jogador nos registros `deaths`:",
            "",
            f"- Eliminações (`killer`, exceto autoeliminação): **{metrics['kills']}**",
            f"- Mortes (`victim`): **{metrics['deaths']}**",
            f"- Assists (`assister`): **{metrics['assists']}**",
            f"- Autoeliminações (`killer` = `victim`): **{metrics['self_eliminations']}**",
        ])

    lines.extend(["", "### Valores de `weapon` nas eliminações atribuídas", ""])
    if analysis["weapon_counts"]:
        for weapon, count in analysis["weapon_counts"].items():
            lines.append(f"- {_inline(weapon)}: **{count}**")
    elif metrics is None:
        lines.append("Indisponível porque os eventos `deaths` não foram fornecidos.")
    else:
        lines.append("Nenhuma arma verificável em eliminações atribuídas.")

    lines.extend(["", "### Janela de eventos individuais", ""])
    window = analysis["event_window"]
    if window is None:
        lines.append("Nenhum tick individual verificável nos eventos disponíveis.")
    else:
        lines.append(f"- Ticks observados: **{window['first_tick']}–{window['last_tick']}**.")
        if "start_seconds" in window:
            lines.append(
                "- Intervalo desde `startTick` até os eventos observados: "
                f"**{window['start_seconds']:.3f}–{window['end_seconds']:.3f} s**."
            )
        else:
            lines.append(
                "- Tempo relativo não calculado: `startTick` ou `intervalPerTick` "
                "ausente, inválido ou incompatível com os ticks observados."
            )
        lines.append("- Esta janela cobre eventos registrados, não períodos contínuos de atividade.")

    lines.extend(["", "### Eventos registrados para o jogador", ""])
    events = analysis["events"]
    if events is None:
        lines.append("Indisponível porque o campo `deaths` não foi fornecido.")
    elif not events:
        lines.append("Nenhum evento individual encontrado nos registros `deaths`.")
    else:
        lines.extend([
            "Somente registros em que o jogador aparece em `killer`, `victim` ou `assister`; identidades dos demais participantes foram omitidas.",
            "",
            "| Tick | Participação | Valor de `weapon` (se `killer`) |",
            "|---:|---|---|",
        ])
        for event in events:
            tick = str(event["tick"]) if event["tick"] is not None else "—"
            role_text = ", ".join(event["roles"])
            weapon = _inline(event["weapon"]) if "weapon" in event else "—"
            lines.append(f"| {tick} | {role_text} | {weapon} |")

    lines.extend(["", "## Contexto global de rodadas", ""])
    if analysis["rounds"] is None:
        lines.append("Campo `rounds` ausente; contexto de rodadas indisponível.")
    elif not analysis["rounds"]:
        lines.append("Nenhuma rodada registrada no resumo.")
    else:
        lines.append("Dados globais da demo; não são estatísticas individuais:")
        lines.append("")
        for index, round_record in enumerate(analysis["rounds"], start=1):
            parts = [f"Rodada {index}"]
            if "winner" in round_record:
                parts.append(f"vencedor {_inline(round_record['winner'])}")
            if "length_seconds" in round_record:
                parts.append(f"duração {round_record['length_seconds']:.2f} s")
            lines.append("- " + "; ".join(parts) + ".")

    lines.extend([
        "",
        "## Limitações",
        "",
        "- O relatório resume apenas campos observados no JSON padrão do parser.",
        "- `deaths` descreve eventos do resumo; não demonstra posições, mira, visibilidade ou intenção.",
        "- Os valores de `weapon` são reproduzidos como o parser os registrou; rótulos como `world` não comprovam uma arma equipada.",
        "- Chat, nicks, SteamIDs e nome do servidor foram omitidos.",
        "- Métricas globais da demo não foram atribuídas ao jogador.",
        "",
    ])
    return "\n".join(lines)


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="JSON já produzido por tf-demo-parser")
    parser.add_argument("--output", type=Path, help="Destino privado do relatório Markdown")
    parser.add_argument("--steam-id", help="SteamID do jogador a selecionar; nunca é escrito no relatório")
    parser.add_argument("--force", action="store_true", help="Autoriza substituir o arquivo de relatório existente")
    args = parser.parse_args(argv)

    output = args.output or Path("data/reports") / f"{args.json_file.stem}.md"
    try:
        if args.json_file.resolve() == output.resolve():
            raise AnalysisError("O destino não pode substituir o JSON de entrada.")
        parsed = json.loads(args.json_file.read_text(encoding="utf-8"))
        report = render_report(build_analysis(parsed, steam_id=args.steam_id))
        if output.exists() and not args.force:
            raise AnalysisError("O destino já existe; escolha --output ou use --force para substituí-lo.")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, json.JSONDecodeError, AnalysisError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    print(f"Relatório gravado em {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
