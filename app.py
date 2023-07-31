from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_reservations.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)

# Definir o modelo de dados
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    num_pessoas = db.Column(db.Integer, nullable=False)

class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    num_disponiveis = db.Column(db.Integer, nullable=False)

# Definir esquemas de serialização com Marshmallow
class ReservaEsquema(ma.Schema):
    class Meta:
        fields = ('id', 'data', 'horario', 'num_pessoas')

reserva_esquema = ReservaEsquema()
reservas_esquema = ReservaEsquema(many=True)

class MesaEsquema(ma.Schema):
    class Meta:
        fields = ('id', 'data', 'horario', 'num_disponiveis')

mesa_esquema = MesaEsquema()
mesas_esquema = MesaEsquema(many=True)

# Rota para listar todas as mesas disponíveis
@app.route('/mesas', methods=['GET'])
def listar_mesas():
    mesas = Mesa.query.all()
    return jsonify(mesas_esquema.dump(mesas)), 200

# Rota para fazer uma reserva
@app.route('/reservas', methods=['POST'])
def fazer_reserva():
    data = request.json.get('data')
    horario = request.json.get('horario')
    num_pessoas = request.json.get('num_pessoas')

    if not data or not horario or not num_pessoas:
        return jsonify({'error': 'Dados de reserva incompletos.'}), 400

    mesa = Mesa.query.filter_by(data=data, horario=horario).first()

    if not mesa:
        return jsonify({'error': 'Data ou horário inválido.'}), 400
    
    # Verificar se já existe uma reserva com os mesmos dados de data e horário
    reserva_existente = Reserva.query.filter_by(data=data, horario=horario).first()

    if reserva_existente:
        return jsonify({'error': 'Já existe uma reserva para esta data e horário.'}), 409

    if mesa.num_disponiveis < num_pessoas:
        return jsonify({'error': 'Não há mesas disponíveis para o número de pessoas informado.'}), 409

    mesa.num_disponiveis -= num_pessoas
    db.session.add(Reserva(data=data, horario=horario, num_pessoas=num_pessoas))
    db.session.commit()
    return jsonify({'message': 'Reserva feita com sucesso.'}), 200

# Rota para verificar disponibilidade de mesas para uma data e horário específicos
@app.route('/mesas_disponiveis', methods=['GET'])
def verificar_mesas_disponiveis():
    data = request.args.get('data')
    horario = request.args.get('horario')

    if not data or not horario:
        return jsonify({'error': 'Dados de data e horário são necessários para verificar a disponibilidade das mesas.'}), 400

    mesa = Mesa.query.filter_by(data=data, horario=horario).first()

    if not mesa:
        return jsonify({'error': 'Data ou horário inválido.'}), 400

    return jsonify({'mesas_disponiveis': mesa.num_disponiveis}), 200

# Rota para cancelar uma reserva
@app.route('/reservas/<int:reserva_id>', methods=['DELETE'])
def cancelar_reserva(reserva_id):
    print(f"Cancelando reserva com ID: {reserva_id}")
    reserva = Reserva.query.get(reserva_id)

    if not reserva:
        return jsonify({'error': 'Reserva não encontrada.'}), 404

    mesa = Mesa.query.filter_by(data=reserva.data, horario=reserva.horario).first()
    mesa.num_disponiveis += reserva.num_pessoas

    db.session.delete(reserva)
    db.session.commit()
    return jsonify({'message': 'Reserva cancelada com sucesso.'}), 200

# Rota para visualizar as reservas passadas
@app.route('/reservas', methods=['GET'])
def visualizar_reservas():
    reservas = Reserva.query.all()
    return jsonify(reservas_esquema.dump(reservas)), 200

if __name__ == '__main__':
    with app.app_context():  # Configurar o contexto de aplicativo aqui
        db.create_all()

        # Criar todas as mesas disponíveis em cada data e horário possível
        datas_possiveis = ['27/07/2023', '28/07/2023']  # Adicione mais datas se necessário
        horarios_possiveis = ['11:00', '12:00', '13:00', '14:00', '18:00', '19:00', '20:00']

        for data in datas_possiveis:
            for horario in horarios_possiveis:
                db.session.add(Mesa(data=data, horario=horario, num_disponiveis=10))  # Número inicial de mesas disponíveis
        db.session.commit()

    app.run(debug=True)