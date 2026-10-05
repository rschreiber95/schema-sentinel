using System;
using System;
using System.Reflection;
using Google.Protobuf;

class Program
{
    static void ProcessEntity(byte[] rawBytes, string version)
    {
        // 1. Build namespace and class name string (e.g. "Simulation.V1.Entity")
        string targetNamespace = $"Simulation.{version.ToUpper()}";
        string fullClassName = $"{targetNamespace}.Entity";

        // 2. Resolve the compiled Type via reflection
        Type entityType = Type.GetType(fullClassName);
        if (entityType == null)
        {
            throw new ArgumentException($"Unsupported version: {version}");
        }

        // 3. Access static Parser property generated on Protobuf class
        PropertyInfo parserProperty = entityType.GetProperty("Parser", BindingFlags.Public | BindingFlags.Static);
        var parser = parserProperty.GetValue(null);

        // 4. Invoke ParseFrom(byte[]) method on the parser
        MethodInfo parseFromMethod = parser.GetType().GetMethod("ParseFrom", new[] { typeof(byte[]) });
        IMessage entity = (IMessage)parseFromMethod.Invoke(parser, new object[] { rawBytes });

        // 5. Read fields using PropertyInfo
        string entityId = (string)entityType.GetProperty("EntityId").GetValue(entity);
        string name = (string)entityType.GetProperty("Name").GetValue(entity);

        Console.WriteLine($"[C# ({version})] entityId: {entityId}");
        Console.WriteLine($"[C# ({version})] name:     {name}");
    }

    static void Main()
    {
        // Example usage with Simulation.V1.Entity
        var mockV1 = new Simulation.V1.Entity { EntityId = "cs_202", Name = "Sensor B" };
        byte[] bytes = mockV1.ToByteArray();

        ProcessEntity(bytes, "v1");
    }
}