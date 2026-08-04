import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the trajectory archive", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<html lang="zh-CN">/);
  assert.match(html, /<title>Gen-Retry 轨迹档案<\/title>/);
  assert.match(html, /VERIFIER-GROUNDED IMAGE RETRY/);
  assert.match(html, /看见 Retry 如何改对一张图/);
  assert.match(html, /COUNT \+ LAYOUT/);
  assert.match(html, /按失败维度筛选/);
  assert.match(html, /历史恢复/);
  assert.match(html, /FINAL RETRY PROMPT/);
  assert.match(html, /1,301/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|SkeletonPreview/);
});

test("ships canonical trajectory assets and no starter preview", async () => {
  const requiredAssets = [
    "../public/trajectories/ep-005/attempt-3.png",
    "../public/trajectories/ep-012/attempt-2.png",
    "../public/trajectories/ep-056/attempt-4.png",
    "../public/trajectories/ep-079/attempt-3.png",
    "../public/trajectories/ep-108/attempt-2.png",
    "../public/trajectories/ep-157/attempt-3.png",
    "../public/trajectories/ep-158/attempt-2.png",
    "../public/trajectories/ep-176/attempt-2.png",
  ];

  await Promise.all(requiredAssets.map((path) => access(new URL(path, import.meta.url))));
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));

  const [page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /TrajectoryCard/);
  assert.match(page, /dimension-filters/);
  assert.match(page, /batch-controls/);
  assert.match(page, /PromptParagraphs/);
  assert.match(layout, /Gen-Retry 轨迹档案/);
  assert.match(packageJson, /gen-retry-trajectory-showcase/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
});
