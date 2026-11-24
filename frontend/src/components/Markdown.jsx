import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Markdown({ children }) {
  const text = String(children ?? "").replace(/<br\s*\/?>/gi, "\n\n");
  return (
    <div className="answer-markdown min-w-0 text-sm leading-7">
      <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
        ),
        table: ({ children }) => <div className="overflow-x-auto"><table>{children}</table></div>,
      }}>
        {text}
      </ReactMarkdown>
    </div>
  );
}