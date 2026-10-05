FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY generated/csharp ./generated/csharp
COPY runtimes/csharp ./runtimes/csharp
RUN dotnet publish runtimes/csharp/CsharpApp.csproj --configuration Release --output /app/publish
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/publish .
CMD ["dotnet", "CsharpApp.dll", "--serve"]
