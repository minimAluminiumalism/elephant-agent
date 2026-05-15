import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const targetFile = path.resolve(
  __dirname,
  "../node_modules/@docusaurus/bundler/lib/currentBundler.js"
);

const originalSnippet = "    return webpackbar_1.default;";
const patchedSnippet = `    class SilentWebpackBarPlugin {
        apply() {
            // Disable the progress UI only. Build output stays unchanged.
        }
    }
    return SilentWebpackBarPlugin;`;

async function patchBundler() {
  try {
    const source = await fs.readFile(targetFile, "utf8");

    if (source.includes("return SilentWebpackBarPlugin;")) {
      console.log("Docusaurus bundler progress patch already applied");
      return;
    }

    if (!source.includes(originalSnippet)) {
      throw new Error(`Expected snippet not found in ${targetFile}`);
    }

    const patched = source.replace(originalSnippet, patchedSnippet);
    await fs.writeFile(targetFile, patched, "utf8");
    console.log("Patched Docusaurus webpack progress plugin for local builds");
  } catch (error) {
    console.error(error);
    process.exitCode = 1;
  }
}

await patchBundler();
