from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/echo', methods=['POST'])
def echo():
    if request.method == 'POST':
        data = request.json  # Получить данные из POST-запроса в формате JSON
        print(data)
        print('ok')
        return jsonify({"result":"ok"})  # Отправить данные обратно в ответе

if __name__ == '__main__':
    app.run(debug=True)
