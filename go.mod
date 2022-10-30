module github.com/MoserMichael/s9k

go 1.13

require (
	golang.org/x/sys v0.1.0 // indirect
	k8s.io/api v0.0.0-20200726131424-9540e4cac147
	k8s.io/apimachinery v0.0.0-20200726131235-945d4ebf362b
	k8s.io/client-go v0.0.0-20200726131703-36233866f1c7
)

replace (
	k8s.io/api => k8s.io/api v0.0.0-20200726131424-9540e4cac147
	k8s.io/apimachinery => k8s.io/apimachinery v0.0.0-20200726131235-945d4ebf362b
	k8s.io/cli-runtime => k8s.io/cli-runtime v0.0.0-20200726133633-b4586cbefd36
	k8s.io/client-go => k8s.io/client-go v0.0.0-20200726131703-36233866f1c7
	k8s.io/code-generator => k8s.io/code-generator v0.0.0-20200726131043-26c52896b75b
	k8s.io/component-base => k8s.io/component-base v0.0.0-20200726132252-a5fb6b31bf34
	k8s.io/metrics => k8s.io/metrics v0.0.0-20200726133515-acfc769389fb
)
