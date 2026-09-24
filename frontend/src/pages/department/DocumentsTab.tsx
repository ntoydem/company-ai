import { useState } from "react";
import { useOutletContext } from "react-router-dom";

import { useDocuments } from "../../api/documents";
import { projectNameById, useProjects } from "../../api/projects";
import type { Department, DocumentListItem } from "../../api/types";
import { DocumentDetailPanel } from "../../components/DocumentDetailPanel";
import { DocumentTable } from "../../components/DocumentTable";
import { ErrorBox } from "../../components/ErrorBox";
import { Spinner } from "../../components/Spinner";
import { S } from "../../lib/strings";
import type { DepartmentContext } from "../Department";

function matchesSubdepartment(document: DocumentListItem, sub: Department): boolean {
  const value = document.subdepartment?.toLocaleLowerCase("tr") ?? "";
  return value === sub.name.toLocaleLowerCase("tr") || value === sub.slug;
}

export function DocumentsTab() {
  const { department, children, subdepartment, isAdmin } = useOutletContext<DepartmentContext>();
  const documents = useDocuments({ department: department.slug });
  const projects = useProjects();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (documents.isLoading) return <Spinner />;
  if (documents.isError) return <ErrorBox error={documents.error} />;
  const all = documents.data ?? [];
  const visible = subdepartment ? all.filter((d) => matchesSubdepartment(d, subdepartment)) : all;
  const projectNames = projectNameById(projects.data);

  return (
    <>
      <h2>{S.documents.title}</h2>
      <DocumentTable
        documents={visible}
        projectNames={projectNames}
        selectedId={selectedId}
        onSelect={(id) => setSelectedId(id === selectedId ? null : id)}
        showSubdepartment={children.length > 0}
        subdepartmentLabel={(value) =>
          children.find((c) => c.slug === value || c.name === value)?.name ?? value
        }
      />
      {selectedId && (
        <div style={{ marginTop: 16 }}>
          <DocumentDetailPanel
            id={selectedId}
            isAdmin={isAdmin}
            projectNames={projectNames}
            onClose={() => setSelectedId(null)}
          />
        </div>
      )}
    </>
  );
}
