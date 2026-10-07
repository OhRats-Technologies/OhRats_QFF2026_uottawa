import { resolve, extname } from "node:path";

const root = resolve(import.meta.dir, "../..");
const directory = "/web/presentation/";
const port = Number(
  Bun.argv.find((arg) => arg.startsWith("--port="))?.split("=")[1] ?? 8790,
);
const server = Bun.serve({
  hostname: "127.0.0.1",
  port,
  async fetch(request) {
    if (!["GET", "HEAD"].includes(request.method))
      return new Response(null, { status: 405 });
    let name: string;
    try {
      name = decodeURIComponent(new URL(request.url).pathname);
    } catch {
      return new Response(null, { status: 400 });
    }
    if (name === "/")
      return Response.redirect(new URL(directory, request.url), 302);
    if ([directory, "/web/demo/"].includes(name)) name += "index.html";
    const path = resolve(root, `.${name}`);
    const allowed =
      ["web/presentation", "web/demo"].some((dir) =>
        path.startsWith(resolve(root, dir) + "/"),
      ) &&
      [
        ".html",
        ".css",
        ".js",
        ".json",
        ".pdf",
        ".pptx",
        ".png",
        ".svg",
        ".wav",
      ].includes(extname(path));
    if (!allowed) return new Response("Not found", { status: 404 });
    const file = Bun.file(path);
    if (!(await file.exists()))
      return new Response("Not found", { status: 404 });
    return new Response(request.method === "HEAD" ? null : file, {
      headers: { "Content-Type": file.type, "Cache-Control": "no-cache" },
    });
  },
});
console.log(
  `Presentation: http://${server.hostname}:${server.port}${directory}`,
);
