#!/usr/bin/python3
import logging
import shlex
import argparse
import os

from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from gevent.select import select
from gevent.subprocess import Popen, PIPE

import bottle
from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket


ERROR_MESSAGE_NO_DATA = "The server failed to get the requested command."

def read_static_file(file_name):
    file_name = "./static-file/{}".format(file_name)
    with open(file_name, "r") as file:
        return file.read()

    print("!! 404 {}".format(file_name))
    return "404"

def get_style_sheet():
    return read_static_file("css.css")

class Params:
    kubeconfig_file = ""
    command_name = "kubectl"
    cert_file = "cert.pem"
    key_file = "key.pem"

    def __init__(self):
        pass

    def set_config(self, kubeconfig_cmd, kubeconfig_dir):
        self.command_name = kubeconfig_cmd
        if kubeconfig_dir != "":
            self.kubeconfig_file = " --kubeconfig={}/config".format(kubeconfig_dir)
            self.command_name += self.kubeconfig_file

    def set_cert_files(self, key_file, cert_file):
        self.cert_file = cert_file
        self.key_file = key_file

params = Params()

def get_home_link():
    return "<a href='/'>Home</a>&nbsp;"

class RunCommand:
    def __init__(self, command_line, split_lines=True, pipe_as_input=None):
        self.command_line = command_line
        self.lines = []
        self.exit_code = 0
        self.run(command_line, split_lines, pipe_as_input)

    def run(self, command_line, split_lines, pipe_as_input):

        logging.info("command line: %s", command_line)


        if pipe_as_input is None:
            process = Popen(shlex.split(command_line), \
                        stdout=PIPE, stderr=PIPE)

            (output, error_out) = process.communicate()
            self.exit_code = process.wait()
        else:
            process = Popen(shlex.split(command_line), \
                        stdin=PIPE, stdout=PIPE, stderr=PIPE)

            (output, error_out) = process.communicate(input=pipe_as_input.encode("utf-8"))
            self.exit_code = process.wait()


        if split_lines:
            self.lines = output.splitlines()
        else:
            self.output = output.decode("utf-8")

        self.error_out = error_out

        return self.exit_code

    def result(self):
        return self.exit_code, self.lines

def make_error_message(command):
    return_value = ERROR_MESSAGE_NO_DATA

    if command.command_line != "":
        return_value += " command line: {}.".format(command.command_line)
    if command.exit_code != 0:
        return_value += " exit status: {}. ".format(command.exit_code)
    if command.error_out != "":
        return_value += " " + command.error_out.decode("utf-8")
    return return_value


class TextCommand:
    def __init__(self, command):
        self.token_start = []
        self.token_end = []

        self.titles = []
        self.parsed_lines = []

        self.parse_header(command.lines[0].decode("utf-8"))
        self.parse_fields(command)

    def parse_header(self, header_line):

        # here it becomes a bit hacky
        header_line = header_line.replace("CREATED AT", "CREATED_AT")
        header_line = header_line.replace("NOMINATED NODE", "NOMINATED_NODE")
        header_line = header_line.replace("READINESS GATES", "READINESS_GATES")

        self.titles = header_line.split()
        start = 0
        for title_pos in range(len(self.titles)):

            word_pos = header_line.find(self.titles[title_pos], start)
            start = word_pos + len(self.titles[title_pos])

            self.token_start.append(word_pos)
            self.token_end.append(-1)

            if title_pos > 0:
                self.token_end[title_pos - 1] = word_pos

    def parse_fields(self, command):
        for line_pos in range(len(command.lines)):
            if line_pos > 0:
                line = command.lines[line_pos].decode("utf-8")
                line_vals = []
                for field_pos in range(len(self.token_start)):
                    tstart = self.token_start[field_pos]
                    tend = self.token_end[field_pos]
                    if  tend != -1:
                        field_value = line[tstart : tend]
                    else:
                        field_value = line[tstart:]
                    line_vals.append(field_value.strip())
                self.parsed_lines.append(line_vals)

    def dump(self):
        logging.info("header: %s", self.titles)
        for line in self.parsed_lines:
            logging.info("line: %s", line)



