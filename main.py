from kafka.errors import AuthenticationFailedError, MessageSizeTooLargeError, UnknownTopicOrPartitionError, KafkaError # type: ignore
from flask import Flask, request, jsonify # type: ignore
from kafka import KafkaProducer # type: ignore
from CustomLogger import CustomLogger
import json
import sys
import os

logger = CustomLogger()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB

@app.route('/produce_to_kafka', methods=['POST'])
def receive_data():
    data = request.get_json()
    kafka_config = data.get('kafka_config')
    metadata = data.get('metadata')
    message = data.get('data')

    validation = body_validation(data)
    if validation:
        return validation
    
    bootstrap_servers = kafka_config.get('bootstrap_servers')
    username = kafka_config.get('username')
    password = kafka_config.get('password')
    topic = kafka_config.get('topic')
    message_type = metadata.get('message_type').lower()

    producer_config = {
        "bootstrap_servers":bootstrap_servers,
        "sasl_mechanism":'PLAIN',
        "sasl_plain_username":username,
        "sasl_plain_password":password,
        "security_protocol":'SASL_SSL',
        "max_request_size":104857600,  # 100MB
        "request_timeout_ms":60000,
        "ssl_check_hostname":False,
        # "ssl_cafile":"CARoot.pem",
        "compression_type":"gzip",
        "retries":sys.maxsize,
        "acks":"all"
    }
    # logger.debug(producer_config)
    
    if message_type == 'json':
        producer_config["value_serializer"] = lambda v: json.dumps(v).encode('utf-8')

    kafka_producer = KafkaProducer(**producer_config)  

    try:
        for _ in message:
            if message_type == 'string':
                kafka_producer.send(topic, value=_.encode('utf-8'))
            elif message_type == 'json':
                kafka_producer.send(topic, value=_)
            else:
                return jsonify({'error': 'Invalid message type'}), 400
        kafka_producer.flush()
        logger.info(f"Successfuly sent message {message} to {topic}")
        return jsonify({'message': 'Data sent to Kafka successfully'}), 201
    except AuthenticationFailedError as e:
        logger.error(e)
        return jsonify({'error': 'Invalid Kafka authentication: ' + str(e)}), 401
    except MessageSizeTooLargeError as e:
        logger.error(e)
        return jsonify({'error': 'Message size too large: ' + str(e)}), 413
    except UnknownTopicOrPartitionError as e:
        logger.error(e)
        return jsonify({'error': 'Unknown topic or partition: ' + str(e)}), 404
    except KafkaError as e:
        logger.error(e)
        return jsonify({'error': 'Failed to send message to Kafka: ' + str(e)}), 500

def body_validation(data):
    kafka_config = data.get('kafka_config')
    metadata = data.get('metadata')
    message = data.get('data')
    
    if not kafka_config:
        return jsonify({'error': 'Invalid request body! No "kafka_config"'}), 400
    
    bootstrap_servers = kafka_config.get('bootstrap_servers')
    username = kafka_config.get('username')
    password = kafka_config.get('password')
    topic = kafka_config.get('topic')
    if not bootstrap_servers:
        return jsonify({'error': 'Invalid request body! No "bootstrap_servers"'}), 400
    if not username:
        return jsonify({'error': 'Invalid request body! No "username"'}), 400
    if not password:
        return jsonify({'error': 'Invalid request body! No "password"'}), 400
    if not topic:
        return jsonify({'error': 'Invalid request body! No "topic"'}), 400
    
    if not metadata :
        return jsonify({'error': 'Invalid request body! No "metadata"'}), 400
    
    message_type = metadata.get('message_type').lower()
    if not message_type:
        return jsonify({'error': 'Invalid message type! Must be either string or json'}), 400
    
    if not message:
        return jsonify({'error': 'Invalid request body! No "data"'}), 400
    if not isinstance(message, list):
        return jsonify({'error': 'Invalid data format! Must be a list(array)!'}), 400
    return False
    
# development purpose only
# if __name__ == '__main__':
#     app.run(debug=True)

# production
if __name__ == "__main__":
    from waitress import serve # type: ignore
    serve(app, host="0.0.0.0", port=8080, threads=200)