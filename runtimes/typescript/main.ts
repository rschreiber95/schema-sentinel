import { Entity as EntityV1 } from "../generated/ts/v1/entity";

async function processEntity(rawBytes: Uint8Array, version: string) {
  let module: any;

  try {
    // Dynamic ES module import based on version string
    module = await import(`../generated/ts/${version}/entity`);
  } catch (err) {
    throw new Error(`Unsupported schema version: ${version}`);
  }

  // ts-proto exports helper namespace matching the type name (Entity)
  const EntityCodec = module.Entity;

  // Deserialize raw byte array
  const entity = EntityCodec.decode(rawBytes);

  // Read field values directly from resulting object
  console.log(`[TypeScript (${version})] entityId: ${entity.entityId}`);
  console.log(`[TypeScript (${version})] name:     ${entity.name}`);

  if (version === "v2" && entity.description) {
    console.log(`[TypeScript (${version})] description: ${entity.description}`);
  }
}

async function main() {
  // Example usage creating mock v1 payload
  const mockV1: EntityV1 = { entityId: "ts_303", name: "Sensor C" };
  const bytes = EntityV1.encode(mockV1).finish();

  await processEntity(bytes, "v1");
}

main();