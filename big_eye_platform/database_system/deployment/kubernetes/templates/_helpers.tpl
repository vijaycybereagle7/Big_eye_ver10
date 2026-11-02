{{/*
Expand the name of the chart.
*/}}
{{- define "threatintel-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "threatintel-platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "threatintel-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "threatintel-platform.labels" -}}
helm.sh/chart: {{ include "threatintel-platform.chart" . }}
{{ include "threatintel-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "threatintel-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "threatintel-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "threatintel-platform.serviceAccountName" -}}
{{- if .Values.fastapi.serviceAccount.create }}
{{- default (include "threatintel-platform.fullname" .) .Values.fastapi.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.fastapi.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate certificates for TLS
*/}}
{{- define "threatintel-platform.certs" -}}
{{- $cert := .Values.tls.cert | default .Values.ingress.tls }}
{{- if and $cert .Values.tls.enabled }}
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {{ include "threatintel-platform.fullname" . }}-tls
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
spec:
  secretName: {{ include "threatintel-platform.fullname" . }}-tls-secret
  dnsNames:
  {{- range .Values.ingress.hosts }}
  - {{ .host }}
  {{- end }}
  issuerRef:
    name: {{ .Values.tls.issuer }}
    kind: ClusterIssuer
{{- end }}
{{- end }}

{{/*
Generate persistent volume claims
*/}}
{{- define "threatintel-platform.pvc" -}}
{{- $fullName := include "threatintel-platform.fullname" . }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ $fullName }}-fastapi-logs
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
    component: fastapi
spec:
  accessModes:
    - ReadWriteOnce
  {{- if .Values.fastapi.persistence.storageClass }}
  storageClassName: {{ .Values.fastapi.persistence.storageClass }}
  {{- end }}
  resources:
    requests:
      storage: {{ .Values.fastapi.persistence.size | default "10Gi" }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ $fullName }}-celery-logs
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
    component: celery
spec:
  accessModes:
    - ReadWriteOnce
  {{- if .Values.celeryWorker.persistence.storageClass }}
  storageClassName: {{ .Values.celeryWorker.persistence.storageClass }}
  {{- end }}
  resources:
    requests:
      storage: {{ .Values.celeryWorker.persistence.size | default "5Gi" }}
{{- end }}

{{/*
Generate ConfigMaps
*/}}
{{- define "threatintel-platform.config" -}}
{{- $fullName := include "threatintel-platform.fullname" . }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ $fullName }}-nginx-config
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
    component: nginx
data:
  nginx.conf: |
    worker_processes auto;
    error_log /var/log/nginx/error.log warn;
    pid /var/run/nginx.pid;
    
    events {
        worker_connections 1024;
        use epoll;
        multi_accept on;
    }
    
    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
        
        log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for"';
        
        access_log /var/log/nginx/access.log main;
        
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        keepalive_requests 1000;
        
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_proxied any;
        gzip_comp_level 6;
        
        upstream backend {
            {{- if .Values.fastapi.autoscaling.enabled }}
            {{- range $i, $e := until (.Values.fastapi.autoscaling.maxReplicas | int) }}
            server {{ $fullName }}-fastapi-{{ $i }}.{{ $fullName }}-fastapi.{{ $.Release.Namespace }}.svc.cluster.local:8000;
            {{- end }}
            {{- else }}
            server {{ $fullName }}-fastapi:8000;
            {{- end }}
        }
        
        server {
            listen 80;
            server_name _;
            
            location / {
                proxy_pass http://backend;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_cache_bypass $http_upgrade;
            }
            
            location /health {
                access_log off;
                return 200 "healthy\n";
                add_header Content-Type text/plain;
            }
        }
    }
{{- end }}

{{/*
Generate RBAC resources
*/}}
{{- define "threatintel-platform.rbac" -}}
{{- if .Values.fastapi.serviceAccount.create }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "threatintel-platform.serviceAccountName" . }}
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
  {{- with .Values.fastapi.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "threatintel-platform.fullname" . }}-leader-election
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["configmaps/status"]
  verbs: ["get", "update", "patch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "threatintel-platform.fullname" . }}-leader-election
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
subjects:
- kind: ServiceAccount
  name: {{ include "threatintel-platform.serviceAccountName" . }}
  namespace: {{ .Release.Namespace }}
roleRef:
  kind: Role
  name: {{ include "threatintel-platform.fullname" . }}-leader-election
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "threatintel-platform.fullname" . }}-metrics-reader
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
rules:
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {{ include "threatintel-platform.fullname" . }}-metrics-reader
  labels:
    {{- include "threatintel-platform.labels" . | nindent 4 }}
subjects:
- kind: ServiceAccount
  name: {{ include "threatintel-platform.serviceAccountName" . }}
  namespace: {{ .Release.Namespace }}
roleRef:
  kind: ClusterRole
  name: {{ include "threatintel-platform.fullname" . }}-metrics-reader
  apiGroup: rbac.authorization.k8s.io
{{- end }}