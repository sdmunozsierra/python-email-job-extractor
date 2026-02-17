# Kubernetes Deployment

Deploy the Email Opportunity Pipeline to a Kubernetes cluster.

## Architecture

| Resource | Purpose |
|----------|---------|
| **Deployment** | Streamlit UI dashboard (1 replica) |
| **CronJob** | Scheduled `run-all` pipeline execution (every 6h) |
| **Service** | ClusterIP exposing the UI on port 80 |
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

Port-forward to access the Streamlit dashboard locally:

```bash
kubectl -n email-pipeline port-forward svc/email-pipeline-ui 8502:80
# Open http://localhost:8502
```

For external access, add an Ingress resource pointing to the `email-pipeline-ui` service.

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
