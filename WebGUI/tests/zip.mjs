/* zip.mjs - reads a zip file the page made: {file name: bytes}.  (Stored and deflated entries, no zip64.) */
import zlib from "node:zlib";

export function unzip(buf) {
  let end = buf.length - 22;
  while (end >= 0 && buf.readUInt32LE(end) !== 0x06054b50) end--;
  if (end < 0) throw new Error("not a zip file");
  const count = buf.readUInt16LE(end + 10);
  let at = buf.readUInt32LE(end + 16);
  const out = {};
  for (let i = 0; i < count; i++) {
    if (buf.readUInt32LE(at) !== 0x02014b50) throw new Error("damaged zip directory");
    const method = buf.readUInt16LE(at + 10), size = buf.readUInt32LE(at + 20);
    const nameLen = buf.readUInt16LE(at + 28), extraLen = buf.readUInt16LE(at + 30), commentLen = buf.readUInt16LE(at + 32);
    const local = buf.readUInt32LE(at + 42);
    const name = buf.toString("utf8", at + 46, at + 46 + nameLen);
    const dataAt = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
    const data = buf.subarray(dataAt, dataAt + size);
    if (!name.endsWith("/")) out[name] = method === 0 ? Buffer.from(data) : zlib.inflateRawSync(data);
    at += 46 + nameLen + extraLen + commentLen;
  }
  return out;
}