class ClientGoCmd:
    def __init__(self, entity, is_namespaced, column_defs):
        self.titles = []
        self.parsed_lines = []

        self.process(entity, is_namespaced, column_defs)

    def process(self, entity, is_namespaced, column_defs):
        if is_namespaced:
            command_text = "{} get {} -A".format(params.command_name, entity)
        else:
            command_text = "{} get {}".format(params.command_name, entity)


        if column_defs is not None:
            command_text += ClientGoCmd.make_column_filter(column_defs)
            command = RunCommand(command_text)

            self.titles = []
            for entry in column_defs:
                self.titles.append(entry[0])

            self.parsed_lines = []
            for line in command.lines:
                self.parsed_lines.append(line.split(","))
        else:
            command_text += " -o wide "
            command = RunCommand(command_text)
            text_command = TextCommand(command)
            self.titles = text_command.titles
            self.parsed_lines = text_command.parsed_lines

    @staticmethod
    def make_column_filter(column_defs):
        command_text = ' -o go-template --template=\'{{range .items}}{{printf "'

        command_text += "%s," * len(column_defs)
        command_text += '\\n" '
        for column_def in column_defs:
            command_text += column_def[1]
            command_text += " "
        command_text += "}}{{end}}'"

        return command_text

def find_index_in_list(slist, elem):

    for i, item in enumerate(slist):
        if item == elem:
            return i
    return -1


class HtmlTable:
    def __init__(self, titles, parsed_lines):
        self.titles = titles
        self.parsed_lines = parsed_lines
        self.html_text = ""

    def make_html(self, column_subset, link_cb, is_editable, editlink):
        if self.html_text != "":
            return self.html_text
        if link_cb is None:
            link_cb = HtmlTable.make_object_link_def

        if self.titles is None or self.parsed_lines is None:
            ret = ERROR_MESSAGE_NO_DATA
        else:
            ret = get_style_sheet()

            if is_editable:
                ret += HtmlTable.make_script_switch_to_edit()

            ret += self.make_table_header(column_subset)

            if isinstance(self.parsed_lines, list):
                for line in self.parsed_lines:
                    ret += '<tr>'
                    for pos in range(len(self.titles)):
                        if column_subset is None or pos in column_subset:
                            ret += '<td>{}</td>'.format(link_cb(line, pos))
                    ret += '</tr>\n'
            else:
                ret += '<tr id="displayform"><td>'
                if is_editable:
                    ret += '<input type="button" onclick="startedit();" value="edit"/> &nbsp; '
                    ret += '<input type="button" onclick="deleteobj();" value="Delete"/>'
                    ret += '<br/>'
                ret += '<pre id="toedit">{}</pre></td></tr>'.format(self.parsed_lines)
                if is_editable:
                    ret += HtmlTable.make_edit_row(editlink)
            ret += '</table>'

        self.html_text = ret
        return self.html_text

    def make_table_header(self, column_subset):
        hdr = HtmlTable.make_sort_jscript()

        hdr += '<table class="js-sort-table"><thead><tr>'
        for pos in range(len(self.titles)):
            if column_subset is None or pos in column_subset:
                title = self.titles[pos]
                #hdr += '<th align="left"><a onclick="sortTable({})">{}</a></th>'.format(pos, title)
                hdr += '<th align="left">{}</th>'.format(title)
        hdr += '</tr></thead>'
        return hdr

    @staticmethod
    def make_sort_jscript():
        return "<script>\n" + \
                read_static_file("sorttable/sort-table.min.js") + \
                '</script>'

    @staticmethod
    def make_object_link_def(line, title_pos):
        return line[title_pos]

    @staticmethod
    def make_edit_row(editlink):
        return '<tr id ="editform" style="display:none"><td>{} {}</td></tr>'.\
                format(HtmlTable.make_edit_form(editlink), HtmlTable.make_delete_form(editlink))

    @staticmethod
    def make_edit_form(editlink):
        return '''<form method="post" action="{}" >\
<input type="submit" value="save"/><br/>\
<textarea name="edit" id="contentOnEdit" rows="40", cols="80"></textarea>\
</form>'''.format(editlink[0])


    @staticmethod
    def make_delete_form(editlink):
        return '''<form id="deleteobj" method="post" action={} style="display:none">\
<textarea name="edit" id="contentOnDelete" style="display:none"></textarea>\
</form>'''.format(editlink[1])

    @staticmethod
    def make_script_switch_to_edit():
        return '''<script>
function  startedit() {
    toedit = document.getElementById("toedit");
    displayform = document.getElementById("displayform");
    editform = document.getElementById("editform");
    editctl = document.getElementById("contentOnEdit");

    displayform.style.display = 'none';
    editctl.value = toedit.innerHTML;
    editform.style.display = '';
}

function deleteobj() {
    if (confirm("Do you really want to delete the object ?")) {
        toedit = document.getElementById("toedit");
        edit = document.getElementById("contentOnDelete");
        edit.value = toedit.innerHTML;

        form = document.getElementById("deleteobj");
        form.submit();
    }
}
</script>
'''

