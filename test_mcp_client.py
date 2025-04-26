import asyncio
from mcp.client import MCPClient

async def test_solr_search():
    async with MCPClient(url="http://localhost:8765") as client:
        # Suche durchführen
        search_result = await client.call_tool(
            "search", 
            arguments={
                "query": "*:*",
                "rows": 5
            }
        )
        print("Suchergebnisse:", search_result)
        
        # Falls Dokumente gefunden wurden, das erste abrufen
        if "response" in search_result and search_result["response"]["numFound"] > 0:
            doc_id = search_result["response"]["docs"][0]["id"]
            document = await client.call_tool(
                "get_document",
                arguments={
                    "id": doc_id
                }
            )
            print(f"Dokument mit ID {doc_id}:", document)

if __name__ == "__main__":
    asyncio.run(test_solr_search())