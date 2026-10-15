import React from "react";
import api from "../../lib/axios";

export interface ChatExportCitation {
  ref: string;
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_start?: number | null;
  excerpt: string;
}

export interface ChatExportDocxPayload {
  question: string;
  answer: string;
  document_id?: string | null;
  citations?: ChatExportCitation[];
}

type PostClient = (
  url: string,
  data: unknown,
  config: { responseType: "blob" },
) => Promise<{
  data: BlobPart;
  headers?: Record<string, string | undefined>;
}>;

const HEADING_RE = /^\s*(#{1,6})\s+(.+?)\s*#*$/;
const BULLET_RE = /^\s*[-*•]\s+(.+)$/;
const NUMBERED_RE = /^\s*(\d+)[.)]\s+(.+)$/;
const QUOTE_RE = /^\s*>\s*(.+)$/;
const HR_RE = /^\s*(?:---+|\*\*\*+|___+)\s*$/;

// Captura tokens inline: **negrito**, __negrito__, `código`, *itálico* e citações [1] / [A]
const INLINE_TOKEN_RE =
  /(\*\*[^*\n]+\*\*|__[^_\n]+__|`[^`\n]+`|\*[^*\n]+\*|\[(?:\d+|[A-Z])\])/g;

function cleanLooseMarkers(segment: string): string {
  return segment.replace(/\*\*/g, "").replace(/__/g, "");
}

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let tokenIndex = 0;

  for (const match of text.matchAll(INLINE_TOKEN_RE)) {
    const matchIndex = match.index ?? 0;
    if (matchIndex > lastIndex) {
      nodes.push(cleanLooseMarkers(text.slice(lastIndex, matchIndex)));
    }
    const token = match[0];
    const key = `${keyPrefix}-t-${tokenIndex++}`;

    if (
      (token.startsWith("**") && token.endsWith("**")) ||
      (token.startsWith("__") && token.endsWith("__"))
    ) {
      nodes.push(
        <strong key={key} className="font-semibold text-tinta-profunda">
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      nodes.push(
        <code
          key={key}
          className="rounded bg-papel-areia/70 px-1.5 py-0.5 font-mono text-xs text-tinta-profunda"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      nodes.push(
        <em key={key} className="italic text-tinta">
          {token.slice(1, -1)}
        </em>,
      );
    } else if (token.startsWith("[") && token.endsWith("]")) {
      nodes.push(
        <span
          key={key}
          className="mx-0.5 inline-flex items-center rounded border border-latiim/60 bg-papel-alta px-1.5 py-0.5 font-mono text-[11px] font-medium leading-none text-latiim-texto"
        >
          {token}
        </span>,
      );
    } else {
      nodes.push(cleanLooseMarkers(token));
    }

    lastIndex = matchIndex + token.length;
  }

  if (lastIndex < text.length) {
    nodes.push(cleanLooseMarkers(text.slice(lastIndex)));
  }

  return nodes;
}

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] }
  | { kind: "quote"; lines: string[] }
  | { kind: "hr" };

function parseBlocks(raw: string): Block[] {
  const lines = (raw || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n");
  const blocks: Block[] = [];
  let paragraphBuffer: string[] = [];
  let ulBuffer: string[] = [];
  let olBuffer: string[] = [];
  let quoteBuffer: string[] = [];

  const flushParagraph = () => {
    if (paragraphBuffer.length === 0) return;
    const joined = paragraphBuffer.join(" ").trim();
    paragraphBuffer = [];
    if (joined) blocks.push({ kind: "paragraph", text: joined });
  };

  const flushUl = () => {
    if (ulBuffer.length === 0) return;
    blocks.push({ kind: "ul", items: ulBuffer });
    ulBuffer = [];
  };

  const flushOl = () => {
    if (olBuffer.length === 0) return;
    blocks.push({ kind: "ol", items: olBuffer });
    olBuffer = [];
  };

  const flushQuote = () => {
    if (quoteBuffer.length === 0) return;
    blocks.push({ kind: "quote", lines: quoteBuffer });
    quoteBuffer = [];
  };

  const flushAll = () => {
    flushParagraph();
    flushUl();
    flushOl();
    flushQuote();
  };

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();
    if (!trimmed) {
      flushAll();
      continue;
    }

    if (HR_RE.test(trimmed)) {
      flushAll();
      blocks.push({ kind: "hr" });
      continue;
    }

    const headingMatch = rawLine.match(HEADING_RE);
    if (headingMatch) {
      flushAll();
      blocks.push({
        kind: "heading",
        level: Math.min(headingMatch[1].length, 4),
        text: headingMatch[2].trim(),
      });
      continue;
    }

    const bulletMatch = rawLine.match(BULLET_RE);
    if (bulletMatch) {
      flushParagraph();
      flushOl();
      flushQuote();
      ulBuffer.push(bulletMatch[1].trim());
      continue;
    }

    const numberedMatch = rawLine.match(NUMBERED_RE);
    if (numberedMatch) {
      flushParagraph();
      flushUl();
      flushQuote();
      olBuffer.push(numberedMatch[2].trim());
      continue;
    }

    const quoteMatch = rawLine.match(QUOTE_RE);
    if (quoteMatch) {
      flushParagraph();
      flushUl();
      flushOl();
      quoteBuffer.push(quoteMatch[1].trim());
      continue;
    }

    flushUl();
    flushOl();
    flushQuote();
    paragraphBuffer.push(trimmed);
  }

  flushAll();
  return blocks;
}

export function ChatFormattedText({ text }: { text: string }) {
  if (!text || !text.trim()) {
    return <p className="text-tinta-muda">…</p>;
  }

  const blocks = parseBlocks(text);

  return (
    <div className="space-y-3 text-sm leading-7 text-tinta">
      {blocks.map((block, idx) => {
        const key = `blk-${idx}`;
        if (block.kind === "hr") {
          return <hr key={key} className="my-2 border-linha" />;
        }
        if (block.kind === "heading") {
          const HeadingTag = block.level <= 2 ? "h3" : "h4";
          const headingClass =
            block.level <= 2
              ? "mt-2 font-display text-base font-semibold tracking-tight text-tinta-profunda"
              : "mt-1.5 text-sm font-semibold uppercase tracking-[0.08em] text-tinta-profunda";
          return (
            <HeadingTag key={key} className={headingClass}>
              {renderInline(block.text, key)}
            </HeadingTag>
          );
        }
        if (block.kind === "ul") {
          return (
            <ul key={key} className="space-y-1.5 pl-4">
              {block.items.map((item, itemIdx) => (
                <li
                  key={`${key}-li-${itemIdx}`}
                  className="flex items-start gap-2.5 leading-6"
                >
                  <span
                    aria-hidden="true"
                    className="mt-2 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-latiim-texto"
                  />
                  <span className="flex-1">
                    {renderInline(item, `${key}-li-${itemIdx}`)}
                  </span>
                </li>
              ))}
            </ul>
          );
        }
        if (block.kind === "ol") {
          return (
            <ol key={key} className="space-y-1.5 pl-1">
              {block.items.map((item, itemIdx) => (
                <li
                  key={`${key}-oli-${itemIdx}`}
                  className="flex items-start gap-2.5 leading-6"
                >
                  <span className="mt-0.5 inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border border-linha bg-papel-alta font-mono text-[11px] font-medium text-tinta-profunda">
                    {itemIdx + 1}
                  </span>
                  <span className="flex-1">
                    {renderInline(item, `${key}-oli-${itemIdx}`)}
                  </span>
                </li>
              ))}
            </ol>
          );
        }
        if (block.kind === "quote") {
          return (
            <blockquote
              key={key}
              className="rounded-r-[5px] border-l-2 border-latiim bg-papel-alta/70 px-3.5 py-2 italic text-tinta-suave"
            >
              {renderInline(block.lines.join(" "), key)}
            </blockquote>
          );
        }
        return (
          <p key={key} className="leading-7">
            {renderInline(block.text, key)}
          </p>
        );
      })}
    </div>
  );
}

function extractFilename(contentDisposition?: string): string {
  const match = contentDisposition?.match(/filename="?([^";]+)"?/i);
  if (match?.[1]) {
    return match[1];
  }
  const datePart = new Date().toISOString().slice(0, 10);
  return `parecer-chat-${datePart}.docx`;
}

export async function downloadChatAnswerDocx(
  payload: ChatExportDocxPayload,
  postClient: PostClient = (url, data, config) => api.post(url, data, config),
): Promise<string> {
  const response = await postClient(
    "/chat/export-docx",
    {
      question: payload.question,
      answer: payload.answer,
      document_id: payload.document_id || null,
      citations: payload.citations ?? [],
    },
    { responseType: "blob" },
  );

  const filename = extractFilename(response.headers?.["content-disposition"]);
  const blob = new Blob([response.data], {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  return filename;
}
