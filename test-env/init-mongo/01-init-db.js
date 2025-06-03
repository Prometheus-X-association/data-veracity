db = db.getSiblingDB('dva');

db.createCollection('requests', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id", "contract", "data", "attesterID", "callbackURL", "mapping"],
      properties: {
        "id": { "bsonType": "string" },
        "contract": { "bsonType": "object" },
        "data": { "bsonType": "binData" },
        "attesterID": { "bsonType": "string" },
        "callbackURL": { "bsonType": "string" },
        "mapping": { "bsonType": "object" }
      }
    }
  }
});

