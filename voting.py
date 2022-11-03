import redis
import json
import uuid
from flask import Flask, request, redirect, url_for, render_template, abort, make_response, g, jsonify
from config import config

class VotingWebsite:
    def __init__(self):
        self.app = Flask(__name__, static_url_path='/static')

        self.redis = redis.Redis()

        check = self.redis.get("votes")
        if check == None:
            print("Creating empty votes")
            self.redis.set("votes", "[]")

    def register(self):
        @self.app.before_request
        def before_request_handler():
            g.redis = redis.Redis()

        @self.app.route('/', methods=['GET'])
        def homepage():
            data = g.redis.get("votes")
            data = json.loads(data.decode("utf-8"))

            content = {
                'votes': data,
            }

            return render_template("homepage.html", **content)

        @self.app.route('/admin/new', methods=['POST'])
        def admin_new():
            data = g.redis.get("votes")
            data = json.loads(data.decode("utf-8"))

            print(request.form)

            name = request.form.get("newvote")
            if name != None:
                vote = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "options": [],
                }

                data.append(vote)
                g.redis.set("votes", json.dumps(data))

                return redirect("/admin")

            delete = request.form.get("delete")
            if delete == "true":
                id = request.form.get("id")
                found = -1
                index = 0

                for vote in data:
                    if vote['id'] == id:
                        found = index

                    index += 1

                del data[found]
                g.redis.set("votes", json.dumps(data))

                return redirect("/admin")

            option = request.form.get("option")
            if option != None:
                id = request.form.get("id")
                name = request.form.get("name")

                for vote in data:
                    if vote['id'] == id:
                        vote['options'].append({'name': name, 'value': 0})

                g.redis.set("votes", json.dumps(data))

                return redirect("/admin")

            return redirect("/admin")


        @self.app.route('/admin', methods=['GET'])
        def admin():
            data = g.redis.get("votes")
            data = json.loads(data.decode("utf-8"))

            content = {
                'votes': data,
            }

            return render_template("admin.html", **content)

        @self.app.route('/result', methods=['GET'])
        def result():
            data = g.redis.get("votes")
            data = json.loads(data.decode("utf-8"))

            for vote in data:
                winner = 0

                for option in vote['options']:
                    if option['value'] > winner:
                        winner = option['value']

                for option in vote['options']:
                    option['winner'] = True if option['value'] == winner else False

            content = {
                'votes': data,
            }

            return render_template("result.html", **content)

        @self.app.route('/vote', methods=['POST'])
        def vote():
            data = g.redis.get("votes")
            data = json.loads(data.decode("utf-8"))

            for vote in data:
                value = request.form.get(vote['id'])
                for option in vote['options']:
                    if option['name'] == value:
                        option['value'] += 1

            g.redis.set("votes", json.dumps(data))

            return redirect("/")

    def start(self):
        self.app.run(host="0.0.0.0", port=18001, debug=True, threaded=True)

if __name__ == '__main__':
    vote = VotingWebsite()
    vote.register()
    vote.start()
