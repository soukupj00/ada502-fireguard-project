# FireGuard Documentation Platform — Deployment Guide

## Overview

The documentation platform is implemented as a fully integrated solution with CI/CD pipelines, Docker containers, and Kubernetes deployment. It serves three documentation sources:

1. **Backend API Reference** — Generated via mkdocstrings from Python docstrings
2. **Intelligence System Reference** — Generated via mkdocstrings from Python docstrings
3. **Frontend API Reference** — Generated via TypeDoc from TypeScript definitions

All documentation is compiled into a single MkDocs site and served at `/docs` endpoint via Nginx.

---

## Architecture

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **MkDocs** | Static site generator with Material theme | `mkdocs.yml` |
| **TypeDoc** | TypeScript API documentation generator | `frontend/typedoc.json` |
| **Nginx** | Serves compiled site in Kubernetes | `docs/nginx.conf` |
| **GitHub Actions** | CI/CD for docs build and deployment | `.github/workflows/docs.yml` |
| **Kubernetes** | Docs service deployment | `k8s-manifests/docs-*.yaml` |
| **Docker** | Multi-stage container build | `docs/Dockerfile` |

### Build Pipeline

```
TypeDoc (frontend/:src/index.ts)
    ↓
frontend/dist/docs/reference/*
    ↓
Sync to docs/frontend/reference/
    ↓
MkDocs Build
    ↓
site/ (compiled HTML)
    ↓
Nginx Container
```

---

## Deployment Scenarios

### Local Development

**Build documentation locally:**

```bash
# Install dependencies
uv sync --directory docs
cd frontend && npm install && npm run docs:api && cd ..

# Sync frontend reference
mkdir -p docs/frontend/reference
cp -R frontend/dist/docs/reference/. docs/frontend/reference/

# Build MkDocs site
PYTHONPATH=backend/src:intelligence-system/src uv run --directory docs mkdocs build

# Serve locally (with live reload)
PYTHONPATH=backend/src:intelligence-system/src uv run --directory docs mkdocs serve
```

The site will be available at `http://localhost:8000`

### GitHub Actions — GitHub Pages Deployment

**Workflow:** `.github/workflows/docs.yml`

**Trigger:** Push to `main` branch or manual workflow dispatch

**What it does:**
1. Generates TypeDoc frontend reference
2. Syncs reference into docs tree
3. Builds MkDocs site
4. Uploads to GitHub Pages artifact
5. Deploys to GitHub Pages (if build succeeds)

