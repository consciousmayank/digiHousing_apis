from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
    tags=["Root"],
    name="Root",
    operation_id="root",
    summary="Root endpoint",
    description="Root endpoint for the API.",
)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Digihousing</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Playwrite+HR+Lijeva:wght@100..400&display=swap" rel="stylesheet">
        <style>
            body, html {
                height: 100%;
                margin: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                background-color: white;
            }
            #welcome-text {
                font-size: 48px;
                text-align: center;
                color: #333;
                margin-bottom: 20px;
                font-family: 'Playwrite HR Lijeva', sans-serif;
                font-weight: 400;
            }
            #docs-button {
                position: absolute;
                bottom: 40px;
                padding: 10px 20px;
                font-size: 18px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            #docs-button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div id="welcome-text">Welcome to Digihousing</div>
        <button id="docs-button" onclick="window.location.href='/docs'">Go to Docs</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)