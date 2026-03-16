Pulse Frontend - Dockerized Production Run

This project is a Vite + React application.

Docker (production)

- Build image:
  docker build -t pulse-frontend .

- Run container (app will be available at http://localhost:5173):
  docker run --rm -p 5173:80 pulse-frontend

Notes

- The image builds the app and serves the static files with Nginx.
- If you need environment variables for the build, create a .env file (see .env.example) before building the image.

Local development (without Docker)

- Install deps: npm ci
- Start dev server: npm run dev
- Build: npm run build
- Preview built app: npm run preview
