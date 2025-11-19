"""
Dashboard template
"""

DATABASE: str = """
<main class="container py-4" aria-label="Dashboard">
    <div class="mx-auto my-3 p-2 text-center rounded w-75"
      style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25);">
        <small style="color: var(--brand-600);">
            <i class="fa-solid fa-circle-info me-1"></i>
            Metrics include the <strong>entire database</strong>, not only registered models.
        </small>
    </div>
    <div class="row g-4">
      <!-- Schemas -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-brands fa-sketch"></i>
            </span>
            <div>
              <div class="metric-value">{{ schemas_count }}</div>
              <div class="metric-label">Schemas</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Views -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-display"></i>
            </span>
            <div>
              <div class="metric-value">{{ views_count }}</div>
              <div class="metric-label">Views</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tables -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-table"></i>
            </span>
            <div>
              <div class="metric-value">{{ tables_count }}</div>
              <div class="metric-label">Tables</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Records -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-list-ol"></i>
            </span>
            <div>
              <div class="metric-value">{{ rows_count }}</div>
              <div class="metric-label">Rows</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Columns -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-chart-simple"></i>
            </span>
            <div>
              <div class="metric-value">{{ columns_count }}</div>
              <div class="metric-label">Columns</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Size -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-floppy-disk"></i>
            </span>
            <div>
              <div class="metric-value">{{ size_bytes * 0.000001 }} MB</div>
              <div class="metric-label">Size</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-center flex-wrap gap-3 mt-3">
      {% for model in database_models[db_name] %}
        <a role="button" class="btn btn-light flex-fill text-center px-3" 
          style="min-width: 120px; max-width: 180px;" title="{{ model.__name__ }} Table"
          href="{{ url_for('AdminController.model_table', db_name=db_name, model_name=model.__name__) }}?page=1&per_page=10">
          {{ model.__name__ }} Table
        </a>
      {% endfor %}
  </div>
</main>
"""