class ApiResources:
    def __init__(self):
        self.html_table = None
        self.name_index = None
        self.namespaced_index = None
        self.error_message = None

    def load(self):
        cmd = params.command_name + " api-resources"
        run_command = RunCommand(cmd)

        #for whatever reasons kubectl api-resources often returns error status,
        #even it returned all resources.
        #if run_command.exit_code == 0 and len(run_command.lines) != 0:

        if len(run_command.lines) != 0:

            text_command = TextCommand(run_command)

            parsed_lines = sorted(text_command.parsed_lines, key=lambda entry: entry[0])

            self.html_table = HtmlTable(text_command.titles, parsed_lines)
            self.name_index = find_index_in_list(self.html_table.titles, "NAME")
            self.namespaced_index = find_index_in_list(self.html_table.titles, "NAMESPACED")
        else:
            self.html_table = None
            self.error_message = make_error_message(run_command)

    def make_html(self, column_subset):
        html = '<b>{}</b></br>'.format(get_home_link())

        if self.html_table:
            html += self.html_table.make_html(column_subset, self.make_object_link, False, "")
        else:
            html += self.error_message

        return html

    def make_object_link(self, line, title_pos):
        return '<a href="/objectinstances/{}/{}">{}</a>'.\
                format(line[self.name_index], line[self.namespaced_index], line[title_pos])

class ObjectListScreen:

    def __init__(self, oname, namespaced, field_sel, label_sel):
        cli_param = ""

        self.namespaced = namespaced
        self.object_type = oname

        if namespaced == "true":
            cli_param = "-A"

        add = ""
        if field_sel:
            add += "--field-selector {}".format(field_sel)

        if label_sel:
            add += "--selector {}".format(label_sel)

        cmd = "{} get {} -o wide {} --show-labels {}".format(\
                params.command_name, oname, cli_param, add)
        run_command = RunCommand(cmd)

        if run_command.exit_code == 0 and len(run_command.lines) != 0:
            text_command = TextCommand(run_command)
            self.name_index = find_index_in_list(text_command.titles, "NAME")
            self.namespace_index = find_index_in_list(text_command.titles, "NAMESPACE")

            self.html_table = HtmlTable(text_command.titles, text_command.parsed_lines)
        else:
            self.html_table = None
            self.error_message = make_error_message(run_command)

    def make_html(self):
        ret = get_home_link()
        ret += self.get_self_link() + '</br>'

        ret += self.make_query_fields()

        if self.html_table is not None:
            return ret + self.html_table.make_html(None, self.make_object_link, False, '')
        return ret + self.error_message

    def get_self_link(self):
        return "<b><a href='/objectinstances/{0}/{1}'>{0}</a></b>&nbsp;".\
                format(self.object_type, self.namespaced)

    def make_object_link(self, line, title_pos):
        if self.object_type != 'customresourcedefinitions':
            if self.namespace_index != -1:
                link = '<a href="/objectinfo/get-yaml/{}/{}/{}/{}">{}</a>'.\
                    format(self.object_type, line[self.name_index],\
                            line[self.namespace_index], self.namespaced, line[title_pos])
            else:
                link = '<a href="/objectinfo/get-yaml/{}/{}/None/{}">{}</a>'.\
                    format(self.object_type, line[self.name_index], \
                            self.namespaced, line[title_pos])
        else:
            link = '<a href="/crds/list-objects/{}">{}</a>'.\
                    format(line[self.name_index], line[self.name_index])

        return link

    def make_query_fields(self):
        return '''<form method="post" action="/objectinstances/{}/{}"><table><tr>\
<td width="1%">LabelSelector</td>\
<td><input name="labelsel"></td></tr>\
<tr><td>FieldSelector:</td><td><input name="fieldsel"></td></tr></table>\
<input type="submit" style="display: none" /></form>'''\
        .format(self.object_type, self.namespaced)

