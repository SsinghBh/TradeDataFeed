from flask import Flask, request

app = Flask(__name__)

@app.route('/message', methods=['POST'])
def receive_message():
    print("Message Received")
    return "Message Received", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005, debug=True)