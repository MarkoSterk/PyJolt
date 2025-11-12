"""
Dashboard template
"""

DATABASE: str = """
<main class="container py-4" aria-label="Dashboard">
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
              <i class="fa-solid fa-eye"></i>
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
    </div>
</main>
"""