"""
Table markup for model data
"""

MODEL_TABLE_STYLE: str = """
<style>
    .table-wrap {
      width: 100%;
      overflow: auto;
    }

    table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.95rem;
    }

    thead th {
      position: sticky;
      top: 0;
      background: var(--thead-bg);
      text-align: left;
      padding: 12px 16px;
      font-weight: 700;
      color: #111827;
      border-bottom: 1px solid var(--table-border);
    }

    tbody td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--table-border);
      vertical-align: top;
      max-width: 420px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    tbody tr:hover {
      background: var(--row-hover);
    }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 9999px;
      background: var(--badge-bg);
      color: var(--badge-text);
      font-size: .8rem;
      font-weight: 600;
    }

    .empty {
      padding: 28px 24px;
      color: var(--muted);
      text-align: center;
    }

    .toolbar {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border: 0;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--brand), var(--brand-600));
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      transition: transform .02s ease, filter .2s ease;
    }
    .btn:active { transform: translateY(1px); }
    .btn:hover { filter: brightness(1.05); }
  </style>
"""

MODEL_TABLE: str = """
<main class="card" aria-label="Records table">
    <div class="card-header">
        <div>
        <h1 class="title">{{ title or "All Records" }}</h1>
        </div>
    </div>

    <div class="card-body">
        {% if all_data and columns %}
        <div class="table-wrap">
            <table aria-label="Data table">
            <thead>
                <tr>
                <th></th>
                {# columns can be strings or objects with .key and optional .label #}
                {% for col in columns %}
                    {% set col_key = (col.key if col is not string and col.key is defined else col) %}
                    {% set col_label = (
                        col.label if col is not string and col.label is defined
                        else (col_key | replace('_',' ') | title)
                    ) %}
                    <th scope="col">{{ col_label }}</th>
                {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in all_data %}
                <tr>
                    <td>
                        <button class="btn btn-sm me-1 p-2" title="Edit record">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-sm me-1 p-2" title="Delete record">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                    {% for col in columns %}
                    {% set col_key = (col.key if col is not string and col.key is defined else col) %}
                    {% set value = attribute(row, col_key) %}
                    <td>
                        {# Render heuristics: booleans as badges, dates trimmed, objects by string #}
                        {% if value is boolean %}
                        <span class="badge">{{ "Yes" if value else "No" }}</span>
                        {% elif value is none %}
                        <span class="muted">—</span>
                        {% else %}
                        {{ value }}
                        {% endif %}
                    </td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty">No data available.</div>
        {% endif %}
    </div>
</main>
"""