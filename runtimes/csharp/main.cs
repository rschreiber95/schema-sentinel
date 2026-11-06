using System.Text.Json;
using Google.Protobuf;

const string observationsHeader = "X-Schema-Sentinel-Observations";
const string traceHeader = "X-Service-Trace";

static (IMessage Entity, Dictionary<string, string> Fields) ProcessEntity(byte[] rawBytes, string version)
{
    IMessage entity;
    Dictionary<string, string> fields;
    if (version == "v1")
    {
        var decoded = Simulation.V1.Entity.Parser.ParseFrom(rawBytes);
        entity = decoded;
        fields = new() { ["entity_id"] = decoded.EntityId, ["name"] = decoded.Name };
    }
    else if (version == "v2")
    {
        var decoded = Simulation.V2.Entity.Parser.ParseFrom(rawBytes);
        entity = decoded;
        fields = new() { ["entity_id"] = decoded.EntityId };
    }
    else throw new ArgumentException($"Unsupported version: {version}");
    Console.WriteLine(JsonSerializer.Serialize(new { runtime = "csharp", version, fields }));
    return (entity, fields);
}

if (args.Contains("--healthcheck"))
{
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
    try { return (await client.GetAsync("http://localhost:8002/health")).IsSuccessStatusCode ? 0 : 1; }
    catch (Exception error) when (error is HttpRequestException or TaskCanceledException) { return 1; }
}
if (!args.Contains("--serve"))
{
    var version = args.Contains("--v2") ? "v2" : "v1";
    IMessage entity = version == "v1"
        ? new Simulation.V1.Entity { EntityId = "cs_202", Name = "Sensor B" }
        : new Simulation.V2.Entity { EntityId = "cs_202" };
    ProcessEntity(entity.ToByteArray(), version);
    return 0;
}
var builder = WebApplication.CreateBuilder(args.Where(arg => arg != "--serve").ToArray());
var app = builder.Build();
app.MapGet("/health", () => Results.Json(new { status = "ok", runtime = "csharp" }));
app.MapPost("/relay", async (HttpRequest request, HttpResponse response) =>
{
    try
    {
        using var body = new MemoryStream();
        await request.Body.CopyToAsync(body);
        var (entity, fields) = ProcessEntity(body.ToArray(), "v1");
        var trace = JsonSerializer.Deserialize<List<string>>(request.Headers[traceHeader].FirstOrDefault() ?? "[]")
            ?? throw new JsonException("Trace must be an array");
        trace.Add("csharp");
        response.Headers[observationsHeader] = JsonSerializer.Serialize(new[] { new { runtime = "csharp", fields } });
        response.Headers[traceHeader] = JsonSerializer.Serialize(trace);
        response.ContentType = "application/x-protobuf";
        await response.Body.WriteAsync(entity.ToByteArray());
    }
    catch (Exception error) when (error is InvalidProtocolBufferException or JsonException)
    {
        response.StatusCode = 400;
        await response.WriteAsJsonAsync(new { error = error.Message });
    }
});
app.Run();
return 0;
