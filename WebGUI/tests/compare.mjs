/* compare.mjs - two board files compared the way the generators' own regression tests do it
   (regression/RegressionTools.py, compare_text): token by token, numbers within a tolerance, everything else exactly.
   Returns the first differences as text lines; an empty list means the files are the same board. */
const NUMBER = /^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$/;

export function differences(expected, actual, tol = 1e-5, limit = 8) {
  const a = String(expected).split(/\s+|(?=[()])|(?<=[()])/).filter(Boolean);
  const b = String(actual).split(/\s+|(?=[()])|(?<=[()])/).filter(Boolean);
  const out = [];
  if (a.length !== b.length) out.push(`${a.length} tokens expected, ${b.length} found`);
  for (let i = 0; i < Math.min(a.length, b.length) && out.length < limit; i++) {
    if (a[i] === b[i]) continue;
    if (NUMBER.test(a[i]) && NUMBER.test(b[i]) && Math.abs(+a[i] - +b[i]) <= tol) continue;
    out.push(`token ${i}: expected ${a[i]}, found ${b[i]}   (… ${a.slice(Math.max(0, i - 4), i).join(" ")} [${a[i]}] ${a.slice(i + 1, i + 4).join(" ")} …)`);
  }
  return out;
}
