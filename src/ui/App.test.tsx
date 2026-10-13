import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App, SiteFooter } from "./App";
import { cleanup } from "@testing-library/react";

const originalMatchMedia = window.matchMedia;
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: originalMatchMedia,
  });
});

describe("TF2 Coach interface", () => {
  it("offers the retro navigation and clearly marks fictional entries", () => {
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Navegação principal" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "CHEATS" }).getAttribute("href")).toBe("#cheats");
    expect(screen.getAllByText("DADOS DE DEMONSTRAÇÃO")).toHaveLength(2);
  });

  it("expands an entry and reports that sample statistics are unavailable", () => {
    render(<App />);
    fireEvent.click(screen.getAllByRole("button", { name: /Abrir análise/ })[0]);
    expect(within(screen.getByRole("region", { name: /Análise:/ }))
      .getByText(/Nenhuma estatística real disponível/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Fechar análise/ }).getAttribute("aria-expanded")).toBe("true");
  });

  it("imports only validated report fields and surfaces malformed JSON", async () => {
    render(<App />);
    const input = screen.getByLabelText("Importar relatório JSON local") as HTMLInputElement;
    const valid = new File([JSON.stringify({
      schemaVersion: 1,
      selection: "POV do cabeçalho, correspondência única",
      map: "ctf_test",
      metrics: { kills: 2, deaths: 1 },
      chat: [{ text: "private" }],
      users: [{ steamId: "STEAM_PRIVATE" }],
    })], "report.json", { type: "application/json" });
    fireEvent.change(input, { target: { files: [valid] } });
    expect(await screen.findByText("2", { selector: "b" })).toBeTruthy();
    expect(screen.queryByText("private")).toBeNull();
    expect(screen.queryByText("STEAM_PRIVATE")).toBeNull();

    const invalid = new File(["{"], "broken.json", { type: "application/json" });
    fireEvent.change(input, { target: { files: [invalid] } });
    expect(await screen.findByRole("alert")).toBeTruthy();
  });

  it("uses a static poster when reduced motion is requested", () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    });
    render(
      <SiteFooter gifs={[{
        src: "/assets/gifs/engineer.gif",
        poster: "/assets/gifs/engineer-poster.png",
        href: "https://tenor.com/example",
        alt: "Engineer animado",
      }]}>
        <span>créditos</span>
      </SiteFooter>,
    );
    expect(screen.getByAltText("Engineer animado").getAttribute("src"))
      .toBe("/assets/gifs/engineer-poster.png");
  });

  it("shows all three footer GIFs as links without visible Tenor captions", () => {
    render(<App />);
    expect(screen.queryByText("Via Tenor")).toBeNull();
    expect(screen.getByRole("img", { name: "Adesivo animado de Team Fortress 2" }).getAttribute("src"))
      .toContain("tf2.gif");
    expect(screen.getByRole("img", { name: "Adesivo animado de Engineer do Team Fortress 2" }).getAttribute("src"))
      .toContain("tf2-team-fortress-2.gif");
    expect(screen.getByRole("img", { name: "Demoman animado do Team Fortress 2" }).getAttribute("src"))
      .toContain("demoman-tf2.gif");
    const gifs = screen.getAllByRole("link", { name: /abrir fonte no Tenor/ });
    expect(gifs.map((gif) => gif.getAttribute("href")))
      .toEqual(expect.arrayContaining([
        expect.stringContaining("7306907520168166995"),
        expect.stringContaining("3663369177204038737"),
        expect.stringContaining("12960034587810629563"),
      ]));
  });

  it("uses a native scroll region for each analysis panel", () => {
    const { container } = render(<App />);
    expect(container.querySelectorAll(".entry-panel .entry-scroll").length).toBeGreaterThan(0);
    expect(container.querySelector(".entry-rail")).toBeNull();
    expect(container.querySelector(".entry-marker")).toBeNull();
  });

  it("replaces today's sample with the private catalog report and opens its video", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ replays: [{
        id: "2026-10-13_00-00-00",
        date: "13/10/26",
        label: "análise gameplay",
        report: {
          schemaVersion: 1,
          selection: "POV do cabeçalho, correspondência única",
          map: "ctf_test",
          metrics: { kills: 4, deaths: 2, assists: 1, self_eliminations: 0 },
          chat: [{ text: "PRIVATE_CHAT_MUST_NOT_APPEAR" }],
        },
        videoUrl: "/api/replays/2026-10-13_00-00-00/video",
      }] }),
    }));
    const { container } = render(<App />);
    expect(await screen.findByText(/4 eliminações/)).toBeTruthy();
    expect(screen.getAllByText("DADOS DE DEMONSTRAÇÃO")).toHaveLength(1);
    expect(screen.getByRole("button", { name: /Fechar análise análise gameplay 13\/10\/26/ })
      .getAttribute("aria-expanded")).toBe("true");
    expect(container.querySelector("video")?.getAttribute("src"))
      .toBe("/api/replays/2026-10-13_00-00-00/video");
    expect(screen.queryByText("PRIVATE_CHAT_MUST_NOT_APPEAR")).toBeNull();
  });
});
