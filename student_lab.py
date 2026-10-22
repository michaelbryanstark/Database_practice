"""
Student Lab - a small Flask web app for your SQLite database.

Setup:
    pip install flask
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""
import sqlite3
from pathlib import Path

from flask import (Flask, abort, flash, g, redirect, render_template_string,
                   request, url_for)

# Change this to the name of your database file (kept next to app.py)
DB_PATH = Path(__file__).parent / "student_lab.db"

app = Flask(__name__)
app.secret_key = "change-me"  # needed for flash messages


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------- page configuration (matches student_lab.sql) ----------
PAGES = {
    "students": {
        "title": "Students",
        "table": "Students",
        "pk": "studentId",
        "fields": [
            {"name": "studentId", "label": "Student ID", "type": "number",
             "required": False, "hint": "Leave blank to auto-assign"},
            {"name": "firstName", "label": "First name",
                "type": "text", "required": True},
            {"name": "lastName", "label": "Last name",
                "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
        ],
    },
    "departments": {
        "title": "Departments",
        "table": "Departments",
        "pk": "departmentId",
        "fields": [
            {"name": "departmentId", "label": "Department ID", "type": "number",
             "required": False, "hint": "Leave blank to auto-assign"},
            {"name": "departmentName", "label": "Department name",
                "type": "text", "required": True},
        ],
    },
    "courses": {
        "title": "Courses",
        "table": "Courses",
        "pk": "courseId",
        "fields": [
            {"name": "courseId", "label": "Course ID", "type": "number",
             "required": False, "hint": "Leave blank to auto-assign"},
            {"name": "courseName", "label": "Course name",
                "type": "text", "required": False},
            {"name": "courseCode", "label": "Course code",
                "type": "number", "required": True},
            {"name": "creditHours", "label": "Credit hours",
                "type": "number", "required": True},
            {"name": "departmentId", "label": "Department", "type": "select", "required": False,
             "options": "SELECT departmentId, departmentName FROM Departments ORDER BY departmentName"},
        ],
    },
    "enrollment": {
        "title": "Enrollment",
        "table": "Enrollment",
        "pk": None,
        "fields": [
            {"name": "studentId", "label": "Student", "type": "select", "required": True,
             "options": "SELECT studentId, firstName || ' ' || lastName FROM Students ORDER BY lastName"},
            {"name": "courseId", "label": "Course", "type": "select", "required": True,
             "options": "SELECT courseId, COALESCE(courseName, 'Course ' || courseId) FROM Courses ORDER BY courseName"},
        ],
    },
}


# ---------- template ----------
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ cfg.title }} - Student Lab</title>
<style>
  :root { --bg:#f6f7f9; --card:#fff; --text:#1d2330; --muted:#667085; --line:#e3e6eb;
          --accent:#2f5bea; --danger:#c62828; --flash:#fdecea; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14171d; --card:#1d2129; --text:#e8eaef; --muted:#9aa3b2; --line:#2c323d;
            --accent:#6d8cff; --danger:#ff6b6b; --flash:#3a1f21; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, sans-serif;
         background:var(--bg); color:var(--text); }
  header { background:var(--card); border-bottom:1px solid var(--line); padding:0 1.5rem; }
  nav { display:flex; gap:.25rem; max-width:960px; margin:0 auto; }
  nav a { padding:1rem .9rem; color:var(--muted); text-decoration:none;
          border-bottom:2px solid transparent; }
  nav a.active { color:var(--accent); border-bottom-color:var(--accent); font-weight:600; }
  main { max-width:960px; margin:1.5rem auto; padding:0 1.5rem; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px;
          padding:1.25rem; margin-bottom:1.5rem; }
  h2 { margin:0 0 1rem; font-size:1.1rem; }
  form.add { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; }
  label { display:block; font-size:.85rem; color:var(--muted); margin-bottom:.3rem; }
  input, select { width:100%; padding:.55rem .65rem; border:1px solid var(--line);
                  border-radius:6px; background:var(--bg); color:var(--text); font:inherit; }
  button { padding:.55rem 1rem; border:0; border-radius:6px; background:var(--accent);
           color:#fff; font:inherit; cursor:pointer; align-self:end; }
  button.link { background:none; color:var(--danger); padding:0; }
  .table-wrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; }
  th, td { text-align:left; padding:.6rem .5rem; border-bottom:1px solid var(--line); }
  th { font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
  .empty { color:var(--muted); padding:.5rem 0; }
  .flash { background:var(--flash); border:1px solid var(--danger); color:var(--danger);
           padding:.7rem 1rem; border-radius:8px; margin-bottom:1rem; }
  .ok { border-color:var(--accent); color:var(--accent); background:transparent; }
  small { color:var(--muted); }
</style>
</head>
<body>
<header>
  <nav>
    {% for key, p in pages.items() %}
      <a href="{{ url_for('index', page=key) }}" class="{{ 'active' if key == page else '' }}">{{ p.title }}</a>
    {% endfor %}
  </nav>
</header>
<main>
  {% for category, msg in get_flashed_messages(with_categories=true) %}
    <div class="flash {{ 'ok' if category == 'ok' else '' }}">{{ msg }}</div>
  {% endfor %}

  <div class="card">
    <h2>Add to {{ cfg.title }}</h2>
    <form class="add" method="post">
      {% for f in cfg.fields %}
        <div>
          <label for="{{ f.name }}">{{ f.label }}{% if f.required %} *{% endif %}</label>
          {% if f.type == 'select' %}
            <select id="{{ f.name }}" name="{{ f.name }}" {{ 'required' if f.required }}>
              <option value="">-- choose --</option>
              {% for value, label in options[f.name] %}
                <option value="{{ value }}">{{ label }} ({{ value }})</option>
              {% endfor %}
            </select>
          {% else %}
            <input id="{{ f.name }}" name="{{ f.name }}" type="{{ f.type }}"
                   {{ 'required' if f.required }} {% if f.hint %}placeholder="{{ f.hint }}"{% endif %}>
          {% endif %}
        </div>
      {% endfor %}
      <button type="submit">Add</button>
    </form>
  </div>

  <div class="card">
    <h2>{{ cfg.title }} ({{ rows|length }})</h2>
    {% if rows %}
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              {% for col in columns %}<th>{{ col }}</th>{% endfor %}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {% for row in rows %}
              <tr>
                {% for col in columns %}<td>{{ row[col] if row[col] is not none else '' }}</td>{% endfor %}
                <td>
                  <form method="post" action="{{ url_for('delete', page=page, rowid=row['_rowid']) }}"
                        onsubmit="return confirm('Delete this row?')">
                    <button class="link" type="submit">Delete</button>
                  </form>
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <p class="empty">No rows yet.</p>
    {% endif %}
  </div>
</main>
</body>
</html>
"""


