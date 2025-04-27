import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="mcp",
        args=["run", "src/server/mcp_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Liste der verfügbaren Tools anzeigen
            tools = await session.list_tools()
            print("Verfügbare Tools:", tools)
            
            # Eine Suche durchführen
            result = await session.call_tool("search", {
                "params": {
                    "query": "beispiel", 
                    "rows": 5
                }
            })
            print("Suchergebnisse:", result)
            
            # Ein Dokument abrufen (vorausgesetzt, die ID existiert)
            try:
                doc_result = await session.call_tool("get_document", {
                    "params": {
                        "id": "doc1"
                    }
                })
                print("Abgerufenes Dokument:", doc_result)
            except Exception as e:
                print(f"Fehler beim Abrufen des Dokuments: {e}")

if __name__ == "__main__":
    asyncio.run(main())