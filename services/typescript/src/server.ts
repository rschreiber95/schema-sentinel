import { createServer, IncomingMessage, ServerResponse } from "node:http";
import { resolve } from "node:path";
import protobuf from "protobufjs";

const port = Number.parseInt(process.env.PORT ?? "8001", 10);
const protoPath = resolve(process.cwd(), "proto", "testbed.proto");
const csharpRelayUrl =
  process.env.CSHARP_RELAY_URL ?? "http://localhost:8002/relay";

async function readBody(request: IncomingMessage): Promise<Buffer> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

function sendJson(
  response: ServerResponse,
  status: number,
  body: Record<string, unknown>,
): void {
  const encoded = Buffer.from(JSON.stringify(body));
  response.writeHead(status, {
    "content-type": "application/json",
    "content-length": encoded.length,
  });
  response.end(encoded);
}

async function main(): Promise<void> {
  const root = await protobuf.load(protoPath);
  const TestbedMessage = root.lookupType(
    "schema_sentinel.testbed.TestbedMessage",
  );

  const server = createServer(async (request, response) => {
    if (request.method === "GET" && request.url === "/health") {
      sendJson(response, 200, { status: "ok", runtime: "typescript" });
      return;
    }

    if (request.method !== "POST" || request.url !== "/relay") {
      sendJson(response, 404, { error: "not found" });
      return;
    }

    try {
      const decoded = TestbedMessage.decode(await readBody(request));
      const message = TestbedMessage.toObject(decoded, {
        arrays: true,
        defaults: true,
      }) as {
        messageId: string;
        payload: string;
        visitedServices: string[];
      };

      message.visitedServices.push("typescript");
      const encoded = TestbedMessage.encode(
        TestbedMessage.create(message),
      ).finish();

      const csharpResponse = await fetch(csharpRelayUrl, {
        method: "POST",
        headers: { "content-type": "application/x-protobuf" },
        body: Buffer.from(encoded),
      });
      if (!csharpResponse.ok) {
        throw new Error(`C# relay returned ${csharpResponse.status}`);
      }
      const relayed = Buffer.from(await csharpResponse.arrayBuffer());

      response.writeHead(200, {
        "content-type": "application/x-protobuf",
        "content-length": relayed.length,
      });
      response.end(relayed);
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      sendJson(response, 400, { error: "invalid protobuf message", detail });
    }
  });

  server.listen(port, "0.0.0.0", () => {
    console.log(`typescript-service listening on ${port}`);
  });
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
