from confluent_kafka import Producer, Consumer, KafkaError
import json
from sqlalchemy.orm import Session
from data_models import PlannedIncomesDB
from dependencies import SessionLocal
from settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
import redis

# Настройка Redis
redis_client = redis.from_url("redis://cache:6379/0", decode_responses=True)

# Kafka Producer
def get_kafka_producer():
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

# Kafka Consumer
def kafka_consumer_service():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "income-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([KAFKA_TOPIC])

    while True:
        msg = consumer.poll(1.0)  # Ожидание сообщений с таймаутом 1 секунда
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Ошибка Kafka: {msg.error()}")
                break

        # Обработка сообщения
        incomes = json.loads(msg.value().decode("utf-8"))
        db = SessionLocal()
        try:
            db_incomes = PlannedIncomesDB(**incomes)
            db.add(db_incomes)
            db.commit()
            db.refresh(db_incomes)

            # Обновление кеша
            cache_key = f"incomes:user_id:{incomes['user_id']}"
            incomes = db.query(PlannedIncomesDB).filter(PlannedIncomesDB.user_id == incomes['user_id']).all()
            redis_client.set(cache_key, json.dumps([income.dict() for income in incomes]))
        finally:
            db.close()

    consumer.close()