class CrdScreen:

    def __init__(self, screentype, oname, nspace):

        self.screentype = screentype
        self.oname = oname
        self.namespaced = nspace
        self.namespace_index = -1
        self.name_index = -1

    def make_html(self):
        hdr = CrdScreen.make_hdr_links()
        cmd = '{} get -A {}'.format(params.command_name, self.oname)
        run_command = RunCommand(cmd)

        if run_command.exit_code == 0 and len(run_command.lines) != 0:
            text_command = TextCommand(run_command)
            html_table = HtmlTable(text_command.titles, text_command.parsed_lines)

            self.namespace_index = find_index_in_list(html_table.titles, "NAMESPACE")
            self.name_index = find_index_in_list(html_table.titles, "NAME")

            return hdr + html_table.make_html(None, self.make_object_link, False, '')
        return hdr + make_error_message(run_command)


    @staticmethod
    def make_hdr_links():
        ret = get_home_link()
        ret += '<b><a href="/objectinstances/customresourcedefinitions/false">crds</a></b><br/>'
        return ret

    def make_object_link(self, line, title_pos):
        if self.namespace_index != -1:
            return '<a href="/crdinfo/get-yaml/{}/{}/{}">{}</a>'.\
                    format(self.oname, line[self.name_index],\
                            line[self.namespace_index], line[title_pos])

        return '<a href="/crdinfo/get-yaml/{}/{}/None">{}</a>'.\
                    format(self.oname, line[self.name_index], line[title_pos])


class ObjectDetailScreenBase:
    def __init__(self, urlbase, screentype, otype, oname, namespace, namespaced, request_types):

        self.request_types = request_types
        self.urlbase = urlbase

        self.oname = oname
        self.namespaced = namespaced
        self.namespace = namespace

        self.html_header = self.make_hdr_links(screentype, otype, oname, namespace, namespaced)
        self.html = self.html_header

        for request_def in self.request_types:
            if screentype == request_def[0]:
                cmd = ObjectDetailScreen.make_kubectl_cmd(request_def, namespace, otype, oname)
                self.add_table(cmd, request_def[2])
                return
        logging.error("Illegal screen type %s", screentype)


    @staticmethod
    def make_kubectl_cmd(request_def, namespace, otype, oname):
        nspace = ""
        if namespace != 'None':
            nspace = '-n {}'.format(namespace)
        cmd = request_def[1].format(params.command_name, otype, oname, nspace)
        return cmd

    def add_table(self, cmd, is_editable):
        run_command = RunCommand(cmd, False)
        if run_command.exit_code == 0 and run_command.output != "":
            html_table = HtmlTable([cmd], run_command.output)
            self.html += html_table.make_html(None, None, is_editable, \
                    ['/editobj/apply', '/editobj/delete'])
        else:
            self.html += make_error_message(run_command)

    def make_html(self):
        return self.html

    def make_hdr_links(self, screen_type, otype, oname, namespace, isnamespaced):
        ret = get_home_link()

        ret += self.make_back_link(otype, isnamespaced)

        for request_def in self.request_types:
            if request_def[0] == screen_type:
                ret += '<b>'

            link = "<a href='/{}/{}/{}/{}/{}/{}'>{}</a>".\
                    format(self.urlbase, request_def[0], otype, \
                        oname, namespace, isnamespaced, request_def[0])

            ret += link

            if request_def[0] == screen_type:
                ret += '</b>'
            ret += '&nbsp;'

        if otype == "pods":
            container_names = self.list_containers()
            for container_name in container_names:
                ret += '<a href="/shell-attach/{}/{}/{}/{}">attach-{}</a>'.\
                        format(isnamespaced, oname, namespace, container_name, container_name)
        return ret

    def make_back_link(self, otype, isnamespaced):
        return "<a href='/objectinstances/{0}/{1}'>{0}</a>&nbsp;".format(otype, isnamespaced)

    def list_containers(self):
        namespace_opt = ""
        if self.namespaced:
            namespace_opt = '-n {}'.format(self.namespace)

        list_cmd = "{} get pods {} {} -o jsonpath='{}'".\
                format(params.command_name, namespace_opt, self.oname, \
                    '{.spec.containers[*].name}')
        command = RunCommand(list_cmd, False)

        if command.exit_code != 0:
            return []

        print("list_cmd: {} out: {}".format(list_cmd, command.output))
        return command.output.split()



