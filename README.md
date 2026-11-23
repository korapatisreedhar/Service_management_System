Urban Company style Flask project scaffold with admin, provider, customer modules."# Service_management_System" 

## Deploy the Flask backend on Render Free

The Netlify site serves the static homepage. Login, registration, and booking
are handled by the Flask backend, deployed separately using `render.yaml`.

1. In Render, choose **New → Blueprint**, connect this GitHub repository, and
   deploy the `render.yaml` blueprint from the `main` branch.
2. Keep the service on the **Free** plan. Set the prompted `ADMIN_EMAIL` and
   `ADMIN_PASSWORD` values to credentials you control. Render generates
   `SECRET_KEY`. Do not add a paid plan or persistent disk.
3. Wait for the service health check at `/health` to pass. The configured
   backend URL is
   `https://service-management-system-korapatisreedhar-api.onrender.com`.
   If Render assigns a different URL, update `static/js/backend-config.js` to
   match it and push the change.
4. Once Render is running, redeploy the Netlify site from `main`. The homepage's
   Login, Register, and Book Now links will open the Flask backend.

**Free-tier limitation:** Render Free services sleep after 15 minutes without
traffic and may take about a minute to wake. Their filesystem is temporary, so
SQLite accounts and bookings can be lost whenever the service sleeps, restarts,
or redeploys. This setup uses no persistent disk and does not migrate local
accounts or bookings."# Service_management_System"
