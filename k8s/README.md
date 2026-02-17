# Kubernetes Deployment

Deploy the Email Opportunity Pipeline to a Kubernetes cluster using **ArgoCD** for GitOps-based continuous delivery.

## Architecture

| Resource | Purpose |
|----------|---------|
| **Deployment** | Streamlit UI dashboard (1 replica) |
| **CronJob** | Scheduled `run-all` pipeline execution (every 6h) |
| **Service** | ClusterIP exposing the UI on port 80 |
| **Ingress** | Internal hostname routing to the Streamlit UI |
| **PVCs** | Persistent storage for `data/`, `output/`, and `resumes/` |
| **Secret** | OpenAI API key + Gmail OAuth credentials |
| **ConfigMap** | Filter rules and questionnaire configuration |

## Prerequisites

1. A running Kubernetes cluster
2. `kubectl` configured to target the cluster
3. A Gmail OAuth `credentials.json` from Google Cloud Console
4. A cached `token.json` (run the pipeline locally once to complete the OAuth flow)
5. An OpenAI API key (for LLM features)

## Setup

### 1. Build and push the Docker image

```bash
docker build -t email-pipeline:latest .
# Tag and push to your registry:
docker tag email-pipeline:latest <your-registry>/email-pipeline:latest
docker push <your-registry>/email-pipeline:latest
```

### 2. Configure secrets

Edit `k8s/secrets.yaml` and replace the placeholder values:

- `OPENAI_API_KEY` — your OpenAI API key
- `credentials.json` — paste the full contents of your Google OAuth credentials file
- `token.json` — paste the full contents of your cached OAuth token file

> **Tip**: For production, use `kubectl create secret` or a secrets manager (e.g., Sealed Secrets, External Secrets Operator) instead of committing secrets to version control.

### 3. Configure the pipeline

Edit `k8s/configmap.yaml` to customize:

- `filter_rules.json` — email classification rules for your job search
- `questionnaire.json` — reply composition preferences and tone

### 4. Upload your resume

After deploying, copy your resume into the `pipeline-resumes` PVC:

```bash
# Find the UI pod name
POD=$(kubectl -n email-pipeline get pod -l app.kubernetes.io/component=ui -o jsonpath='{.items[0].metadata.name}')

# Copy resume into the pod
kubectl -n email-pipeline cp your_resume.json "$POD:/app/resumes/resume.json"
```

### 5. Update the image reference

Edit `k8s/kustomization.yaml` and set `newName` to your registry path:

```yaml
images:
  - name: email-pipeline
    newName: <your-registry>/email-pipeline
    newTag: latest
```

### 6. Deploy

```bash
kubectl apply -k k8s/
```

## Accessing the UI

### Via Ingress (recommended for internal networks)

The Ingress resource routes traffic from your internal DNS to the Streamlit dashboard. After deploying, configure your internal DNS to point `email-pipeline.internal` at your ingress controller's load balancer IP.

Then open: `http://email-pipeline.internal`

To customize the hostname, edit `k8s/ingress.yaml`:

```yaml
rules:
  - host: my-custom-hostname.corp.internal
```

The Ingress is configured for `nginx-internal` ingress class. Adjust `ingressClassName` and the annotation `kubernetes.io/ingress.class` to match your cluster's internal ingress controller.

### Via port-forward (local development)

```bash
kubectl -n email-pipeline port-forward svc/email-pipeline-ui 8502:80
# Open http://localhost:8502
```

## Running the pipeline manually

Trigger a one-off pipeline run outside the CronJob schedule:

```bash
kubectl -n email-pipeline create job --from=cronjob/email-pipeline-run manual-run
```

## Customizing the schedule

The CronJob runs every 6 hours by default. Edit the `schedule` field in `k8s/cronjob.yaml`:

```yaml
schedule: "0 */6 * * *"   # Every 6 hours
schedule: "0 8,20 * * *"  # Twice daily at 8am and 8pm
schedule: "0 9 * * 1-5"   # Weekdays at 9am
```

## Volume layout

| PVC | Mount path | Contents |
|-----|-----------|----------|
| `pipeline-data` | `/app/data` | JSON artifacts (messages, filtered, opportunities, analyses) |
| `pipeline-output` | `/app/output` | Reports, matches, tailored resumes, reply drafts |
| `pipeline-resumes` | `/app/resumes` | Your resume file(s) |

---

## ArgoCD Deployment (GitOps)

The `argocd/` directory contains manifests for deploying through ArgoCD, providing automated sync from this Git repository to your cluster.

### Prerequisites

1. ArgoCD installed on your cluster ([install guide](https://argo-cd.readthedocs.io/en/stable/getting_started/))
2. This repository accessible from the cluster (HTTPS or SSH)
3. Secrets and ConfigMap values populated (see steps 2–3 above)

### ArgoCD resources

| File | Kind | Purpose |
|------|------|---------|
| `argocd/project.yaml` | `AppProject` | Scoped project restricting allowed repos, namespaces, and resource types |
| `argocd/application.yaml` | `Application` | Points ArgoCD at the `k8s/` directory and defines sync policy |

### Setup

#### 1. Configure the repository URL

Edit both `argocd/project.yaml` and `argocd/application.yaml` and set `repoURL` / `sourceRepos` to your actual Git repository URL.

#### 2. Set the container image

In `argocd/application.yaml`, replace the image override under `spec.source.kustomize.images`:

```yaml
kustomize:
  images:
    - email-pipeline=myregistry.corp.internal/email-pipeline:latest
```

#### 3. Set the Ingress hostname

Edit `k8s/ingress.yaml` and replace `email-pipeline.internal` with your internal DNS hostname. Adjust `ingressClassName` to match your cluster's internal ingress controller.

#### 4. Apply the ArgoCD resources

```bash
kubectl apply -f argocd/project.yaml
kubectl apply -f argocd/application.yaml
```

ArgoCD will detect the `k8s/` directory and automatically sync all resources to the `email-pipeline` namespace.

### Sync policy

The Application is configured with:

- **Automated sync** — changes pushed to the `main` branch are deployed automatically
- **Self-heal** — manual cluster drift is reverted to match Git
- **Prune** — resources removed from Git are deleted from the cluster
- **Retry** — failed syncs retry up to 3 times with exponential backoff

### Monitoring

```bash
# Check application status via ArgoCD CLI
argocd app get email-pipeline

# View sync history
argocd app history email-pipeline

# Trigger a manual sync
argocd app sync email-pipeline

# Open the ArgoCD web UI
kubectl -n argocd port-forward svc/argocd-server 8080:443
# Open https://localhost:8080
```

### GitOps workflow

Once ArgoCD is set up, the deployment workflow becomes:

1. Make changes to manifests in `k8s/` or application code
2. Build and push a new container image with an updated tag
3. Update the image tag in `argocd/application.yaml` (or use ArgoCD Image Updater)
4. Push to `main` — ArgoCD detects the change and syncs automatically
