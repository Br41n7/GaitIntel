# Deploying to Render

## Steps

1. **Push this repo to GitHub** (Render deploys from a git repo, not a zip upload).

2. **In the Render dashboard:** New → Blueprint → connect the repo. Render
   reads `render.yaml` at the repo root and proposes creating three
   resources: `gaitintel-db` (Postgres), `gaitintel-api`
   (Docker web service), `gaitintel-frontend` (static site).

3. **Click Apply.** First deploy will take a while — the backend image
   installs MediaPipe + OpenCV, which is a genuinely large dependency set
   (expect several minutes, not seconds).

4. **Check the actual URLs Render assigned.** `render.yaml` assumes the
   services land at `gaitintel-api.onrender.com` and
   `gaitintel-frontend.onrender.com` (Render derives the URL from
   the service name when it's available). If either name was taken and
   Render appended a suffix, the `CORS_ORIGINS` and `VITE_API_URL` values
   in `render.yaml` will be wrong. Fix by editing those two env vars
   directly in the Render dashboard for each service, then manually
   trigger a redeploy — for the frontend specifically, use "Clear build
   cache & deploy," since `VITE_API_URL` is baked in at build time, not
   read at runtime.

5. **Test the acceptance flow** against the frontend URL, same steps as
   local testing (see `SETUP.md`).

## Things that will bite you if you don't know about them first

- **Uploaded videos and pose data do not survive a restart or redeploy**
  on Render's free tier. `VIDEO_STORAGE_PATH` writes to the container's
  local disk, which free web services don't persist. This is fine for a
  one-session testing pass — just know that if the service restarts
  (idles out, redeploys, etc.) mid-test, you'll need to re-upload. Fixing
  this properly means either a Render persistent Disk (paid plans only,
  and only safe with a single instance — multiple instances would each
  get their own disk and diverge) or moving to S3-compatible storage,
  which is exactly why `StorageBackend` was built as a swappable
  interface in the first place — see `backend/app/storage/`.

- **Free web services spin down after ~15 minutes of inactivity.** The
  first request after that will be slow — cold container start, then
  MediaPipe's model load on top. Don't mistake that for a bug if your
  first "Extract pose" click after leaving it idle takes 20-30+ seconds.

- **The free Postgres instance expires after 30 days.** Fine for testing
  this version now; if you want this environment to persist, upgrade the
  database plan before that clock runs out.

- **`VITE_API_URL` is compiled into the frontend at build time.** If you
  ever change the API's URL (custom domain, renamed service), you must
  rebuild the frontend, not just restart it — a plain restart will keep
  serving the old URL.
