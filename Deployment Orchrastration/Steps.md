## Steps to work on one-click deployment orchrastration

1. Learn Kubernets  
    - Need to learn what kubectl can do and why we run the commands.
    - Understand clusters, pods and inter-connectivity in a kubernetes cluster
    - Understand ingress gateway and service mesh.
    - Some advance things include, sidecar and monitoring tooling (istio includes it, check step 3)
    - Ref:
        - https://kubernetes.io/docs/tutorials/kubernetes-basics/


2. Helm Setup
    - Ref:
        - https://www.freecodecamp.org/news/what-is-a-helm-chart-tutorial-for-kubernetes-beginners/
        - https://wkrzywiec.medium.com/how-to-deploy-application-on-kubernetes-with-helm-39f545ad33b8
        - https://medium.com/swlh/how-to-declaratively-run-helm-charts-using-helmfile-ac78572e6088
        - https://docs.aws.amazon.com/AmazonECR/latest/userguide/using-helm-charts-eks.html


3. Setup istio (for service discovery and service mesh)
    - Ref:
        -  https://istio.io/latest/docs/setup/getting-started/
        - https://medium.com/@muppedaanvesh/getting-started-with-istio-a-hands-on-guide-for-beginners-0f73939e153a

4. Containerize Demo app and push to ECR
    - Ref:
        - [Simple step to push to AWS ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html)
        - [Push multi-arch image](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-multi-architecture-image.html)
        - [Push helm chart](https://docs.aws.amazon.com/AmazonECR/latest/userguide/push-oci-artifact.html)

5. Run things on cloud to test inter-connectivity
