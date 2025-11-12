"""
Dashboard template
"""

DASHBOARD_STYLE: str = """
<style>
    .metric-card {
      border: 0;
      border-radius: 1rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
      height: 160px; /* Increased height */
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.1s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
    }

    .metric-icon {
      width: 64px;  /* bigger icon container */
      height: 64px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: #eef2ff;
      color: #3730a3;
      font-size: 1.75rem; /* bigger icon */
      flex-shrink: 0;
    }

    .metric-value {
      font-weight: 800;
      font-size: 2rem; /* larger number */
      line-height: 1;
    }

    .metric-label {
      color: #6b7280;
      font-size: 1.05rem;
      margin-top: .3rem;
    }
</style>

"""

DASHBOARD: str = """
<main class="container py-4" aria-label="Dashboard">
    <div class="row g-4">
      <!-- Databases -->
      <div class="col-12 col-sm-6 col-lg-4">
        <div class="card metric-card">
          <div class="card-body d-flex align-items-center gap-4">
            <span class="metric-icon">
              <i class="fa-solid fa-database"></i>
            </span>
            <div>
              <div class="metric-value">{{ num_of_db }}</div>
              <div class="metric-label">Databases</div>
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
              <div class="metric-value">{{ row_count }}</div>
              <div class="metric-label">Records</div>
            </div>
          </div>
        </div>
      </div>
    </div>
</main>
"""