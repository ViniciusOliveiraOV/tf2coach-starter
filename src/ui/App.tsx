import { useEffect, useRef, useState, type ReactNode } from "react";
import { sampleReplays } from "../data/sample-replays";
import { parseIndividualReport, type IndividualReport } from "../reports/report";

type Replay = {
  id: string;
  date: string;
  label: string;
  kind: "sample" | "imported" | "catalog";
  note?: string;
  report?: IndividualReport;
  videoUrl?: string;
};

function parseCatalog(value: unknown): { replays: Replay[]; error: string | null } {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("O catálogo local não é um objeto JSON.");
  }
  const payload = value as Record<string, unknown>;
  if (!Array.isArray(payload.replays)) throw new Error("A lista de replays é inválida.");
  const replays = payload.replays.map((entry): Replay => {
    if (typeof entry !== "object" || entry === null || Array.isArray(entry)) {
      throw new Error("Um replay do catálogo é inválido.");
    }
    const item = entry as Record<string, unknown>;
    if (typeof item.id !== "string" || !/^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$/.test(item.id)
      || typeof item.date !== "string" || !/^\d{2}\/\d{2}\/\d{2}$/.test(item.date)) {
      throw new Error("Um replay tem identificação ou data inválida.");
    }
    const expectedVideoUrl = `/api/replays/${item.id}/video`;
    if (item.videoUrl !== null && item.videoUrl !== undefined && item.videoUrl !== expectedVideoUrl) {
      throw new Error("Um replay tem endereço de vídeo inválido.");
    }
    return {
      id: item.id,
      date: item.date,
      label: "análise gameplay",
      kind: "catalog",
      report: parseIndividualReport(item.report),
      videoUrl: item.videoUrl === expectedVideoUrl ? expectedVideoUrl : undefined,
    };
  });
  return {
    replays,
    error: typeof payload.error === "string" && payload.error ? payload.error : null,
  };
}

function readEmbeddedCatalog(): ReturnType<typeof parseCatalog> | null {
  if (typeof document === "undefined") return null;
  const embedded = document.getElementById("tf2coach-initial-catalog")?.textContent;
  if (!embedded) return null;
  try {
    return parseCatalog(JSON.parse(embedded));
  } catch {
    return null;
  }
}

const initialCatalog = readEmbeddedCatalog();

function readLocalFile(file: File): Promise<string> {
  if (typeof file.text === "function") return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Não foi possível ler o arquivo local."));
    reader.onload = () => typeof reader.result === "string"
      ? resolve(reader.result)
      : reject(new Error("O relatório local não foi lido como texto."));
    reader.readAsText(file);
  });
}

function SiteHeader() {
  return (
    <header className="site-header" id="inicio">
      <a className="brand" href="#inicio" aria-label="TF2 Coach AI, início">
        <span>TF2 - AI COACH</span>
        <span>ANALYSES</span>
      </a>
      <img
        className="engineer-art"
        src="/assets/engineer-header.png"
        alt="Engineer do Team Fortress 2"
        width="134"
        height="75"
      />
    </header>
  );
}

function NavigationBar() {
  return (
    <nav className="navigation" aria-label="Navegação principal">
      <a href="#inicio">INÍCIO</a>
      <a href="#replays">REPLAYS</a>
      <a href="#cheats">CHEATS</a>
      <a href="#sobre">SOBRE</a>
    </nav>
  );
}

