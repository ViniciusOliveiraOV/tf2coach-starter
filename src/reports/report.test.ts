import { describe, expect, it } from "vitest";
import { parseIndividualReport } from "./report";
import fixture from "../../tests/fixtures/ui-report-anonymized.json";

describe("parseIndividualReport", () => {
  it("accepts the privacy-safe report contract and keeps only verified fields", () => {
    const report = parseIndividualReport(fixture);

    expect(report).toEqual({
      map: "ctf_test",
      durationSeconds: 120.0,
      metrics: { kills: 3, deaths: 2, assists: 1, selfEliminations: 0 },
      weaponCounts: { flamethrower: 2 },
      eventWindow: { firstTick: 120, lastTick: 280, startSeconds: 1.5, endSeconds: 3.9 },
      events: [
        { tick: 120, roles: ["eliminação atribuída"], weapon: "flamethrower" },
        { tick: 280, roles: ["morte"] },
      ],
      rounds: [{ winner: "blue", lengthSeconds: 98.5 }],
    });
    expect(JSON.stringify(report)).not.toContain("STEAM_");
    expect(JSON.stringify(report)).not.toContain("chat");
  });

  it("rejects malformed or unsupported metric values", () => {
    expect(() => parseIndividualReport({ ...fixture, metrics: { kills: -1 } }))
      .toThrow(/metrics/);
    expect(() => parseIndividualReport({ ...fixture, schemaVersion: 99 }))
      .toThrow(/schemaVersion/);
    expect(() => parseIndividualReport({ header: {}, users: {}, deaths: [], chat: [] }))
      .toThrow(/selection/);
    expect(() => parseIndividualReport({ ...fixture, events: [{ tick: 10, roles: ["STEAM_PRIVATE"] }] }))
      .toThrow(/roles/);
  });
});
