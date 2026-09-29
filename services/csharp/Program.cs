using Google.Protobuf;
using SchemaSentinel.Testbed;

if (args.Contains("--healthcheck", StringComparer.Ordinal))
{
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
    try
    {
        using var response = await client.GetAsync("http://localhost:8002/health");
        return response.IsSuccessStatusCode ? 0 : 1;
    }
    catch (HttpRequestException)
    {
        return 1;
    }
    catch (TaskCanceledException)
    {
        return 1;
    }
}

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () => Results.Json(new { status = "ok", runtime = "csharp" }));

app.MapPost("/relay", async (HttpRequest request, HttpResponse response) =>
{
    try
    {
        using var requestBody = new MemoryStream();
        await request.Body.CopyToAsync(requestBody);
        var message = TestbedMessage.Parser.ParseFrom(requestBody.ToArray());
        message.VisitedServices.Add("csharp");
        var encoded = message.ToByteArray();

        response.StatusCode = StatusCodes.Status200OK;
        response.ContentType = "application/x-protobuf";
        response.ContentLength = encoded.Length;
        await response.Body.WriteAsync(encoded);
    }
    catch (InvalidProtocolBufferException error)
    {
        response.StatusCode = StatusCodes.Status400BadRequest;
        await response.WriteAsJsonAsync(
            new { error = "invalid protobuf message", detail = error.Message }
        );
    }
});

app.Run();
return 0;
