from kafka.errors import AuthenticationFailedError, MessageSizeTooLargeError, UnknownTopicOrPartitionError, KafkaError, NoBrokersAvailable, TopicAuthorizationFailedError # type: ignore
from flask import Flask, request, jsonify # type: ignore
from kafka import KafkaProducer # type: ignore
from CustomLogger import CustomLogger
import json
import copy
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
        "request_timeout_ms":120000,
        "ssl_check_hostname":False,
        # "ssl_cafile":"CARoot.pem",
        "max_in_flight_requests_per_connection": 50,
        "compression_type":"gzip",
        # "batch_size": 100000,
        "linger_ms": 100,
        "retries":sys.maxsize,
        "acks":"all"
    }
    # logger.debug(producer_config)
    
    if message_type == 'json':
        producer_config["value_serializer"] = lambda v: json.dumps(v).encode('utf-8')

    return_message = jsonify({'message': 'Data sent to Kafka successfully'}), 201
    i=0
    kafka_producer: KafkaProducer= None
    
    queue = copy.deepcopy(message)
    kafka_producer = init_broker(producer_config)
    while i<=5:
        try:
            i+=1
            while queue:
                if message_type == 'string':
                    kafka_producer.send(topic, value=queue.pop(0).encode('utf-8'))
                elif message_type == 'json':
                    kafka_producer.send(topic, value=queue.pop(0))
            # for _ in message:
                # if message_type == 'string':
                #     kafka_producer.send(topic, value=_.encode('utf-8'))
                # elif message_type == 'json':
                #     kafka_producer.send(topic, value=_)
                else:
                    return jsonify({'error': 'Invalid message type'}), 400
            kafka_producer.flush()
            
            log_message = json.dumps(message)
            if len(log_message) > 40:
                logger.info(f"Successfuly sent message {json.dumps(message)[:40]}... to {topic}")
            else:
                logger.info(f"Successfuly sent message {message} to {topic}")
                
            break
        except AuthenticationFailedError as e:
            logger.error(e)
            return_message = jsonify({'error': 'Invalid Kafka authentication: ' + str(e)}), 401
        except MessageSizeTooLargeError as e:
            logger.error(e)
            return_message = jsonify({'error': 'Message size too large: ' + str(e)}), 413
        except UnknownTopicOrPartitionError as e:
            logger.error(e)
            return_message = jsonify({'error': 'Unknown topic or partition: ' + str(e)}), 404
        except TopicAuthorizationFailedError as e:
            logger.error(e)
            return_message = jsonify({'error': 'Topic Authorization Error, Check your kafka config: ' + str(e)}), 404
        except NoBrokersAvailable as e:
            logger.error(e)
            return_message = jsonify({'error': 'Check your kafka url, username, password config: ' + str(e)}), 404
        except KafkaError as e:
            logger.error(e)
            return_message = jsonify({'error': 'Failed to send message to Kafka: ' + str(e)}), 500

    if kafka_producer:
        kafka_producer.close()
    return return_message

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
    if message_type not in ['string', 'json']:
        return jsonify({'error': "Invalid message type! Must be either 'string' or 'json'"}), 400
    
    if not message:
        return jsonify({'error': 'Invalid request body! No "data"'}), 400
    if not isinstance(message, list):
        return jsonify({'error': 'Invalid data format! Must be a list(array)!'}), 400
    return False
    
def init_broker(producer_config):
    return KafkaProducer(**producer_config)
    
# development purpose only
# if __name__ == '__main__':
#     app.run(debug=True)

# production
if __name__ == "__main__":
    from waitress import serve # type: ignore
    serve(app, host="0.0.0.0", port=8080, threads=50)