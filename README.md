Urban Company style Flask project scaffold with admin, provider, customer modules."# Service_management_System" 

## Deploy the Flask backend on Render

The Netlify site serves the static homepage. Login, registration, and booking
are handled by the Flask backend, deployed separately using `render.yaml`.

1. In Render, choose **New → Blueprint**, connect this GitHub repository, and
   deploy the `render.yaml` blueprint from the `main` branch.
2. Set the prompted `ADMIN_EMAIL` and `ADMIN_PASSWORD` values to credentials
   you control. Render generates `SECRET_KEY`. The blueprint uses a persistent
   disk for SQLite booking and account data; that disk is a paid Render resource.
3. Wait for the service health check at `/health` to pass. The configured
   backend URL is
   `https://service-management-system-korapatisreedhar-api.onrender.com`.
   If Render assigns a different URL, update `static/js/backend-config.js` to
   match it and push the change.
4. Once Render is running, redeploy the Netlify site from `main`. The homepage's
   Login, Register, and Book Now links will open the Flask backend.

The Render disk starts with a new database; existing local accounts and booking
records are not copied automatically."# Service_management_System"
