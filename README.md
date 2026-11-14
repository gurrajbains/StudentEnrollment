# Student Enrollment System — Lab 8

A Flask + SQLite app incorporating the original team's login, student, teacher, and admin pages, with working JSON API endpoints.

## Windows setup

Run in the repository root:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000 . **Do not use** `py -m http.server 8000`; that static server cannot handle `/api/...`.

## Seeded example accounts (from teammate's Lab 8 code)

At first startup with an empty database, example data is generated. Student: `cnorris`, teacher: `ahepworth`, admin: `admin`. Their initial password is `password123`. **These credentials are only for local coursework demonstrations. Change them before any public deployment.** Existing database records are preserved. The database and local auth keys are in `instance/` and are ignored by Git.

## Main routes

- `POST /api/login` JSON `{ "username": "...", "password": "..." }`
- `POST /api/logout`, `GET /api/me`
- Student: `GET /api/student/courses`, `GET /api/courses`, `POST /api/student/courses` JSON `{"course_id": 1}`, `DELETE /api/student/courses/<id>`
- Teacher: `GET /api/teacher/courses`, `GET /api/teacher/courses/<id>/students`, `PATCH /api/teacher/courses/<id>/students/<student_id>/grade` JSON `{"grade": 90}`
- Admin: `GET/POST /api/admin/users|courses|enrollments`, `GET/PUT/DELETE /api/admin/<resource>/<id>`.

For admin POST/PUT, the backend expects these database-oriented field names: users `username`, `name`, `password` (input only), `role`; courses `name`, `teacherID`, `time`, `capacity`; enrollments `studentID`, `courseID`, `grade`. Student/teacher dashboards continue to use frontend-facing fields `id`, `name`, `teacher`, `time`, `enrolled_count`, `capacity`, and student roster `id`, `name`, `grade`.

Only a verified role can use its protected pages and APIs. API POST/PATCH/PUT/DELETE requests use an `X-CSRF-TOKEN` cookie-derived header. Login uses `POST /api/login` and receives the session cookie.

## Git team workflow

Make a new branch for each feature, commit and push, and open a pull request. Do not commit `instance/`, passwords, or `.env` files.
