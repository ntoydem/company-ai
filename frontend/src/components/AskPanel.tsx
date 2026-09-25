import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { ask } from "../api/ask";
import { useDocuments } from "../api/documents";
import { projectNameById, useProjects } from "../api/projects";
import type { AskResponse, Department } from "../api/types";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";
import { ExcelSourceCardList, SourceCardList } from "./SourceCardList";

/** Shared by "Genel Sor" (no scope) and each department's Sor tab (`department` set).
 * The backend answers only from documents the user may see (ADR-004); scope only narrows. */
export function AskPanel({ department }: { department?: Department }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const documents = useDocuments(department ? { department: department.slug } : {});
  const projects = useProjects();
  const projectNames = projectNameById(projects.data);
  const projectOfDocument = (documentId: string): string | null => {
    const doc = documents.data?.find((d) => d.id === documentId);
    return doc?.project_id ? (projectNames.get(doc.project_id) ?? null) : null;
  };

  const mutation = useMutation({
    mutationFn: (q: string) =>
      ask({ question: q, department: department ? department.slug : undefined }),
    onSuccess: (data) => setResult(data),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const q = question.trim();
    if (q.length < 3) return;
    setResult(null);
    mutation.mutate(q);
  }

  return (
    <div>
      {department ? (
        <p className="notice">{S.ask.scopeNote(department.name)}</p>
      ) : (
        <p className="notice">{S.home.askHint}</p>
      )}
      <form className="ask-form" onSubmit={onSubmit}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={S.ask.placeholder}
          minLength={3}
          maxLength={1000}
          required
        />
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? S.ask.submitting : S.ask.submit}
        </button>
      </form>
      <div className="examples">
        {S.ask.examples}{" "}
        {S.ask.exampleQuestions.map((q) => (
          <a key={q} onClick={() => setQuestion(q)}>
            {q}
          </a>
        ))}
      </div>
      {mutation.isError && <ErrorBox error={mutation.error} />}
      {result && (
        <>
          <section className="card">
            <h2>
              {S.ask.answerTitle}{" "}
              <span className={`badge ${result.query_type === "GENERAL_QUERY" ? "warn" : "neutral"}`}>
                {S.ask.queryType[result.query_type]}
              </span>
            </h2>
            {/* GENERAL answers already start with the same sentence (ADR-010). */}
            {result.query_type !== "GENERAL_QUERY" && <p className="notice">{result.notice}</p>}
            <div className={`answer${result.answered ? "" : " no"}`}>{result.answer}</div>
            {result.model && (
              <div className="meta">
                {S.ask.model}: {result.model} · {result.tokens_in}/{result.tokens_out} {S.ask.tokens}
              </div>
            )}
          </section>
          {result.answered && result.query_type !== "GENERAL_QUERY" && (
            <>
              {result.query_type !== "DATA_QUERY" && (
                <section className="card">
                  <h2>{S.ask.sourcesTitle}</h2>
                  <SourceCardList sources={result.sources} projectOfDocument={projectOfDocument} />
                </section>
              )}
              {result.query_type !== "DOCUMENT_QUERY" && (
                <section className="card">
                  <h2>{S.ask.excelSourcesTitle}</h2>
                  <ExcelSourceCardList sources={result.excel_sources} />
                </section>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
