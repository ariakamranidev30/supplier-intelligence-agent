import os
from contextlib import AsyncExitStack
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# The standard Google GenAI SDK
from google import genai
from google.genai import types

app = FastAPI()

# Automatically authenticates using the GEMINI_API_KEY environment variable
ai_client = genai.Client()

mcp_stack = AsyncExitStack()
mcp_session = None

class ChatRequest(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    global mcp_session
    
    # 1. Launch the MCP Server as a subprocess and connect via stdio
    server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    server_params = StdioServerParameters(command="python", args=[server_script])
    
    stdio_transport = await mcp_stack.enter_async_context(stdio_client(server_params))
    read, write = stdio_transport
    
    mcp_session = await mcp_stack.enter_async_context(ClientSession(read, write))
    await mcp_session.initialize()
    print("✅ MCP Client securely connected to Supplier Database!")

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_stack.aclose()

def convert_mcp_to_gemini(mcp_tool) -> types.FunctionDeclaration:
    """Dynamically translates standard MCP tools into Google Gemini function declarations."""
    properties = {}
    required = mcp_tool.inputSchema.get("required", [])
    
    for prop_name, prop_details in mcp_tool.inputSchema.get("properties", {}).items():
        properties[prop_name] = types.Schema(
            type=types.Type.STRING,
            description=prop_details.get("description", "")
        )
        
    return types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties=properties,
            required=required
        ) if properties else None
    )

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if not mcp_session:
        raise HTTPException(status_code=500, detail="MCP Server offline.")
        
    # 2. Dynamically discover tools from MCP
    tools_response = await mcp_session.list_tools()
    gemini_functions = [convert_mcp_to_gemini(t) for t in tools_response.tools]
    gemini_tool = types.Tool(function_declarations=gemini_functions)
    
    # 3. Setup Gemini Chat Session with supply chain context
    chat = ai_client.chats.create(
        model="gemini-3.8-flash",
        config=types.GenerateContentConfig(
            tools=[gemini_tool],
            temperature=0.2,
            system_instruction="You are a Supply Chain Risk AI. Use tools to query supplier risk profiles and answer concisely."
        )
    )
    
    # 4. Send User Prompt
    response = chat.send_message(req.message)
    
    # 5. Orchestrate Tool Execution if Gemini requests it
    if response.function_calls:
        for function_call in response.function_calls:
            print(f"🤖 Gemini requested DB Tool: {function_call.name} with args: {function_call.args}")
            
            # Execute safely via MCP standard
            mcp_result = await mcp_session.call_tool(
                function_call.name, 
                arguments=function_call.args
            )
            
            tool_text = mcp_result.content[0].text
            
            # Return DB data back to Gemini so it can generate the final answer
            response = chat.send_message(
                types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": tool_text}
                )
            )
            
    return {"reply": response.text}

