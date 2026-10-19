export type Segment =
  | { kind: "text"; text: string }
  | { kind: "removed"; text: string; label: string };

const PLACEHOLDER = /<([A-Z][A-Z0-9_]*)>/g;

/**
 * The gateway returns the redacted text and entity counts, but no character offsets.
 * This recovers what was removed by aligning the kept text between placeholders
 * against the original. It is a best-effort alignment: it returns null when the two
 * texts do not line up, and the caller then shows the original without markers.
 */
export function markRedactions(original: string, redacted: string): Segment[] | null {
  if (original === redacted) return [{ kind: "text", text: original }];

  const labels: string[] = [];
  const literals: string[] = [];
  let last = 0;
  for (const match of redacted.matchAll(PLACEHOLDER)) {
    literals.push(redacted.slice(last, match.index));
    labels.push(match[1]);
    last = match.index + match[0].length;
  }
  literals.push(redacted.slice(last));

  const first = literals[0];
  const tail = literals[literals.length - 1];
  if (!original.startsWith(first)) return null;
  if (labels.length > 0 && !original.endsWith(tail)) return null;

  const segments: Segment[] = [];
  if (first) segments.push({ kind: "text", text: first });
  let position = first.length;

  for (let index = 0; index < labels.length; index += 1) {
    const isLast = index === labels.length - 1;
    const nextLiteral = literals[index + 1];
    const end = isLast
      ? original.length - nextLiteral.length
      : original.indexOf(nextLiteral, position);
    if (end < position) return null;
    segments.push({ kind: "removed", text: original.slice(position, end), label: labels[index] });
    if (nextLiteral) segments.push({ kind: "text", text: nextLiteral });
    position = end + nextLiteral.length;
  }

  return labels.length === 0 ? null : segments;
}
