import "dotenv/config";
import cors from "cors";
import express from "express";
import { handleMcpRequest } from "./route-handlers.js";
import { shutdown as shutdownDb } from "./db.js";

const app = express();
const PORT = parseInt(process.env.PORT || "3100");
const MCP_ACCESS_KEY = process.env.MCP_ACCESS_KEY!;
const CITATION_BASE_URL = process.env.OPEN_BRAIN_CITATION_BASE_URL || "https://openbrain.local/thoughts";

app.use(express.json());
app.use(cors());

app.use("/mcp", (req, res, next) => {
  const provided =
    req.headers["x-brain-key"] as string | undefined ||
    new URL(req.url, `http://${req.headers.host}`).searchParams.get("key");

  if (!provided || provided !== MCP_ACCESS_KEY) {
    res.status(401).json({ error: "Invalid or missing access key" });
    return;
  }
  next();
});

app.post("/mcp", async (req, res) => {
  await handleMcpRequest(req, res);
});

app.get("/mcp", (_req, res) => {
  res.status(405).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "SSE not supported" },
    id: null,
  });
});

app.delete("/mcp", (_req, res) => {
  res.status(405).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Sessions not supported" },
    id: null,
  });
});

const server = app.listen(PORT, "0.0.0.0", () => {
  console.log(`Open Brain MCP server listening on port ${PORT}`);
  console.log(`MCP endpoint: http://0.0.0.0:${PORT}/mcp`);
  console.log(`Health check: http://0.0.0.0:${PORT}/health`);
  console.log(`Citation base URL: ${CITATION_BASE_URL}`);
});

const gracefulShutdown = (signal: string) => {
  console.log(`${signal} received, shutting down...`);
  shutdownDb();
  server.close(() => {
    console.log("Server closed");
    process.exit(0);
  });
};

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
