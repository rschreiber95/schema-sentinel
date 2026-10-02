.PHONY: all generate run-python run-csharp run-ts run-all clean

all: generate run-all

generate:
	@echo "--- Generating Protobuf Code ---"
	buf generate

run-python:
	@echo "--- Running Python ---"
	python python_app/main.py

run-csharp:
	@echo "--- Running C# ---"
	dotnet run --project csharp_app/CsharpApp.csproj

run-ts:
	@echo "--- Running TypeScript ---"
	cd ts_app && npx ts-node main.ts

run-all: run-python run-csharp run-ts

clean:
	rm -rf generated/