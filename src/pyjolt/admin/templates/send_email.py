"""
Page for sending emails
"""

SEND_EMAIL: str = """
<main class="container py-4" aria-label="Send Email">
  <div class="row justify-content-center">
    <div class="col-12 col-lg-8">
      <div class="card shadow-sm">
        <div class="card-header">
          <h2 class="title mb-0 d-flex align-items-center gap-2">
            <i class="fa-solid fa-envelope-open-text"></i>
            Send Email
          </h2>
        </div>

        <form
          method="post"
          enctype="multipart/form-data"
          class="card-body p-4 d-flex flex-column gap-3"
        >
          <!-- Recipient -->
          <div class="mb-3">
            <label for="recipient" class="form-label fw-semibold">
              Recipients
            </label>
            <recipients-input query-url="{{ url_for('AdminController.email_query') }}"></recipients-input>
          </div>

          <!-- Subject -->
          <div class="mb-3">
            <label for="subject" class="form-label fw-semibold">
              Subject
            </label>
            <input
              type="text"
              class="form-control"
              id="subject"
              name="subject"
              placeholder="Subject of your email"
              required
            />
          </div>

          <!-- Attachments -->
          <div class="mb-3">
            <label for="attachments" class="form-label fw-semibold d-flex align-items-center gap-2">
              <i class="fa-solid fa-paperclip"></i>
              Attachments
            </label>
            <input
              class="form-control"
              type="file"
              id="attachments"
              name="attachments"
              multiple
            />
            <div class="form-text" style="color: var(--muted);">
              You can select multiple files.
            </div>
          </div>

          <!-- Content -->
          <div class="mb-3">
            <label for="content" class="form-label fw-semibold">
              Message
            </label>
            <textarea
              class="form-control"
              id="content"
              name="content"
              rows="8"
              placeholder="Write your message here..."
              required
            ></textarea>
          </div>

          <!-- Actions -->
          <div class="d-flex justify-content-end gap-2 mt-2">
            <button
              type="reset"
              class="btn btn-outline-secondary"
            >
              Clear
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              style="background: var(--brand); border-color: var(--brand-600);"
            >
              <i class="fa-solid fa-paper-plane me-1"></i>
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</main>
"""