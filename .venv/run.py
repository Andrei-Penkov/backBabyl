from back import create_app
import json
from flask import render_template

app = create_app()

with open('openapi.json', 'r', encoding='utf-8') as f:
    swagger_spec = json.load(f)

@app.route('/docs')
def serve_docs():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css" />
        <style>
            body {{ margin: 0; padding: 0; }}
            #swagger-ui {{ padding: 20px; }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script>
            const spec = {json.dumps(swagger_spec)};
            SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "BaseLayout"
            }});
        </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(port=20000, debug=True)