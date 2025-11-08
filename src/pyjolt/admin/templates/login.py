"""Login page string template"""

LOGIN_TEMPLATE: str = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Login</title>
  <style>
    :root {
      --bg: #0f172a;            /* slate-900 */
      --bg-2: #111827;          /* gray-900 */
      --card: #ffffff;
      --text: #0f172a;          /* slate-900 */
      --muted: #6b7280;         /* gray-500 */
      --brand: #3b82f6;         /* blue-500 */
      --brand-600: #2563eb;     /* blue-600 */
      --ring: rgba(59,130,246,.35);
      --shadow: 0 10px 25px rgba(0,0,0,.15);
      --radius: 16px;
    }

    /* Page layout */
    html, body {
      height: 100%;
    }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      background: radial-gradient(1200px 800px at 20% 10%, #1f2937 0%, var(--bg) 60%),
                  radial-gradient(1000px 700px at 80% 90%, #0b1220 0%, var(--bg-2) 60%);
      color: var(--text);
      display: grid;
      place-items: center; /* centers horizontally & vertically */
      padding: 24px;
    }

    /* Card */
    .card {
      width: 100%;
      max-width: 380px;
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .card-header {
      padding: 24px 24px 0;
      text-align: center;
    }

    .brand {
      display: inline-flex;
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--brand), var(--brand-600));
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 800;
      letter-spacing: .5px;
      box-shadow: 0 6px 18px rgba(37,99,235,.35);
      margin-bottom: 12px;
      user-select: none;
    }

    h1 {
      margin: 0 0 6px;
      font-size: 1.375rem;
      line-height: 1.2;
    }
    p.sub {
      margin: 0 0 18px;
      color: var(--muted);
      font-size: .95rem;
    }

    .card-body {
      padding: 24px;
    }

    /* Form */
    form {
      display: grid;
      gap: 14px;
    }

    label {
      display: block;
      font-size: .9rem;
      margin-bottom: 6px;
      color: #111827;
      font-weight: 600;
    }

    .field {
      display: grid;
      gap: 6px;
    }
    .input {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid #e5e7eb; /* gray-200 */
      border-radius: 12px;
      font-size: 1rem;
      outline: none;
      background: #fff;
      transition: box-shadow .15s ease, border-color .15s ease, transform .02s ease;
    }
    .input:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 4px var(--ring);
    }

    .row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-top: 4px;
    }

    .checkbox {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-size: .9rem;
      color: #374151; /* gray-700 */
    }
    .checkbox input {
      width: 18px;
      height: 18px;
      border-radius: 6px;
      border: 1px solid #d1d5db;
    }

    .link {
      font-size: .9rem;
      color: var(--brand-600);
      text-decoration: none;
    }
    .link:hover { text-decoration: underline; }

    .btn {
      margin-top: 8px;
      display: inline-block;
      width: 100%;
      padding: 12px 16px;
      border: 0;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--brand), var(--brand-600));
      color: #fff;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      transition: transform .02s ease, filter .2s ease;
    }
    .btn:active { transform: translateY(1px); }
    .btn:hover { filter: brightness(1.05); }

    .card-footer {
      padding: 18px 24px 24px;
      text-align: center;
      font-size: .95rem;
      color: #374151;
    }
  </style>
</head>
<body>
  <main class="card" aria-label="Login form">
    <div class="card-header">
      <div class="brand" aria-hidden="true">L</div>
      <h1>Welcome back</h1>
      <p class="sub">Admin Dashboard</p>
    </div>

    <div class="card-body">
      <form action="#" method="post" autocomplete="on">
        <div class="field">
          <label for="email">Email address</label>
          <input id="email" class="input" name="email" type="email" placeholder="you@example.com" autocomplete="email" required />
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input id="password" class="input" name="password" type="password" placeholder="••••••••" autocomplete="current-password" required />
        </div>

        <div class="row">
          <label class="checkbox">
            <input type="checkbox" name="remember" />
            <span>Remember me</span>
          </label>
          <a class="link" href="#">Forgot password?</a>
        </div>

        <button class="btn" type="submit">Login</button>
      </form>
    </div>
  </main>
</body>
</html>

"""