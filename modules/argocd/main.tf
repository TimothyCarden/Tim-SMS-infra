resource "kubernetes_namespace" "argocd" {
  metadata {
    name = var.argocd_namespace
  }
}

resource "helm_release" "argocd" {
  depends_on = [kubernetes_namespace.argocd]
  name       = var.release_name
  chart      = "argo-cd"
  repository = "https://argoproj.github.io/argo-helm"
  namespace  = kubernetes_namespace.argocd.id
  version    = var.chart_version
  values = [<<EOF
server:
    extraArgs:
        - --insecure
        - --rootpath=/argo-cd
    ingress:
        enabled: true
        pathType: Prefix
        paths:
            - /argo-cd
        annotations:
            nginx.ingress.kubernetes.io/ssl-redirect: "true"
            nginx.ingress.kubernetes.io/certificate: ${var.certificate_arn}
            kubernetes.io/ingress.class: "nginx"
            ingressClassName: "nginx"
            external-dns.alpha.kubernetes.io/hostname: "argo-cd.dev.actrusfm.com"
            alb.ingress.kubernetes.io/backend-protocol: "HTTPS"
            alb.ingress.kubernetes.io/ssl-policy: "ELBSecurityPolicy-2016-08"
        hosts: ["argo-cd.dev.actrusfm.com"]
image:
    tag: v2.6.7
EOF
  ]
}