# Importar las librerias
import datetime
import hashlib
import json
from urllib import request

from flask import Flask, jsonify
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Parte 1 - Crear la cadena de bloques
class Blockchain:
    def _init_(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }

        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof * 2 - previous_proof * 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof * 2 - previous_proof * 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    # Emisor, receptor y la cantidad
    def add_transaction(self, sender, recipient, amount):
        self.transactions.append(
            {
                'sender': sender,
                'recipient': recipient,
                'amount': amount
            }
        )
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Parte 2 - Minado de un Bloque de la Cadena
# Crear una aplicación web
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Crear la dirección del nodo en el puerto 5000
node_address = str(uuid4()).replace('-', '')

# Crear una Blockchain
blockchain = Blockchain()


# Minar un nuevo bloque
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, recipient=node_address, amount=10)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Enhorabuena, has minado un nuevo bloque!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


# Obtener la cadena de bloques al completo
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'Chain is valid'}
    else:
        response = {'message': 'Chain is invalid'}
    return jsonify(response), 200


#Añadir una nuva transacción a la cadena de bloques
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        response = {'message': 'Faltan algunos elemenost de la transacción'}


#Parte 3 - Descentralizar la Cadena de bloques

#Conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return  'No hay nodos para añadir', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'Todos los nodos han sido conectado. La cadena de MJcoins contiene ahora los nodos siguientes: ',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# Reemplazar la cadena por la más larga (si es necesario)
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'Los nodos tenían diferentes cadenas, que han sido todas reemplazadas por la más larga.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message' : 'Todo correcto. La cadena en todos los nodos ya es la más larga.',
                    'actual_chain' : blockchain.chain}
    return jsonify(response), 200


# Ejecutar la app
app.run(host='0.0.0.0', port=5000)
