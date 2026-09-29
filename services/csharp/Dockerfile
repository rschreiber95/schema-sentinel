FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

WORKDIR /src

COPY proto /src/proto
COPY services/csharp /src/services/csharp

WORKDIR /src/services/csharp
RUN dotnet restore
RUN dotnet publish --configuration Release --output /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0

WORKDIR /app
COPY --from=build /app/publish .

CMD ["dotnet", "SchemaSentinel.Testbed.dll"]
