package  main

import (
	// "bytes"
	"os"
	"log"
	"io"
	"bufio"
	"context"
	"fmt"
	"flag"
	"path/filepath"
	"encoding/json"
	"net/http"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/remotecommand"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/kubernetes"
	"k8s.io/apimachinery/pkg/runtime/schema"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	corev1 "k8s.io/api/core/v1"
	scheme "k8s.io/client-go/kubernetes/scheme"
)

var DebugOn = false

//kubectl get pods kube-proxy-x88vt -n kube-system  -o jsonpath='{.spec.containers[*].name}'
//kubectl exec --stdin --tty -n kube-system kube-proxy-x88vt -c kube-proxy -- /bin/sh
// { "pod_namespace": "kube-system", "pod_name": "kube-proxy-x88vt", "container_name": "kube-proxy" }
type TermConnectPayload struct {
	Namespace     string `json:"pod_namespace"`
	PodName       string `json:"pod_name"`
	ContainerName string `json:"container_name"`
}

type TermSizePayload struct {
	Columns int `json:"cols"`
	Rows    int `json:"rows"`
}

type DataPayload struct {
	Data string `json:"data"`
}


func HomeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		return h
	}
	return os.Getenv("USERPROFILE") // for windows
}

func DefaultConfigFile() (string, bool) {
	if home := HomeDir(); home != "" {
		p := filepath.Join(home, ".kube", "config")
		_, err := os.Stat(p)
		if err != nil {
			return "", false
		}
		return p, true
	}
	return "", false
}

func NewExecRequest(config *rest.Config, p TermConnectPayload) *rest.Request {

	rest, err := rest.RESTClientFor(config)
	if err != nil {
		log.Fatal("can't get rest client: ", err)
	}

	req := rest.
		Post().
		Namespace(p.Namespace).
		Resource("pods").
		Name(p.PodName).
		SubResource("exec").
		VersionedParams(&corev1.PodExecOptions{
			Command:   []string{"/bin/sh"},
			Stdin:     true,
			Stdout:    true,
			Stderr:    true,
			TTY:       true,
			Container: p.ContainerName,
		}, scheme.ParameterCodec)

	return req
}

func readConnectCmd(reader *bufio.Reader) (*TermConnectPayload, error) {

	jsonString, err := reader.ReadString('\n')
	if err !=  nil {
		return nil, err
	}

	if DebugOn {
		log.Print("connect-cmd: ", jsonString)
	}

	connectPayload := &TermConnectPayload{}

	if err := json.Unmarshal([]byte(jsonString), &connectPayload); err != nil {
		return nil, err
	}

	return connectPayload, nil
}

type  StdinReader struct {
	reader *bufio.Reader
	resizeChannel chan TermSizePayload
	resizePayload *TermSizePayload
	dataPayload *DataPayload
	bufferToSend []byte
	bufferToSendPos int
}

func NewStdinReader(reader *bufio.Reader) (*StdinReader) {
	return &StdinReader{reader: reader, //bufio.NewReader(os.Stdin),
						resizeChannel: make(chan TermSizePayload),
						resizePayload: &TermSizePayload{},
						dataPayload: &DataPayload{},
						bufferToSend: nil,
						bufferToSendPos: -1}
}

func (r *StdinReader) Read(rdata []byte) (int, error) {

	if r.bufferToSend == nil {
		if err := r.readMore(); err != nil {
			return  0, err
		}
	}

	remainingLen := len(r.bufferToSend) - r.bufferToSendPos
	if remainingLen  <= len(rdata) {
		ncopied := copy(rdata, r.bufferToSend[r.bufferToSendPos:])
		r.bufferToSend = nil

		if DebugOn {
			log.Printf("copied %d", ncopied)
		}
		return ncopied, nil
	}

	toCopy := len(rdata)
	copy(rdata, r.bufferToSend[r.bufferToSendPos: r.bufferToSendPos+toCopy])
	r.bufferToSendPos+=toCopy

	if DebugOn {
		log.Printf("copied (short-buffer) %d", toCopy)
	}
	return  toCopy, io.ErrShortBuffer
}

func (r *StdinReader) readMore() error {
	for {
		jsonString, err := r.reader.ReadString('\n')
		if err != nil {
			return err
		}

		if DebugOn {
			log.Print("json: ", jsonString)
		}

		// the beauty of golang json parsing ....
		r.resizePayload.Rows = -1
		r.resizePayload.Columns = -1

		err = json.Unmarshal([]byte(jsonString), &r.resizePayload)
		if err != nil {
			return err
		}

		if r.resizePayload.Rows != -1 && r.resizePayload.Columns != -1 {
			resizeMsg := *r.resizePayload
			if DebugOn {
				log.Printf("send resiz msg to channel cols: %d rows: %d", resizeMsg.Columns, resizeMsg.Rows)
			}
			r.resizeChannel <- resizeMsg
			continue
		}

		err = json.Unmarshal([]byte(jsonString), &r.dataPayload)
		if err != nil {
			return err
		}
		r.bufferToSend = []byte(r.dataPayload.Data)
		r.bufferToSendPos = 0

		if DebugOn {
			log.Printf("data message: %v", r.bufferToSend)
		}

		return nil
	}
}

