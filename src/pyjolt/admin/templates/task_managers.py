"""
Dashboard template
"""

TASK_MANAGERS: str = """
<main class="container py-4" aria-label="Task managers">
    <div class="row g-4">
        {% for name, task_manager in task_managers.items() %}
            <div class="col-12 col-sm-6 col-lg-4">
                <div class="card metric-card">
                    <div class="card-body d-flex align-items-center gap-4 p-2">
                        <span class="metric-icon">
                            <i class="fa-solid fa-clock fa-5x"></i>
                        </span>
                        {{task_manager.nice_name}} ({{len(task_manager.jobs.keys())}})
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
</main>
"""