class ObjectDetailScreen(ObjectDetailScreenBase):
    def __init__(self, screentype, otype, oname, namespace, namespaced):

        request_types = [['describe', '{} describe {} {} {}', False], \
                              ['get-yaml', '{} get {} {} {} -o yaml', True],\
                              ['get-json', '{} get {} {} {} -o json', False],\
                              ['logs', '{} logs {}/{} {}', False]]

        super().__init__("objectinfo", screentype, otype, oname,\
                        namespace, namespaced, request_types)


class CrdInfoScreen(ObjectDetailScreenBase):
    def __init__(self, screentype, otype, oname, namespace, namespaced):

        request_types = [['get-yaml', '{} get {} {} {} -o yaml', True],\
                             ['get-json', '{} get {} {} {} -o json', False],\
                             ['crd-yaml', '{} describe customresourcedefinition {}', False]]

        super().__init__("crdinfo", screentype, otype, oname, namespace, namespaced, request_types)

    def make_back_link(self, otype, _):
        return '<a href="/crds/list-objects/{0}">crd {0}</a>&nbsp;'.format(otype)


class EditObjectScreen:
    def __init__(self, action, object_to_save):
        self.message = ""
        self.success_msg = {'apply' : "Object saved successfully", \
                            'delete': "Object deleted successfully"}
        self.run(action, object_to_save)

    def run(self, action, object_to_save):
        cmd = "{} {} -f -".format(params.command_name, action)
        print("cmd:", cmd)
        run_command = RunCommand(cmd, True, pipe_as_input=object_to_save)
        if run_command.exit_code == 0:
            self.message = self.success_msg.get(action)
        else:
            self.message = make_error_message(run_command)

    def make_html(self):
        return '{}<br/><button onclick="window.history.back();">Go Back</button>'\
                .format(self.message)


class TerminalAttachScreen(ObjectDetailScreen):
    def __init__(self, isnamespaced, podname, namespace, containername):

        self.isnamespaced = isnamespaced
        self.podname = podname
        self.namespace = namespace
        self.containername = containername

        super().__init__("terminal-attach", "pods", podname, namespace, isnamespaced)
        super

    def make_html(self):
        ret = self.html_header
        template = read_static_file('xterm/index.html')

        html = template.format(self.podname, self.namespace, self.containername)
        return ret + html



api_resources_screen = ApiResources()

app = bottle.Bottle()
@app.route('/')
def mainscr():
    return api_resources_screen.make_html([0, 2, 4, 5])

@app.route('/objectinstances/<oname>/<namespaced>', method=['GET', 'POST'])
def objectlinkscr(oname, namespaced):
    bottle.response.set_header('Cache-Control', 'no-store')
    field_sel = bottle.request.forms.get("fieldsel")
    label_sel = bottle.request.forms.get("labelsel")
    object_screen = ObjectListScreen(oname, namespaced, field_sel, label_sel)
    return object_screen.make_html()

@app.route('/objectinfo/<screentype>/<otype>/<instancename>/<namespace>/<isnamespaced>')
def objectinfoscr(otype, screentype, instancename, namespace, isnamespaced):
    bottle.response.set_header('Cache-Control', 'no-store')
    object_screen = ObjectDetailScreen(screentype, otype, instancename, namespace, isnamespaced)
    return object_screen.make_html()

@app.route('/crds/<screentype>/<oname>')
def crdscr(screentype, oname):
    bottle.response.set_header('Cache-Control', 'no-store')
    object_screen = CrdScreen(screentype, oname, None)
    return object_screen.make_html()

@app.route('/crdinfo/<sccreentype>/<otype>/<oname>/<namespace>')
def crdinfoscr(sccreentype, otype, oname, namespace):
    bottle.response.set_header('Cache-Control', 'no-store')
    object_screen = CrdInfoScreen(sccreentype, otype, oname, namespace, "")
    return object_screen.make_html()

@app.route('/crdinfo/<sccreentype>/<otype>/<oname>/<namespace>/')
def crdinfoscr2(sccreentype, otype, oname, namespace):
    bottle.response.set_header('Cache-Control', 'no-store')
    object_screen = CrdInfoScreen(sccreentype, otype, oname, namespace, "")
    return object_screen.make_html()


@app.route('/editobj/<action>', method='POST')
def edit_object_action(action):
    bottle.response.set_header('Cache-Control', 'no-store')
    object_to_save = bottle.request.forms.get("edit")
    object_screen = EditObjectScreen(action, object_to_save)
    return object_screen.make_html()