function MetricList({ report }: { report: IndividualReport }) {
  const metrics = report.metrics;
  const rows = metrics
    ? [
        ["Eliminações", metrics.kills],
        ["Mortes", metrics.deaths],
        ["Assists", metrics.assists],
        ["Autoeliminações", metrics.selfEliminations],
      ].filter((row): row is [string, number] => row[1] !== undefined)
    : [];

  return (
    <div className="report-facts">
      {report.map && <p><strong>Mapa:</strong> {report.map}</p>}
      {report.durationSeconds !== undefined && (
        <p><strong>Duração no cabeçalho:</strong> {report.durationSeconds.toFixed(2)} s</p>
      )}
      {rows.length > 0 ? (
        <ul className="metric-list">
          {rows.map(([label, value]) => <li key={label}>{label}: <b>{value}</b></li>)}
        </ul>
      ) : (
        <p>O relatório não contém métricas individuais verificáveis.</p>
      )}
      {Object.keys(report.weaponCounts).length > 0 && (
        <p><strong>Armas nos registros:</strong> {Object.entries(report.weaponCounts)
          .map(([weapon, count]) => `${weapon} (${count})`).join(", ")}</p>
      )}
      {report.eventWindow && (
        <p>
          <strong>Janela de eventos individuais:</strong> ticks {report.eventWindow.firstTick}–{report.eventWindow.lastTick}
          {report.eventWindow.startSeconds !== undefined && report.eventWindow.endSeconds !== undefined
            ? ` · ${report.eventWindow.startSeconds.toFixed(3)}–${report.eventWindow.endSeconds.toFixed(3)} s relativos`
            : " · tempo relativo não disponível"}
        </p>
      )}
      {report.events === null && <p>Eventos individuais indisponíveis no relatório.</p>}
      {report.events && report.events.length > 0 && (
        <div>
          <strong>Participações individuais registradas:</strong>
          <ul className="event-list">
            {report.events.map((event, index) => (
              <li key={`${event.tick ?? "sem-tick"}-${index}`}>
                {event.tick === null ? "tick não informado" : `tick ${event.tick}`} · {event.roles.join(", ")}
                {event.weapon ? ` · ${event.weapon}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {report.events && report.events.length === 0 && (
        <p>Nenhuma participação individual registrada.</p>
      )}
      {report.rounds && report.rounds.length > 0 && (
        <div>
          <strong>Contexto global da partida · rodadas</strong>
          <ul className="event-list">
            {report.rounds.map((round, index) => (
              <li key={index}>
                {round.winner ? `vencedor: ${round.winner}` : "vencedor não informado"}
                {round.lengthSeconds !== undefined ? ` · ${round.lengthSeconds.toFixed(2)} s` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="privacy-note">IDs de participantes e mensagens não são exibidos.</p>
    </div>
  );
}

function ReplayEntry({
  replay,
  expanded,
  onToggle,
}: {
  replay: Replay;
  expanded: boolean;
  onToggle: () => void;
}) {
  const metrics = replay.report?.metrics;
  const summary = metrics
    ? ([
      ["eliminações", metrics.kills],
      ["mortes", metrics.deaths],
      ["assists", metrics.assists],
    ] as const).filter((item) => item[1] !== undefined).map(([label, count]) => `${count} ${label}`).join(" · ")
    : "Métricas individuais indisponíveis";
  return (
    <article className="replay-entry">
      <h2>{replay.label} {replay.date}</h2>
      <div className={`entry-panel${expanded ? " entry-panel-expanded" : ""}`}>
        <div className="entry-scroll" tabIndex={0} aria-label={`Conteúdo da análise ${replay.date}`}>
          <div className="entry-content">
            <button
              className="entry-toggle"
              type="button"
              aria-label={`${expanded ? "Fechar" : "Abrir"} análise ${replay.label} ${replay.date}`}
              aria-expanded={expanded}
              onClick={onToggle}
            >
              <span className="entry-summary">
          {replay.kind === "sample" ? (
            <p><span className="sample-label">DADOS DE DEMONSTRAÇÃO</span><br />Prévia sem relatório de partida.<br />Estatísticas não disponíveis.<br />Sem demo real.</p>
          ) : (
            <p>
              <span className="sample-label">{replay.kind === "catalog" ? "RELATÓRIO DA DEMO" : "JSON IMPORTADO"}</span>
              <br />{replay.report?.map ? `Mapa: ${replay.report.map}` : "Mapa não informado"}
              <br />{summary}
              <br />{replay.videoUrl ? "Vídeo disponível · abrir análise" : "Vídeo não associado"}
            </p>
          )}
              </span>
            </button>
            {expanded && (
              <section className="entry-detail" aria-label={`Análise: ${replay.label} ${replay.date}`}>
                {replay.videoUrl && (
                  <div className="replay-video">
                    <h3>Vídeo associado à partida</h3>
                    <video controls playsInline preload="metadata" src={replay.videoUrl} aria-label={`Vídeo associado à partida de ${replay.date}`} />
                    <p>O vídeo pode cobrir apenas um trecho da demo.</p>
                  </div>
                )}
                {replay.report ? <MetricList report={replay.report} /> : (
                  <p>{replay.note} Importe um JSON de análise para consultar dados reais.</p>
                )}
              </section>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

type FooterGif = { src: string; poster: string; href: string; alt: string };

export function SiteFooter({ children, gifs }: { children: ReactNode; gifs: FooterGif[] }) {
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduceMotion(preference.matches);
    update();
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);

  return (
    <footer className="site-footer" id="cheats">
      <div className="footer-tools">{children}</div>
      <div className="footer-gifs" aria-label="GIFs de Team Fortress 2">
        {gifs.map((gif) => (
          <a
            className="footer-gif"
            key={gif.src}
            href={gif.href}
            target="_blank"
            rel="noreferrer"
            aria-label={`${gif.alt} — abrir fonte no Tenor`}
          >
            <img src={reduceMotion ? gif.poster : gif.src} alt={gif.alt} />
          </a>
        ))}
      </div>
      <p className="copyright" id="sobre">© 2026 OvniCiusDev. All Rights Reserved.</p>
    </footer>
  );
}

const footerGifs: FooterGif[] = [
  {
    src: "https://media1.tenor.com/m/ZWdZrQpBBlMAAAAC/tf2.gif",
    poster: "https://media1.tenor.com/m/ZWdZrQpBBlMAAAAe/tf2.png",
    href: "https://tenor.com/pt-BR/view/tf2-gif-7306907520168166995",
    alt: "Adesivo animado de Team Fortress 2",
  },
  {
    src: "https://media1.tenor.com/m/Mtbm23hcnFEAAAAC/tf2-team-fortress-2.gif",
    poster: "https://media.tenor.com/Mtbm23hcnFEAAAAe/tf2-team-fortress-2.png",
    href: "https://tenor.com/pt-BR/view/tf2-team-fortress-2-engineer-tf2-engineer-tf2-engineer-gif-3663369177204038737",
    alt: "Adesivo animado de Engineer do Team Fortress 2",
  },
  {
    src: "https://media1.tenor.com/m/s9tKyts6h7sAAAAC/demoman-tf2.gif",
    poster: "https://media.tenor.com/s9tKyts6h7sAAAAe/demoman-tf2.png",
    href: "https://tenor.com/pt-BR/view/demoman-tf2-team-fortress-2-skyrim-skeleton-meme-rahh-skeleton-meme-gif-12960034587810629563",
    alt: "Demoman animado do Team Fortress 2",
  },
];

export function App() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [catalogReplays, setCatalogReplays] = useState<Replay[]>(initialCatalog?.replays ?? []);
  const [importedReplays, setImportedReplays] = useState<Replay[]>([]);
  const [catalogError, setCatalogError] = useState<string | null>(initialCatalog?.error ?? null);
  const [expandedId, setExpandedId] = useState<string | null>(initialCatalog?.replays[0]?.id ?? null);
  const [importError, setImportError] = useState<string | null>(null);
  const samples: Replay[] = import.meta.env.DEV ? sampleReplays
    .filter((sample) => !catalogReplays.some((replay) => replay.date === sample.date))
    .map((sample) => ({ ...sample, label: "análise gameplay", kind: "sample" })) : [];
  const replays = [...importedReplays, ...catalogReplays, ...samples];

  useEffect(() => {
    const controller = new AbortController();
    async function loadCatalog() {
      try {
        const response = await fetch("/api/replays", { signal: controller.signal });
        if (!response.ok) throw new Error("O catálogo local não respondeu.");
        const catalog = parseCatalog(await response.json());
        if (!controller.signal.aborted) {
          setCatalogReplays(catalog.replays);
          setCatalogError(catalog.error);
          setExpandedId((current) => current ?? catalog.replays[0]?.id ?? null);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setCatalogError(error instanceof Error ? error.message : "Catálogo local indisponível.");
        }
      }
    }
    void loadCatalog();
    return () => controller.abort();
  }, []);

  async function importReport(file?: File) {
    setImportError(null);
    if (!file) return;
    if (file.size > 2_000_000) {
      setImportError("O arquivo excede o limite local de 2 MB.");
      return;
    }
    try {
      const parsed = parseIndividualReport(JSON.parse(await readLocalFile(file)));
      const replay: Replay = {
        id: `import-${Date.now()}`,
        date: "data não informada",
        label: "análise individual",
        kind: "imported",
        report: parsed,
      };
      setImportedReplays((current) => [replay, ...current]);
      setExpandedId(replay.id);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Não foi possível ler o relatório.");
    }
    if (fileInput.current) fileInput.current.value = "";
  }

  return (
    <div className="app-shell">
      <SiteHeader />
      <NavigationBar />
      <main className="main-scroll" id="replays">
        <section className="replay-list" aria-label="Análises de partidas">
          {catalogError && <p className="catalog-error" role="status">{catalogError}</p>}
          {importError && <p className="import-error" role="alert">Erro ao importar: {importError}</p>}
          {replays.length === 0 ? (
            <p className="empty-state">Nenhuma análise disponível. Importe um relatório JSON local.</p>
          ) : (
            <div className="replay-items">
              {replays.map((replay) => (
                <ReplayEntry
                  key={replay.id}
                  replay={replay}
                  expanded={expandedId === replay.id}
                  onToggle={() => setExpandedId((current) => current === replay.id ? null : replay.id)}
                />
              ))}
            </div>
          )}
        </section>
        <SiteFooter gifs={footerGifs}>
          <label className="import-control">
            IMPORTAR JSON
            <input
              ref={fileInput}
              type="file"
              accept="application/json,.json"
              aria-label="Importar relatório JSON local"
              onChange={(event) => void importReport(event.currentTarget.files?.[0])}
            />
          </label>
        </SiteFooter>
      </main>
    </div>
  );
}