**Status:**
- ✅ All code deployment workflows remain **unaffected** if docs build fails
- ✅ Docs build failures are **non-blocking** (reported but don't prevent other services)
- ✅ Pages deployment is **skipped** if MkDocs build has errors
- 📊 Build status shown in workflow output

**To enable GitHub Pages deployment:**
1. Go to Repository Settings → Pages
2. Select "Deploy from a branch"
3. Choose `gh-pages` branch as source
4. Save

### Docker Image Build

**Workflow:** `.github/workflows/docker-publish.yml`

**Trigger:** Push to `main` branch or manual workflow dispatch

**What it does:**
1. Builds Backend, Frontend, Intelligence, and **Docs** Docker images
2. Pushes all images to GitHub Container Registry (GHCR)

**Key improvement:** Docs image build uses `continue-on-error: true`
- If docs build fails, Backend/Frontend/Intelligence images still build and push ✅
- Other services are **never blocked** by documentation build issues
- Docs build status reported clearly in workflow output

**To use these images:**
```bash
# Example: Pull and run docs image
docker pull ghcr.io/yourusername/ada502-fireguard-project-docs:latest
docker run -p 8080:80 ghcr.io/yourusername/ada502-fireguard-project-docs:latest
```

Visit `http://localhost:8080` to view documentation

### Kubernetes Deployment

**Manifests:**
- `k8s-manifests/docs-deployment.yaml` — Docs pod (1 replica, latest image)
- `k8s-manifests/docs-service.yaml` — ClusterIP service on port 80
- `k8s-manifests/ingress.yaml` — Routes `/docs` to docs service

**Apply manifests:**
```bash
kubectl apply -f k8s-manifests/docs-deployment.yaml
kubectl apply -f k8s-manifests/docs-service.yaml
kubectl apply -f k8s-manifests/ingress.yaml
```

**Access documentation:**
- External: `https://group10.ada502-fireguard.live/docs`
- Internal: `http://docs:80` (from within cluster)

**Scaling documentation service:**
```bash
kubectl scale deployment/docs --replicas=3
```

**View logs:**
```bash
kubectl logs -f deployment/docs
kubectl logs deployment/docs --all-containers=true
```

**Update documentation (after image rebuild):**
```bash
kubectl set image deployment/docs \
  docs=ghcr.io/yourusername/ada502-fireguard-project-docs:latest
```

---

## Troubleshooting

### Docs Build Fails But Code Deployment Works ✅

This is expected! The workflows are designed so that:
- **Code CI/CD is separate** from docs CI/CD
- **Docker publish continues** even if docs build fails
- **GitHub Pages deployment is skipped** gracefully

Check the GitHub Actions workflow logs to identify the specific error:
- Missing imports → Check PYTHONPATH setup in workflow
- Markdown syntax errors → Review `docs/` files for valid Markdown
- Docstring parsing errors → Check docstring formatting in Python/TypeScript files

### Docs Kubernetes Pod Fails to Start

1. **Check image availability:**
   ```bash
   kubectl describe pod -l app=docs
   kubectl logs -l app=docs --tail=50
   ```

2. **Verify image was pushed to GHCR:**
   ```bash
   docker pull ghcr.io/yourusername/ada502-fireguard-project-docs:latest
   ```

3. **Check ingress routing:**
   ```bash
   kubectl get ingress
   kubectl describe ingress fireguard-ingress
   kubectl get svc docs
   ```

### Documentation Not Updating After Code Changes

1. **Rebuild Docker image:**
   ```bash
   docker build -f docs/Dockerfile -t ghcr.io/yourusername/ada502-fireguard-project-docs:latest .
   docker push ghcr.io/yourusername/ada502-fireguard-project-docs:latest
   ```

2. **Force Kubernetes to pull latest:**
   ```bash
   kubectl rollout restart deployment/docs
   ```

### MkDocs Build Times Out

If mkdocs build takes longer than 60 seconds:
- Check for large imports or file operations in setup_commands
- Review `docs.yml` mkdocstrings configuration
- Optimize docstring processing in setup_commands

---

## Configuration Files

### mkdocs.yml

**Purpose:** MkDocs configuration, navigation structure, plugins

**Key sections:**
- `plugins.mkdocstrings.handlers.python.setup_commands` — Injects PYTHONPATH for imports
- `nav` — Documentation site structure
- `theme.material` — Material for MkDocs theme settings

### docs/Dockerfile

**Purpose:** Multi-stage Docker build for documentation container

**Stages:**
1. `frontend-docs` — Node.js build, runs TypeDoc
2. `docs-builder` — Python build, runs MkDocs
3. `stage-2` — Nginx serving compiled site

**Note:** Includes build dependencies (`gcc`, `musl-dev`, `python3-dev`) for Alpine Python

### docs/pyproject.toml

**Purpose:** Python dependencies for MkDocs build environment

**Key packages:**
- `mkdocs` — Site generator
- `mkdocs-material` — Material theme
- `mkdocstrings[python]` — Python autodocs plugin

---

## Monitoring & Maintenance

### Pre-Deployment Checklist

- [ ] Run `mkdocs build` locally and verify no errors
- [ ] Check TypeDoc generation: `npm run docs:api` (from frontend/)
- [ ] Verify Docker build: `docker build -f docs/Dockerfile . -t test:latest`
- [ ] Test Kubernetes manifests: `kubectl apply --dry-run=client -f k8s-manifests/docs-*.yaml`
- [ ] Check GitHub Actions workflow syntax (Actions tab)
- [ ] Verify PYTHONPATH is correct in workflows

### Regular Tasks

1. **Update docstrings** when API changes
   - Add module-level docstrings to new files
   - Use Google style for mkdocstrings compatibility
   - Run local mkdocs build to verify rendering

2. **Review generated documentation** regularly
   - Check GitHub Pages site after main branch pushes
   - Look for undocumented endpoints or parameters
   - Add usage examples to relevant pages in `docs/backend/` and `docs/intelligence/`

3. **Monitor build times** in CI/CD
   - MkDocs build should complete in < 5 seconds
   - If builds exceed 10 seconds, optimize mkdocstrings setup
   - TypeDoc should complete in < 15 seconds

4. **Test image pulls** periodically
   ```bash
   docker pull ghcr.io/yourusername/ada502-fireguard-project-docs:latest
   ```

---

## References

- **MkDocs Docs:** https://www.mkdocs.org/
- **Material for MkDocs:** https://squidfunk.github.io/mkdocs-material/
- **mkdocstrings:** https://mkdocstrings.github.io/
- **TypeDoc:** https://typedoc.org/
- **Kubernetes Ingress:** https://kubernetes.io/docs/concepts/services-networking/ingress/

---

## Summary

The documentation platform is fully automated with:
- ✅ GitHub Actions workflows for building and deploying
- ✅ Docker container for easy deployment to any environment
- ✅ Kubernetes manifests for production deployments
- ✅ Non-blocking docs builds that don't prevent code deployments
- ✅ Comprehensive error handling and status reporting
- ✅ Automated synchronization of frontend API reference with MkDocs site

All documentation is version-controlled and built from source during deployment, ensuring it always matches the current code.
