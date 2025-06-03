db = db.getSiblingDB('dva');

db.createCollection('requests', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id", "vlaId", "data", "attesterID", "callbackURL", "mapping"],
      properties: {
        "id": { "bsonType": "string" },
        "vlaId": { "bsonType": "string" },
        "data": { "bsonType": "binData" },
        "attesterID": { "bsonType": "string" },
        "callbackURL": { "bsonType": "string" },
        "mapping": { "bsonType": "object" }
      }
    }
  }
});

