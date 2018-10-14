from flask import Flask, request, make_response

app = Flask(__name__)

sources = {}


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/status', methods=['GET'])
def status():
    return 'Current running sources: \n' + str(sources)


@app.route('/source', methods=['GET', 'POST'])
def manage_source():
    if request.method == 'GET':
        name = request.args.get('name')
        if name in sources:
            source_status = sources[name]
        else:
            source_status = 'unknown'
        return 'Source status: ' + source_status
    if request.method == 'POST':
        name = request.form.get('name')
        new_status = request.form.get('status')
        sources[name] = new_status
        return 'updated'


if __name__ == '__main__':
    app.run()
