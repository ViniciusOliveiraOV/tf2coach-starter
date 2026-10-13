export type IndividualReport = {
  map?: string;
  durationSeconds?: number;
  metrics?: {
    kills?: number;
    deaths?: number;
    assists?: number;
    selfEliminations?: number;
  };
  weaponCounts: Record<string, number>;
  eventWindow?: {
    firstTick: number;
    lastTick: number;
    startSeconds?: number;
    endSeconds?: number;
  };
  events?: Array<{
    tick: number | null;
    roles: Array<"morte" | "assist" | "autoeliminação" | "eliminação atribuída">;
    weapon?: string;
  }> | null;
  rounds?: Array<{
    winner?: string;
    lengthSeconds?: number;
  }>;
};

type UnknownRecord = Record<string, unknown>;

function record(value: unknown, label: string): UnknownRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} precisa ser um objeto.`);
  }
  return value as UnknownRecord;
}

function finiteNumber(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error(`${label} precisa ser um número finito não negativo.`);
  }
  return value;
}

function optionalText(value: unknown): string | undefined {
  return typeof value === "string" && /^[a-z0-9_]{1,48}$/i.test(value)
    ? value
    : undefined;
}

function optionalMetric(source: UnknownRecord, key: string): number | undefined {
  const value = source[key];
  if (value === undefined || value === null) return undefined;
  const count = finiteNumber(value, `metrics.${key}`);
  if (!Number.isInteger(count)) throw new Error(`metrics.${key} precisa ser inteiro.`);
  return count;
}

/**
 * Accepts the privacy-safe projection of scripts/analyze_demo.py's
 * build_analysis() result. Parser JSON is deliberately not accepted directly.
 * Unknown properties (including identities and chat) are never copied.
 */
export function parseIndividualReport(value: unknown): IndividualReport {
  const input = record(value, "Relatório");
  if (input.schemaVersion !== undefined && input.schemaVersion !== 1) {
    throw new Error("schemaVersion não suportada; esperado 1.");
  }
  if (input.selection !== "POV do cabeçalho, correspondência única"
    && input.selection !== "SteamID informado explicitamente") {
    throw new Error("selection ausente ou inválida; importe uma projeção individual de build_analysis().");
  }

  const output: IndividualReport = { weaponCounts: {} };
  const map = optionalText(input.map);
  if (map !== undefined) output.map = map;

  if (input.duration_seconds !== undefined && input.duration_seconds !== null) {
    output.durationSeconds = finiteNumber(input.duration_seconds, "duration_seconds");
  }

  if (input.metrics !== undefined && input.metrics !== null) {
    const metrics = record(input.metrics, "metrics");
    const parsed: NonNullable<IndividualReport["metrics"]> = {};
    for (const [key, reportKey] of [
      ["kills", "kills"],
      ["deaths", "deaths"],
      ["assists", "assists"],
      ["selfEliminations", "self_eliminations"],
    ] as const) {
      const count = optionalMetric(metrics, reportKey);
      if (count !== undefined) parsed[key] = count;
    }
    output.metrics = parsed;
  }

  if (input.weapon_counts !== undefined && input.weapon_counts !== null) {
    const counts = record(input.weapon_counts, "weapon_counts");
    for (const [weapon, value] of Object.entries(counts)) {
      if (!/^[a-z0-9_]{1,48}$/i.test(weapon)) {
        throw new Error("weapon_counts contém um rótulo inválido.");
      }
      const count = finiteNumber(value, `weapon_counts.${weapon}`);
      if (!Number.isInteger(count)) {
        throw new Error(`weapon_counts.${weapon} precisa ser inteiro.`);
      }
      output.weaponCounts[weapon] = count;
    }
  }

  if (input.event_window !== undefined && input.event_window !== null) {
    const window = record(input.event_window, "event_window");
    const firstTick = finiteNumber(window.first_tick, "event_window.first_tick");
    const lastTick = finiteNumber(window.last_tick, "event_window.last_tick");
    if (!Number.isInteger(firstTick) || !Number.isInteger(lastTick) || lastTick < firstTick) {
      throw new Error("event_window precisa conter ticks inteiros em ordem.");
    }
    const parsedWindow: NonNullable<IndividualReport["eventWindow"]> = { firstTick, lastTick };
    if (window.start_seconds !== undefined && window.start_seconds !== null) {
      parsedWindow.startSeconds = finiteNumber(window.start_seconds, "event_window.start_seconds");
    }
    if (window.end_seconds !== undefined && window.end_seconds !== null) {
      parsedWindow.endSeconds = finiteNumber(window.end_seconds, "event_window.end_seconds");
    }
    if ((parsedWindow.startSeconds === undefined) !== (parsedWindow.endSeconds === undefined)
      || (parsedWindow.endSeconds !== undefined && parsedWindow.startSeconds !== undefined
        && parsedWindow.endSeconds < parsedWindow.startSeconds)) {
      throw new Error("event_window precisa conter um período relativo válido.");
    }
    output.eventWindow = parsedWindow;
  }

  if (input.events === null) {
    output.events = null;
  } else if (input.events !== undefined) {
    if (!Array.isArray(input.events)) throw new Error("events precisa ser uma lista ou null.");
    const acceptedRoles = new Set(["morte", "assist", "autoeliminação", "eliminação atribuída"]);
    output.events = input.events.map((event, index) => {
      const source = record(event, `events[${index}]`);
      const tick = source.tick === null ? null : finiteNumber(source.tick, `events[${index}].tick`);
      if (tick !== null && !Number.isInteger(tick)) {
        throw new Error(`events[${index}].tick precisa ser inteiro ou null.`);
      }
      if (!Array.isArray(source.roles) || source.roles.length === 0
        || source.roles.some((role) => typeof role !== "string" || !acceptedRoles.has(role))) {
        throw new Error(`events[${index}].roles contém uma participação desconhecida.`);
      }
      const parsedEvent: NonNullable<IndividualReport["events"]>[number] = {
        tick,
        roles: source.roles as NonNullable<IndividualReport["events"]>[number]["roles"],
      };
      if (source.weapon !== undefined && source.weapon !== null) {
        const weapon = optionalText(source.weapon);
        if (!weapon) throw new Error(`events[${index}].weapon contém um rótulo inválido.`);
        parsedEvent.weapon = weapon;
      }
      return parsedEvent;
    });
  }

  if (input.rounds !== undefined && input.rounds !== null) {
    if (!Array.isArray(input.rounds)) throw new Error("rounds precisa ser uma lista.");
    output.rounds = input.rounds.map((round, index) => {
      const source = record(round, `rounds[${index}]`);
      const parsedRound: NonNullable<IndividualReport["rounds"]>[number] = {};
      const winner = source.winner;
      if (winner !== undefined && winner !== null) {
        if (winner !== "red" && winner !== "blue" && winner !== "stalemate") {
          throw new Error(`rounds[${index}].winner contém um valor inválido.`);
        }
        parsedRound.winner = winner;
      }
      if (source.length_seconds !== undefined && source.length_seconds !== null) {
        parsedRound.lengthSeconds = finiteNumber(
          source.length_seconds,
          `rounds[${index}].length_seconds`,
        );
      }
      return parsedRound;
    });
  }

  return output;
}
