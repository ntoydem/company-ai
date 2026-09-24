import { useOutletContext } from "react-router-dom";

import { AskPanel } from "../../components/AskPanel";
import type { DepartmentContext } from "../Department";

export function AskTab() {
  const { department } = useOutletContext<DepartmentContext>();
  return <AskPanel department={department} />;
}
