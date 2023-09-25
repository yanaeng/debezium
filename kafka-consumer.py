from confluent_kafka import Consumer, KafkaError
from pymongo import MongoClient
import json

consumer = Consumer({
    'bootstrap.servers': '192.168.1.64:9092',
    'group.id': 'streamer',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
})


def consume(consumer, timeout):
    while True:
        message = consumer.poll(timeout)

        if message is None:
            continue
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(message.error())
                break

        yield message
    consumer.close()


def consume_to_lake():
    consumer.subscribe(['postgres.public.data'])

    mongo_client = MongoClient("mongodb://localhost:27017/")
    mongo_db = mongo_client['poc_datalake']
    mongo_collection = mongo_db['point_transactions']

    for msg in consume(consumer, 1.0):
        if msg.value() is not None:
            try:
                payload = json.loads(msg.value().decode('utf-8'))['payload']

                # Check if the payload is empty before processing
                if payload:
                    data = {"offset": msg.offset(
                    ), "message": payload['after'], "operation": payload['op']}
                    mongo_collection.insert_one(data)
                    print('Message offset: {} loaded!'.format(msg.offset()))
                else:
                    print('Empty payload, skipping message with offset: {}'.format(
                        msg.offset()))
            except (KeyError, ValueError) as e:
                print('Error parsing JSON or extracting payload from message with offset {}: {}'.format(
                    msg.offset(), e))
        else:
            print('No value associated with message with offset: {}'.format(
                msg.offset()))


consume_to_lake()
