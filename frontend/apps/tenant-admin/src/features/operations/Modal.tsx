"use client";

export function Modal({ title, eyebrow, close, children, small = false }: {
  title: string;
  eyebrow: string;
  close: () => void;
  children: React.ReactNode;
  small?: boolean;
}) {
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
    <section className={`editor-panel${small ? " small-editor" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
      <div className="editor-heading"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div><button className="close-button" onClick={close} type="button" aria-label="Close">×</button></div>
      {children}
    </section>
  </div>;
}
