const file = Bun.file(new URL("index.html", import.meta.url));
const server = Bun.serve({
  hostname: "127.0.0.1",
  port: Number(process.env.FLY_PORT) || 8765,
  fetch(request) {
    const path = new URL(request.url).pathname;
    if (path === "/" || path === "/index.html")
      return new Response(file, { headers: { "Cache-Control": "no-store" } });
    return new Response("Not found", { status: 404 });
  },
});
console.log(`Fly explorer: ${server.url}`);
