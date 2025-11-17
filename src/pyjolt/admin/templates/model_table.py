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
      width: 100%;                 /* fill the card */
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.95rem;
      table-layout: auto;          /* natural content-based sizing */
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
      white-space: nowrap;
    }

    /* Make all non-last columns as compact as possible */
    thead th:not(:last-child),
    tbody td:not(:last-child) {
      width: 1%;
      max-width: 300px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Let the last column expand to fill the remaining space */
    thead th:last-child,
    tbody td:last-child {
      width: 100%;
      white-space: normal;         /* allow wrapping in last column */
      overflow: hidden;
      text-overflow: ellipsis;     /* optional: keep this or drop it */
    }

    tbody td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--table-border);
      vertical-align: top;
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

    .btn:active { transform: translateY(1px); }
    .btn:hover { filter: brightness(1.05); }
  </style>
"""

MODEL_TABLE_SCRIPTS = """
  <script>
    const table = document.querySelector("table");
    const deleteDialog = document.querySelector(".delete-dialog");
    const confirmDelete = deleteDialog.querySelector(".confirm-delete");
    const closeBtn = deleteDialog.querySelector(".close-delete");

    function deleteRow(url){
      const row = table.querySelector(`[data-delete-url="${url}"]`)?.closest("tr");
      if(!row){
        return;
      }
      row.remove();
    }

    closeBtn.addEventListener("click", (event) => {
      confirmDelete.removeAttribute("data-delete-url");
      deleteDialog.close();
    });

    confirmDelete.addEventListener("click", async (event) => {
      //console.log("Deleting: ", confirmDelete.getAttribute("data-delete-url"));
      const url = confirmDelete.getAttribute("data-delete-url");
      const response = await fetch(url, {method: "DELETE"});
      if(response.status == 204){
        setMessage("Record deleted successfully", "success");
        deleteRow(url);
      }else{
        setMessage("Something went wrong.", "danger");
      }
      closeBtn.click();
    })

    const delBtns = document.querySelectorAll(".delete")
    delBtns.forEach(btn => {
      btn.addEventListener("click", (event) => {
        btn.blur();
        confirmDelete.setAttribute("data-delete-url", btn.getAttribute("data-delete-url"));
        deleteDialog.showModal();
      })
    });
  </script>
"""

MODEL_TABLE: str = """
<main class="card" aria-label="Records table">
    <div class="card-header">
        <div>
          <h1 class="mb-4"><a class="text-reset text-decoration-none" href="{{ url_for('AdminController.database', db_name=db_name) }}"><i class="fa-solid fa-chevron-left"></i> {{ db_nice_name }}</a></h1>
          <h2 class="title ms-3">{{ title }}</h2>
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
                    {% for row in all_data["items"] %}
                    <tr>
                        <td>
                            <button class="btn btn-sm btn-primary me-1 p-2" title="Edit record">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn btn-sm btn-danger me-1 p-2 delete" title="Delete record" 
                            data-delete-url="{{ url_for('AdminController.delete_model_record', db_name=db_name, model_name=model_name,
                                                        attr_val=create_path(row, pk_names)) }}">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                        {% for col in columns %}
                          {% set col_key = (col.key if col is not string and col.key is defined else col) %}
                          {% set value = attribute(row, col_key) %}
                          <td>
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
{% if all_data["pages"] > 1 %}
  <div class="row">
    <div class="col mx-auto">
      <nav class="my-2 text-center" aria-label="Page navigation example">
        <ul class="pagination justify-content-center">
            {% if all_data["has_prev"] == True %}
              <li class="page-item"><a class="page-link" href="#">Previous</a></li>
              <li class="page-item"><a class="page-link" href="#">{{all_data["page"]-1}}</a></li>
            {% endif %}
            <li class="page-item"><a class="page-link" href="#">{{all_data["page"]}}</a></li>
            {% if all_data["has_next"] == True %}
              <li class="page-item"><a class="page-link" href="#">{{all_data["page"]+1}}</a></li>
              <li class="page-item"><a class="page-link" href="#">Next</a></li>
            {% endif %}
        </ul>
      </nav>
    </div>
  </div>
{% endif %}
<dialog class="delete-dialog">
  <p>Are you sure you wish to delete the record?</p>
  <div>
    <button type="button" class="btn btn-sm btn-danger m-1 confirm-delete">Confirm</button>
    <button type="button" class="btn btn-sm btn-primary m-1 close-delete">Close</button>
  </div>
</dialog>
"""