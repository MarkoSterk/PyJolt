"""
Dashboard template
"""

EMAIL_CLIENTS: str = """
<main class="container py-4" aria-label="Email Clients">
    <div class="row g-4">
        {% for name, client in email_clients.items() %}
            <div class="col-12 col-sm-6 col-lg-4">
                <div class="card metric-card">
                    <div class="card-body d-flex align-items-center gap-4">
                        <span class="metric-icon">
                            <i class="fa-solid fa-envelope fa-5x"></i>
                        </span>
                        <div>
                            <div class="metric-label">
                                {{ client.configs["SENDER_NAME_OR_ADDRESS"] }}
                            </div>
                            <div>
                                <a class="text-reset text-decoration-none" href="{{ url_for('AdminController.send_email') }}?client={{client.configs["SENDER_NAME_OR_ADDRESS"]}}">Send Message</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
</main>
"""