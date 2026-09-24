import { AskPanel } from "../components/AskPanel";
import { S } from "../lib/strings";

export function AskPage() {
  return (
    <>
      <h1>{S.ask.generalTitle}</h1>
      <AskPanel />
    </>
  );
}