@app.route('/static-file/<fname:path>')
def get_static_file(fname):
    return read_static_file(fname)

@app.route('/shell-attach/<isnamespaced>/<podname>/<namespace>/<containername>')
def shell_attach(isnamespaced, podname, namespace, containername):
    terminal_attach = TerminalAttachScreen(isnamespaced, podname, namespace, containername)
    return terminal_attach.make_html()

#@app.route('/socket.io/<fname:path>', apply=[websocket], method="GET")
@app.get('/wssh', apply=[websocket], method="GET")
def echo(web_socket):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = "{}/kubeexec {}".format(script_dir, params.kubeconfig_file)

    process = Popen(shlex.split(cmd), \
                        stdout=PIPE, stdin=PIPE) #, stderr=PIPE)

    stream = web_socket.stream.handler.rfile
    fd_stream = stream.fileno()

    fd_out = process.stdout.fileno()

    #print("fd_out {} fd-stream {} fd_stream-in {}".\
    #   format(fd_out, fd_stream, process.stdin.fileno()))

    loop_select = True
    while loop_select:
        try:
            #print("before select")
            read_sock, _, error_socks = \
                    select([fd_stream, fd_out], [], [fd_stream, fd_out], 1)
            #print("after select read_events {} error_events {}".\
            #        format(len(read_sock), len(error_socks)))

            if len(read_sock) != 0:
                for sock in read_sock:
                    if sock == fd_out:
                        #print("read from stdout")
                        msg = process.stdout.readline()
                        if msg is None or len(msg) == 0:
                            loop_select = False
                            break
                        smsg = msg.decode('utf-8')
                        #print("msg-from-kubectl {}".format(smsg))
                        web_socket.send(smsg)

                    elif sock == fd_stream:
                        #print("read from sock {}".format(sock))
                        msg = web_socket.receive()
                        if msg is None or msg == "":
                            loop_select = False
                            break
                        #print("msg-net {}".format(msg))
                        msg += '\n'
                        process.stdin.write(msg.encode('utf-8'))
                        process.stdin.flush()
            if len(error_socks) != 0:
                #print("error:")
                loop_select = False
                break
        except WebSocketError:
            loop_select = False
            break
        except BrokenPipeError:
            loop_select = False
            break

    try:
        process.stdin.close()
        process.stdout.close()
    except BrokenPipeError:
        pass


def parse_cmd_line():
    usage = '''Web application that parses kubectl output in a nice manner.
'''
    parse = argparse.ArgumentParser(description=usage)

    parse.add_argument('--command', '-c', type=str, default='kubectl', dest='kubectl',\
            help='kubectl command name')

    parse.add_argument('--port', '-p', type=int, default=8000, dest='port',\
            help='listening port')

    parse.add_argument('--host', '-i', type=str, dest='host', default='localhost',\
            help='listening on host')

    parse.add_argument('--cert', '-r', type=str, dest='cert', default='',\
            help='TLS certifificate file')

    parse.add_argument('--key', '-k', type=str, dest='key', default='',\
            help='TLS private key file')

    parse.add_argument('--kubeconfig', '-f', type=str, dest='config', default='',\
            help='kubeconfig directory (use default if empty)')

    return parse.parse_args()

def set_info_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    file_handler = logging.FileHandler("gh.log")
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    root.addHandler(console_handler)

class GeventWebSocketServerSSL(bottle.ServerAdapter):
    def run(self, handler):
        server = pywsgi.WSGIServer((self.host, self.port), handler,\
                        handler_class=WebSocketHandler, \
                        keyfile=params.key_file, certfile=params.cert_file)

        server.serve_forever()

def main():

    cmd = parse_cmd_line()

    logging.info("host: %s port: %s command: %s certfile: %s keyfile: %s",\
                cmd.host, cmd.port, cmd.kubectl, cmd.cert, cmd.key)

    params.set_config(cmd.kubectl, cmd.config)

    api_resources_screen.load()

    if cmd.cert == "" and cmd.key == "":
        bottle.run(app, host=cmd.host, port=cmd.port, server=GeventWebSocketServer)
    else:
        params.set_cert_files(cmd.key, cmd.cert)

        bottle.run(app, host=cmd.host, port=cmd.port, server=GeventWebSocketServerSSL)


if __name__ == '__main__':
    main()