# ---------- routes ----------
@app.route("/", defaults={"page": "students"}, methods=["GET", "POST"])
@app.route("/<page>", methods=["GET", "POST"])
def index(page):
    cfg = PAGES.get(page)
    if cfg is None:
        abort(404)
    db = get_db()

    if request.method == "POST":
        values = {}
        for f in cfg["fields"]:
            raw = request.form.get(f["name"], "").strip()
            values[f["name"]] = raw or None

        # Auto-assign the primary key (INT PRIMARY KEY doesn't auto-increment)
        pk = cfg["pk"]
        if pk and values.get(pk) is None:
            row = db.execute(
                f"SELECT COALESCE(MAX({pk}), 0) + 1 FROM {cfg['table']}").fetchone()
            values[pk] = row[0]

        cols = list(values)
        sql = (f"INSERT INTO {cfg['table']} ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)})")
        try:
            db.execute(sql, [values[c] for c in cols])
            db.commit()
            flash("Row added.", "ok")
        except sqlite3.Error as e:
            db.rollback()
            flash(f"Could not add row: {e}")
        return redirect(url_for("index", page=page))

    options = {
        f["name"]: [tuple(r) for r in db.execute(f["options"]).fetchall()]
        for f in cfg["fields"] if f["type"] == "select"
    }
    cur = db.execute(
        f"SELECT rowid AS _rowid, * FROM {cfg['table']} ORDER BY rowid")
    rows = cur.fetchall()
    columns = [c[0] for c in cur.description if c[0] != "_rowid"]

    return render_template_string(TEMPLATE, pages=PAGES, page=page, cfg=cfg,
                                  rows=rows, columns=columns, options=options)


@app.route("/<page>/delete/<int:rowid>", methods=["POST"])
def delete(page, rowid):
    cfg = PAGES.get(page)
    if cfg is None:
        abort(404)
    db = get_db()
    try:
        db.execute(f"DELETE FROM {cfg['table']} WHERE rowid = ?", (rowid,))
        db.commit()
        flash("Row deleted.", "ok")
    except sqlite3.Error as e:
        db.rollback()
        flash(f"Could not delete row: {e}")
    return redirect(url_for("index", page=page))


if __name__ == "__main__":
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}\nEdit DB_PATH at the top of app.py.")
    app.run(debug=True)
