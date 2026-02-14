/**
 * Yjs WebSocket Collaboration Server
 *
 * Provides real-time CRDT-based collaboration for the dashboard.
 * Supports:
 * - Room-based collaboration
 * - Awareness (cursor positions, user presence)
 * - Persistent state sync across clients
 *
 * Port: 3001
 */

const WebSocket = require("ws");
const http = require("http");
const { setupWSConnection } = require("y-websocket");

const PORT = process.env.COLLAB_PORT || 3001;
const HOST = process.env.COLLAB_HOST || "localhost";

const server = http.createServer((request, response) => {
  response.writeHead(200, { "Content-Type": "text/plain" });
  response.end("Yjs Collaboration Server\n");
});

const wss = new WebSocket.Server({ server });

wss.on("connection", (ws, req) => {
  setupWSConnection(ws, req);
  console.log(`[Collab] Client connected from ${req.socket.remoteAddress}`);
});

server.listen(PORT, HOST, () => {
  console.log(`\n[Collab Server] Running on ws://${HOST}:${PORT}`);
  console.log(
    `[Collab Server] Rooms are created dynamically on client connection`,
  );
  console.log(`[Collab Server] Ready for collaboration!\n`);
});

server.on("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(`[Collab Server] ERROR: Port ${PORT} is already in use`);
    console.error(
      `[Collab Server] Try stopping the existing server or changing the port`,
    );
    process.exit(1);
  } else {
    console.error("[Collab Server] ERROR:", err);
  }
});

process.on("SIGINT", () => {
  console.log("\n[Collab Server] Shutting down gracefully...");
  wss.close(() => {
    server.close(() => {
      console.log("[Collab Server] Server closed");
      process.exit(0);
    });
  });
});
