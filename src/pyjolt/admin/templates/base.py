"""
Base layout
"""
from .scripts import LOGOUT_SCRIPT, MESSAGES_SCRIPT

BASE_LAYOUT: str = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
        <link href="{{ url_for('AdminController.static', filename='fontawesome/css/fontawesome.css') }}" rel="stylesheet" />
        <link href="{{ url_for('AdminController.static', filename='fontawesome/css/brands.css') }}" rel="stylesheet" />
        <link href="{{ url_for('AdminController.static', filename='fontawesome/css/solid.css') }}" rel="stylesheet" />

        <style>
            :root {
                --bg: #0f172a;
                --bg-2: #111827;
                --card: #ffffff;
                --text: #0f172a;
                --muted: #6b7280;
                --brand: #3b82f6;
                --brand-600: #2563eb;
                --ring: rgba(59,130,246,.35);
                --shadow: 0 10px 25px rgba(0,0,0,.15);

                --table-border: #e5e7eb;
                --thead-bg: #f3f4f6;
                --row-hover: #f9fafb;
                --badge-bg: #eef2ff;
                --badge-text: #3730a3;
            }

            html, body { height: 100%; }
            body {
                margin: 0;
                font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
                background: radial-gradient(1200px 800px at 20% 10%, #1f2937 0%, var(--bg) 60%),
                            radial-gradient(1000px 700px at 80% 90%, #0b1220 0%, var(--bg-2) 60%);
                color: var(--text);
                display: grid;
                grid-template-rows: auto auto 1fr auto;
                place-items: start center;
                min-height: 100vh;
            }

            .card {
                width: 100%;
                max-width: 1200px;
                background: var(--card);
                box-shadow: var(--shadow);
                overflow: hidden;
                }

            .card-header {
                padding: 20px 24px;
                border-bottom: 1px solid var(--table-border);
                display: flex;
                align-items: center;
                gap: 12px;
                justify-content: space-between;
                flex-wrap: wrap;
            }

            .card-body {
                padding: 0;
            }

            .title {
                margin: 0;
                font-size: 1.25rem;
                line-height: 1.2;
            }

            .navbar-brand img {
                width: 75px;
                height: auto;
            }
        </style>

        {% if styles is defined %}
            {% for style in styles %}
                {{style | safe}}
            {%endfor%}
        {% endif%}

        {{MESSAGES_SCRIPT}}

    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-light w-100 m-0 mb-2">
            <div class="container-fluid">
                <a class="navbar-brand" href="{{ url_for('AdminController.index') }}">
                    <img src="{{ url_for('AdminController.static', filename='pyjolt_logo.png') }}" alt="PyJolt logo" />
                </a>

                <button
                class="navbar-toggler"
                type="button"
                data-bs-toggle="collapse"
                data-bs-target="#navbarSupportedContent"
                aria-controls="navbarSupportedContent"
                aria-expanded="false"
                aria-label="Toggle navigation"
                >
                    <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbarSupportedContent">
                    <!-- Left side nav -->
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                        <li class="nav-item">
                            <a class="nav-link active" aria-current="page" href="{{ url_for('AdminController.index') }}">Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#">Link</a>
                        </li>
                        <li class="nav-item dropdown">
                            <a
                                class="nav-link dropdown-toggle"
                                href="#"
                                id="dbDropdown"
                                role="button"
                                data-bs-toggle="dropdown"
                                aria-expanded="false"
                            >
                                Databases
                            </a>
                            <ul class="dropdown-menu" aria-labelledby="dbDropdown">
                                {% for db in all_dbs %}
                                <li>
                                    <a class="dropdown-item" href="{{ url_for('AdminController.database', db_name=db.db_name) }}">
                                    {{ db.nice_name }}
                                    </a>
                                </li>
                                {% endfor %}
                            </ul>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" tabindex="-1">Profile</a>
                        </li>
                    </ul>

                    <!-- Right side nav -->
                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
                        <li class="nav-item">
                            <a
                                class="nav-link logout"
                                href="#"
                                data-logout-url="{{ url_for(configs.URL_FOR_FOR_LOGOUT) }}"
                                data-login-url="{{ url_for('AdminController.login') }}"
                                role="button"
                            >
                                Logout
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <div class="messages"></div>
        {{body}}
        <footer class="text-center w-100 bg-light p-3 mt-2">PyJolt dashboard</footer>
        {% if scripts is defined %}
            {% for script in scripts %}
                {{script | safe}}
            {% endfor %}
        {% endif %}
        {{LOGOUT_SCRIPT}}
    </body>
</html>
"""

def get_template_string(body: str):
    template: str = BASE_LAYOUT.replace("{{body}}", body)
    template = template.replace("{{MESSAGES_SCRIPT}}", MESSAGES_SCRIPT)
    template = template.replace("{{LOGOUT_SCRIPT}}", LOGOUT_SCRIPT)
    return template