type TerminalSizeQueueImp struct {
	resizeChannel chan TermSizePayload
}

func (r *TerminalSizeQueueImp) Next() *remotecommand.TerminalSize {
	resizeMsg := <-r.resizeChannel

	ret := &remotecommand.TerminalSize{Width: uint16(resizeMsg.Columns), Height: uint16(resizeMsg.Rows)}

	if DebugOn {
		log.Print("got resize message: ", ret.Height, ret.Width)
	}
	return ret
}

type DataWriter struct {
	dataPayload *DataPayload
}

func NewDataWriter() *DataWriter {
	return &DataWriter{dataPayload: &DataPayload{}}
}

func (r *DataWriter) Write(data []byte) (n int, err error) {

	r.dataPayload.Data = string(data)
	jsonData,_ := json.Marshal(r.dataPayload)

	if DebugOn {
		log.Printf("out-data: %s", string(jsonData))
	}
	fmt.Printf("%s\n", string(jsonData))
	return len(data), nil
}

func makeConfig(kubeconfig string)  (*rest.Config, error) {
	restConfig, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		log.Fatal(err)
	}

	// vodoo, i like kkkkubernetes. (from: pkg/cmd/util/kubectl_match_version.go in kubectl)
	restConfig.GroupVersion = &schema.GroupVersion{Group: "", Version: "v1"}


	if restConfig.APIPath == "" {
		restConfig.APIPath = "/api"
	}
	if restConfig.NegotiatedSerializer == nil {
		// This codec factory ensures the resources are not converted. Therefore, resources
		// will not be round-tripped through internal versions. Defaulting does not happen
		// on the client.
		restConfig.NegotiatedSerializer = scheme.Codecs.WithoutConversion()
	}
	err = rest.SetKubernetesDefaults(restConfig)

	return restConfig, err
}

func checkIfPodExists(restConfig *rest.Config, termConnectPayload  *TermConnectPayload) error {

	clientset, err := kubernetes.NewForConfig(restConfig)
	if err != nil {
		log.Fatal(err)
	}
	_, err = clientset.CoreV1().Pods(termConnectPayload.Namespace).Get(context.TODO(), termConnectPayload.PodName, metav1.GetOptions{})
	if err != nil {
		return err
	}
	return nil
}

func setLogFile() (*os.File) {
	file, err := os.OpenFile("info.log", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil {
        log.Fatal(err)
    }

    log.SetOutput(file)

	return file
}

func main() {

	/*
	file := setLogFile()
	defer file.Close()
	*/

	defaultConfig, _ := DefaultConfigFile()
	kubeconfig := flag.String("kubeconfig", defaultConfig, "absolute path to the kubeconfig file")
	flag.Parse()

	restConfig, err := makeConfig(*kubeconfig)
	if err != nil {
		log.Fatal("Can't create rest config", err)
	}

	inReader := bufio.NewReader(os.Stdin)
	termConnectPayload, err := readConnectCmd(inReader)
	if err != nil {
		log.Fatal("can't read command def", err)
	}

	if termConnectPayload.PodName == "" {
		log.Fatal("no podname defined in connect command")
	}

	if DebugOn {
		log.Printf("pod_name: %s namespace: %s container: %s", termConnectPayload.PodName, termConnectPayload.Namespace, termConnectPayload.ContainerName)
	}

	err = checkIfPodExists(restConfig, termConnectPayload)
	if err != nil {
		log.Fatalf("pod %s namespace %s does not exist.", termConnectPayload.PodName, termConnectPayload.Namespace)
	}

	req := NewExecRequest(restConfig, *termConnectPayload)

	exec, err := remotecommand.NewSPDYExecutor(restConfig, http.MethodPost, req.URL())
	if err != nil {
		log.Fatal("failed to create spdy executor", err)
	}

	stdinReader := NewStdinReader(inReader)
	terminalSizeQueue := TerminalSizeQueueImp{resizeChannel: stdinReader.resizeChannel}
	dataWriter := NewDataWriter()

	var rawTerm = true

	if DebugOn {
		log.Printf("streaming...")
	}
	err = exec.Stream(remotecommand.StreamOptions{
					Stdin:             stdinReader,
					Stdout:            dataWriter,
					Stderr:            dataWriter,
					Tty:               rawTerm,
					TerminalSizeQueue: &terminalSizeQueue,
				})
	if err != nil {
		log.Fatalf("stream error: %v", err)
	}
	log.Print("exit")
	os.Exit(0)
}
