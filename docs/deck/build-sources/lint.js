// Pre-compile lint: reject non-ASCII quotes / full-width punctuation in slide sources.
// All characters are written as \u escapes so this file stays pure ASCII itself.
const fs = require("fs");
const path = require("path");

const DIR = path.join(__dirname);
const BAD = /[\u201c\u201d\u2018\u2019\u3001\u3002\uff0c\uff1b\uff1a\uff01\uff1f\uff08\uff09\u2014\u2013\u2026\u00a0]/g;
const ANY_NON_ASCII = /[^\x00-\x7F]/;

let ok = true;

for (const f of fs.readdirSync(DIR).filter((f) => f.endsWith(".js"))) {
  const src = fs.readFileSync(path.join(DIR, f), "utf8");
  const lines = src.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(BAD);
    if (m) {
      console.error("NON-ASCII PUNCTUATION in slides/" + f + ":" + (i + 1) + " -> " + JSON.stringify(m));
      ok = false;
    }
    if (ANY_NON_ASCII.test(lines[i])) {
      console.error("NON-ASCII CHARACTER in slides/" + f + ":" + (i + 1) + " -> " + JSON.stringify(lines[i].trim()));
      ok = false;
    }
  }
}

if (!ok) {
  console.error("FIX non-ASCII characters before compiling!");
  process.exit(1);
}
console.log("Pre-compile lint passed (pure ASCII, no smart quotes).");
