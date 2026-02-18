import React from 'react';

interface MarkdownMessageProps {
  content: string;
  role: 'user' | 'assistant';
}

/**
 * Lightweight markdown renderer for the Co-Pilot chat
 * Handles: **bold**, *italic*, `code`, ```blocks```, - lists, headers, links
 */
export function MarkdownMessage({ content, role }: MarkdownMessageProps) {
  const isAssistant = role === 'assistant';
  
  // Parse markdown and convert to React elements
  const parseMarkdown = (text: string): React.ReactNode[] => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let codeBlock = false;
    let codeContent: string[] = [];
    let codeLanguage = '';
    
    lines.forEach((line, idx) => {
      // Code block start/end
      if (line.startsWith('```')) {
        if (!codeBlock) {
          codeBlock = true;
          codeLanguage = line.slice(3).trim();
          codeContent = [];
        } else {
          // End code block
          elements.push(
            <pre 
              key={`code-${idx}`} 
              className="bg-slate-950 rounded-lg p-3 my-2 overflow-x-auto border border-slate-700"
            >
              {codeLanguage && (
                <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-2 font-medium">
                  {codeLanguage}
                </div>
              )}
              <code className="text-xs font-mono text-emerald-400">
                {codeContent.join('\n')}
              </code>
            </pre>
          );
          codeBlock = false;
          codeLanguage = '';
        }
        return;
      }
      
      if (codeBlock) {
        codeContent.push(line);
        return;
      }
      
      // Empty line
      if (!line.trim()) {
        elements.push(<div key={idx} className="h-2" />);
        return;
      }
      
      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={idx} className="text-sm font-bold text-slate-100 mt-3 mb-1">
            {parseInline(line.slice(4))}
          </h3>
        );
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={idx} className="text-base font-bold text-slate-100 mt-3 mb-1">
            {parseInline(line.slice(3))}
          </h2>
        );
        return;
      }
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={idx} className="text-lg font-bold text-slate-100 mt-3 mb-1">
            {parseInline(line.slice(2))}
          </h1>
        );
        return;
      }
      
      // Bullet lists
      if (line.match(/^[-*]\s/)) {
        elements.push(
          <div key={idx} className="flex gap-2 pl-2 py-0.5">
            <span className="text-blue-400 flex-shrink-0">•</span>
            <span>{parseInline(line.slice(2))}</span>
          </div>
        );
        return;
      }
      
      // Numbered lists
      const numberedMatch = line.match(/^(\d+)\.\s/);
      if (numberedMatch) {
        elements.push(
          <div key={idx} className="flex gap-2 pl-2 py-0.5">
            <span className="text-blue-400 flex-shrink-0 min-w-[1.25rem]">{numberedMatch[1]}.</span>
            <span>{parseInline(line.slice(numberedMatch[0].length))}</span>
          </div>
        );
        return;
      }
      
      // Regular paragraph
      elements.push(
        <p key={idx} className="py-0.5 leading-relaxed">
          {parseInline(line)}
        </p>
      );
    });
    
    return elements;
  };
  
  // Parse inline markdown (bold, italic, code, links)
  const parseInline = (text: string): React.ReactNode[] => {
    const elements: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;
    
    // Pattern matching for inline elements
    const patterns = [
      // Bold: **text** or __text__
      { regex: /\*\*(.+?)\*\*/g, render: (match: string) => <strong key={key++} className="font-semibold text-slate-100">{match}</strong> },
      { regex: /__(.+?)__/g, render: (match: string) => <strong key={key++} className="font-semibold text-slate-100">{match}</strong> },
      // Italic: *text* or _text_
      { regex: /\*([^*]+?)\*/g, render: (match: string) => <em key={key++} className="italic text-slate-300">{match}</em> },
      { regex: /_([^_]+?)_/g, render: (match: string) => <em key={key++} className="italic text-slate-300">{match}</em> },
      // Inline code: `code`
      { regex: /`([^`]+?)`/g, render: (match: string) => <code key={key++} className="bg-slate-800 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-400">{match}</code> },
      // Links: [text](url)
      { regex: /\[([^\]]+)\]\(([^)]+)\)/g, render: (text: string, url: string) => (
        <a key={key++} href={url} target="_blank" rel="noopener noreferrer" 
           className="text-blue-400 hover:text-blue-300 underline underline-offset-2">
          {text}
        </a>
      ) },
    ];
    
    // Simple approach: process sequentially
    // First handle bold
    remaining = remaining.replace(/\*\*(.+?)\*\*/g, '⟨BOLD:$1⟩');
    // Then inline code (before italic to avoid conflicts)
    remaining = remaining.replace(/`([^`]+?)`/g, '⟨CODE:$1⟩');
    // Then italic (single asterisks that remain)
    remaining = remaining.replace(/\*([^*\s][^*]*?)\*/g, '⟨ITALIC:$1⟩');
    // Then links
    remaining = remaining.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '⟨LINK:$1|$2⟩');
    
    // Split and render
    const parts = remaining.split(/(⟨[A-Z]+:[^⟩]+⟩)/g);
    
    return parts.map((part, i) => {
      if (part.startsWith('⟨BOLD:')) {
        const content = part.slice(6, -1);
        return <strong key={i} className="font-semibold text-slate-100">{content}</strong>;
      }
      if (part.startsWith('⟨CODE:')) {
        const content = part.slice(6, -1);
        return <code key={i} className="bg-slate-800 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-400">{content}</code>;
      }
      if (part.startsWith('⟨ITALIC:')) {
        const content = part.slice(8, -1);
        return <em key={i} className="italic text-slate-300">{content}</em>;
      }
      if (part.startsWith('⟨LINK:')) {
        const content = part.slice(6, -1);
        const [text, url] = content.split('|');
        return (
          <a key={i} href={url} target="_blank" rel="noopener noreferrer" 
             className="text-blue-400 hover:text-blue-300 underline underline-offset-2">
            {text}
          </a>
        );
      }
      return part;
    });
  };
  
  return (
    <div className={`text-sm leading-relaxed break-words overflow-wrap-anywhere ${isAssistant ? 'text-slate-200' : 'text-white'}`} style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
      {parseMarkdown(content)}
    </div>
  );
}
