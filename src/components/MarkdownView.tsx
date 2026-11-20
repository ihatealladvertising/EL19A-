import React from 'react';

interface MarkdownViewProps {
  content: string;
  onSelectAddress?: (addr: string) => void;
}

const TOKEN_REGEX = /(\*\*[^*]+\*\*|`[^`]+`|\b0x[0-9A-Fa-f]{4,8}\b)/g;

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, onSelectAddress }) => {
  const renderInline = (text: string) => {
    const parts = text.split(TOKEN_REGEX);
    return parts.map((part, idx) => {
      if (!part) return null;
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        const inner = part.slice(1, -1);
        if (/^0x[0-9A-Fa-f]{4,8}$/i.test(inner) && onSelectAddress) {
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectAddress(inner)}
              className="mx-0.5 rounded bg-sky-50 px-1.5 py-0.5 font-mono text-xs text-sky-700 underline decoration-sky-300 underline-offset-2 hover:bg-sky-100"
            >
              {inner}
            </button>
          );
        }
        return (
          <code
            key={idx}
            className="mx-0.5 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-800"
          >
            {inner}
          </code>
        );
      }
      if (/^0x[0-9A-Fa-f]{4,8}$/i.test(part) && onSelectAddress) {
        const num = parseInt(part, 16);
        if (num < 0x100000) {
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectAddress(part)}
              className="rounded px-1 font-mono text-xs text-sky-700 underline decoration-sky-300 underline-offset-2 hover:bg-sky-50"
              title="Inspect address in ROM Explorer"
            >
              {part}
            </button>
          );
        }
      }
      return <React.Fragment key={idx}>{part}</React.Fragment>;
    });
  };

  const lines = content.split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith('```')) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre
          key={`code-${i}`}
          className="my-3 overflow-x-auto rounded-lg border border-slate-200 bg-slate-900 p-3 font-mono text-xs leading-relaxed text-slate-100"
        >
          {codeLines.join('\n')}
        </pre>
      );
      i++;
      continue;
    }

    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={i} className="mb-3 text-xl font-bold tracking-tight text-slate-900">
          {renderInline(line.slice(2))}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2
          key={i}
          className="mt-6 mb-2 border-b border-slate-200 pb-1.5 text-base font-semibold text-slate-900"
        >
          {renderInline(line.slice(3))}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} className="mt-4 mb-1.5 text-sm font-semibold text-slate-800">
          {renderInline(line.slice(4))}
        </h3>
      );
    } else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const listItems: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="my-2 space-y-1.5 pl-5 text-sm leading-relaxed text-slate-700 list-disc">
          {listItems.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    } else if (/^\d+\.\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ''));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="my-2 space-y-1.5 pl-5 text-sm leading-relaxed text-slate-700 list-decimal">
          {listItems.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ol>
      );
      continue;
    } else if (line.trim() === '---') {
      elements.push(<hr key={i} className="my-4 border-slate-200" />);
    } else if (line.trim().length > 0) {
      elements.push(
        <p key={i} className="my-1.5 text-sm leading-relaxed text-slate-700">
          {renderInline(line)}
        </p>
      );
    }

    i++;
  }

  return <div className="max-w-none">{elements}</div>;
};
