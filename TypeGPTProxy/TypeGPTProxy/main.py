from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
import httpx
import socket

app = FastAPI(middleware=[
    Middleware(CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"])
])

def sanitize_error_detail(detail: str) -> str:
    """Sanitize error messages"""
    return detail.replace("typegpt", "api").replace("fast.typegpt.net", "backend")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    exc.detail = sanitize_error_detail(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

import os
# Load from environment variables
REAL_API_KEY = os.getenv("SAMURAI_API_KEY", "sk-kwWVUQPDsLemvilLcyzSSWRzo8sctCzxzlbdN0ZC5ZUCCv0m")
BASE_URL = "https://fast.typegpt.net"  # Hidden backend
PUBLIC_AUTH_TOKEN = os.getenv("SAMURAI_AUTH_TOKEN", "Samurai-AP1-Fr33")
SAMURAI_API_NAME = "Samurai-API"

@app.on_event("startup")
async def startup_event():
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
        print("===== Samurai API Gateway Started =====")
        print(f"📡 Server IP: {server_ip}")
        print(f"🔒 Authentication Token: {PUBLIC_AUTH_TOKEN}")
    except Exception as e:
        print(f"⚠️ Could not determine server IP: {e}")

@app.get("/")
async def welcome_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Samurai API Gateway</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                   max-width: 800px; margin: 40px auto; padding: 20px;
                   background-color: #f8f9fa; }
            .header { color: #2c3e50; border-bottom: 3px solid #e74c3c; 
                     padding-bottom: 15px; margin-bottom: 30px; }
            .content { background: white; padding: 30px; border-radius: 10px;
                      box-shadow: 0 2px 15px rgba(0,0,0,0.1); }
            h1 { color: #e74c3c; margin-bottom: 0; }
            h2 { color: #2c3e50; margin-top: 30px; }
            h3 { color: #34495e; margin-bottom: 10px; }
            code { background: #f8f9fa; padding: 3px 7px; border-radius: 4px;
                  font-family: 'Courier New', Courier, monospace; }
            a { color: #e74c3c; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .telegram { background: #0088cc; color: white; padding: 10px 20px;
                       border-radius: 5px; display: inline-block; margin-top: 15px; }
            .model-docs { margin-left: 20px; }
            .model-docs p { margin: 8px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚔️ Samurai API Gateway</h1>
            <p>Version 1.0.0 | Powered by Samurai Technologies</p>
        </div>
        
        <div class="content">
            <h2>🚀 Getting Started</h2>
            <p>Access our API using your authentication token:</p>
            <code>Authorization: Bearer Samurai-AP1-Fr33</code>
            
            <h2>📚 Model Documentation</h2>
            <div class="model-docs">
                <h3>OpenAI Models</h3>
                <p>Use standard OpenAI API parameters. Reference: 
                    <a href="https://platform.openai.com/docs/api-reference" target="_blank">
                        OpenAI API Documentation
                    </a>
                </p>
                
                <h3>BlackForest AI (Image Generation)</h3>
                <p>Requires specific parameters for image generation. Reference: 
                    <a href="https://docs.together.ai/reference/inference" target="_blank">
                        Together AI Documentation
                    </a>
                </p>
                
                <h3>Perplexity Models</h3>
                <p>Optimized for search and factual responses. Reference: 
                    <a href="https://docs.perplexity.ai/" target="_blank">
                        Perplexity API Documentation
                    </a>
                </p>
                
                <h3>Anthropic Models</h3>
                <p>Follow Anthropic's message format requirements. Reference: 
                    <a href="https://docs.anthropic.com/claude/reference/getting-started-with-the-api" target="_blank">
                        Anthropic API Documentation
                    </a>
                </p>
            </div>
            
            <h2>💬 Join Our Community</h2>
            <p>Get support, updates, and API documentation:</p>
            <a href="https://t.me/+a-R6SnnjJphlNDg1" target="_blank" class="telegram">
                Join Telegram Channel
            </a>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@app.get("/v1/models")
async def list_models():
    """Proxy model listing endpoint"""
    target_url = f"{BASE_URL}/v1/models"
    headers = {
        "Authorization": f"Bearer {REAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(target_url, headers=headers)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="API service unavailable. Please try again later.")

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(request: Request, path: str, authorization: str = Header(None)):
    # Validate Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    
    token = authorization.replace("Bearer ", "").strip()
    if token != PUBLIC_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token. Use 'Samurai-AP1-Fr33'")

    # Build backend request
    target_url = f"{BASE_URL}/{path}"
    headers = {
        "Authorization": f"Bearer {REAL_API_KEY}",
        "Content-Type": request.headers.get("content-type", "application/json"),
        "Accept": "text/event-stream",
        "User-Agent": "Samurai-Proxy/1.0",
        "X-Powered-By": "Samurai-API"
    }

    body = await request.body()
    is_stream = b'"stream":true' in body or b'"stream": true' in body

    print(f"🔄 Forwarding request to backend API")
    print(f"🔁 Stream mode: {'✅ Enabled' if is_stream else '❌ Disabled'}")

    if is_stream:
        # Stream response immediately, as chunks arrive
        async def stream_generator():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body
                ) as upstream_response:
                    async for chunk in upstream_response.aiter_raw():
                        yield chunk  # raw bytes streamed directly

        return StreamingResponse(
            stream_generator(),
            status_code=200,
            media_type="text/event-stream"
        )

    else:
        # Normal JSON response
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body
                )
            except httpx.RequestError as e:
                raise HTTPException(status_code=502, detail="API service unavailable. Please try again later.")

        print(f"↩️ Samurai API Status: {response.status_code}")

        try:
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception:
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type", "text/plain")
            )
