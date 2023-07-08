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
            external-dns.alpha.kubernetes.io/hostname: "argo-cd.${var.domain_name}"
            alb.ingress.kubernetes.io/backend-protocol: "HTTPS"
            alb.ingress.kubernetes.io/ssl-policy: "ELBSecurityPolicy-2016-08"
        ingressClassName: ${var.ingress_class_name}
        hosts: ["argo-cd.${var.domain_name}"]
configs:
    secret:
        argocdServerAdminPassword: ${var.argocd_password}
    repositories:
        private-repo:
            url: https://github.com/ZapNURSE/sms-infrastructure.git
            password: ${var.github_token}
        workforce-management:
            url: https://github.com/ZapNURSE/workforce-management.git
            password: ${var.github_token}
image:
    tag: v2.6.7
EOF
  ]
}


resource "helm_release" "argocd-apps" {
  depends_on = [helm_release.argocd]
  chart      = "argocd-apps"
  name       = "argocd-apps"
  namespace  = "argocd"
  repository = "https://argoproj.github.io/argo-helm"

  values = [
    "${file("./argo-apps-values/${var.env}.yaml")}"
  ]
}